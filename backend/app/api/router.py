from fastapi import APIRouter

from app.api.routes import auth, dependencies, events, health, incidents

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(events.router)
api_router.include_router(incidents.router)
api_router.include_router(dependencies.router)
