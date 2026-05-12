"""Main FastAPI application for LexChain Sovereign."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings
from app.core.database import init_db, close_db, get_redis, close_redis
from app.core.middleware import SecurityHeadersMiddleware, RequestIDMiddleware
from app.core.logging import setup_logging, get_logger, request_id_var
from app.api.v1 import auth, users, assets, documents, compliance, legal_ai, governance, did, evidence, analytics, audit

setup_logging()
logger = get_logger(__name__)

request_counter = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
request_duration = Histogram("http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Starting LexChain Sovereign API...")

    await init_db()
    logger.info("Database initialized")

    redis = await get_redis()
    if redis:
        await redis.ping()
        logger.info("Redis connection established")

    yield

    logger.info("Shutting down LexChain Sovereign API...")
    await close_db()
    await close_redis()
    logger.info("Connections closed")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Decentralized Legal Infrastructure for Compliant RWA Tokenization",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-CSRF-Token"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Add metrics tracking to requests."""
    import time
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time
    request_counter.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response


@app.exception_handler(status.HTTP_401_UNAUTHORIZED)
async def unauthorized_handler(request: Request, exc):
    """Handle 401 errors."""
    return JSONResponse(
        status_code=401,
        content={
            "error": "Unauthorized",
            "message": "Authentication required",
            "code": "AUTH_REQUIRED"
        }
    )


@app.exception_handler(status.HTTP_403_FORBIDDEN)
async def forbidden_handler(request: Request, exc):
    """Handle 403 errors."""
    return JSONResponse(
        status_code=403,
        content={
            "error": "Forbidden",
            "message": str(exc.detail) if hasattr(exc, 'detail') else "Access denied",
            "code": "ACCESS_DENIED"
        }
    )


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "Resource not found",
            "code": "NOT_FOUND"
        }
    )


@app.exception_handler(status.HTTP_429_TOO_MANY_REQUESTS)
async def rate_limit_handler(request: Request, exc):
    """Handle rate limit errors."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Rate limit exceeded. Please try again later.",
            "code": "RATE_LIMIT_EXCEEDED"
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    import time
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "timestamp": __import__("datetime").datetime.now(timezone=True).isoformat(),
        "uptime": 0
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return JSONResponse(
        content=generate_latest().decode("utf-8"),
        media_type=CONTENT_TYPE_LATEST
    )


app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["Assets"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(compliance.router, prefix="/api/v1/compliance", tags=["Compliance"])
app.include_router(legal_ai.router, prefix="/api/v1/legal-ai", tags=["Legal AI"])
app.include_router(governance.router, prefix="/api/v1/governance", tags=["Governance"])
app.include_router(did.router, prefix="/api/v1/did", tags=["Decentralized Identity"])
app.include_router(evidence.router, prefix="/api/v1/evidence", tags=["Legal Evidence"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["Audit"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )