from fastapi import APIRouter

from app.modules.transfer_penalty.router import router as transfer_penalty_router
from app.routers import dashboard, edges, fares, history, quote, settings, stations

api = APIRouter(prefix="/api")
for r in (dashboard, stations, edges, fares, quote, history, settings):
    api.include_router(r.router)
api.include_router(transfer_penalty_router)
