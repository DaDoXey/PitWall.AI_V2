"""app/main.py — FastAPI entry point.

Avvio (dalla cartella backend/):
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.api import analysis, catalog, csv, session, setup, vision

app = FastAPI(title="PitWall.AI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for _router in (session.router, analysis.router, setup.router, csv.router, vision.router, catalog.router):
    app.include_router(_router, prefix="/api")


@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "PitWall.AI API",
        "version": "0.1.0",
        "demo_mode": config.demo_mode(),
        "live_allowed": config.allow_live(),
    }
