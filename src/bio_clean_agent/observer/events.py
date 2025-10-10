"""Event system for real-time job monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(str, Enum):
    """Types of events that can be emitted during job execution."""

    JOB_SUBMITTED = "job.submitted"
    JOB_STARTED = "job.started"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"

    STEP_STARTED = "step.started"
    STEP_PROGRESS = "step.progress"
    STEP_COMPLETED = "step.completed"
    STEP_FAILED = "step.failed"

    DECISION_REQUIRED = "decision.required"
    DECISION_RESOLVED = "decision.resolved"

    DATA_PROFILED = "data.profiled"
    ISSUE_DETECTED = "issue.detected"
    ISSUE_RESOLVED = "issue.resolved"

    LOG_INFO = "log.info"
    LOG_WARNING = "log.warning"
    LOG_ERROR = "log.error"


@dataclass
class Event:
    """A single event in the job execution timeline."""

    event_type: EventType
    job_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type.value,
            "job_id": self.job_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "message": self.message,
        }


EventListener = Callable[[Event], None]


class EventStream:
    """Manages event emission and subscription."""

    def __init__(self):
        self._listeners: Dict[str, List[EventListener]] = {}
        self._global_listeners: List[EventListener] = []
        self._event_history: List[Event] = []
        self._max_history_size = 1000

    def emit(self, event: Event) -> None:
        """Emit an event to all subscribers."""
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]

        # Notify job-specific listeners
        job_listeners = self._listeners.get(event.job_id, [])
        for listener in job_listeners:
            try:
                listener(event)
            except Exception as e:
                # Prevent listener errors from breaking event emission
                print(f"Error in event listener: {e}")

        # Notify global listeners
        for listener in self._global_listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"Error in global event listener: {e}")

    def subscribe(
        self,
        listener: EventListener,
        job_id: Optional[str] = None
    ) -> Callable[[], None]:
        """
        Subscribe to events.

        Args:
            listener: Callback function to receive events
            job_id: If specified, only receive events for this job.
                   If None, receive all events.

        Returns:
            Unsubscribe function
        """
        if job_id:
            if job_id not in self._listeners:
                self._listeners[job_id] = []
            self._listeners[job_id].append(listener)

            def unsubscribe():
                if job_id in self._listeners:
                    self._listeners[job_id].remove(listener)
        else:
            self._global_listeners.append(listener)

            def unsubscribe():
                self._global_listeners.remove(listener)

        return unsubscribe

    def get_history(
        self,
        job_id: Optional[str] = None,
        event_types: Optional[List[EventType]] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get historical events with optional filtering."""
        events = self._event_history

        if job_id:
            events = [e for e in events if e.job_id == job_id]

        if event_types:
            events = [e for e in events if e.event_type in event_types]

        return events[-limit:]

    def clear_history(self, job_id: Optional[str] = None) -> None:
        """Clear event history for a job or all jobs."""
        if job_id:
            self._event_history = [
                e for e in self._event_history
                if e.job_id != job_id
            ]
        else:
            self._event_history.clear()


# Global event stream
_event_stream: Optional[EventStream] = None


def get_event_stream() -> EventStream:
    """Get or create global event stream."""
    global _event_stream
    if _event_stream is None:
        _event_stream = EventStream()
    return _event_stream
