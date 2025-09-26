"""Helper routines for scaffolding dataset configuration files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .utils.io import detect_delimiter, normalise_paths, read_text_header


SEQUENCING_EXTENSIONS = {".fastq", ".fastq.gz", ".fq", ".fq.gz"}
TABULAR_EXTENSIONS = {".csv", ".tsv", ".txt"}


@dataclass
class WizardContext:
    dataset_type: str
    dataset_id: str
    raw_paths: List[str]
    output_dir: str
    report_dir: Optional[str] = None
    parameters: Dict[str, object] = field(default_factory=dict)
    extras: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        payload: Dict[str, object] = {
            "dataset": {
                "dataset_id": self.dataset_id,
                "dataset_type": self.dataset_type,
                "raw_paths": self.raw_paths,
            },
            "output_dir": self.output_dir,
        }
        if self.report_dir:
            payload["report_dir"] = self.report_dir
        if self.parameters:
            payload["parameters"] = self.parameters
        payload["dataset"].update(self.extras)
        return payload


def guess_dataset_type(paths: Iterable[str | Path]) -> Optional[str]:
    paths = list(paths)
    if not paths:
        return None
    lower_exts = {Path(path).suffix.lower() for path in paths}
    if any(ext in SEQUENCING_EXTENSIONS for ext in lower_exts):
        return "sequencing"
    if lower_exts.issubset(TABULAR_EXTENSIONS):
        header = read_text_header(paths[0])
        if "Metabolite name" in header or "metabolite" in header.lower():
            return "metabolomics"
        return "transcriptomics"
    return None


def suggest_parameters(dataset_type: str, file_path: str) -> Dict[str, object]:
    if dataset_type == "metabolomics":
        header = read_text_header(file_path)
        delimiter = detect_delimiter(header)
        return {
            "qc_threshold": 0.2,
            "normalization": "pqn",
            "detected_delimiter": delimiter,
        }
    if dataset_type == "transcriptomics":
        return {
            "min_counts": 10,
            "min_cells": 3,
            "normalization": "log1p",
        }
    if dataset_type == "sequencing":
        return {
            "quality_threshold": 20,
            "adapter_sequence": "",
        }
    return {}


def build_context(
    dataset_paths: Iterable[str | Path],
    dataset_type: str,
    dataset_id: str,
    output_dir: str | Path,
    report_dir: Optional[str | Path] = None,
    parameters: Optional[Dict[str, object]] = None,
    extras: Optional[Dict[str, object]] = None,
) -> WizardContext:
    raw_paths = normalise_paths(dataset_paths)
    context = WizardContext(
        dataset_type=dataset_type,
        dataset_id=dataset_id,
        raw_paths=raw_paths,
        output_dir=str(Path(output_dir).expanduser().resolve()),
        report_dir=str(Path(report_dir).expanduser().resolve()) if report_dir else None,
        parameters=parameters or {},
        extras=extras or {},
    )
    return context
