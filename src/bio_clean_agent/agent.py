from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Dict, Optional

from .dataspec.models import Dataset, load_dataset
from .pipelines.base import Pipeline, PipelineReport, ToolExecutor
from .utils.logging import get_logger
from .utils.preflight import run_preflight_checks

if TYPE_CHECKING:
    from .llm import QwenPlanner


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

    def plan(self, dataset: Dataset, output_dir: Optional[str | Path] = None, parameters: Optional[Dict[str, object]] = None) -> Dict[str, object]:
        pipeline_factory = self._get_pipeline_factory(dataset.dataset_type)
        workdir = Path(output_dir or self.default_output_root / dataset.dataset_id)
        pipeline = pipeline_factory(dataset, workdir)
        steps = [{"name": step.name, "description": step.description} for step in pipeline.steps]
        parameter_map: Dict[str, object] = parameters or {}
        warnings = run_preflight_checks(dataset, parameter_map)
        return {
            "dataset_id": dataset.dataset_id,
            "dataset_type": dataset.dataset_type,
            "pipeline": pipeline.name,
            "workdir": str(workdir),
            "steps": steps,
            "parameters": parameter_map,
            "warnings": warnings,
        }

    def plan_with_llm(
        self,
        user_request: str,
        planner: "QwenPlanner",
        dataset_payload: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        payload = dataset_payload or {}
        dataset_section = payload.get("dataset") if isinstance(payload, dict) else None
        context_hint = None
        dataset_obj: Optional[Dataset] = None
        if dataset_section:
            dataset_obj = load_dataset(dataset_section["dataset_type"], dataset_section)
            context_hint = f"Dataset id={dataset_section.get('dataset_id')} type={dataset_section.get('dataset_type')}"
        planner_output = planner.plan(user_request, context_hint=context_hint)
        response: Dict[str, object] = {"planner": asdict(planner_output)}
        if dataset_obj:
            base_params = payload.get("parameters", {}) if isinstance(payload, dict) else {}
            merged_parameters = {**base_params, **planner_output.parameters}
            response["parameters"] = merged_parameters
            response["agent_plan"] = self.plan(
                dataset_obj, output_dir=payload.get("output_dir"), parameters=merged_parameters
            )
        return response

    def run(self, request: AgentRequest) -> PipelineReport:
        dataset = load_dataset(request.dataset["dataset_type"], request.dataset)
        workdir = Path(request.output_dir or self.default_output_root / dataset.dataset_id)
        workdir.mkdir(parents=True, exist_ok=True)
        pipeline_factory = self._get_pipeline_factory(dataset.dataset_type)
        pipeline = pipeline_factory(dataset, workdir)
        parameter_map = request.parameters or {}
        warnings = run_preflight_checks(dataset, parameter_map)
        if warnings and any(msg.startswith('Missing input files') for msg in warnings) and not parameter_map.get('allow_missing_inputs'):
            missing_message = next(msg for msg in warnings if msg.startswith('Missing input files'))
            raise FileNotFoundError(missing_message)
        context = {
            "dataset": dataset,
            "dataset_id": dataset.dataset_id,
            "workdir": str(workdir),
            "executor": self.executor,
            "parameters": parameter_map,
            "warnings": warnings,
        }
        if hasattr(pipeline, "executor") and getattr(pipeline, "executor") is None:
            pipeline.executor = self.executor
        report = pipeline.run(context)
        self._logger.info("Pipeline %s finished for %s (success=%s)", pipeline.name, dataset.dataset_id, report.success)
        return report

    def _get_pipeline_factory(self, dataset_type: str) -> Callable[[Dataset, Path], Pipeline]:
        try:
            return self.pipeline_registry[dataset_type]
        except KeyError as exc:
            raise ValueError(f"No pipeline registered for dataset_type {dataset_type}") from exc
