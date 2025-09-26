from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from .base import Pipeline, PipelineStep, StepResult
from ..utils.io import detect_delimiter, read_text_header


class TranscriptomicsCleaningPipeline(Pipeline):
    name = "transcriptomics_cleaning"
    dataset_type = "transcriptomics"

    def __init__(self, output_dir: str | Path, min_counts: int = 10, min_cells: int = 3):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.min_counts = min_counts
        self.min_cells = min_cells
        self.add_step(PipelineStep("load_matrix", "Load expression matrix", self.load_matrix))
        self.add_step(PipelineStep("filter_genes", "Filter lowly expressed genes", self.filter_genes))
        self.add_step(PipelineStep("normalize", "Log normalize counts", self.normalize))
        self.add_step(PipelineStep("batch_correct", "Correct batch effects if metadata supplied", self.batch_correct))
        self.add_step(PipelineStep("export", "Export cleaned matrix", self.export))

    def validate_context(self, context: Dict) -> None:
        if "dataset" not in context:
            raise ValueError("Transcriptomics pipeline requires 'dataset' in context")
        dataset = context["dataset"]
        if not dataset.raw_paths:
            raise ValueError("Transcriptomics dataset needs at least one matrix path")
        context.setdefault("workdir", str(self.output_dir))
        Path(context["workdir"]).mkdir(parents=True, exist_ok=True)

    def load_matrix(self, context: Dict) -> StepResult:
        dataset = context["dataset"]
        matrix_path = dataset.raw_paths[0]
        try:
            df = pd.read_csv(matrix_path, index_col=0)
        except Exception as exc:
            header = read_text_header(matrix_path)
            delimiter = detect_delimiter(header, fallback=",")
            try:
                df = pd.read_csv(matrix_path, index_col=0, sep=delimiter)
            except Exception as retry_exc:
                return StepResult(name="load_matrix", success=False, error=str(retry_exc))
        context.setdefault("frames", {})["counts"] = df
        return StepResult(name="load_matrix", success=True, details={"shape": df.shape})

    def filter_genes(self, context: Dict) -> StepResult:
        df = context.get("frames", {}).get("counts")
        if df is None:
            return StepResult(name="filter_genes", success=False, error="Counts matrix not loaded")
        params = context.get("parameters", {})
        min_counts = params.get("min_counts", self.min_counts)
        min_cells = params.get("min_cells", self.min_cells)
        mask = (df.sum(axis=1) >= min_counts) & ((df > 0).sum(axis=1) >= min_cells)
        filtered = df.loc[mask]
        context["frames"]["counts"] = filtered
        removed = int(df.shape[0] - filtered.shape[0])
        return StepResult(name="filter_genes", success=True, details={"remaining_genes": filtered.shape[0], "removed_genes": removed})

    def normalize(self, context: Dict) -> StepResult:
        df = context.get("frames", {}).get("counts")
        if df is None:
            return StepResult(name="normalize", success=False, error="Counts matrix not loaded")
        params = context.get("parameters", {})
        method = params.get("normalization", "log1p")
        if method == "log1p":
            normalized = np.log1p(df)
        elif method == "cpm":
            counts_per_million = df.div(df.sum(axis=0), axis=1) * 1e6
            normalized = counts_per_million
        else:
            return StepResult(name="normalize", success=False, error=f"Unsupported normalization method {method}")
        context["frames"]["normalized"] = normalized
        return StepResult(name="normalize", success=True, details={"max_value": float(normalized.to_numpy().max())})

    def batch_correct(self, context: Dict) -> StepResult:
        dataset = context["dataset"]
        if not dataset.metadata_path:
            return StepResult(name="batch_correct", success=True, details={"skipped": True})
        try:
            metadata = pd.read_csv(dataset.metadata_path, index_col=0)
        except Exception as exc:
            return StepResult(name="batch_correct", success=False, error=str(exc))
        if "batch" not in metadata.columns:
            return StepResult(name="batch_correct", success=True, details={"skipped": True})
        params = context.get("parameters", {})
        if params.get("skip_batch_correction"):
            return StepResult(name="batch_correct", success=True, details={"skipped": True})
        normalized = context.get("frames", {}).get("normalized")
        if normalized is None:
            return StepResult(name="batch_correct", success=False, error="Normalized matrix not available")
        shared = normalized.columns.intersection(metadata.index)
        if shared.empty:
            return StepResult(name="batch_correct", success=False, error="No overlapping samples between data and metadata")
        normalized = normalized[shared]
        metadata = metadata.loc[shared]
        corrected = self._zscore_by_batch(normalized, metadata["batch"].astype(str))
        context["frames"]["corrected"] = corrected
        return StepResult(name="batch_correct", success=True, details={"batches": metadata["batch"].nunique()})

    def export(self, context: Dict) -> StepResult:
        frame_key = "corrected" if "corrected" in context.get("frames", {}) else "normalized"
        matrix = context.get("frames", {}).get(frame_key)
        if matrix is None:
            return StepResult(name="export", success=False, error="No matrix available for export")
        workdir = Path(context["workdir"])
        out_path = workdir / f"{context['dataset'].dataset_id}_{frame_key}.csv"
        matrix.to_csv(out_path)
        context.setdefault("products", {})["expression_matrix"] = str(out_path)
        return StepResult(name="export", success=True, details={"path": str(out_path)})

    def _zscore_by_batch(self, matrix: pd.DataFrame, batches: pd.Series) -> pd.DataFrame:
        result = matrix.copy()
        for batch, idx in batches.groupby(batches).groups.items():
            subset = result[idx]
            centered = subset.subtract(subset.mean(axis=1), axis=0)
            std = subset.std(axis=1).replace(0, 1)
            result[idx] = centered.divide(std, axis=0)
        return result
