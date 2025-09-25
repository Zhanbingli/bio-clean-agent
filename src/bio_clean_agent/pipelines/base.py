from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional


@dataclass
class StepResult:
    """Outcome of a single pipeline step."""

    name: str
    success: bool
    details: Dict[str, object] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class PipelineReport:
    """Aggregate report produced after running a pipeline."""

    pipeline_name: str
    dataset_id: str
    results: List[StepResult]

    @property
    def success(self) -> bool:
        return all(step.success for step in self.results)

    def summary(self) -> Dict[str, object]:
        return {
            "pipeline": self.pipeline_name,
            "dataset_id": self.dataset_id,
            "success": self.success,
            "steps": [step.__dict__ for step in self.results],
        }


class PipelineStep:
    """A callable pipeline step with metadata."""

    def __init__(self, name: str, description: str, action: Callable[[dict], StepResult]):
        self.name = name
        self.description = description
        self._action = action

    def run(self, context: dict) -> StepResult:
        return self._action(context)


class Pipeline:
    """Base pipeline orchestrating ordered steps."""

    name: str = "pipeline"
    dataset_type: str = "generic"

    def __init__(self) -> None:
        self.steps: List[PipelineStep] = []

    def add_step(self, step: PipelineStep) -> None:
        self.steps.append(step)

    def validate_context(self, context: dict) -> None:
        """Optional validation hook."""

    def build_steps(self, context: dict) -> Iterable[PipelineStep]:
        if not self.steps:
            raise ValueError(f"No steps configured for pipeline {self.name}")
        return self.steps

    def run(self, context: dict) -> PipelineReport:
        self.validate_context(context)
        results: List[StepResult] = []
        for step in self.build_steps(context):
            result = step.run(context)
            context.setdefault("results", {})[step.name] = result
            results.append(result)
            if not result.success:
                break
        return PipelineReport(pipeline_name=self.name, dataset_id=context.get("dataset_id", "unknown"), results=results)


class ToolExecutor:
    """Interface for executing external tools; can be mocked in tests."""

    def run(self, command: List[str], workdir: Optional[str] = None) -> Dict[str, object]:
        raise NotImplementedError
