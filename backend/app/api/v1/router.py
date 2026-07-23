"""API v1 router — aggregates all endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, tenants

# Create the v1 router with the /api/v1 prefix applied in main.py
api_v1_router = APIRouter()

# Include all endpoint routers
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(tenants.router)

# Future sprints will add:
# api_v1_router.include_router(events.router)        # Sprint 2
# api_v1_router.include_router(threats.router)       # Sprint 4-5
# api_v1_router.include_router(dashboard.router)     # Sprint 7
# api_v1_router.include_router(reports.router)       # Sprint 6
# api_v1_router.include_router(feedback.router)      # Sprint 6
# api_v1_router.include_router(response.router)      # Sprint 5
