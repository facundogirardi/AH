"""Punto de entrada de la aplicación FastAPI."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app import db
from app.config import settings
from app.logging_config import RequestIdMiddleware, configure_logging
from app.routers import visitas

configure_logging(settings.log_level)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    logger.info("Aplicación iniciada")
    yield
    db.close()
    logger.info("Aplicación detenida")


app = FastAPI(title="Registro de Visitas", version="1.0.0", lifespan=lifespan)
app.add_middleware(RequestIdMiddleware)
app.include_router(visitas.router)


@app.get("/health")
def health():
    mongo_ok = db.ping()
    status_code = 200 if mongo_ok else 503
    return JSONResponse(status_code=status_code, content={"status": "ok" if mongo_ok else "degraded", "mongo": mongo_ok})
