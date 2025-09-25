from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from .base import Pipeline, PipelineStep, StepResult, ToolExecutor


class SequencingCleaningPipeline(Pipeline):
    name = "sequencing_cleaning"
    dataset_type = "sequencing"

    def __init__(self, executor: ToolExecutor, output_dir: str | Path):
        super().__init__()
        self.executor = executor
        self.output_dir = Path(output_dir)
        self.add_step(PipelineStep("fastqc_pre", "Initial quality control", self.fastqc_pre))
        self.add_step(PipelineStep("adapter_trimming", "Adapter and quality trimming", self.adapter_trimming))
        self.add_step(PipelineStep("fastqc_post", "Post-trimming quality control", self.fastqc_post))

    def validate_context(self, context: Dict) -> None:
        if "dataset" not in context:
            raise ValueError("Sequencing pipeline requires 'dataset' in context")
        dataset = context["dataset"]
        if not dataset.raw_paths:
            raise ValueError("Sequencing dataset must contain raw FASTQ paths")
        context.setdefault("workdir", str(self.output_dir))
        Path(context["workdir"]).mkdir(parents=True, exist_ok=True)

    def fastqc_pre(self, context: Dict) -> StepResult:
        dataset = context["dataset"]
        workdir = Path(context["workdir"]) / "fastqc_pre"
        workdir.mkdir(parents=True, exist_ok=True)
        params = context.get("parameters", {})
        threads = params.get("fastqc_threads") or params.get("threads")
        command: List[str] = ["fastqc", "-o", str(workdir)]
        if threads:
            command.extend(["--threads", str(threads)])
        command.extend(dataset.raw_paths)
        return self._run_command("fastqc_pre", command, workdir)

    def adapter_trimming(self, context: Dict) -> StepResult:
        dataset = context["dataset"]
        workdir = Path(context["workdir"]) / "trimmed"
        workdir.mkdir(parents=True, exist_ok=True)
        output_files = []
        params = context.get("parameters", {})
        quality = str(params.get("quality_threshold", 20))
        min_length = str(params.get("min_length", 30))
        adapter = params.get("adapter_sequence")
        threads = params.get("threads")
        if dataset.read_type == "paired":
            if len(dataset.raw_paths) != 2:
                return StepResult(name="adapter_trimming", success=False, error="Paired data must supply two FASTQ files")
            trimmed1 = workdir / "trimmed_R1.fastq.gz"
            trimmed2 = workdir / "trimmed_R2.fastq.gz"
            command = [
                "cutadapt",
                "-q",
                quality,
                "-m",
                min_length,
                "-o",
                str(trimmed1),
                "-p",
                str(trimmed2),
                *dataset.raw_paths,
            ]
            output_files = [str(trimmed1), str(trimmed2)]
        else:
            trimmed = workdir / "trimmed.fastq.gz"
            command = ["cutadapt", "-q", quality, "-m", min_length, "-o", str(trimmed), dataset.raw_paths[0]]
            output_files = [str(trimmed)]
        if adapter:
            command.insert(1, "-a")
            command.insert(2, adapter)
        if threads:
            command.insert(1, str(threads))
            command.insert(1, "-j")
        result = self._run_command("adapter_trimming", command, workdir)
        if result.success:
            result.details["trimmed_files"] = output_files
            context.setdefault("products", {})["trimmed_fastq"] = output_files
        return result

    def fastqc_post(self, context: Dict) -> StepResult:
        trimmed_files = context.get("products", {}).get("trimmed_fastq")
        if not trimmed_files:
            return StepResult(name="fastqc_post", success=False, error="No trimmed files found; did trimming succeed?")
        workdir = Path(context["workdir"]) / "fastqc_post"
        workdir.mkdir(parents=True, exist_ok=True)
        params = context.get("parameters", {})
        threads = params.get("fastqc_threads") or params.get("threads")
        command = ["fastqc", "-o", str(workdir)]
        if threads:
            command.extend(["--threads", str(threads)])
        command.extend(trimmed_files)
        return self._run_command("fastqc_post", command, workdir)

    def _run_command(self, name: str, command: List[str], workdir: Path) -> StepResult:
        try:
            exec_result = self.executor.run(command, workdir=str(workdir))
        except Exception as exc:  # pragma: no cover - defensive
            return StepResult(name=name, success=False, error=str(exc))
        success = exec_result.get("returncode", 1) == 0
        details = {
            "command": " ".join(command),
            "stdout": exec_result.get("stdout", ""),
        }
        error = exec_result.get("stderr") if not success else None
        return StepResult(name=name, success=success, details=details, error=error)
