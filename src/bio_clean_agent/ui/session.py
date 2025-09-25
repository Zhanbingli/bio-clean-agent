from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ..agent import AgentRequest, BioCleaningAgent
from ..llm import PlannerOutput, QwenPlanner
from ..pipelines.base import PipelineReport
from ..utils.storage import estimate_dataset_size, format_bytes


@dataclass
class InteractiveSession:
    agent: BioCleaningAgent
    planner: QwenPlanner
    dataset_payload: Optional[Dict[str, Any]] = None
    console: Console = Console()

    def run(self, auto_execute: bool = False) -> None:
        self.console.print(
            Panel(
                "Type your cleaning goal. Use 'exit' to quit."
                " Provide dataset configs via CLI options for execution.",
                title="Bio Clean Agent (Qwen-powered)",
            )
        )
        if self.dataset_payload:
            self._show_dataset_summary(self.dataset_payload)
        while True:
            user_message = Prompt.ask("[bold cyan]You[/]", default="")
            if user_message.strip().lower() in {"exit", "quit"}:
                break
            if not user_message.strip():
                continue
            plan = self.planner.plan(user_message, context_hint=self._context_hint())
            self._display_plan(plan)
            if auto_execute:
                report = self._maybe_execute(plan)
                if report:
                    self._display_report(report)

    # internal helpers -------------------------------------------------

    def _context_hint(self) -> Optional[str]:
        if not self.dataset_payload:
            return None
        dataset = self.dataset_payload.get("dataset", {})
        return f"Dataset id={dataset.get('dataset_id')} type={dataset.get('dataset_type')}"

    def _show_dataset_summary(self, payload: Dict[str, Any]) -> None:
        dataset = payload.get("dataset", {})
        table = Table(title="Dataset Summary")
        table.add_column("Field")
        table.add_column("Value")
        for key, value in dataset.items():
            table.add_row(key, str(value))
        size = estimate_dataset_size(dataset.get("raw_paths", []))
        if size:
            table.add_row("estimated_size", format_bytes(size))
        self.console.print(table)

    def _display_plan(self, plan: PlannerOutput) -> None:
        table = Table(title="LLM Plan", show_lines=True)
        table.add_column("Field")
        table.add_column("Detail")
        table.add_row("dataset_type", plan.dataset_type)
        table.add_row("dataset_id", plan.dataset_id or "<unspecified>")
        table.add_row("reasoning", plan.reasoning)
        param_table = Table(show_header=True, title="Parameters")
        param_table.add_column("Key")
        param_table.add_column("Value")
        if plan.parameters:
            for key, value in plan.parameters.items():
                param_table.add_row(key, str(value))
        else:
            param_table.add_row("-", "<none>")
        action_table = Table(title="Actions")
        action_table.add_column("#")
        action_table.add_column("Step")
        action_table.add_column("Description")
        if plan.actions:
            for idx, action in enumerate(plan.actions, start=1):
                action_table.add_row(str(idx), action.get("step", "?"), action.get("description", ""))
        else:
            action_table.add_row("-", "-", "<none>")
        self.console.print(table)
        self.console.print(param_table)
        self.console.print(action_table)

    def _maybe_execute(self, plan: PlannerOutput) -> Optional[PipelineReport]:
        if not self.dataset_payload:
            self.console.print("[yellow]No dataset config provided; skipping execution.")
            return None
        dataset_section = self.dataset_payload.get("dataset")
        if not dataset_section:
            self.console.print("[yellow]Dataset section missing; cannot execute.")
            return None
        merged_parameters = {**self.dataset_payload.get("parameters", {}), **plan.parameters}
        request = AgentRequest(
            dataset=dataset_section,
            output_dir=self.dataset_payload.get("output_dir"),
            parameters=merged_parameters,
        )
        try:
            return self.agent.run(request)
        except Exception as exc:  # pragma: no cover - UI layer
            self.console.print(f"[red]Execution failed:[/] {exc}")
            return None

    def _display_report(self, report: PipelineReport) -> None:
        status = "success" if report.success else "failure"
        self.console.print(Panel(f"Pipeline {report.pipeline_name} finished with {status}", title="Execution"))
        table = Table(title="Step Results")
        table.add_column("Step")
        table.add_column("Success")
        table.add_column("Details")
        table.add_column("Error")
        for step in report.results:
            table.add_row(
                step.name,
                "✅" if step.success else "❌",
                json_safe(step.details),
                step.error or "",
            )
        self.console.print(table)


def json_safe(value: Any) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    if isinstance(value, list):
        preview = ", ".join(str(item) for item in value[:5])
        return preview + ("…" if len(value) > 5 else "")
    return str(value)
