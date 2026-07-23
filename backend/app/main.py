"""
Adaptive SOC CoPilot — FastAPI Application Entry Point.

This module:
    1. Bootstraps the FastAPI app with OpenAPI metadata.
    2. Registers CORS middleware (React frontend).
    3. Registers the logging middleware (request tracing).
    4. Registers global exception handlers (domain → HTTP mapping).
    5. Mounts the /api/v1 router.
    6. Provides startup / shutdown lifecycle events.

Run locally (without Docker):
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    DuplicateResourceError,
    InvalidTokenError,
    ResourceNotFoundError,
    SOCCopilotException,
    ValidationError,
)
from app.core.logging_config import get_logger, setup_logging
from app.middleware.logging_middleware import LoggingMiddleware

# Initialize structured logging before anything else
setup_logging()
logger = get_logger(__name__)


# =============================================================================
# Lifespan — startup and shutdown events
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Code before `yield` runs on startup.
    Code after `yield` runs on shutdown.
    """
    # ---- Startup ----
    logger.info("=" * 60)
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)
    logger.info("Environment : %s", settings.ENVIRONMENT)
    logger.info("Database    : %s", settings.DATABASE_URL.split("@")[-1])  # Hide credentials
    logger.info("CORS Origins: %s", settings.cors_origins_list)
    logger.info("=" * 60)

    # Verify database connectivity on startup
    try:
        from app.db.session import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✓ Database connection established.")
    except Exception as exc:
        logger.error("✗ Database connection FAILED: %s", exc)
        # Don't block startup — Docker Compose health checks handle retry logic

    yield

    # ---- Shutdown ----
    logger.info("Shutting down %s...", settings.APP_NAME)


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-Powered Security Operations Center (SOC) Platform for "
        "Intelligent Threat Detection, Explainable AI, and Automated Incident Response.\n\n"
        "## Authentication\n"
        "All protected endpoints require a Bearer JWT token in the `Authorization` header.\n\n"
        "## Multi-Tenancy\n"
        "All data is scoped to the authenticated user's tenant. Cross-tenant access is not permitted."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",            # Swagger UI
    redoc_url="/redoc",          # ReDoc UI
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "SOC CoPilot Team",
        "url": "https://github.com/your-org/adaptive-soc-copilot",
    },
    license_info={
        "name": "MIT",
    },
)


# =============================================================================
# Middleware Registration
# Order matters — outermost middleware = registered last
# =============================================================================

# 1. CORS — must be first so preflight OPTIONS requests are handled before auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# 2. Request/Response logging
app.add_middleware(LoggingMiddleware)


# =============================================================================
# Global Exception Handlers
# Maps domain exceptions → structured HTTP responses
# =============================================================================

def _error_response(status_code: int, error: str, message: str, detail=None) -> JSONResponse:
    """Build a consistent error response envelope."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error,
            "message": message,
            "detail": detail,
        },
    )


@app.exception_handler(InvalidTokenError)
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: SOCCopilotException) -> JSONResponse:
    return _error_response(
        status.HTTP_401_UNAUTHORIZED,
        error="AUTHENTICATION_ERROR",
        message=exc.message,
    )


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: SOCCopilotException) -> JSONResponse:
    return _error_response(
        status.HTTP_403_FORBIDDEN,
        error="AUTHORIZATION_ERROR",
        message=exc.message,
    )


@app.exception_handler(ResourceNotFoundError)
async def not_found_error_handler(request: Request, exc: SOCCopilotException) -> JSONResponse:
    return _error_response(
        status.HTTP_404_NOT_FOUND,
        error="RESOURCE_NOT_FOUND",
        message=exc.message,
        detail=exc.detail,
    )


@app.exception_handler(DuplicateResourceError)
async def duplicate_error_handler(request: Request, exc: SOCCopilotException) -> JSONResponse:
    return _error_response(
        status.HTTP_409_CONFLICT,
        error="DUPLICATE_RESOURCE",
        message=exc.message,
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: SOCCopilotException) -> JSONResponse:
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        error="VALIDATION_ERROR",
        message=exc.message,
        detail=exc.detail,
    )


@app.exception_handler(SOCCopilotException)
async def generic_soc_error_handler(request: Request, exc: SOCCopilotException) -> JSONResponse:
    """Catch-all handler for any unhandled domain exceptions."""
    logger.error("Unhandled domain exception: %s", exc.message)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again.",
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler for completely unhandled exceptions."""
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="INTERNAL_SERVER_ERROR",
        message="An internal server error occurred.",
    )


# =============================================================================
# Router Registration
# =============================================================================

app.include_router(api_v1_router, prefix="/api/v1")


# =============================================================================
# Root redirect
# =============================================================================

@app.get("/", include_in_schema=False)
def root() -> JSONResponse:
    """Redirect root to API docs."""
    return JSONResponse(
        content={
            "message": f"Welcome to {settings.APP_NAME} API",
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/api/v1/health",
        }
    )
