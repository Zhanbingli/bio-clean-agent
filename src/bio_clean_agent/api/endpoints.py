"""REST API endpoints for task submission and monitoring."""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .jobs import (
    DecisionPoint,
    JobManager,
    JobRequest,
    JobStatus,
    get_job_manager,
)


def create_api_app() -> Any:
    """Create FastAPI application for job management."""
    if not FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI is required for the API server. "
            "Install with: pip install 'bio-clean-agent[api]'"
        )

    app = FastAPI(
        title="Bio Clean Agent API",
        description="Task-oriented API for medical data cleaning",
        version="0.1.0"
    )

    # Enable CORS for web dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    job_manager = get_job_manager()

    @app.get("/")
    async def root():
        """API health check."""
        return {
            "status": "healthy",
            "service": "Bio Clean Agent API",
            "version": "0.1.0"
        }

    @app.post("/jobs", response_model=Dict[str, str])
    async def submit_job(
        request: JobRequest,
        background_tasks: BackgroundTasks
    ):
        """Submit a new data cleaning job."""
        job_id = job_manager.submit(request)

        # TODO: Add background task to execute job
        # background_tasks.add_task(execute_job, job_id)

        return {"job_id": job_id, "status": "submitted"}

    @app.get("/jobs/{job_id}")
    async def get_job(job_id: str):
        """Get job status and progress."""
        status = job_manager.get_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        return status

    @app.get("/jobs")
    async def list_jobs(
        status: Optional[JobStatus] = None,
        limit: int = 50
    ):
        """List jobs with optional status filter."""
        jobs = job_manager.list_jobs(status=status, limit=limit)
        return {"jobs": jobs, "count": len(jobs)}

    @app.post("/jobs/{job_id}/cancel")
    async def cancel_job(job_id: str):
        """Cancel a running job."""
        success = job_manager.cancel(job_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Job cannot be cancelled (not found or already finished)"
            )
        return {"job_id": job_id, "status": "cancelled"}

    @app.post("/jobs/{job_id}/decisions/{decision_id}")
    async def resolve_decision(
        job_id: str,
        decision_id: str,
        choice: Dict[str, Any]
    ):
        """Resolve a pending decision."""
        success = job_manager.resolve_decision(job_id, decision_id, choice)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Job or decision not found"
            )
        return {"decision_id": decision_id, "status": "resolved"}

    @app.get("/jobs/{job_id}/report")
    async def get_report(job_id: str):
        """Get job report (if completed)."""
        status = job_manager.get_status(job_id)
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")

        if status["status"] != JobStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400,
                detail="Job is not completed yet"
            )

        report_path = status.get("report_path")
        if not report_path:
            raise HTTPException(
                status_code=404,
                detail="Report not available"
            )

        # TODO: Return report content or redirect to static file
        return {"report_path": report_path}

    return app


def run_api_server(host: str = "0.0.0.0", port: int = 8000):
    """Run the API server."""
    if not FASTAPI_AVAILABLE:
        raise ImportError(
            "FastAPI and uvicorn are required for the API server. "
            "Install with: pip install 'bio-clean-agent[api]'"
        )

    try:
        import uvicorn
    except ImportError:
        raise ImportError(
            "uvicorn is required for the API server. "
            "Install with: pip install 'bio-clean-agent[api]'"
        )

    app = create_api_app()
    uvicorn.run(app, host=host, port=port)
