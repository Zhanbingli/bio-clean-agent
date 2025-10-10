"""Handler for medical imaging metadata."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd


class ImagingMetadataHandler:
    """
    Handler for medical imaging metadata (DICOM tags, scan parameters).

    Note: This handles metadata CSV/Excel files, not actual DICOM files.
    For DICOM file processing, use pydicom library separately.
    """

    def __init__(self, data_path: str | Path):
        self.data_path = Path(data_path)
        self.df: Optional[pd.DataFrame] = None
        self.issues: List[Dict[str, Any]] = []

    def load_data(self) -> pd.DataFrame:
        """Load imaging metadata."""
        if self.data_path.suffix == ".csv":
            self.df = pd.read_csv(self.data_path)
        elif self.data_path.suffix in {".xlsx", ".xls"}:
            self.df = pd.read_excel(self.data_path)
        else:
            raise ValueError(f"Unsupported format: {self.data_path.suffix}")

        return self.df

    def validate_modality(self, modality_column: str = "modality") -> Dict[str, Any]:
        """
        Validate imaging modality values.

        Standard modalities: CT, MRI, PET, US, XR, etc.
        """
        if self.df is None or modality_column not in self.df.columns:
            return {"valid": 0, "invalid": 0}

        valid_modalities = {
            "CT", "MR", "MRI", "PT", "PET", "US", "XR", "CR", "DX",
            "MG", "NM", "OT", "RF", "SC"
        }

        is_valid = self.df[modality_column].str.upper().isin(valid_modalities)
        valid_count = is_valid.sum()
        invalid_count = (~is_valid).sum()

        return {
            "valid": int(valid_count),
            "invalid": int(invalid_count),
            "unique_modalities": list(self.df[modality_column].unique()),
        }

    def check_scan_parameters(self) -> List[Dict[str, Any]]:
        """Check for missing or invalid scan parameters."""
        if self.df is None:
            return []

        issues = []

        # Check slice thickness (for CT/MRI)
        if "slice_thickness" in self.df.columns:
            missing = self.df["slice_thickness"].isna().sum()
            if missing > 0:
                issues.append({
                    "field": "slice_thickness",
                    "issue": "missing_values",
                    "count": int(missing),
                })

        # Check acquisition date
        if "acquisition_date" in self.df.columns:
            self.df["acquisition_date"] = pd.to_datetime(
                self.df["acquisition_date"],
                errors="coerce"
            )
            invalid = self.df["acquisition_date"].isna().sum()
            if invalid > 0:
                issues.append({
                    "field": "acquisition_date",
                    "issue": "invalid_dates",
                    "count": int(invalid),
                })

        return issues
