"""Handler for clinical trial data cleaning."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np


class ClinicalTrialHandler:
    """
    Specialized handler for clinical trial data.

    Handles common clinical trial data issues:
    - Missing patient data
    - Inconsistent visit dates
    - Out-of-range vital signs
    - Protocol deviations
    - Adverse event reporting
    """

    def __init__(self, data_path: str | Path):
        self.data_path = Path(data_path)
        self.df: Optional[pd.DataFrame] = None
        self.issues: List[Dict[str, Any]] = []
        self.cleaning_log: List[Dict[str, Any]] = []

    def load_data(self) -> pd.DataFrame:
        """Load clinical trial data from CSV or Excel."""
        if self.data_path.suffix in {".csv", ".txt"}:
            self.df = pd.read_csv(self.data_path)
        elif self.data_path.suffix in {".xlsx", ".xls"}:
            self.df = pd.read_excel(self.data_path)
        else:
            raise ValueError(f"Unsupported file format: {self.data_path.suffix}")

        return self.df

    def profile_data(self) -> Dict[str, Any]:
        """Generate data profile report."""
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")

        profile = {
            "total_records": len(self.df),
            "total_columns": len(self.df.columns),
            "missing_values": {},
            "data_types": {},
            "numeric_summary": {},
            "categorical_summary": {},
        }

        # Missing values analysis
        for col in self.df.columns:
            missing_count = self.df[col].isna().sum()
            if missing_count > 0:
                profile["missing_values"][col] = {
                    "count": int(missing_count),
                    "percentage": float(missing_count / len(self.df) * 100),
                }

        # Data types
        for col in self.df.columns:
            profile["data_types"][col] = str(self.df[col].dtype)

        # Numeric summary
        numeric_cols = self.df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            profile["numeric_summary"][col] = {
                "mean": float(self.df[col].mean()),
                "median": float(self.df[col].median()),
                "std": float(self.df[col].std()),
                "min": float(self.df[col].min()),
                "max": float(self.df[col].max()),
            }

        # Categorical summary
        categorical_cols = self.df.select_dtypes(include=["object"]).columns
        for col in categorical_cols:
            value_counts = self.df[col].value_counts()
            profile["categorical_summary"][col] = {
                "unique_values": int(self.df[col].nunique()),
                "top_values": value_counts.head(5).to_dict(),
            }

        return profile

    def detect_issues(self) -> List[Dict[str, Any]]:
        """Detect data quality issues specific to clinical trials."""
        if self.df is None:
            raise ValueError("Data not loaded.")

        self.issues = []

        # 1. Check for missing patient IDs
        if "patient_id" in self.df.columns:
            missing_ids = self.df["patient_id"].isna().sum()
            if missing_ids > 0:
                self.issues.append({
                    "severity": "critical",
                    "category": "missing_data",
                    "field": "patient_id",
                    "message": f"{missing_ids} records missing patient ID",
                    "count": int(missing_ids),
                })

        # 2. Check for duplicate patient visits
        if {"patient_id", "visit_date"}.issubset(self.df.columns):
            duplicates = self.df.duplicated(subset=["patient_id", "visit_date"], keep=False)
            dup_count = duplicates.sum()
            if dup_count > 0:
                self.issues.append({
                    "severity": "high",
                    "category": "duplicates",
                    "field": "patient_id,visit_date",
                    "message": f"{dup_count} duplicate patient visits detected",
                    "count": int(dup_count),
                })

        # 3. Check vital signs ranges
        vital_ranges = {
            "systolic_bp": (70, 200),
            "diastolic_bp": (40, 130),
            "heart_rate": (40, 150),
            "temperature": (35.0, 42.0),
            "weight": (20, 300),  # kg
        }

        for col, (min_val, max_val) in vital_ranges.items():
            if col in self.df.columns:
                out_of_range = (
                    (self.df[col] < min_val) | (self.df[col] > max_val)
                ).sum()
                if out_of_range > 0:
                    self.issues.append({
                        "severity": "medium",
                        "category": "out_of_range",
                        "field": col,
                        "message": f"{out_of_range} values outside normal range ({min_val}-{max_val})",
                        "count": int(out_of_range),
                        "valid_range": (min_val, max_val),
                    })

        # 4. Check date consistency
        if {"enrollment_date", "visit_date"}.issubset(self.df.columns):
            self.df["enrollment_date"] = pd.to_datetime(self.df["enrollment_date"], errors="coerce")
            self.df["visit_date"] = pd.to_datetime(self.df["visit_date"], errors="coerce")

            invalid_dates = (self.df["visit_date"] < self.df["enrollment_date"]).sum()
            if invalid_dates > 0:
                self.issues.append({
                    "severity": "high",
                    "category": "date_inconsistency",
                    "field": "visit_date",
                    "message": f"{invalid_dates} visits dated before enrollment",
                    "count": int(invalid_dates),
                })

        # 5. Check for missing required fields
        required_fields = ["patient_id", "visit_date", "treatment_arm"]
        for field in required_fields:
            if field in self.df.columns:
                missing = self.df[field].isna().sum()
                if missing > 0:
                    self.issues.append({
                        "severity": "critical",
                        "category": "missing_required",
                        "field": field,
                        "message": f"Required field '{field}' has {missing} missing values",
                        "count": int(missing),
                    })

        return self.issues

    def clean_duplicates(self, keep: str = "first") -> int:
        """Remove duplicate records."""
        if self.df is None:
            raise ValueError("Data not loaded.")

        original_count = len(self.df)

        if {"patient_id", "visit_date"}.issubset(self.df.columns):
            self.df = self.df.drop_duplicates(
                subset=["patient_id", "visit_date"],
                keep=keep
            )

        removed_count = original_count - len(self.df)

        if removed_count > 0:
            self.cleaning_log.append({
                "action": "remove_duplicates",
                "records_removed": removed_count,
                "strategy": keep,
            })

        return removed_count

    def handle_missing_values(
        self,
        column: str,
        strategy: str = "drop",
        fill_value: Any = None
    ) -> int:
        """
        Handle missing values in a specific column.

        Args:
            column: Column name
            strategy: One of "drop", "mean", "median", "mode", "constant"
            fill_value: Value to use for "constant" strategy
        """
        if self.df is None:
            raise ValueError("Data not loaded.")

        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found.")

        original_missing = self.df[column].isna().sum()

        if strategy == "drop":
            self.df = self.df.dropna(subset=[column])
            action = f"Dropped {original_missing} rows"

        elif strategy == "mean":
            fill_val = self.df[column].mean()
            self.df[column].fillna(fill_val, inplace=True)
            action = f"Filled with mean ({fill_val:.2f})"

        elif strategy == "median":
            fill_val = self.df[column].median()
            self.df[column].fillna(fill_val, inplace=True)
            action = f"Filled with median ({fill_val:.2f})"

        elif strategy == "mode":
            fill_val = self.df[column].mode()[0]
            self.df[column].fillna(fill_val, inplace=True)
            action = f"Filled with mode ({fill_val})"

        elif strategy == "constant":
            self.df[column].fillna(fill_value, inplace=True)
            action = f"Filled with constant ({fill_value})"

        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        self.cleaning_log.append({
            "action": "handle_missing_values",
            "column": column,
            "strategy": strategy,
            "records_affected": int(original_missing),
            "details": action,
        })

        return int(original_missing)

    def validate_vital_signs(self, column: str, min_val: float, max_val: float, action: str = "flag") -> int:
        """
        Validate vital signs are within acceptable ranges.

        Args:
            column: Vital sign column name
            min_val: Minimum acceptable value
            max_val: Maximum acceptable value
            action: "flag" or "cap" or "remove"
        """
        if self.df is None:
            raise ValueError("Data not loaded.")

        if column not in self.df.columns:
            raise ValueError(f"Column '{column}' not found.")

        out_of_range = (self.df[column] < min_val) | (self.df[column] > max_val)
        count = out_of_range.sum()

        if action == "flag":
            flag_col = f"{column}_out_of_range"
            self.df[flag_col] = out_of_range

        elif action == "cap":
            self.df[column] = self.df[column].clip(lower=min_val, upper=max_val)

        elif action == "remove":
            self.df = self.df[~out_of_range]

        self.cleaning_log.append({
            "action": "validate_vital_signs",
            "column": column,
            "range": (min_val, max_val),
            "strategy": action,
            "records_affected": int(count),
        })

        return int(count)

    def save_cleaned_data(self, output_path: str | Path) -> None:
        """Save cleaned data."""
        if self.df is None:
            raise ValueError("No data to save.")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix == ".csv":
            self.df.to_csv(output_path, index=False)
        elif output_path.suffix in {".xlsx", ".xls"}:
            self.df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")

    def get_cleaning_summary(self) -> Dict[str, Any]:
        """Get summary of cleaning operations performed."""
        return {
            "total_operations": len(self.cleaning_log),
            "operations": self.cleaning_log,
            "final_record_count": len(self.df) if self.df is not None else 0,
            "issues_detected": len(self.issues),
            "issues": self.issues,
        }
