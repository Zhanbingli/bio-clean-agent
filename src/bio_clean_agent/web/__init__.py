"""Web interface for Bio Clean Agent.

FastAPI/uvicorn are optional; imports are kept lazy so the base package stays lightweight.
"""

from __future__ import annotations

from typing import Any


def create_app() -> Any:
    """
    Lazily create the FastAPI app if the optional dependencies are installed.

    Raises:
        ImportError: When FastAPI is missing. Install with `pip install "bio-clean-agent[api]"`.
    """
    try:
        from .app import create_app as _create_app
    except ImportError as exc:
        raise ImportError(
            "FastAPI is required for the web interface. Install with `pip install \"bio-clean-agent[api]\"`."
        ) from exc
    return _create_app()


def run_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False) -> None:
    """Run the uvicorn server with lazy imports for optional dependencies."""
    try:
        from .server import run_server as _run_server
    except ImportError as exc:
        raise ImportError(
            "FastAPI and uvicorn are required for the web interface. Install with `pip install \"bio-clean-agent[api]\"`."
        ) from exc
    _run_server(host=host, port=port, reload=reload)


__all__ = ["create_app", "run_server"]
