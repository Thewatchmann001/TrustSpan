from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
from app.core.security import decode_access_token
# UnauthorizedAccess removed - using HTTPException directly

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    
    Validates:
    - Token signature and expiration
    - User exists in database
    - User account is not locked
    - JWT payload includes role (for role validation)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # Check if account is locked
    from datetime import datetime
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is locked. Please try again in {remaining_minutes} minutes."
        )
    
    # Verify role in token matches user's role (prevent token tampering)
    token_role = payload.get("role")
    if token_role and user.role.value != token_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token role mismatch. Please login again."
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    return current_user


def require_role(allowed_roles: list):
    """
    Dependency factory for role-based access control.
    
    Usage:
        @router.get("/admin/users")
        async def get_users(
            current_user: User = Depends(require_role(["admin"]))
        ):
            ...
    
    Args:
        allowed_roles: List of role strings (e.g., ["admin", "investor"])
    
    Returns:
        Dependency that validates user role against allowed roles
    """
    async def role_checker(current_user: User = Depends(get_current_user)):
        user_role = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}, your role: {user_role}"
            )
        return current_user
    return role_checker


def get_current_user_role(payload: dict = None) -> str:
    """
    Extract role from JWT payload.
    
    This is a helper function to get role from token without database lookup.
    Used for logging and audit purposes.
    """
    if payload is None:
        return None
    
    return payload.get("role")

