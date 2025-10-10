"""Handler for Electronic Health Record (EHR) data."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np


class EHRHandler:
    """
    Handler for EHR/EMR data cleaning.

    Common EHR data issues:
    - PHI (Protected Health Information) that needs redaction
    - Inconsistent coding (ICD-10, CPT)
    - Missing encounter data
    - Medication reconciliation issues
    """

    def __init__(self, data_path: str | Path):
        self.data_path = Path(data_path)
        self.df: Optional[pd.DataFrame] = None
        self.issues: List[Dict[str, Any]] = []
        self.phi_fields: List[str] = []

    def load_data(self) -> pd.DataFrame:
        """Load EHR data."""
        if self.data_path.suffix == ".csv":
            self.df = pd.read_csv(self.data_path)
        elif self.data_path.suffix in {".xlsx", ".xls"}:
            self.df = pd.read_excel(self.data_path)
        else:
            raise ValueError(f"Unsupported format: {self.data_path.suffix}")

        return self.df

    def detect_phi_fields(self) -> List[str]:
        """
        Detect potential PHI fields that may need redaction.

        Common PHI identifiers:
        - Names, addresses, phone numbers
        - Medical record numbers
        - Email addresses
        """
        if self.df is None:
            raise ValueError("Data not loaded.")

        phi_patterns = {
            "name": ["name", "patient_name", "first_name", "last_name"],
            "address": ["address", "street", "city", "zip"],
            "contact": ["phone", "email", "fax"],
            "identifier": ["mrn", "ssn", "medical_record_number"],
        }

        detected_phi = []

        for col in self.df.columns:
            col_lower = col.lower()
            for phi_type, patterns in phi_patterns.items():
                if any(pattern in col_lower for pattern in patterns):
                    detected_phi.append(col)
                    break

        self.phi_fields = detected_phi
        return detected_phi

    def redact_phi(self, fields: Optional[List[str]] = None) -> int:
        """
        Redact PHI fields by replacing with hashed identifiers.

        Args:
            fields: List of field names to redact. If None, uses auto-detected fields.
        """
        if self.df is None:
            raise ValueError("Data not loaded.")

        fields_to_redact = fields or self.phi_fields
        redacted_count = 0

        for field in fields_to_redact:
            if field in self.df.columns:
                # Create hashed identifier
                self.df[field] = self.df[field].apply(
                    lambda x: f"REDACTED_{hash(str(x)) % 1000000}" if pd.notna(x) else x
                )
                redacted_count += 1

        return redacted_count

    def validate_icd10_codes(self, code_column: str = "icd10_code") -> Dict[str, Any]:
        """
        Validate ICD-10 diagnosis codes.

        Basic validation:
        - Format check (e.g., A00.0)
        - Character validity
        """
        if self.df is None or code_column not in self.df.columns:
            return {"valid": 0, "invalid": 0, "issues": []}

        # Simple ICD-10 format validation
        # Real implementation would use a full ICD-10 code table
        valid_pattern = r'^[A-Z][0-9]{2}(\\.[0-9]{1,2})?$'

        import re
        def is_valid_icd10(code):
            if pd.isna(code):
                return False
            return bool(re.match(valid_pattern, str(code)))

        validation_results = self.df[code_column].apply(is_valid_icd10)
        valid_count = validation_results.sum()
        invalid_count = (~validation_results).sum()

        invalid_codes = self.df[~validation_results][code_column].unique()[:10]

        return {
            "valid": int(valid_count),
            "invalid": int(invalid_count),
            "sample_invalid": list(invalid_codes),
        }

    def save_cleaned_data(self, output_path: str | Path) -> None:
        """Save cleaned EHR data."""
        if self.df is None:
            raise ValueError("No data to save.")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if output_path.suffix == ".csv":
            self.df.to_csv(output_path, index=False)
        elif output_path.suffix in {".xlsx", ".xls"}:
            self.df.to_excel(output_path, index=False)
