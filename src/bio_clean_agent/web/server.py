"""Server runner for web interface."""

from __future__ import annotations


def run_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False) -> None:
    """
    Run the web server.

    Args:
        host: Host to bind to (0.0.0.0 for all interfaces)
        port: Port to run on
        reload: Enable auto-reload for development

    Raises:
        ImportError: When uvicorn/FastAPI are not available.
    """
    try:
        import uvicorn  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency guard
        raise ImportError(
            "uvicorn is required to run the web interface. Install with `pip install \"bio-clean-agent[api]\"`."
        ) from exc

    from .app import create_app

    app = create_app()
    uvicorn.run(app, host=host, port=port, reload=reload, log_level="info")


if __name__ == "__main__":
    run_server(reload=True)
