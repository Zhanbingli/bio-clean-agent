"""Job management for task-oriented data cleaning."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job execution status."""

    SUBMITTED = "submitted"
    PLANNING = "planning"
    AWAITING_DECISION = "awaiting_decision"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    """Job execution priority."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class DataType(str, Enum):
    """Supported medical data types."""

    CLINICAL_TRIAL = "clinical_trial"
    EHR = "ehr"
    GENOMICS = "genomics"
    TRANSCRIPTOMICS = "transcriptomics"
    METABOLOMICS = "metabolomics"
    IMAGING_METADATA = "imaging_metadata"
    GENERAL = "general"


class JobRequest(BaseModel):
    """Request to submit a data cleaning job."""

    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data_type: DataType
    input_paths: List[str] = Field(..., description="Paths to input data files")
    output_dir: str = Field(..., description="Directory for cleaned data and reports")

    # Task specification (non-conversational)
    objectives: List[str] = Field(
        default_factory=list,
        description="List of cleaning objectives, e.g., ['remove duplicates', 'handle missing values']"
    )

    # Optional parameters
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    auto_approve: bool = Field(
        default=False,
        description="Auto-approve all decisions (use with caution)"
    )

    # Notification settings
    notify_on_decision: bool = Field(
        default=True,
        description="Notify user when decision is required"
    )
    notify_on_completion: bool = Field(default=True)

    class Config:
        use_enum_values = True


class DecisionPoint(BaseModel):
    """A point where user decision is required."""

    decision_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    context: Dict[str, Any] = Field(default_factory=dict)
    options: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Available options for the user"
    )
    default_option: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class StepProgress(BaseModel):
    """Progress of a single pipeline step."""

    step_name: str
    status: str  # "pending", "running", "completed", "failed"
    progress_percent: float = 0.0
    message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


@dataclass
class Job:
    """Internal job representation."""

    request: JobRequest
    status: JobStatus = JobStatus.SUBMITTED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Execution tracking
    current_step: Optional[str] = None
    steps: List[StepProgress] = field(default_factory=list)
    pending_decisions: List[DecisionPoint] = field(default_factory=list)

    # Results
    output_files: List[str] = field(default_factory=list)
    report_path: Optional[str] = None
    error_message: Optional[str] = None

    # Metrics
    records_processed: int = 0
    records_cleaned: int = 0
    issues_found: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API responses."""
        return {
            "job_id": self.request.job_id,
            "status": self.status.value,
            "data_type": self.request.data_type,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "current_step": self.current_step,
            "steps": [step.dict() for step in self.steps],
            "pending_decisions": [d.dict() for d in self.pending_decisions],
            "output_files": self.output_files,
            "report_path": self.report_path,
            "error_message": self.error_message,
            "metrics": {
                "records_processed": self.records_processed,
                "records_cleaned": self.records_cleaned,
                "issues_found": self.issues_found,
            },
        }


class JobManager:
    """Manages job lifecycle and execution."""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self._job_queue: List[str] = []

    def submit(self, request: JobRequest) -> str:
        """Submit a new job and return job ID."""
        job = Job(request=request)
        self.jobs[request.job_id] = job
        self._job_queue.append(request.job_id)
        return request.job_id

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current job status."""
        job = self.jobs.get(job_id)
        return job.to_dict() if job else None

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List jobs, optionally filtered by status."""
        jobs = self.jobs.values()
        if status:
            jobs = [j for j in jobs if j.status == status]

        # Sort by created_at descending
        sorted_jobs = sorted(
            jobs,
            key=lambda j: j.created_at,
            reverse=True
        )[:limit]

        return [j.to_dict() for j in sorted_jobs]

    def cancel(self, job_id: str) -> bool:
        """Cancel a job."""
        job = self.jobs.get(job_id)
        if not job:
            return False

        if job.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
            return False

        job.status = JobStatus.CANCELLED
        return True

    def update_progress(
        self,
        job_id: str,
        step_name: str,
        progress_percent: float,
        message: str = ""
    ) -> None:
        """Update job progress."""
        job = self.jobs.get(job_id)
        if not job:
            return

        job.current_step = step_name

        # Update or create step progress
        for step in job.steps:
            if step.step_name == step_name:
                step.progress_percent = progress_percent
                step.message = message
                step.status = "running"
                return

        # Create new step
        job.steps.append(StepProgress(
            step_name=step_name,
            status="running",
            progress_percent=progress_percent,
            message=message,
            started_at=datetime.now()
        ))

    def add_decision_point(
        self,
        job_id: str,
        decision: DecisionPoint
    ) -> None:
        """Add a decision point for user approval."""
        job = self.jobs.get(job_id)
        if not job:
            return

        job.pending_decisions.append(decision)
        job.status = JobStatus.AWAITING_DECISION

    def resolve_decision(
        self,
        job_id: str,
        decision_id: str,
        choice: Dict[str, Any]
    ) -> bool:
        """Resolve a pending decision."""
        job = self.jobs.get(job_id)
        if not job:
            return False

        # Remove the resolved decision
        job.pending_decisions = [
            d for d in job.pending_decisions
            if d.decision_id != decision_id
        ]

        # If no more pending decisions, resume execution
        if not job.pending_decisions and job.status == JobStatus.AWAITING_DECISION:
            job.status = JobStatus.RUNNING

        return True


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get or create global job manager."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager
