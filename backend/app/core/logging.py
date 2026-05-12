"""Structured logging configuration for LexChain Sovereign."""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any
from contextvars import ContextVar
from app.core.config import settings


request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if request_id_var.get():
            log_data["request_id"] = request_id_var.get()

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        request_id = request_id_var.get()
        req_id_str = f"[{request_id}] " if request_id else ""
        return f"{timestamp} {record.levelname:8} {req_id_str}{record.name}: {record.getMessage()}"


def setup_logging():
    """Configure application logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING if settings.ENVIRONMENT == "production" else logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class AuditLogger:
    """Audit logger for security-sensitive operations."""

    def __init__(self):
        self.logger = get_logger("audit")

    def log(
        self,
        action: str,
        user_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        success: bool = True,
        error: str | None = None
    ):
        """Log an audit event."""
        extra = {
            "extra_data": {
                "action": action,
                "user_id": user_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "success": success,
                "error": error
            }
        }
        if details:
            extra["extra_data"]["details"] = details

        if success:
            self.logger.info(f"AUDIT: {action}", extra=extra)
        else:
            self.logger.error(f"AUDIT FAILURE: {action}", extra=extra)


audit_logger = AuditLogger()