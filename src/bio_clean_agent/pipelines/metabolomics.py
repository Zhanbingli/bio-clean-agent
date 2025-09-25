from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer

from .base import Pipeline, PipelineStep, StepResult


class MetabolomicsCleaningPipeline(Pipeline):
    name = "metabolomics_cleaning"
    dataset_type = "metabolomics"

    def __init__(self, output_dir: str | Path, knn_neighbors: int = 5, qc_threshold: float = 0.2):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.knn_neighbors = knn_neighbors
        self.qc_threshold = qc_threshold
        self.add_step(PipelineStep("load_table", "Load metabolite intensity table", self.load_table))
        self.add_step(PipelineStep("qc_filter", "Remove metabolites with excessive missingness", self.qc_filter))
        self.add_step(PipelineStep("impute", "Impute missing values using KNN", self.impute))
        self.add_step(PipelineStep("normalize", "Normalize by probabilistic quotient", self.normalize))
        self.add_step(PipelineStep("export", "Export cleaned metabolomics table", self.export))

    def validate_context(self, context: Dict) -> None:
        if "dataset" not in context:
            raise ValueError("Metabolomics pipeline requires 'dataset' in context")
        dataset = context["dataset"]
        if not dataset.raw_paths:
            raise ValueError("Metabolomics dataset needs an intensity table path")
        context.setdefault("workdir", str(self.output_dir))
        Path(context["workdir"]).mkdir(parents=True, exist_ok=True)

    def load_table(self, context: Dict) -> StepResult:
        dataset = context["dataset"]
        table_path = dataset.raw_paths[0]
        try:
            df = pd.read_csv(table_path, index_col=0)
        except Exception as exc:
            return StepResult(name="load_table", success=False, error=str(exc))
        context.setdefault("frames", {})["intensity"] = df
        return StepResult(name="load_table", success=True, details={"shape": df.shape})

    def qc_filter(self, context: Dict) -> StepResult:
        df = context.get("frames", {}).get("intensity")
        if df is None:
            return StepResult(name="qc_filter", success=False, error="Intensity table not loaded")
        params = context.get("parameters", {})
        threshold = params.get("qc_threshold", self.qc_threshold)
        missing_fraction = df.isna().mean(axis=1)
        keep_mask = missing_fraction <= threshold
        filtered = df.loc[keep_mask]
        context["frames"]["intensity"] = filtered
        removed = int((~keep_mask).sum())
        return StepResult(name="qc_filter", success=True, details={"removed_metabolites": removed, "remaining": filtered.shape[0]})

    def impute(self, context: Dict) -> StepResult:
        df = context.get("frames", {}).get("intensity")
        if df is None:
            return StepResult(name="impute", success=False, error="Intensity table not loaded")
        params = context.get("parameters", {})
        neighbors = params.get("knn_neighbors", self.knn_neighbors)
        imputer = KNNImputer(n_neighbors=neighbors)
        imputed_array = imputer.fit_transform(df)
        imputed = pd.DataFrame(imputed_array, index=df.index, columns=df.columns)
        context["frames"]["imputed"] = imputed
        return StepResult(name="impute", success=True, details={"imputed_fraction": float(np.mean(df.isna()))})

    def normalize(self, context: Dict) -> StepResult:
        matrix = context.get("frames", {}).get("imputed")
        if matrix is None:
            return StepResult(name="normalize", success=False, error="Imputed matrix not available")
        params = context.get("parameters", {})
        method = params.get("normalization", "pqn")
        if method == "pqn":
            ref = matrix.median(axis=0)
            scaled = matrix.divide(ref, axis=1)
            quotients = scaled.median(axis=0)
            normalized = matrix.divide(quotients, axis=1)
            detail = {"median_quotient": float(quotients.median())}
        elif method == "log":
            normalized = np.log1p(matrix)
            detail = {"transform": "log1p"}
        else:
            return StepResult(name="normalize", success=False, error=f"Unsupported normalization method {method}")
        context["frames"]["normalized"] = normalized
        return StepResult(name="normalize", success=True, details=detail)

    def export(self, context: Dict) -> StepResult:
        matrix = context.get("frames", {}).get("normalized")
        if matrix is None:
            return StepResult(name="export", success=False, error="No normalized matrix to export")
        workdir = Path(context["workdir"])
        out_path = workdir / f"{context['dataset'].dataset_id}_metabolomics.csv"
        matrix.to_csv(out_path)
        context.setdefault("products", {})["metabolomics_table"] = str(out_path)
        return StepResult(name="export", success=True, details={"path": str(out_path)})
