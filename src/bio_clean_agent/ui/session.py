from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ..agent import AgentPlan, AgentRequest, BioCleaningAgent
from ..dataspec.models import Dataset, load_dataset
from ..llm import (
    DEFAULT_LLM_REGISTRY,
    LLMPlanner,
    LLMProviderError,
    LLMRegistry,
    ModelConfig,
    ModelDescriptor,
    PlannerOutput,
)
from ..pipelines.base import PipelineReport
from ..utils.storage import estimate_dataset_size, format_bytes


@dataclass
class InteractiveSession:
    agent: BioCleaningAgent
    planner: LLMPlanner
    dataset_payload: Optional[Dict[str, Any]] = None
    console: Console = field(default_factory=Console)
    model_registry: Optional[LLMRegistry] = None
    model_options: Dict[str, Any] = field(default_factory=dict)
    api_key: Optional[str] = None
    active_model: Optional[ModelDescriptor] = None
    _auto_execute_flag: bool = field(default=False, init=False)
    _plan_history: List[PlannerOutput] = field(default_factory=list, init=False)
    _last_agent_plan: Optional[AgentPlan] = field(default=None, init=False)
    _dataset_obj: Optional[Dataset] = field(default=None, init=False)
    _last_parameters: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.model_registry is None:
            self.model_registry = DEFAULT_LLM_REGISTRY
        if not self.active_model and hasattr(self.planner, "descriptor"):
            self.active_model = self.planner.descriptor
        if self.dataset_payload and isinstance(self.dataset_payload, dict):
            dataset_section = self.dataset_payload.get("dataset")
            if dataset_section:
                self._dataset_obj = load_dataset(dataset_section["dataset_type"], dataset_section)

    def run(self, auto_execute: bool = False) -> None:
        self._auto_execute_flag = auto_execute or self._auto_execute_flag
        self._render_header()
        if self.dataset_payload:
            self._show_dataset_summary(self.dataset_payload)
        while True:
            try:
                user_message = Prompt.ask("[bold cyan]You[/]", default="")
            except (KeyboardInterrupt, EOFError):  # pragma: no cover - interactive fallback
                self.console.print("\n[bold yellow]Session interrupted. Bye![/]")
                break
            message = user_message.strip()
            if not message:
                continue
            if message.lower() in {"exit", "quit"}:
                break
            if message.startswith("/"):
                should_continue = self._handle_command(message)
                if not should_continue:
                    break
                continue
            self._handle_goal(message)

    # internal helpers -------------------------------------------------

    def _render_header(self) -> None:
        model_label = f"{self.active_model.name} [{self.active_model.key}]" if self.active_model else "<unbound>"
        auto_label = "on" if self._auto_execute_flag else "off"
        body = (
            "Type a cleaning goal to generate a plan. Commands start with '/'."
            "\nUse /help for available commands and /exit to leave the session."
            f"\nModel: {model_label} | Auto-execute: {auto_label}"
        )
        self.console.print(Panel(body, title="Bio Clean Agent", subtitle="Ready"))

    def _handle_goal(self, message: str) -> None:
        try:
            plan = self.planner.plan(message, context_hint=self._context_hint())
        except Exception as exc:  # pragma: no cover - defensive UI guard
            self.console.print(f"[red]Planner error:[/] {exc}")
            return
        self._plan_history.append(plan)
        self._display_plan(plan)
        agent_plan = self._prepare_agent_plan(plan)
        if agent_plan:
            self._display_agent_plan(agent_plan)
            if self._auto_execute_flag:
                report = self._execute_agent_plan(agent_plan)
                if report:
                    self._display_report(report)
        elif self._auto_execute_flag:
            self.console.print("[yellow]Auto-execute requested but no dataset payload is loaded.")

    def _handle_command(self, raw_command: str) -> bool:
        command = raw_command.lstrip("/").strip()
        if not command:
            self.console.print("[yellow]Empty command ignored.[/]")
            return True
        parts = command.split(maxsplit=1)
        name = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""
        if name in {"exit", "quit"}:
            return False
        if name in {"help", "h"}:
            self._show_help()
            return True
        if name in {"models", "model-list"}:
            self._list_models()
            return True
        if name == "model":
            self._command_model(argument)
            return True
        if name == "auto":
            self._command_auto(argument)
            return True
        if name == "plan":
            self._show_last_agent_plan()
            return True
        if name == "execute":
            self._execute_last_plan()
            return True
        self.console.print(f"[yellow]Unknown command '{name}'. Use /help for guidance.[/]")
        return True

    def _context_hint(self) -> Optional[str]:
        if not self._dataset_obj:
            return None
        return f"Dataset id={self._dataset_obj.dataset_id} type={self._dataset_obj.dataset_type}"

    def _show_dataset_summary(self, payload: Dict[str, Any]) -> None:
        dataset = payload.get("dataset", {})
        table = Table(title="Dataset Summary")
        table.add_column("Field")
        table.add_column("Value")
        for key, value in dataset.items():
            table.add_row(str(key), str(value))
        size = estimate_dataset_size(dataset.get("raw_paths", []))
        if size:
            table.add_row("estimated_size", format_bytes(size))
        self.console.print(table)

    def _display_plan(self, plan: PlannerOutput) -> None:
        table = Table(title="LLM Plan", show_lines=True)
        table.add_column("Field")
        table.add_column("Detail")
        if plan.diagnostics.metadata.get("model"):
            model_meta = plan.diagnostics.metadata["model"]
            table.add_row("model", f"{model_meta.get('name')} ({model_meta.get('key')})")
        table.add_row("dataset_type", plan.dataset_type)
        table.add_row("dataset_id", plan.dataset_id or "<unspecified>")
        table.add_row("reasoning", plan.reasoning)
        self.console.print(table)

        param_table = Table(show_header=True, title="Suggested Parameters")
        param_table.add_column("Key")
        param_table.add_column("Value")
        if plan.parameters:
            for key, value in plan.parameters.items():
                param_table.add_row(str(key), str(value))
        else:
            param_table.add_row("-", "<none>")
        self.console.print(param_table)

        action_table = Table(title="Planned Actions")
        action_table.add_column("#")
        action_table.add_column("Step")
        action_table.add_column("Description")
        if plan.actions:
            for idx, action in enumerate(plan.actions, start=1):
                action_table.add_row(str(idx), str(action.get("step", "?")), str(action.get("description", "")))
        else:
            action_table.add_row("-", "-", "<none>")
        self.console.print(action_table)

        if plan.diagnostics.warnings:
            warn_table = Table(title="Planner Warnings")
            warn_table.add_column("Warning")
            for warning in plan.diagnostics.warnings:
                warn_table.add_row(str(warning))
            self.console.print(warn_table)

    def _display_agent_plan(self, plan: AgentPlan) -> None:
        table = Table(title="Agent Pipeline Plan", show_lines=True)
        table.add_column("Field")
        table.add_column("Detail")
        table.add_row("dataset_id", plan.dataset_id)
        table.add_row("dataset_type", plan.dataset_type)
        table.add_row("pipeline", plan.pipeline)
        table.add_row("workdir", plan.workdir)
        self.console.print(table)

        param_table = Table(title="Merged Parameters")
        param_table.add_column("Key")
        param_table.add_column("Value")
        if plan.parameters:
            for key, value in plan.parameters.items():
                param_table.add_row(str(key), str(value))
        else:
            param_table.add_row("-", "<none>")
        self.console.print(param_table)

        step_table = Table(title="Pipeline Steps")
        step_table.add_column("#")
        step_table.add_column("Name")
        step_table.add_column("Description")
        for idx, step in enumerate(plan.steps, start=1):
            step_table.add_row(str(idx), step.name, step.description)
        self.console.print(step_table)

        if plan.warnings:
            warn_table = Table(title="Preflight Warnings")
            warn_table.add_column("Warning")
            for warning in plan.warnings:
                warn_table.add_row(str(warning))
            self.console.print(warn_table)

    def _merge_parameters(self, plan: PlannerOutput) -> Dict[str, Any]:
        base = dict(self.dataset_payload.get("parameters", {})) if self.dataset_payload else {}
        merged = {**base, **(plan.parameters or {})}
        self._last_parameters = merged
        return merged

    def _prepare_agent_plan(self, plan: PlannerOutput) -> Optional[AgentPlan]:
        if not self._dataset_obj or not self.dataset_payload:
            return None
        merged = self._merge_parameters(plan)
        agent_plan = self.agent.plan(
            self._dataset_obj,
            output_dir=self.dataset_payload.get("output_dir"),
            parameters=merged,
        )
        self._last_agent_plan = agent_plan
        return agent_plan

    def _execute_agent_plan(self, plan: AgentPlan) -> Optional[PipelineReport]:
        if not self.dataset_payload:
            self.console.print("[yellow]No dataset payload available; cannot execute pipeline.")
            return None
        dataset_section = self.dataset_payload.get("dataset")
        if not dataset_section:
            self.console.print("[yellow]Dataset section missing; cannot execute pipeline.")
            return None
        request = AgentRequest(
            dataset=dataset_section,
            output_dir=self.dataset_payload.get("output_dir"),
            parameters=self._last_parameters,
        )
        try:
            return self.agent.run(request, plan=plan)
        except FileNotFoundError as exc:
            self.console.print(f"[red]Execution blocked:[/] {exc}")
        except Exception as exc:  # pragma: no cover - defensive UI guard
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

    def _list_models(self) -> None:
        if not self.model_registry:
            self.console.print("[yellow]Model registry is unavailable in this session.")
            return
        table = Table(title="Registered Planner Models")
        table.add_column("Active")
        table.add_column("Key")
        table.add_column("Provider")
        table.add_column("Name")
        table.add_column("Tags")
        for descriptor in self.model_registry.available_models():
            active = "✅" if self.active_model and descriptor.key == self.active_model.key else ""
            tags = ", ".join(descriptor.tags) if descriptor.tags else "-"
            table.add_row(active, descriptor.key, descriptor.provider, descriptor.name, tags)
        self.console.print(table)

    def _command_model(self, argument: str) -> None:
        if not self.model_registry:
            self.console.print("[yellow]Model registry not configured; cannot switch models.")
            return
        if not argument:
            self.console.print("[yellow]Usage: /model <key> [option=value ...][/]")
            return
        tokens = argument.split()
        key = tokens[0]
        options = dict(self.model_options)
        api_key = self.api_key
        for token in tokens[1:]:
            if "=" not in token:
                self.console.print(f"[yellow]Ignoring option '{token}' (expected key=value).[/]")
                continue
            opt_key, opt_value = token.split("=", 1)
            if opt_key == "api_key":
                api_key = opt_value
            else:
                options[opt_key] = self._coerce_option(opt_value)
        self._activate_model(key, options, api_key)

    def _command_auto(self, argument: str) -> None:
        normalized = argument.strip().lower()
        if normalized in {"on", "true", "1"}:
            self._auto_execute_flag = True
        elif normalized in {"off", "false", "0"}:
            self._auto_execute_flag = False
        else:
            self._auto_execute_flag = not self._auto_execute_flag
        self.console.print(f"[green]Auto-execute {'enabled' if self._auto_execute_flag else 'disabled'}.[/]")
        self._render_header()

    def _show_help(self) -> None:
        table = Table(title="Session Commands")
        table.add_column("Command")
        table.add_column("Description")
        table.add_row("/help", "Show this help message")
        table.add_row("/models", "List available planner models")
        table.add_row("/model <key> [k=v]", "Switch planner model with optional overrides")
        table.add_row("/auto [on|off]", "Toggle automatic execution after planning")
        table.add_row("/plan", "Show the last computed agent plan")
        table.add_row("/execute", "Execute the last agent plan if available")
        table.add_row("/exit", "Exit the interactive session")
        self.console.print(table)

    def _show_last_agent_plan(self) -> None:
        if not self._last_agent_plan:
            self.console.print("[yellow]No agent plan available yet; ask for a plan first.")
            return
        self._display_agent_plan(self._last_agent_plan)

    def _execute_last_plan(self) -> None:
        if not self._last_agent_plan:
            self.console.print("[yellow]No cached plan to execute. Generate one first.")
            return
        report = self._execute_agent_plan(self._last_agent_plan)
        if report:
            self._display_report(report)

    def _activate_model(self, key: str, options: Dict[str, Any], api_key: Optional[str]) -> None:
        if not self.model_registry:
            self.console.print("[yellow]Model registry not configured; cannot switch models.")
            return
        if self.active_model and key == self.active_model.key:
            self.console.print(f"[green]Model {key} is already active.")
            return
        try:
            llm, descriptor = self.model_registry.create(ModelConfig(choice=key, options=options, api_key=api_key))
        except LLMProviderError as exc:
            self.console.print(f"[red]Failed to switch model:[/] {exc}")
            return
        self.planner = LLMPlanner(llm, config=self.planner.config, descriptor=descriptor)
        self.active_model = descriptor
        self.model_options = options
        self.api_key = api_key
        self._plan_history.clear()
        self.console.print(f"[green]Switched planner model to {descriptor.name} ({descriptor.key}).")
        self._render_header()

    def _coerce_option(self, raw_value: str) -> Any:
        lowered = raw_value.lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        try:
            return int(raw_value)
        except ValueError:
            try:
                return float(raw_value)
            except ValueError:
                return raw_value


def json_safe(value: Any) -> str:
    if isinstance(value, dict):
        return ", ".join(f"{k}={v}" for k, v in value.items())
    if isinstance(value, list):
        preview = ", ".join(str(item) for item in value[:5])
        return preview + ("…" if len(value) > 5 else "")
    return str(value)
