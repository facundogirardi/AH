"""Cliente MongoDB con reintentos de conexión (para el Replica Set)."""

import logging

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from pymongo.errors import PyMongoError

from app.config import settings

logger = logging.getLogger("app.db")

_client: MongoClient | None = None
_db: Database | None = None


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(PyMongoError),
    reraise=True,
)
def _connect() -> MongoClient:
    logger.info("Conectando a MongoDB: %s", settings.mongo_uri)
    client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)
    # Fuerza la selección de servidor para detectar fallas de conexión ya.
    client.admin.command("ping")
    logger.info("Conexión a MongoDB establecida")
    return client


def connect() -> None:
    """Inicializa el cliente global. Se llama en el startup de FastAPI."""
    global _client, _db
    _client = _connect()
    _db = _client[settings.db_name]


def close() -> None:
    """Cierra el cliente global. Se llama en el shutdown de FastAPI."""
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def get_db() -> Database:
    if _db is None:
        raise RuntimeError("La base de datos no está inicializada. Llamar a connect() primero.")
    return _db


def get_visitas_collection() -> Collection:
    return get_db()["visitas"]


def ping() -> bool:
    """Usado por el endpoint /health. Devuelve True si Mongo responde."""
    try:
        if _client is None:
            return False
        _client.admin.command("ping")
        return True
    except PyMongoError:
        logger.exception("Ping a MongoDB falló")
        return False
