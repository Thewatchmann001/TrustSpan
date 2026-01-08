from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
from app.db.session import get_db
from app.db.models import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.config import settings
from app.core.exceptions import InvalidCredentials, UserNotFound
from app.utils.logger import logger

router = APIRouter(prefix="/api/users", tags=["users"])


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole
    wallet_address: Optional[str] = None
    university: Optional[str] = None  # Required for job seekers
    company_name: Optional[str] = None  # Required for startups


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    wallet_address: Optional[str] = None
    university: Optional[str] = None
    company_name: Optional[str] = None
    verified_on_chain: str = "pending"
    created_at: str

    class Config:
        from_attributes = True


class PrivyUserSync(BaseModel):
    """Sync Privy user with backend."""
    privy_id: str
    email: EmailStr
    full_name: Optional[str] = None
    wallet_address: Optional[str] = None
    role: Optional[UserRole] = None
    university: Optional[str] = None
    company_name: Optional[str] = None


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user."""
    logger.info(f"Registering user: {user_data.email}")
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate: Job seekers must provide university
    if user_data.role == UserRole.JOB_SEEKER and not user_data.university:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="University is required for job seekers"
        )
    
    # Validate: Startups must provide company name
    if user_data.role == UserRole.STARTUP and not user_data.company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name is required for startups"
        )
    
    # On-chain verification removed - not part of core solutions
    verified_on_chain = "pending"
    
    # Convert empty wallet_address to None to avoid unique constraint violations
    if user_data.wallet_address:
        wallet_address = user_data.wallet_address.strip() if user_data.wallet_address.strip() else None
    else:
        wallet_address = None
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        wallet_address=wallet_address,
        university=user_data.university if user_data.role == UserRole.JOB_SEEKER else None,
        company_name=user_data.company_name if user_data.role == UserRole.STARTUP else None,
        verified_on_chain=verified_on_chain
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"User registered: {user.id}, verified_on_chain: {verified_on_chain}")
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "wallet_address": user.wallet_address,
        "university": user.university or "",
        "company_name": user.company_name or "",
        "verified_on_chain": user.verified_on_chain or "pending",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.post("/login", response_model=TokenResponse)
async def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token."""
    logger.info(f"Login attempt: {credentials.email}")
    
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise InvalidCredentials()
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.id}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value
    }


@router.post("/privy/sync", response_model=UserResponse)
async def sync_privy_user(privy_data: PrivyUserSync, db: Session = Depends(get_db)):
    """Sync Privy user with backend database. Creates user if doesn't exist, updates if exists."""
    logger.info(f"Syncing Privy user: {privy_data.email} (Privy ID: {privy_data.privy_id})")
    
    # Check if user exists by email
    user = db.query(User).filter(User.email == privy_data.email).first()
    
    if user:
        # Update existing user with Privy data
        if privy_data.full_name:
            user.full_name = privy_data.full_name
        if privy_data.wallet_address:
            from app.utils.helpers import validate_solana_address
            wallet_addr = privy_data.wallet_address.strip()
            if wallet_addr and validate_solana_address(wallet_addr):
                user.wallet_address = wallet_addr
        if privy_data.role:
            user.role = privy_data.role
        if privy_data.university and user.role == UserRole.JOB_SEEKER:
            user.university = privy_data.university
        if privy_data.company_name and user.role == UserRole.STARTUP:
            user.company_name = privy_data.company_name
        
        db.commit()
        db.refresh(user)
        logger.info(f"Updated existing user from Privy: {user.id}")
    else:
        # Create new user from Privy
        # Default role to investor if not provided
        role = privy_data.role or UserRole.INVESTOR
        
        # Validate required fields based on role
        if role == UserRole.JOB_SEEKER and not privy_data.university:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="University is required for job seekers"
            )
        
        if role == UserRole.STARTUP and not privy_data.company_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name is required for startups"
            )
        
        # Convert empty wallet_address to None to avoid unique constraint violations
        wallet_address = None
        if privy_data.wallet_address:
            wallet_addr = privy_data.wallet_address.strip()
            if wallet_addr:
                from app.utils.helpers import validate_solana_address
                if validate_solana_address(wallet_addr):
                    wallet_address = wallet_addr
        
        # Create user without password (Privy handles authentication)
        user = User(
            full_name=privy_data.full_name or privy_data.email.split('@')[0],
            email=privy_data.email,
            hashed_password="privy_authenticated",  # Placeholder, Privy handles auth
            role=role,
            wallet_address=wallet_address,
            university=privy_data.university if role == UserRole.JOB_SEEKER else None,
            company_name=privy_data.company_name if role == UserRole.STARTUP else None,
            verified_on_chain="pending"
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user from Privy: {user.id}")
    
    # Create JWT token for backend API access
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "wallet_address": user.wallet_address,
        "university": user.university or "",
        "company_name": user.company_name or "",
        "verified_on_chain": user.verified_on_chain or "pending",
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "access_token": access_token,  # Include token in response
    }


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound(user_id)
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "wallet_address": user.wallet_address,
        "university": user.university or "",
        "company_name": user.company_name or "",
        "verified_on_chain": user.verified_on_chain or "pending",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


class UserUpdate(BaseModel):
    wallet_address: Optional[str] = None
    full_name: Optional[str] = None
    university: Optional[str] = None
    company_name: Optional[str] = None


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update user information."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound(user_id)
    
    # Validate wallet address if provided
    if user_data.wallet_address:
        wallet_addr = user_data.wallet_address.strip()
        if wallet_addr:  # Only validate if not empty after stripping
            from app.utils.helpers import validate_solana_address
            if not validate_solana_address(wallet_addr):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Solana wallet address format. Please provide a valid base58-encoded Solana address (32-44 characters)."
                )
            user.wallet_address = wallet_addr
        else:
            # Empty string means remove wallet address
            user.wallet_address = None
    
    if user_data.full_name:
        user.full_name = user_data.full_name
    
    if user_data.university and user.role == UserRole.JOB_SEEKER:
        user.university = user_data.university
    
    if user_data.company_name and user.role == UserRole.STARTUP:
        user.company_name = user_data.company_name
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User updated: {user.id}")
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role.value,
        "wallet_address": user.wallet_address,
        "university": user.university or "",
        "company_name": user.company_name or "",
        "verified_on_chain": user.verified_on_chain or "pending",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete a user and all related data (handles foreign key constraints)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound(user_id)
    
    logger.info(f"Deleting user {user_id} and related data")
    
    try:
        # Import models that have foreign keys to User
        from app.db.models import (
            CV, JobApplication, JobMatch, Investment, Startup
        )
        
        # Delete related records (in order to avoid foreign key violations)
        
        # 1. Delete CVs
        cvs = db.query(CV).filter(CV.user_id == user_id).all()
        for cv in cvs:
            db.delete(cv)
        logger.info(f"Deleted {len(cvs)} CV(s)")
        
        # 2. Delete job applications
        job_applications = db.query(JobApplication).filter(JobApplication.user_id == user_id).all()
        for application in job_applications:
            db.delete(application)
        logger.info(f"Deleted {len(job_applications)} job application(s)")
        
        # 3. Delete job matches
        job_matches = db.query(JobMatch).filter(JobMatch.user_id == user_id).all()
        for match in job_matches:
            db.delete(match)
        logger.info(f"Deleted {len(job_matches)} job match(es)")
        
        # 4. Delete investments
        investments = db.query(Investment).filter(Investment.investor_id == user_id).all()
        for investment in investments:
            db.delete(investment)
        logger.info(f"Deleted {len(investments)} investment(s)")
        
        # 5. Handle startups (delete or handle based on business logic)
        # For now, we'll delete startups if user is the founder
        # You might want to transfer ownership instead
        startups = db.query(Startup).filter(Startup.founder_id == user_id).all()
        for startup in startups:
            # Delete jobs associated with these startups
            from app.db.models import Job
            jobs = db.query(Job).filter(Job.startup_id == startup.id).all()
            for job in jobs:
                # Delete job matches and applications for these jobs
                job_matches_to_delete = db.query(JobMatch).filter(JobMatch.job_id == job.id).all()
                for match in job_matches_to_delete:
                    db.delete(match)
                job_apps_to_delete = db.query(JobApplication).filter(JobApplication.job_id == job.id).all()
                for app in job_apps_to_delete:
                    db.delete(app)
                db.delete(job)
            db.delete(startup)
        logger.info(f"Deleted {len(startups)} startup(s) and associated jobs")
        
        # 6. Finally, delete the user
        db.delete(user)
        db.commit()
        
        logger.info(f"Successfully deleted user {user_id}")
        return {
            "message": f"User {user_id} and all related data deleted successfully",
            "deleted": {
                "cvs": len(cvs),
                "job_applications": len(job_applications),
                "job_matches": len(job_matches),
                "investments": len(investments),
                "startups": len(startups),
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

