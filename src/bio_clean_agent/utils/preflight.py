from __future__ import annotations

from pathlib import Path
from shutil import which
from typing import Any, Dict, List

from ..dataspec.models import Dataset
from .storage import estimate_dataset_size, format_bytes


def _warn_missing_tools(tools: List[str], warnings: List[str], parameters: Dict[str, Any]) -> None:
    """Append warnings when required external tools are unavailable."""
    if parameters.get("skip_tool_checks"):
        return
    missing = [tool for tool in tools if which(tool) is None]
    if missing:
        formatted = ", ".join(sorted(missing))
        warnings.append(
            f"External tools missing from PATH: {formatted}. "
            "Install them or set 'skip_tool_checks' to disable this warning."
        )


def run_preflight_checks(dataset: Dataset, parameters: Dict[str, Any] | None = None) -> List[str]:
    """Return human-readable warnings detected before running a pipeline."""
    parameters = parameters or {}
    warnings: List[str] = []

    size_bytes = estimate_dataset_size(dataset.raw_paths)
    if size_bytes:
        limit = parameters.get('max_dataset_bytes')
        if limit and size_bytes > limit:
            warnings.append(
                f"Dataset size {format_bytes(size_bytes)} exceeds configured max_dataset_bytes {format_bytes(limit)}."
            )
        elif size_bytes > parameters.get('large_dataset_warning_bytes', 200 * 1024 ** 3):
            warnings.append(
                f"Large dataset detected (~{format_bytes(size_bytes)}); ensure disk and memory are provisioned or enable chunking."
            )

    missing = [path for path in dataset.raw_paths if not Path(path).exists()]
    if missing:
        warnings.append(
            "Missing input files: " + ", ".join(missing) + ". Set 'allow_missing_inputs' to proceed anyway."
        )

    if dataset.dataset_type == "sequencing":
        if getattr(dataset, "read_type", "single") == "paired" and len(dataset.raw_paths) != 2:
            warnings.append("Paired-end sequencing data should provide exactly two FASTQ files.")
        adapter = (parameters or {}).get("adapter_sequence")
        if not adapter:
            warnings.append("No adapter sequence provided; trimming may be suboptimal.")
        _warn_missing_tools(["fastqc", "cutadapt"], warnings, parameters)

    if dataset.dataset_type == "transcriptomics":
        if dataset.metadata_path and not Path(dataset.metadata_path).exists():
            warnings.append(f"Metadata file not found: {dataset.metadata_path}")
        format_hint = getattr(dataset, "matrix_format", None)
        if format_hint == "counts" and parameters.get("normalization") == "log1p":
            warnings.append("Log1p normalization assumes raw counts; verify input is not already normalized.")

    if dataset.dataset_type == "metabolomics":
        if parameters.get("qc_threshold", 0.2) > 0.4:
            warnings.append("QC threshold above 0.4 may retain too many metabolites with missing values.")

    return warnings
