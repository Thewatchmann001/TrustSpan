from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import timedelta, datetime
from app.db.session import get_db
from app.db.models import User, UserRole
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.config import settings
from app.core.exceptions import InvalidCredentials, UserNotFound
from app.core.dependencies import get_current_user, require_role
from app.utils.logger import logger
from app.utils.validation import (
    validate_email, validate_password_strength, validate_role,
    PASSWORD_MIN_LENGTH
)

router = APIRouter(prefix="/api/users", tags=["users"])


class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: UserRole
    wallet_address: Optional[str] = None
    university: Optional[str] = None  # Required for job seekers
    company_name: Optional[str] = None  # Required for startups
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format and check for disposable domains."""
        is_valid, error_msg = validate_email(v, check_disposable=True)
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower().strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, suggestions = validate_password_strength(v)
        if not is_valid:
            error_msg = "Password does not meet requirements: " + "; ".join(suggestions)
            raise ValueError(error_msg)
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role against whitelist."""
        if isinstance(v, UserRole):
            v = v.value
        is_valid, error_msg = validate_role(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: Optional[UserRole] = None  # Role selection for role-based login
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format."""
        is_valid, error_msg = validate_email(v, check_disposable=False)  # Don't check disposable on login
        if not is_valid:
            raise ValueError(error_msg)
        return v.lower().strip()


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
    verified_on_chain: Optional[str] = "pending"
    created_at: Optional[str] = None
    access_token: Optional[str] = None  # Included for Privy sync and login responses

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
    """
    Register a new user with comprehensive validation.
    
    Validates:
    - Email format and uniqueness
    - Password strength (8+ chars, uppercase, lowercase, number, special char)
    - Role whitelist
    - Role-specific requirements (university for job seekers, company for startups)
    """
    logger.info(f"Registering user: {user_data.email}")
    
    # Backend email validation (re-validate even though Pydantic validates)
    is_valid, error_msg = validate_email(user_data.email, check_disposable=True)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Backend password validation (re-validate even though Pydantic validates)
    is_valid, suggestions = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet requirements: " + "; ".join(suggestions)
        )
    
    # Validate role whitelist (backend validation)
    is_valid, error_msg = validate_role(user_data.role.value if isinstance(user_data.role, UserRole) else user_data.role)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
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
    
    # Create user with auth_provider = 'local'
    hashed_password = get_password_hash(user_data.password)
    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        wallet_address=wallet_address,
        university=user_data.university if user_data.role == UserRole.JOB_SEEKER else None,
        company_name=user_data.company_name if user_data.role == UserRole.STARTUP else None,
        verified_on_chain=verified_on_chain,
        auth_provider="local",  # Local authentication
        failed_login_attempts=0
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
    """
    Login user with role-based authentication.
    
    Validates:
    - Email and password
    - Selected role matches user's stored role
    - Account is not locked
    - OAuth users cannot login with password
    """
    logger.info(f"Login attempt: {credentials.email}, role: {credentials.role}")
    
    user = db.query(User).filter(User.email == credentials.email).first()
    
    # Check if user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if account is locked
    if user.locked_until and user.locked_until > datetime.utcnow():
        remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"Account is locked. Please try again in {remaining_minutes} minutes."
        )
    
    # Check if OAuth user trying to login with password
    if user.auth_provider != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Please sign in with {user.auth_provider.title()}. This account was created using social authentication."
        )
    
    # Verify password
    if not user.hashed_password or not verify_password(credentials.password, user.hashed_password):
        # Increment failed login attempts
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        
        # Lock account after 5 failed attempts
        MAX_ATTEMPTS = 5
        LOCKOUT_MINUTES = 30
        if user.failed_login_attempts >= MAX_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            logger.warning(f"Account locked for user {user.id} after {user.failed_login_attempts} failed attempts")
        
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # ROLE-BASED AUTHENTICATION: Validate selected role matches user's role
    if credentials.role:
        selected_role = credentials.role.value if isinstance(credentials.role, UserRole) else credentials.role
        user_role = user.role.value if isinstance(user.role, UserRole) else user.role
        
        if selected_role != user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You are not authorized to sign in as {selected_role}. Your role is {user_role}."
            )
    
    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token with role
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in: {user.id}, role: {user.role.value}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value
    }


@router.post("/privy/sync", response_model=UserResponse)
async def sync_privy_user(privy_data: PrivyUserSync, db: Session = Depends(get_db)):
    """Sync Privy user with backend database. Creates user if doesn't exist, updates if exists."""
    try:
        logger.info(f"Syncing Privy user: {privy_data.email} (Privy ID: {privy_data.privy_id})")
        logger.info(f"Privy sync data: role={privy_data.role}, university={privy_data.university}, company_name={privy_data.company_name}")
    except Exception as e:
        logger.error(f"Error in sync_privy_user: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid request data: {str(e)}"
        )
    
    # Check if user exists by email
    user = db.query(User).filter(User.email == privy_data.email).first()
    
    if user:
        # ROLE ENFORCEMENT: Existing user's role is authoritative
        # If a different role is requested, reject or use existing role
        if privy_data.role and privy_data.role != user.role:
            # Normalize role names for comparison
            def normalize_role(r):
                if r == UserRole.FOUNDER or r == UserRole.STARTUP:
                    return 'startup'
                if r == UserRole.JOB_SEEKER or r == UserRole.STUDENT:
                    return 'student'
                return r.value if hasattr(r, 'value') else str(r)
            
            existing_normalized = normalize_role(user.role)
            requested_normalized = normalize_role(privy_data.role)
            
            if existing_normalized != requested_normalized:
                # Map role values to user-friendly names
                role_display_names = {
                    'founder': 'Startup',
                    'startup': 'Startup',
                    'student': 'Job Seeker',
                    'investor': 'Investor'
                }
                existing_display = role_display_names.get(user.role.value, user.role.value)
                requested_display = role_display_names.get(privy_data.role.value if hasattr(privy_data.role, 'value') else str(privy_data.role), str(privy_data.role))
                
                logger.warning(
                    f"Role mismatch for user {user.id}: existing={user.role.value}, requested={privy_data.role}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This email is registered as {existing_display}. Please select '{existing_display}' from the role dropdown to sign in, or use a different email address."
                )
        
        # Update existing user with Privy data (but keep existing role)
        if privy_data.full_name:
            user.full_name = privy_data.full_name
        if privy_data.wallet_address:
            from app.utils.helpers import validate_solana_address
            wallet_addr = privy_data.wallet_address.strip()
            if wallet_addr and validate_solana_address(wallet_addr):
                user.wallet_address = wallet_addr
        # DO NOT update role for existing users - it's authoritative
        if privy_data.university and user.role == UserRole.JOB_SEEKER:
            user.university = privy_data.university
        if privy_data.company_name and user.role == UserRole.STARTUP:
            user.company_name = privy_data.company_name
        
        db.commit()
        db.refresh(user)
        logger.info(f"Updated existing user from Privy: {user.id} (role: {user.role.value})")
    else:
        # Create new user from Privy
        # Default role to investor if not provided
        role = privy_data.role or UserRole.INVESTOR
        
        # For Privy signups, make role-specific fields optional
        # Users can fill in these details later in their profile
        # Only validate if they're explicitly provided (not empty strings)
        if role == UserRole.JOB_SEEKER:
            # University is optional for Privy signups - can be set later
            pass
        
        if role == UserRole.STARTUP or role == UserRole.FOUNDER:
            # Company name is optional for Privy signups - can be set later
            pass
        
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
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.
    
    Users can only view their own profile unless they are an admin.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound(user_id)
    
    # Users can only view their own profile unless they are admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user information.
    
    Users can only update their own profile unless they are an admin.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound(user_id)
    
    # Users can only update their own profile unless they are admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user and all related data (handles foreign key constraints).
    
    Users can only delete their own account unless they are an admin.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UserNotFound(user_id)
    
    # Users can only delete their own account unless they are admin
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own account"
        )
    
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

