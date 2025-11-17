from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Sequence

from .dataspec.models import Dataset, load_dataset
from .pipelines.base import Pipeline, PipelineReport, ToolExecutor
from .utils.logging import get_logger
from .utils.preflight import run_preflight_checks

if TYPE_CHECKING:
    from .llm import LLMPlanner, PlannerOutput


class SubprocessToolExecutor(ToolExecutor):
    """Executes external tools using subprocess."""

    def run(self, command, workdir: Optional[str] = None):  # type: ignore[override]
        proc = subprocess.run(
            command,
            cwd=workdir,
            check=False,
            text=True,
            capture_output=True,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "command": command,
            "workdir": workdir,
        }


class SimulatedToolExecutor(ToolExecutor):
    """Simulates external tool execution for dry runs or testing."""

    def __init__(self, succeed: bool = True):
        self.succeed = succeed

    def run(self, command, workdir: Optional[str] = None):  # type: ignore[override]
        return {
            "returncode": 0 if self.succeed else 1,
            "stdout": "simulated execution",
            "stderr": "" if self.succeed else "simulated failure",
            "command": command,
            "workdir": workdir,
        }


@dataclass
class AgentRequest:
    dataset: Dict
    output_dir: Optional[str] = None
    parameters: Optional[Dict] = None


@dataclass
class PlanStep:
    name: str
    description: str

    def to_dict(self) -> Dict[str, str]:
        return {"name": self.name, "description": self.description}


@dataclass
class AgentPlan:
    dataset_id: str
    dataset_type: str
    pipeline: str
    workdir: str
    steps: List[PlanStep] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_type": self.dataset_type,
            "pipeline": self.pipeline,
            "workdir": self.workdir,
            "steps": [step.to_dict() for step in self.steps],
            "parameters": dict(self.parameters),
            "warnings": list(self.warnings),
        }


@dataclass
class LLMPlanBundle:
    planner_output: "PlannerOutput"
    merged_parameters: Dict[str, Any]
    agent_plan: Optional[AgentPlan]
    dataset: Optional[Dataset]


@dataclass
class AgentExecutionResult:
    plan: AgentPlan
    report: PipelineReport
    planner_output: Optional["PlannerOutput"] = None


ConfirmStepCallback = Callable[[PlanStep, int], bool]


class BioCleaningAgent:
    """Agent that selects and executes the correct cleaning pipeline."""

    def __init__(self, default_output_root: str | Path = "outputs", executor: Optional[ToolExecutor] = None):
        self._logger = get_logger()
        self.default_output_root = Path(default_output_root)
        self.executor = executor or SubprocessToolExecutor()
        self.pipeline_registry: Dict[str, Callable[[Dataset, Path], Pipeline]] = {}

    def register_pipeline(self, dataset_type: str, factory: Callable[[Dataset, Path], Pipeline]) -> None:
        self.pipeline_registry[dataset_type] = factory
        self._logger.debug("Registered pipeline for dataset_type=%s", dataset_type)

    def plan(
        self,
        dataset: Dataset,
        output_dir: Optional[str | Path] = None,
        parameters: Optional[Dict[str, object]] = None,
    ) -> AgentPlan:
        pipeline_factory = self._get_pipeline_factory(dataset.dataset_type)
        workdir = Path(output_dir or self.default_output_root / dataset.dataset_id)
        pipeline = pipeline_factory(dataset, workdir)
        steps = [PlanStep(step.name, step.description) for step in pipeline.steps]
        parameter_map: Dict[str, Any] = dict(parameters or {})
        warnings = run_preflight_checks(dataset, parameter_map)
        return AgentPlan(
            dataset_id=dataset.dataset_id,
            dataset_type=dataset.dataset_type,
            pipeline=pipeline.name,
            workdir=str(workdir),
            steps=steps,
            parameters=parameter_map,
            warnings=warnings,
        )

    def plan_with_llm(
        self,
        user_request: str,
        planner: "LLMPlanner",
        dataset_payload: Optional[Dict[str, object]] = None,
    ) -> LLMPlanBundle:
        payload = dataset_payload or {}
        dataset_section = payload.get("dataset") if isinstance(payload, dict) else None
        context_hint = None
        dataset_obj: Optional[Dataset] = None
        if dataset_section:
            dataset_obj = load_dataset(dataset_section["dataset_type"], dataset_section)
            context_hint = f"Dataset id={dataset_section.get('dataset_id')} type={dataset_section.get('dataset_type')}"
        planner_output = planner.plan(user_request, context_hint=context_hint)
        base_params = dict(payload.get("parameters", {})) if isinstance(payload, dict) else {}
        merged_parameters = {**base_params, **planner_output.parameters}
        agent_plan = None
        if dataset_obj:
            agent_plan = self.plan(dataset_obj, output_dir=payload.get("output_dir"), parameters=merged_parameters)
        return LLMPlanBundle(
            planner_output=planner_output,
            merged_parameters=merged_parameters,
            agent_plan=agent_plan,
            dataset=dataset_obj,
        )

    def plan_and_execute(
        self,
        request: AgentRequest,
        user_goal: Optional[str] = None,
        planner: Optional["LLMPlanner"] = None,
        confirm_step: Optional[ConfirmStepCallback] = None,
    ) -> AgentExecutionResult:
        dataset = load_dataset(request.dataset["dataset_type"], request.dataset)
        base_parameters = dict(request.parameters or {})
        active_plan = self.plan(dataset, output_dir=request.output_dir, parameters=base_parameters)
        planner_output: Optional["PlannerOutput"] = None

        if planner and user_goal:
            payload = {
                "dataset": request.dataset,
                "output_dir": request.output_dir,
                "parameters": base_parameters,
            }
            bundle = self.plan_with_llm(user_goal, planner, dataset_payload=payload)
            planner_output = bundle.planner_output
            merged = bundle.merged_parameters or {}
            if bundle.agent_plan:
                active_plan = bundle.agent_plan
            else:
                active_plan = self.plan(dataset, output_dir=request.output_dir, parameters=merged)
            base_parameters = dict(merged)

        if confirm_step:
            for idx, step in enumerate(active_plan.steps):
                if not confirm_step(step, idx):
                    raise RuntimeError(f"Execution aborted before step '{step.name}' was run")

        execution_request = AgentRequest(
            dataset=request.dataset,
            output_dir=request.output_dir or active_plan.workdir,
            parameters=base_parameters,
        )
        report = self.run(execution_request, plan=active_plan)
        return AgentExecutionResult(plan=active_plan, report=report, planner_output=planner_output)

    def run(self, request: AgentRequest, plan: Optional[AgentPlan] = None) -> PipelineReport:
        dataset = load_dataset(request.dataset["dataset_type"], request.dataset)
        base_parameters: Dict[str, Any] = dict(request.parameters or {})
        active_plan = plan
        parameter_map: Dict[str, Any] = {**(active_plan.parameters if active_plan else {}), **base_parameters}
        requested_output_dir = request.output_dir
        plan_mismatch = (
            active_plan is None
            or active_plan.dataset_id != dataset.dataset_id
            or active_plan.dataset_type != dataset.dataset_type
            or active_plan.parameters != parameter_map
            or (requested_output_dir and Path(active_plan.workdir) != Path(requested_output_dir))
        )
        target_output_dir = requested_output_dir or (active_plan.workdir if active_plan else None)
        if plan_mismatch:
            active_plan = self.plan(dataset, output_dir=target_output_dir, parameters=parameter_map)
        parameter_map = dict(active_plan.parameters)
        workdir = Path(active_plan.workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        pipeline = self._initialize_pipeline(dataset, workdir)
        warnings = list(active_plan.warnings)
        missing_tool_warning = next((w for w in warnings if "External tools missing" in w), None)
        if missing_tool_warning and not parameter_map.get("allow_missing_tools"):
            raise RuntimeError(missing_tool_warning)
        if warnings and any(msg.startswith("Missing input files") for msg in warnings) and not parameter_map.get("allow_missing_inputs"):
            missing_message = next(msg for msg in warnings if msg.startswith("Missing input files"))
            raise FileNotFoundError(missing_message)
        context = {
            "dataset": dataset,
            "dataset_id": dataset.dataset_id,
            "workdir": str(workdir),
            "executor": self.executor,
            "parameters": parameter_map,
            "warnings": warnings,
            "plan": active_plan.to_dict(),
        }
        report = pipeline.run(context)
        self._logger.info("Pipeline %s finished for %s (success=%s)", pipeline.name, dataset.dataset_id, report.success)
        return report

    def _get_pipeline_factory(self, dataset_type: str) -> Callable[[Dataset, Path], Pipeline]:
        try:
            return self.pipeline_registry[dataset_type]
        except KeyError as exc:
            raise ValueError(f"No pipeline registered for dataset_type {dataset_type}") from exc

    def _initialize_pipeline(self, dataset: Dataset, workdir: Path) -> Pipeline:
        pipeline_factory = self._get_pipeline_factory(dataset.dataset_type)
        pipeline = pipeline_factory(dataset, workdir)
        if hasattr(pipeline, "executor") and getattr(pipeline, "executor") is None:
            pipeline.executor = self.executor
        return pipeline
