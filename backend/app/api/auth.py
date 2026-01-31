"""
OAuth Authentication Endpoints
Handles Google OAuth 2.0 authentication flow
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
import requests
from urllib.parse import urlencode
import secrets

from app.db.session import get_db
from app.db.models import User, UserRole
from app.core.security import create_access_token
from app.core.config import settings
from app.utils.logger import logger
from app.utils.validation import validate_email

router = APIRouter(prefix="/api/auth", tags=["auth"])


def generate_state_token() -> str:
    """Generate a secure random state token for OAuth."""
    return secrets.token_urlsafe(32)


@router.get("/oauth/google")
async def google_oauth_initiate(request: Request, role: Optional[str] = None):
    """
    Initiate Google OAuth flow.
    
    Args:
        role: Optional role selection (student, founder, investor)
              If provided, will be used when creating new accounts
    
    Returns:
        Redirect to Google OAuth consent screen
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )
    
    # Generate state token for CSRF protection
    state_token = generate_state_token()
    
    # Store state and role in session (or use signed cookie)
    # For simplicity, we'll encode role in state token
    # In production, use proper session storage
    state_data = f"{state_token}:{role or ''}"
    
    # Google OAuth 2.0 authorization URL
    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state_data
    }
    
    auth_url = f"{google_auth_url}?{urlencode(params)}"
    logger.info(f"Google OAuth initiated, redirecting to: {auth_url[:100]}...")
    
    return RedirectResponse(url=auth_url)


@router.get("/oauth/google/callback")
async def google_oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    
    Flow:
    1. Exchange authorization code for access token
    2. Get user info from Google
    3. Create or link user account
    4. Generate JWT token
    5. Redirect to frontend with token
    """
    if error:
        logger.error(f"Google OAuth error: {error}")
        frontend_url = f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        return RedirectResponse(url=frontend_url)
    
    if not code:
        logger.error("Google OAuth callback missing authorization code")
        frontend_url = f"{settings.FRONTEND_URL}/login?error=missing_code"
        return RedirectResponse(url=frontend_url)
    
    # Extract role from state (if provided)
    selected_role = None
    if state:
        try:
            state_token, role = state.split(":", 1) if ":" in state else (state, "")
            selected_role = role if role else None
        except:
            pass
    
    try:
        logger.info(f"Processing Google OAuth callback with code: {code[:20]}..., state: {state}")
        
        # Step 1: Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }
        
        logger.info(f"Exchanging authorization code for access token...")
        token_response = requests.post(token_url, data=token_data, timeout=10)
        token_response.raise_for_status()
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        logger.info(f"Successfully obtained access token from Google")
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to obtain access token from Google"
            )
        
        # Step 2: Get user info from Google
        logger.info(f"Fetching user info from Google...")
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = requests.get(userinfo_url, headers=headers, timeout=10)
        userinfo_response.raise_for_status()
        google_user = userinfo_response.json()
        logger.info(f"Received user info from Google: email={google_user.get('email')}, name={google_user.get('name')}")
        
        google_email = google_user.get("email")
        google_name = google_user.get("name", google_user.get("given_name", ""))
        google_id = google_user.get("id")
        
        if not google_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google account email not available"
            )
        
        # Validate email format
        is_valid, error_msg = validate_email(google_email, check_disposable=False)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid email from Google: {error_msg}"
            )
        
        # Step 3: Check if user exists
        logger.info(f"Checking if user exists with email: {google_email}")
        existing_user = db.query(User).filter(User.email == google_email).first()
        
        if existing_user:
            logger.info(f"User exists: {existing_user.id}, role: {existing_user.role.value}, auth_provider: {existing_user.auth_provider}")
            # User exists - link Google account if not already linked
            if existing_user.auth_provider != "google":
                # Link Google account to existing user
                existing_user.auth_provider = "google"
                existing_user.provider_id = google_id
                db.commit()
                logger.info(f"Linked Google account to existing user: {existing_user.id}")
            
            user = existing_user
        else:
            # New user - create account
            # Use selected role or default to JOB_SEEKER
            default_role = UserRole.JOB_SEEKER
            if selected_role:
                try:
                    default_role = UserRole(selected_role)
                except ValueError:
                    logger.warning(f"Invalid role '{selected_role}' from OAuth, using default")
            
            user = User(
                full_name=google_name or google_email.split("@")[0],
                email=google_email,
                hashed_password=None,  # OAuth users don't have passwords
                role=default_role,
                auth_provider="google",
                provider_id=google_id,
                wallet_address=None,
                failed_login_attempts=0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user from Google OAuth: {user.id}")
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Step 4: Generate JWT token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        jwt_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role.value
            },
            expires_delta=access_token_expires
        )
        
        # Step 5: Redirect to frontend with token
        # Store token in URL hash (more secure than query param)
        # Frontend will extract it and store in localStorage
        frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={jwt_token}&user_id={user.id}&role={user.role.value}"
        logger.info(f"✅ Google OAuth successful for user {user.id} (email: {user.email}, role: {user.role.value})")
        logger.info(f"Redirecting to frontend: {frontend_url[:100]}...")
        
        return RedirectResponse(url=frontend_url)
        
    except requests.RequestException as e:
        logger.error(f"Google OAuth API error: {str(e)}")
        frontend_url = f"{settings.FRONTEND_URL}/login?error=oauth_api_error"
        return RedirectResponse(url=frontend_url)
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}", exc_info=True)
        frontend_url = f"{settings.FRONTEND_URL}/login?error=oauth_error"
        return RedirectResponse(url=frontend_url)
