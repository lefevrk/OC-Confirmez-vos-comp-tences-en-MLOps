"""Unit tests for the readable log format used locally."""

import logging

from loguru import logger

from api.infra.logging import configure_logging


def test_configure_logging_emits_a_readable_line_with_bound_fields(capsys) -> None:
    """A bound log call produces one readable line with its extra fields appended."""
    configure_logging()

    logger.bind(request_id="abc-123", latency_ms=4.2).info("prediction served")

    line = capsys.readouterr().out.strip()
    assert "INFO" in line
    assert "prediction served" in line
    assert "request_id=abc-123" in line
    assert "latency_ms=4.2" in line


def test_configure_logging_respects_the_requested_level(capsys) -> None:
    """DEBUG traces are silent by default and visible once the level is lowered."""
    configure_logging()
    logger.debug("scoring_started")
    assert capsys.readouterr().out == ""

    configure_logging(level="DEBUG")
    logger.debug("scoring_started")
    assert "scoring_started" in capsys.readouterr().out


def test_configure_logging_intercepts_stdlib_logging(capsys) -> None:
    """A stdlib log call (uvicorn, ...) is redirected through the same sink."""
    configure_logging()

    logging.getLogger("uvicorn.error").info("Uvicorn running on http://0.0.0.0:8000")

    line = capsys.readouterr().out.strip()
    assert "INFO" in line
    assert "Uvicorn running on http://0.0.0.0:8000" in line


def test_configure_logging_relays_a_level_unknown_to_loguru(capsys) -> None:
    """A stdlib level with no Loguru equivalent still reaches the sink, by number."""
    configure_logging()

    logging.getLogger("custom").log(25, "custom level message")

    assert "custom level message" in capsys.readouterr().out
