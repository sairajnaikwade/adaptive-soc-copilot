"""Health check endpoint — GET /api/v1/health"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="API Health Check",
    description="Returns the health status of the API server and database connection.",
    response_description="Health status object.",
)
def health_check(db: Session = Depends(get_db)) -> dict:
    """
    Health check endpoint.

    Verifies:
        - API server is running.
        - Database connection is alive (via a lightweight SELECT 1 query).

    Returns a 200 OK response when healthy.
    Used by Docker Compose healthchecks and deployment probes.
    """
    # Lightweight DB connectivity check
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return {
        "status": "ok",
        "database": db_status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
