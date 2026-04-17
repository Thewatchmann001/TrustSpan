from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.db.models import User, UserRole
from app.core.security import decode_access_token
from app.services.user_capabilities import user_has_capability

# Privy is the only auth method. OAuth2 token URL is the sync endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/privy/sync", auto_error=False)

def _effective_role(user: User, payload: dict, db: Session) -> str:
    """Resolve effective role for unified account."""
    primary = user.role.value if hasattr(user.role, "value") else str(user.role)
    active = payload.get("active_role")
    if not active:
        return primary
    if user_has_capability(db, user, active):
        return active
    return primary

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user.
    If no token is provided, returns the superadmin as a fallback
    (satisfying 'remove any auth constraint' if Privy is not set/used).
    """
    if not token:
        # Fallback to superadmin to allow access if auth is not enforced
        admin = db.query(User).filter(User.email == "josephemsamah@gmail.com").first()
        if admin:
            # Set effective_role on the admin user object
            setattr(admin, "effective_role", admin.role.value if hasattr(admin.role, "value") else str(admin.role))
            return admin
        return None

    payload = decode_access_token(token)
    if payload is None:
        return None
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return None
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        return None
    
    # Unified account: set effective_role
    effective = _effective_role(user, payload, db)
    setattr(user, "effective_role", effective)
    
    return user

def require_role(allowed_roles: list):
    """Dependency factory for role-based access control."""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")

        role = getattr(current_user, "effective_role", None) or (
            current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        )

        # Normalize
        if role == "startup": role = "founder"
        allowed_normalized = [r if r != "startup" else "founder" for r in allowed_roles]

        # Superadmin bypass
        if current_user.email == "josephemsamah@gmail.com":
            return current_user

        if role not in allowed_normalized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user
    return role_checker
