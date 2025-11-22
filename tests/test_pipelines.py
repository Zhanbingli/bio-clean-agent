"""Pipeline-level robustness tests."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

import pytest

from bio_clean_agent.pipelines.base import Pipeline, PipelineStep, StepResult
from bio_clean_agent.agent import SimulatedToolExecutor
from bio_clean_agent.dataspec.models import SequencingDataset
from bio_clean_agent.pipelines.sequencing import SequencingCleaningPipeline


def _make_fastq(tmp_path: Path, name: str = "reads.fastq") -> Path:
    path = tmp_path / name
    path.write_text("@id\nACGT\n+\n!!!!\n")
    return path


def test_sequencing_pipeline_requires_existing_inputs(tmp_path: Path) -> None:
    """Missing inputs should fail fast unless explicitly allowed."""
    pipeline = SequencingCleaningPipeline(executor=SimulatedToolExecutor(), output_dir=tmp_path)
    dataset = SequencingDataset(dataset_id="demo", raw_paths=["/no/such/file.fastq"], read_type="single", platform=None)

    with pytest.raises(FileNotFoundError):
        pipeline.run({"dataset": dataset, "parameters": {}})


def test_sequencing_pipeline_allow_missing_inputs(tmp_path: Path) -> None:
    """allow_missing_inputs lets dry runs proceed without real files."""
    pipeline = SequencingCleaningPipeline(executor=SimulatedToolExecutor(), output_dir=tmp_path)
    dataset = SequencingDataset(dataset_id="demo", raw_paths=["/no/such/file.fastq"], read_type="single", platform=None)

    report = pipeline.run({"dataset": dataset, "parameters": {"allow_missing_inputs": True}})

    assert report.success is True
    assert len(report.results) == 3  # all steps attempted


class _DummyExecutor(SimulatedToolExecutor):
    """Simulated executor that triggers missing-output checks."""

    def __init__(self, returncode: int = 0, stderr: str = ""):
        super().__init__(succeed=returncode == 0)
        self._rc = returncode
        self._stderr = stderr

    def run(self, command, workdir: str | None = None):  # type: ignore[override]
        return {"returncode": self._rc, "stdout": "simulated execution", "stderr": self._stderr}


def test_sequencing_pipeline_detects_missing_trimmed_outputs(tmp_path: Path) -> None:
    """When outputs are missing and executor is not the simulated one, fail with a helpful message."""
    executor = _DummyExecutor(returncode=0)
    pipeline = SequencingCleaningPipeline(executor=executor, output_dir=tmp_path)
    fastq = _make_fastq(tmp_path)
    dataset = SequencingDataset(dataset_id="demo", raw_paths=[str(fastq)], read_type="single", platform=None)

    report = pipeline.run({"dataset": dataset, "parameters": {}})

    assert report.success is False
    assert report.results[-1].name == "fastqc_post"
    assert "Trimmed file missing" in (report.results[-1].error or "")


def test_sequencing_run_command_hints_on_missing_tool(tmp_path: Path) -> None:
    """Missing external tool surfaces a diagnostic hint."""
    executor = _DummyExecutor(returncode=127, stderr="cutadapt: command not found")
    pipeline = SequencingCleaningPipeline(executor=executor, output_dir=tmp_path)
    result = pipeline._run_command("adapter_trimming", ["cutadapt", "-h"], tmp_path)  # type: ignore[attr-defined]

    assert result.success is False
    assert "Tool not found" in result.details.get("hint", "")


def test_pipeline_run_catches_step_exceptions(tmp_path: Path) -> None:
    """Exceptions inside steps become failed StepResult instead of crashing."""

    class FailingPipeline(Pipeline):
        name = "failing"
        dataset_type = "test"

        def __init__(self):
            super().__init__()
            self.add_step(PipelineStep("boom", "explode", self._boom))

        def _boom(self, context: Dict) -> StepResult:
            raise RuntimeError("boom!")

    pipeline = FailingPipeline()
    report = pipeline.run({"dataset_id": "demo"})

    assert report.success is False
    assert report.results[0].name == "boom"
    assert "boom!" in (report.results[0].error or "")
    assert report.results[0].details.get("exception_type") == "RuntimeError"
