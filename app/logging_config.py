"""Logging estructurado (JSON) con request-id propagado por middleware."""

import contextvars
import json
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_var.get(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Genera/propaga un request-id por request y loguea método, path, status y duración."""

    def __init__(self, app):
        super().__init__(app)
        self._logger = logging.getLogger("app.request")

    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        token = request_id_var.set(req_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-Id"] = req_id
        self._logger.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
