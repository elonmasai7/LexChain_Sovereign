"""Security middleware for FastAPI application."""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.security import sanitize_input


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://*.infura.io wss://*.walletconnect.org https://api.openai.com; "
                "frame-ancestors 'none';"
            )

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID to each request."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        import uuid
        from app.core.logging import request_id_var

        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict[str, tuple[int, float]] = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        if client_ip in self.request_counts:
            count, first_request = self.request_counts[client_ip]

            if current_time - first_request > 60:
                self.request_counts[client_ip] = (1, current_time)
            else:
                if count >= self.requests_per_minute:
                    return Response(
                        content='{"detail":"Rate limit exceeded"}',
                        status_code=429,
                        media_type="application/json"
                    )
                self.request_counts[client_ip] = (count + 1, first_request)
        else:
            self.request_counts[client_ip] = (1, current_time)

        return await call_next(request)


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Sanitize user inputs to prevent injection attacks."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("content-type", "")

            if "application/json" in content_type:
                try:
                    body = await request.body()
                    body_str = body.decode()
                    sanitized = sanitize_input(body_str)
                    if sanitized != body_str:
                        from starlette.requests import Request
                        request._body = sanitized.encode()
                except Exception:
                    pass

        return await call_next(request)


def setup_cors(app):
    """Configure CORS middleware."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
    )