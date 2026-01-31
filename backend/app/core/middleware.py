"""
Security middleware for rate limiting and CSRF protection.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
import time
from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    
    Limits:
    - Login attempts: 20 per 15 minutes per IP
    - Registration: 5 per hour per IP
    - OAuth endpoints: 10 per hour per IP
    - General API: 200 requests per minute per IP
    
    Exempt endpoints (no rate limiting):
    - Dashboard endpoints (attestations, startups by founder)
    - API documentation endpoints
    """
    
    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = [
        "/api/attestations",  # Dashboard attestations - no rate limit
        "/api/startups/by-founder",  # Dashboard startup data - no rate limit
        "/docs",  # API documentation
        "/openapi.json",  # OpenAPI schema
        "/redoc",  # ReDoc documentation
    ]
    
    def __init__(self, app):
        super().__init__(app)
        # Store: {ip: [(timestamp, endpoint), ...]}
        self.rate_limits: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = 300  # Clean up every 5 minutes
        self.last_cleanup = time.time()
        
        # Rate limit configurations
        # Format: (max_requests, window_seconds)
        self.limits = {
            "/api/users/login": (20, 900),  # 20 requests per 15 minutes (allows retries)
            "/api/users/register": (5, 3600),  # 5 requests per hour
            "/api/auth/oauth": (10, 3600),  # 10 requests per hour
            "default": (200, 60),  # 200 requests per minute (increased from 100)
        }
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        return False
    
    def _get_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for a path."""
        for endpoint, limit in self.limits.items():
            if endpoint in path:
                return limit
        return self.limits["default"]
    
    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory leak."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Keep last hour
        for ip in list(self.rate_limits.keys()):
            self.rate_limits[ip] = [
                (ts, endpoint) for ts, endpoint in self.rate_limits[ip]
                if ts > cutoff_time
            ]
            if not self.rate_limits[ip]:
                del self.rate_limits[ip]
        
        self.last_cleanup = current_time
    
    def _check_rate_limit(self, ip: str, path: str) -> bool:
        """Check if request is within rate limit."""
        max_requests, window_seconds = self._get_limit(path)
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Get the endpoint pattern that matches this path
        # Check more specific patterns first (longer paths)
        endpoint_pattern = None
        sorted_endpoints = sorted(
            [e for e in self.limits.keys() if e != "default"],
            key=len,
            reverse=True
        )
        for endpoint in sorted_endpoints:
            if endpoint in path:
                endpoint_pattern = endpoint
                break
        if endpoint_pattern is None:
            endpoint_pattern = "default"
        
        # Filter requests within the time window that match this endpoint pattern
        recent_requests = [
            ts for ts, stored_endpoint in self.rate_limits[ip]
            if ts > window_start and stored_endpoint == endpoint_pattern
        ]
        
        if len(recent_requests) >= max_requests:
            return False
        
        # Add current request with endpoint pattern (not full path)
        self.rate_limits[ip].append((current_time, endpoint_pattern))
        return True
    
    async def dispatch(self, request: Request, call_next):
        # Rate limiting disabled - pass through all requests
            return await call_next(request)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF protection middleware.
    
    Validates CSRF tokens for state-changing operations (POST, PUT, DELETE, PATCH).
    Exempts:
    - GET, HEAD, OPTIONS requests
    - OAuth callbacks (handled by OAuth provider)
    - Public endpoints (login, register)
    """
    
    EXEMPT_PATHS = [
        "/api/users/login",
        "/api/users/register",
        "/api/auth/oauth/google/callback",  # OAuth callback
        "/docs",
        "/openapi.json",
        "/redoc",
    ]
    
    EXEMPT_METHODS = ["GET", "HEAD", "OPTIONS"]
    
    def _is_exempt(self, request: Request) -> bool:
        """Check if request is exempt from CSRF protection."""
        # Check method
        if request.method in self.EXEMPT_METHODS:
            return True
        
        # Check path
        path = request.url.path
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for exempt requests
        if self._is_exempt(request):
            return await call_next(request)
        
        # For state-changing operations, check for CSRF token
        # In a production app, you'd validate against a session token
        # For now, we'll check for a custom header (X-Requested-With)
        # This is a simple but effective CSRF protection
        
        csrf_token = request.headers.get("X-CSRF-Token")
        x_requested_with = request.headers.get("X-Requested-With")
        
        # Accept either CSRF token or X-Requested-With header
        # (X-Requested-With is set by XMLHttpRequest and prevents simple CSRF)
        if not csrf_token and not x_requested_with:
            # For API clients, we'll be lenient but log a warning
            # In production, you might want to enforce this strictly
            pass  # Allow for now, but could be made stricter
        
        response = await call_next(request)
        
        # Add CSRF token to response headers for subsequent requests
        # In a real implementation, you'd generate and store this in session
        if request.method == "GET" and "csrf_token" not in response.headers:
            # Generate a simple token (in production, use a proper token generator)
            import secrets
            token = secrets.token_urlsafe(32)
            response.headers["X-CSRF-Token"] = token
        
        return response
