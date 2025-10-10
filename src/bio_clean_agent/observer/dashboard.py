"""Terminal-based observer dashboard for real-time monitoring."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Optional

from rich.console import Console, Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text

from ..api.jobs import Job, JobManager, get_job_manager
from .events import Event, EventStream, EventType, get_event_stream


class ObserverDashboard:
    """Real-time terminal dashboard for observing job execution."""

    def __init__(
        self,
        job_id: str,
        job_manager: Optional[JobManager] = None,
        event_stream: Optional[EventStream] = None,
        console: Optional[Console] = None,
    ):
        self.job_id = job_id
        self.job_manager = job_manager or get_job_manager()
        self.event_stream = event_stream or get_event_stream()
        self.console = console or Console()

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        )

        self._task_ids: dict[str, TaskID] = {}
        self._recent_events: list[Event] = []
        self._max_events = 10
        self._running = False

    def observe(self, refresh_rate: float = 0.5) -> None:
        """Start observing the job in real-time."""
        # Subscribe to job events
        unsubscribe = self.event_stream.subscribe(
            self._handle_event,
            job_id=self.job_id
        )

        self._running = True

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="events", size=12),
        )

        try:
            with Live(
                layout,
                console=self.console,
                refresh_per_second=1 / refresh_rate,
                screen=True,
            ):
                while self._running:
                    # Update layout
                    layout["header"].update(self._render_header())
                    layout["main"].update(self._render_main())
                    layout["events"].update(self._render_events())

                    # Check if job is finished
                    job = self.job_manager.jobs.get(self.job_id)
                    if job and job.status.value in {"completed", "failed", "cancelled"}:
                        time.sleep(2)  # Show final state for 2 seconds
                        break

                    time.sleep(refresh_rate)
        finally:
            unsubscribe()

    def _handle_event(self, event: Event) -> None:
        """Handle incoming events."""
        self._recent_events.append(event)
        if len(self._recent_events) > self._max_events:
            self._recent_events = self._recent_events[-self._max_events:]

        # Update progress bars
        if event.event_type == EventType.STEP_STARTED:
            step_name = event.data.get("step_name", "Unknown")
            if step_name not in self._task_ids:
                task_id = self.progress.add_task(
                    step_name,
                    total=100
                )
                self._task_ids[step_name] = task_id

        elif event.event_type == EventType.STEP_PROGRESS:
            step_name = event.data.get("step_name", "Unknown")
            progress_percent = event.data.get("progress_percent", 0)
            if step_name in self._task_ids:
                self.progress.update(
                    self._task_ids[step_name],
                    completed=progress_percent
                )

        elif event.event_type == EventType.STEP_COMPLETED:
            step_name = event.data.get("step_name", "Unknown")
            if step_name in self._task_ids:
                self.progress.update(
                    self._task_ids[step_name],
                    completed=100
                )

        elif event.event_type in {
            EventType.JOB_COMPLETED,
            EventType.JOB_FAILED,
            EventType.JOB_CANCELLED
        }:
            self._running = False

    def _render_header(self) -> Panel:
        """Render dashboard header."""
        job = self.job_manager.jobs.get(self.job_id)
        if not job:
            return Panel("Job not found", style="red")

        status_color = {
            "submitted": "yellow",
            "planning": "cyan",
            "awaiting_decision": "magenta",
            "running": "blue",
            "completed": "green",
            "failed": "red",
            "cancelled": "dim",
        }.get(job.status.value, "white")

        header = Text()
        header.append("Job: ", style="dim")
        header.append(f"{self.job_id}\n", style="bold white")
        header.append("Status: ", style="dim")
        header.append(job.status.value.upper(), style=f"bold {status_color}")

        if job.current_step:
            header.append("\nCurrent Step: ", style="dim")
            header.append(job.current_step, style="cyan")

        return Panel(header, title="[bold]Observer Dashboard[/]", border_style="cyan")

    def _render_main(self) -> Panel:
        """Render main progress section."""
        job = self.job_manager.jobs.get(self.job_id)
        if not job:
            return Panel("No data", style="dim")

        # Create metrics table
        metrics_table = Table.grid(padding=(0, 2))
        metrics_table.add_column(style="cyan")
        metrics_table.add_column(style="yellow")

        metrics_table.add_row(
            "Records Processed:",
            f"{job.records_processed:,}"
        )
        metrics_table.add_row(
            "Records Cleaned:",
            f"{job.records_cleaned:,}"
        )
        metrics_table.add_row(
            "Issues Found:",
            f"{job.issues_found:,}"
        )

        if job.created_at:
            elapsed = datetime.now() - job.created_at
            elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            metrics_table.add_row(
                "Elapsed Time:",
                elapsed_str
            )

        # Combine metrics and progress
        content = Group(
            metrics_table,
            Text(""),  # Spacer
            self.progress,
        )

        return Panel(content, title="Progress", border_style="blue")

    def _render_events(self) -> Panel:
        """Render recent events."""
        if not self._recent_events:
            return Panel(
                "[dim]No events yet...[/]",
                title="Recent Events",
                border_style="yellow"
            )

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Time", style="dim", width=8)
        table.add_column("Type", width=20)
        table.add_column("Message", style="white")

        for event in reversed(self._recent_events):
            time_str = event.timestamp.strftime("%H:%M:%S")

            # Color code event types
            type_color = {
                EventType.JOB_STARTED: "green",
                EventType.JOB_COMPLETED: "bold green",
                EventType.JOB_FAILED: "bold red",
                EventType.STEP_STARTED: "cyan",
                EventType.STEP_COMPLETED: "green",
                EventType.STEP_FAILED: "red",
                EventType.DECISION_REQUIRED: "magenta",
                EventType.ISSUE_DETECTED: "yellow",
                EventType.LOG_WARNING: "yellow",
                EventType.LOG_ERROR: "red",
            }.get(event.event_type, "white")

            type_str = Text(event.event_type.value, style=type_color)
            message = event.message or ""

            table.add_row(time_str, type_str, message)

        return Panel(table, title="Recent Events", border_style="yellow")


def watch_job(job_id: str, refresh_rate: float = 0.5) -> None:
    """
    Watch a job in real-time using the observer dashboard.

    Args:
        job_id: ID of the job to watch
        refresh_rate: Update frequency in seconds
    """
    dashboard = ObserverDashboard(job_id)
    dashboard.observe(refresh_rate=refresh_rate)
