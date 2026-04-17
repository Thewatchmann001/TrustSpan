from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import timedelta, datetime
from app.db.session import get_db
from app.db.models import User, UserRole, Startup
from app.core.security import create_access_token
from app.core.config import settings
from app.core.dependencies import get_current_user, require_role
from app.utils.logger import logger
from app.services.user_capabilities import get_user_capabilities, user_has_capability

router = APIRouter(prefix="/api/users", tags=["users"])

class PrivyUserSync(BaseModel):
    email: EmailStr
    privy_id: str
    full_name: Optional[str] = None
    wallet_address: Optional[str] = None
    role: Optional[UserRole] = None
    university: Optional[str] = None
    company_name: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    active_role: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None

@router.post("/privy/sync", response_model=UserResponse)
async def sync_privy_user(privy_data: PrivyUserSync, db: Session = Depends(get_db)):
    """Sync Privy user with backend database. Canonical auth method."""
    user = db.query(User).filter(User.email == privy_data.email).first()
    
    if user:
        active_role = user.role.value if hasattr(user.role, 'value') else str(user.role)
        if privy_data.role:
            requested = privy_data.role.value if hasattr(privy_data.role, 'value') else str(privy_data.role)
            if user_has_capability(db, user, requested):
                active_role = requested
        
        if privy_data.full_name: user.full_name = privy_data.full_name
        if privy_data.wallet_address: user.wallet_address = privy_data.wallet_address
        
        db.commit()
        db.refresh(user)
    else:
        role = privy_data.role or UserRole.INVESTOR
        user = User(
            full_name=privy_data.full_name or privy_data.email.split('@')[0],
            email=privy_data.email,
            hashed_password="privy_authenticated",
            role=role,
            wallet_address=privy_data.wallet_address,
            university=privy_data.university if role == UserRole.JOB_SEEKER else None,
            company_name=privy_data.company_name if role == UserRole.STARTUP else None
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        active_role = user.role.value if hasattr(user.role, 'value') else str(user.role)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value if hasattr(user.role, 'value') else str(user.role), "active_role": active_role},
        expires_delta=access_token_expires
    )
    
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "active_role": active_role,
        "capabilities": get_user_capabilities(db, user),
        "access_token": access_token
    }

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role),
        "active_role": getattr(current_user, "active_role", current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)),
        "capabilities": get_user_capabilities(db, current_user)
    }
