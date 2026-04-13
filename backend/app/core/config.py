from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://trustspan:trustspan@localhost:5432/trustspandb"  # Override in .env for production
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"  # MUST be changed in .env for production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Solana
    SOLANA_RPC_URL: str = "https://api.devnet.solana.com"
    WALLET_PATH: str = "~/.config/solana/id.json"
    SOLANA_SIGNER_SECRET_KEY: Optional[str] = None  # Base58-encoded secret key for signing transactions
    
    # Devnet USDC Mint (test token - no real value)
    DEVNET_USDC_MINT: Optional[str] = None  # Set to your test mint address
    
    # Program IDs
    CERTIFICATE_PROGRAM_ID: str = "D7SYneSxju3iTtJW9HPQMVjQRXgTCZi2vR2UWRk8nTRa"
    STARTUP_PROGRAM_ID: str = "DqwhC5DDZZmL4E1f4YYQJ9R121NurZV8ttk2dfGoYnTj"
    INVESTMENT_PROGRAM_ID: str = "FEQJZDk4afcXbSrRj7iW3PieNtrmeT2Hjtt5BCmoNfRr"
    
    # Blockchain Scripts Path
    BLOCKCHAIN_SCRIPTS_PATH: str = "../blockchain/scripts"
    
    # AI Service
    OPENAI_API_KEY: Optional[str] = None  # Deprecated - use MISTRAL_API_KEY
    MISTRAL_API_KEY: Optional[str] = None  # Set in .env file - NEVER commit real keys!
    
    # Job Search APIs
    # RemoteOK: Free public API - no key needed!
    # We Work Remotely: Free public API - no key needed!
    # Freelancer.com: OAuth token required
    FREELANCER_OAUTH_TOKEN: Optional[str] = None  # Set in .env file
    FREELANCER_SANDBOX: bool = False  # Set to True for testing
    
    # Adzuna: Free tier (250 req/day) - get keys at https://developer.adzuna.com/
    ADZUNA_APP_ID: Optional[str] = None  # Set in .env file
    ADZUNA_API_KEY: Optional[str] = None  # Set in .env file
    
    # RapidAPI: For Y-Combinator Jobs and Internships
    RAPIDAPI_KEY: Optional[str] = None  # Set in .env file
    
    # App
    APP_NAME: str = "TrustSpan API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    
    # CORS: comma-separated extra origins for production (e.g. https://trustspan-frontend-xxx.run.app)
    CORS_ORIGINS: Optional[str] = None
    
    # Stripe (card payments: investor -> startup)
    STRIPE_SECRET_KEY: Optional[str] = None  # sk_test_... or sk_live_...
    STRIPE_WEBHOOK_SECRET: Optional[str] = None  # whsec_... for webhook signature verification
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None  # pk_test_... for frontend (optional)
    
    # File Uploads
    UPLOAD_DIR: str = "static/uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = None  # Set in .env file - NEVER commit real keys!
    GOOGLE_CLIENT_SECRET: Optional[str] = None  # Set in .env file - NEVER commit real keys!
    # Redirect URI - must match Google Cloud Console configuration
    # For local dev: http://localhost:8000/api/auth/oauth/google/callback
    # For production: https://yourdomain.com/api/auth/oauth/google/callback
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/oauth/google/callback"
    
    # LinkedIn OAuth (for future implementation)
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: Optional[str] = None
    
    # Facebook OAuth (for future implementation)
    FACEBOOK_APP_ID: Optional[str] = None
    FACEBOOK_APP_SECRET: Optional[str] = None
    FACEBOOK_REDIRECT_URI: Optional[str] = None
    
    # Security Settings
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    
    # Attestation Service Settings
    ATTESTATION_MODE: str = "development"  # "development" or "production"
    VERIFY_API_KEY: Optional[str] = None  # Verify.com API key
    VERIFY_API_URL: Optional[str] = None  # Verify.com API URL
    CIVIC_API_KEY: Optional[str] = None  # Civic API key
    CIVIC_API_URL: Optional[str] = None  # Civic API URL
    SAS_API_KEY: Optional[str] = None  # Solana Attestation Service API key
    SAS_API_URL: Optional[str] = "https://attest.solana.com"  # SAS API URL
    
    # Solana Attestation Flags
    USE_REAL_SOLANA: bool = True  # Use real Solana devnet transactions (default: true for devnet testing)
    USE_REAL_VERIFIERS: bool = False  # Use real Civic/Verify APIs (default: false, keep mocked)
    SOLANA_CLUSTER: str = "devnet"  # "devnet" or "mainnet" (mainnet NOT allowed in dev mode)
    # SOLANA_RPC_URL already defined above
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

