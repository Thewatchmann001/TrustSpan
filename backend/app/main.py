from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
from pathlib import Path as PathLib

# Add backend directory to path for imports
backend_dir = PathLib(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.utils.logger import logger
from app.api import users  # Keep users for authentication
from app.api import messages  # Chat/messaging API
from app.api.cv import router as cv_router
from app.api.employers import router as employers_router
from app.api.admin import router as admin_router
from app.api.websocket import manager
from app.core.exceptions import InvalidCredentials, UserNotFound, TrustSpanException
from app.core.middleware import RateLimitMiddleware, CSRFProtectionMiddleware
from routes import router as main_router  # New consolidated routes

# Removed: certificates, startups (old), jobs (old), cv (old), investments (old)
# All functionality moved to new modules in /backend/cv and /backend/investments

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Professional Career & Investment Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
# Note: When allow_credentials=True, cannot use wildcard "*" for allow_origins
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://0.0.0.0:3000",
]
if getattr(settings, "CORS_ORIGINS", None):
    origins.extend(x.strip() for x in settings.CORS_ORIGINS.split(",") if x.strip())
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security middleware (order matters: CSRF first, then rate limiting)
app.add_middleware(CSRFProtectionMiddleware)
app.add_middleware(RateLimitMiddleware)

# Include routers
app.include_router(users.router)  # Keep for authentication
app.include_router(messages.router)  # Chat/messaging
app.include_router(cv_router)
app.include_router(employers_router)
app.include_router(admin_router)
app.include_router(main_router)  # New consolidated routes for CV and Investments

# Mount static files for photo uploads
static_dir = Path(settings.UPLOAD_DIR).parent
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Exception handlers
@app.exception_handler(InvalidCredentials)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentials):
    """Handle invalid credentials exceptions."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Invalid email or password"}
    )


@app.exception_handler(UserNotFound)
async def user_not_found_handler(request: Request, exc: UserNotFound):
    """Handle user not found exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": f"User not found: {str(exc)}"}
    )


@app.exception_handler(TrustSpanException)
async def trustspan_exception_handler(request: Request, exc: TrustSpanException):
    """Handle general TrustSpan exceptions."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "TrustSpan API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/{conversation_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int, user_id: int):
    """WebSocket endpoint for real-time chat"""
    await manager.connect(websocket, conversation_id, user_id)
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            import json
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                
                # Handle different message types
                if message_data.get("type") == "ping":
                    # Respond to ping with pong
                    await websocket.send_json({"type": "pong"})
                elif message_data.get("type") == "typing":
                    # Broadcast typing indicator
                    await manager.broadcast_to_conversation(
                        {
                            "type": "typing",
                            "user_id": user_id,
                            "is_typing": message_data.get("is_typing", False)
                        },
                        conversation_id,
                        exclude_user_id=user_id
                    )
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from user {user_id}")
                
    except WebSocketDisconnect:
        manager.disconnect(conversation_id, user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        manager.disconnect(conversation_id, user_id)


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    logger.info("Shutting down TrustSpan API")

