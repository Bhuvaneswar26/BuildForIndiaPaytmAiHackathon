from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import router

app = FastAPI(title="GST Pulse — Alert Agent", version="0.1.0")
app.include_router(router)
