"""Task-oriented API for medical data cleaning jobs.

This module keeps FastAPI/uvicorn imports lazy so the core package remains
lightweight unless the optional `api` extra is installed.
"""

from __future__ import annotations

from typing import Any

from .jobs import (
    DataType,
    DecisionPoint,
    JobManager,
    JobPriority,
    JobRequest,
    JobStatus,
    StepProgress,
    get_job_manager,
)


def create_api_app() -> Any:
    """
    Lazily import and construct the FastAPI application.

    Raises:
        ImportError: When FastAPI isn't installed. Install via `pip install "bio-clean-agent[api]"`.
    """
    try:
        from .endpoints import create_api_app as _create_api_app
    except ImportError as exc:
        raise ImportError(
            "FastAPI is required for the API server. Install with `pip install \"bio-clean-agent[api]\"`."
        ) from exc
    return _create_api_app()


__all__ = [
    "DataType",
    "DecisionPoint",
    "JobManager",
    "JobPriority",
    "JobRequest",
    "JobStatus",
    "StepProgress",
    "create_api_app",
    "get_job_manager",
]
