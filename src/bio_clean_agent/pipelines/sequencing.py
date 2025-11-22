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
        if dataset.read_type == "paired" and len(dataset.raw_paths) != 2:
            raise ValueError("Paired-end sequencing data must include exactly two FASTQ files")
        allow_missing = context.get("parameters", {}).get("allow_missing_inputs", False)
        self._ensure_inputs_exist(dataset.raw_paths, allow_missing=allow_missing)
        context.setdefault("workdir", str(self.output_dir))
        Path(context["workdir"]).mkdir(parents=True, exist_ok=True)

    def fastqc_pre(self, context: Dict) -> StepResult:
        dataset = context["dataset"]
        allow_missing = context.get("parameters", {}).get("allow_missing_inputs", False)
        self._ensure_inputs_exist(dataset.raw_paths, allow_missing=allow_missing, step="fastqc_pre")
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
        allow_missing = context.get("parameters", {}).get("allow_missing_inputs", False)
        self._ensure_inputs_exist(dataset.raw_paths, allow_missing=allow_missing, step="adapter_trimming")
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
        if not self._should_skip_output_check(context):
            for path in trimmed_files:
                if not Path(path).exists():
                    return StepResult(
                        name="fastqc_post",
                        success=False,
                        error=f"Trimmed file missing before QC: {path}",
                        details={"expected_files": trimmed_files},
                    )
        workdir = Path(context["workdir"]) / "fastqc_post"
        workdir.mkdir(parents=True, exist_ok=True)
        params = context.get("parameters", {})
        threads = params.get("fastqc_threads") or params.get("threads")
        command = ["fastqc", "-o", str(workdir)]
        if threads:
            command.extend(["--threads", str(threads)])
        command.extend(trimmed_files)
        return self._run_command("fastqc_post", command, workdir)

    def _ensure_inputs_exist(self, paths: List[str], allow_missing: bool = False, step: str | None = None) -> None:
        if allow_missing:
            return
        missing = [p for p in paths if not Path(p).exists()]
        if missing:
            suffix = f" for step '{step}'" if step else ""
            raise FileNotFoundError(f"Input files missing{suffix}: {', '.join(missing)}")

    def _run_command(self, name: str, command: List[str], workdir: Path) -> StepResult:
        try:
            exec_result = self.executor.run(command, workdir=str(workdir))
        except Exception as exc:  # pragma: no cover - defensive
            return StepResult(name=name, success=False, error=str(exc))
        success = exec_result.get("returncode", 1) == 0
        stderr = exec_result.get("stderr", "") or ""
        hint = None
        if not success:
            rc = exec_result.get("returncode", 1)
            lower_err = stderr.lower()
            if rc in (126, 127) or "not found" in lower_err:
                hint = "Tool not found or not executable; ensure required binaries are installed and on PATH."
            elif "permission denied" in lower_err:
                hint = "Permission denied running tool; check file permissions or container sandbox."
            else:
                hint = "Command failed; inspect stderr/stdout for details."
        details = {
            "command": " ".join(command),
            "stdout": exec_result.get("stdout", ""),
            "returncode": exec_result.get("returncode", ""),
        }
        if hint:
            details["hint"] = hint
        if stderr:
            details["stderr_snippet"] = stderr[:400]
        error = exec_result.get("stderr") if not success else None
        return StepResult(name=name, success=success, details=details, error=error)

    def _should_skip_output_check(self, context: Dict) -> bool:
        """
        Skip output existence checks when explicitly requested or when using a simulated executor.
        """
        params = context.get("parameters", {})
        if params.get("skip_output_checks"):
            return True
        return self.executor.__class__.__name__ == "SimulatedToolExecutor"
