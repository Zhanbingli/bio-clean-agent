"""Server runner for web interface."""

import uvicorn
from .app import create_app


def run_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    reload: bool = False
):
    """
    Run the web server.

    Args:
        host: Host to bind to (0.0.0.0 for all interfaces)
        port: Port to run on
        reload: Enable auto-reload for development
    """
    app = create_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run_server(reload=True)
