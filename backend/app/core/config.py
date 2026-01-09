from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://trustbridge:trustbridge@localhost:5432/trustbridgedb"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Solana
    SOLANA_RPC_URL: str = "https://api.devnet.solana.com"
    WALLET_PATH: str = "~/.config/solana/id.json"
    
    # Program IDs
    CERTIFICATE_PROGRAM_ID: str = "D7SYneSxju3iTtJW9HPQMVjQRXgTCZi2vR2UWRk8nTRa"
    STARTUP_PROGRAM_ID: str = "DqwhC5DDZZmL4E1f4YYQJ9R121NurZV8ttk2dfGoYnTj"
    INVESTMENT_PROGRAM_ID: str = "FEQJZDk4afcXbSrRj7iW3PieNtrmeT2Hjtt5BCmoNfRr"
    
    # Blockchain Scripts Path
    BLOCKCHAIN_SCRIPTS_PATH: str = "../blockchain/scripts"
    
    # AI Service
    OPENAI_API_KEY: Optional[str] = None  # Deprecated - use MISTRAL_API_KEY
    MISTRAL_API_KEY: Optional[str] = "GdIifsPZmtuRu16zlwFZpu4jXjxBOI0i"
    
    # Job Search APIs
    # RemoteOK: Free public API - no key needed!
    # We Work Remotely: Free public API - no key needed!
    # Freelancer.com: OAuth token required
    FREELANCER_OAUTH_TOKEN: Optional[str] = None
    FREELANCER_SANDBOX: bool = False  # Set to True for testing
    
    # Adzuna: Free tier (250 req/day) - get keys at https://developer.adzuna.com/
    ADZUNA_APP_ID: Optional[str] = None
    ADZUNA_API_KEY: Optional[str] = None
    
    # App
    APP_NAME: str = "TrustBridge API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    FRONTEND_URL: str = "http://localhost:3000"
    
    # File Uploads
    UPLOAD_DIR: str = "static/uploads"
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: list = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

