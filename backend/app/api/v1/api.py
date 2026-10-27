"""Aggregates all v1 routers into a single APIRouter mounted by main.py."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    assets,
    auth,
    backtests,
    health,
    notes,
    portfolio,
    strategies,
    users,
    watchlists,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(assets.router)
api_router.include_router(strategies.router)
api_router.include_router(backtests.router)
api_router.include_router(analytics.router)
api_router.include_router(watchlists.router)
api_router.include_router(notes.router)
api_router.include_router(portfolio.router)
