"""Handler for Electronic Health Record (EHR) data."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np

from ..utils.logging import get_logger
from ..utils.security import hash_phi_value, create_audit_log_entry

logger = get_logger(__name__)


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
        self.audit_log: List[Dict[str, Any]] = []

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

        Common PHI identifiers according to HIPAA:
        - Names, addresses, phone numbers
        - Medical record numbers, SSN
        - Email addresses
        - Date of birth (if combined with other identifiers)
        - Biometric identifiers
        """
        if self.df is None:
            raise ValueError("Data not loaded.")

        phi_patterns = {
            "name": ["name", "patient_name", "first_name", "last_name", "full_name"],
            "address": ["address", "street", "city", "zip", "zipcode", "postal"],
            "contact": ["phone", "email", "fax", "telephone", "mobile"],
            "identifier": ["mrn", "ssn", "medical_record_number", "patient_id", "member_id"],
            "dob": ["dob", "date_of_birth", "birthdate", "birth_date"],
            "biometric": ["fingerprint", "voice", "photo", "image"],
        }

        detected_phi = []

        for col in self.df.columns:
            col_lower = col.lower()
            for phi_type, patterns in phi_patterns.items():
                if any(pattern in col_lower for pattern in patterns):
                    detected_phi.append(col)
                    logger.info(f"Detected PHI field: {col} (type: {phi_type})")
                    break

        # Also check for content-based patterns (e.g., email in values)
        for col in self.df.columns:
            if col not in detected_phi and self._contains_phi_content(col):
                detected_phi.append(col)
                logger.info(f"Detected PHI field by content analysis: {col}")

        self.phi_fields = detected_phi

        # Audit log
        audit_entry = create_audit_log_entry(
            event_type="PHI_DETECTION",
            user_id=None,
            resource_id=str(self.data_path),
            action="DETECT_PHI_FIELDS",
            result="SUCCESS",
            details={"detected_fields": detected_phi, "field_count": len(detected_phi)},
        )
        self.audit_log.append(audit_entry)

        return detected_phi

    def _contains_phi_content(self, column: str) -> bool:
        """Check if column contains PHI-like content (emails, phones, SSN)."""
        if self.df is None or column not in self.df.columns:
            return False

        # Sample first 100 non-null values
        sample = self.df[column].dropna().head(100).astype(str)

        if len(sample) == 0:
            return False

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        # Phone pattern (various formats)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        # SSN pattern
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'

        for value in sample:
            if (re.search(email_pattern, value) or
                re.search(phone_pattern, value) or
                re.search(ssn_pattern, value)):
                return True

        return False

    def redact_phi(
        self,
        fields: Optional[List[str]] = None,
        method: str = "hash",
        salt: Optional[str] = None,
    ) -> int:
        """
        Redact PHI fields using secure methods.

        Args:
            fields: List of field names to redact. If None, uses auto-detected fields.
            method: Redaction method - "hash" (default), "mask", or "remove"
            salt: Optional salt for hashing (recommended for production)

        Returns:
            Number of fields redacted

        Note:
            - "hash": Replace with SHA-256 hash (allows linking without revealing)
            - "mask": Replace with masked value (e.g., "****1234")
            - "remove": Replace with fixed placeholder
        """
        if self.df is None:
            raise ValueError("Data not loaded.")

        fields_to_redact = fields or self.phi_fields
        if not fields_to_redact:
            logger.warning("No PHI fields specified for redaction")
            return 0

        redacted_count = 0
        redaction_details = {}

        for field in fields_to_redact:
            if field not in self.df.columns:
                logger.warning(f"Field not found for redaction: {field}")
                continue

            original_non_null = self.df[field].notna().sum()

            if method == "hash":
                # Secure hash with optional salt
                self.df[field] = self.df[field].apply(
                    lambda x: hash_phi_value(str(x), salt) if pd.notna(x) else x
                )
            elif method == "mask":
                # Show last 4 characters
                self.df[field] = self.df[field].apply(
                    lambda x: f"****{str(x)[-4:]}" if pd.notna(x) and len(str(x)) > 4 else "****" if pd.notna(x) else x
                )
            elif method == "remove":
                # Complete redaction
                self.df[field] = self.df[field].apply(
                    lambda x: "[REDACTED]" if pd.notna(x) else x
                )
            else:
                raise ValueError(f"Unknown redaction method: {method}")

            redacted_count += 1
            redaction_details[field] = {"values_redacted": int(original_non_null)}
            logger.info(f"Redacted PHI field: {field} ({original_non_null} values, method={method})")

        # Audit log
        audit_entry = create_audit_log_entry(
            event_type="PHI_REDACTION",
            user_id=None,
            resource_id=str(self.data_path),
            action="REDACT_PHI",
            result="SUCCESS",
            details={
                "fields_redacted": list(redaction_details.keys()),
                "redaction_count": redacted_count,
                "method": method,
                "details": redaction_details,
            },
        )
        self.audit_log.append(audit_entry)

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
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")

        logger.info(f"Cleaned data saved to: {output_path}")

        # Audit log
        audit_entry = create_audit_log_entry(
            event_type="DATA_EXPORT",
            user_id=None,
            resource_id=str(output_path),
            action="SAVE_CLEANED_DATA",
            result="SUCCESS",
            details={"output_path": str(output_path), "rows": len(self.df)},
        )
        self.audit_log.append(audit_entry)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """
        Get audit log of all PHI-related operations.

        Returns:
            List of audit log entries
        """
        return self.audit_log.copy()

    def save_audit_log(self, output_path: str | Path) -> None:
        """
        Save audit log to file.

        Args:
            output_path: Path to save audit log (JSON format)
        """
        import json

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.audit_log, f, indent=2)

        logger.info(f"Audit log saved to: {output_path}")
