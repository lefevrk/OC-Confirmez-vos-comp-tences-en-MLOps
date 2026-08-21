"""Loguru configuration for readable stdout logs."""

import inspect
import logging

from loguru import logger


class _InterceptHandler(logging.Handler):
    """Redirect standard-library log records (uvicorn, ...) through Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        """Relay one stdlib log record to Loguru, preserving its call site."""
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _format_line(record: dict) -> str:
    """Render one log record as a single readable line, bound fields included.

    A plain "timestamp | LEVEL | message key=value ..." line reads naturally
    in a terminal or `docker logs`. Structured JSON only earns its keep once
    a log pipeline needs to parse it (Alloy/Loki, a later step) — until then
    it's just noise to read by eye.
    """
    extras = " ".join(f"{key}={value}" for key, value in record["extra"].items())
    timestamp = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    line = f"{timestamp} | {record['level'].name:<8} | {record['message']}"
    return f"{line} {extras}" if extras else line


def _sink(message) -> None:
    """Write one formatted record to stdout."""
    print(_format_line(message.record))


def configure_logging(level: str = "INFO") -> None:
    """Configure Loguru to emit readable logs, including from stdlib logging.

    Redirects every standard-library logger (uvicorn's included) through
    Loguru so the whole process emits one consistent format instead of a mix
    of our lines and uvicorn's own. ``level`` defaults to ``INFO`` for a
    quiet production stream; pass ``DEBUG`` locally to see the per-step
    traces emitted while loading the model or scoring a request.
    """
    logger.remove()
    logger.add(_sink, level=level, backtrace=False, diagnose=False)

    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in logging.root.manager.loggerDict:
        stdlib_logger = logging.getLogger(name)
        stdlib_logger.handlers = [_InterceptHandler()]
        stdlib_logger.propagate = False
