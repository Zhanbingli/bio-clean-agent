"""Validation rules engine with scientific knowledge."""

from typing import Any, Dict, List, Optional
import re

from .base import KnowledgeEntry, ConfidenceLevel
from .medical_standards import MedicalStandards


class ValidationResult:
    """Result of a validation check."""

    def __init__(self):
        self.valid = True
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.recommendations: List[str] = []
        self.evidence: List[KnowledgeEntry] = []

    def add_error(self, message: str, evidence: Optional[KnowledgeEntry] = None):
        """Add an error."""
        self.valid = False
        self.errors.append(message)
        if evidence:
            self.evidence.append(evidence)

    def add_warning(self, message: str, evidence: Optional[KnowledgeEntry] = None):
        """Add a warning."""
        self.warnings.append(message)
        if evidence:
            self.evidence.append(evidence)

    def add_recommendation(self, message: str):
        """Add a recommendation."""
        self.recommendations.append(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "evidence_count": len(self.evidence),
        }


class ValidationRules:
    """
    Scientific validation rules engine.

    Validates data against medical knowledge and best practices.
    """

    def __init__(self):
        self.medical_standards = MedicalStandards()

    def validate_vital_sign(
        self,
        field: str,
        value: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Validate a vital sign value.

        Args:
            field: Vital sign name (e.g., "systolic_bp")
            value: Measured value
            context: Patient context (age, etc.)

        Returns:
            ValidationResult with scientific evidence
        """
        result = ValidationResult()
        context = context or {}

        # Define reference ranges based on medical knowledge
        ranges = {
            "systolic_bp": (70, 200, "mmHg"),
            "diastolic_bp": (40, 130, "mmHg"),
            "heart_rate": (40, 150, "bpm"),
            "temperature": (35.0, 42.0, "°C"),
            "respiratory_rate": (8, 30, "breaths/min"),
            "oxygen_saturation": (70, 100, "%"),
        }

        if field not in ranges:
            result.add_warning(f"Unknown vital sign: {field}")
            return result

        min_val, max_val, unit = ranges[field]

        # Get evidence from knowledge base
        evidence = self.medical_standards.get_reference_range(field, context)

        # Check if value is within acceptable range
        if value < min_val or value > max_val:
            result.add_error(
                f"{field} value {value}{unit} is outside acceptable range "
                f"({min_val}-{max_val}{unit})",
                evidence=evidence.get("source") if evidence else None,
            )

            # Provide context-specific recommendations
            if field == "systolic_bp":
                if value > max_val:
                    result.add_recommendation(
                        "High blood pressure detected. Verify measurement technique. "
                        "Consider data entry error or true hypertensive crisis."
                    )
                elif value < min_val:
                    result.add_recommendation(
                        "Low blood pressure detected. May indicate hypotension or measurement error."
                    )

            elif field == "temperature":
                if value > 38.0:
                    result.add_recommendation(
                        f"Fever detected ({value}°C). Document as clinically significant finding."
                    )
                elif value < 35.0:
                    result.add_recommendation(
                        f"Hypothermia detected ({value}°C). Verify measurement."
                    )

        # Check for values that are technically possible but unusual
        elif field == "heart_rate":
            if value < 50 and not context.get("athlete"):
                result.add_warning(
                    f"Bradycardia ({value} bpm). May be normal for athletes or indicate pathology."
                )
            elif value > 100:
                result.add_warning(
                    f"Tachycardia ({value} bpm). May be due to stress, exercise, or pathology."
                )

        return result

    def validate_age(self, age: float) -> ValidationResult:
        """Validate age value."""
        result = ValidationResult()

        if age < 0 or age > 120:
            result.add_error(
                f"Age {age} is outside valid range (0-120 years). Likely data entry error."
            )
        elif age > 110:
            result.add_warning(
                f"Age {age} is extremely high. Verify this is correct."
            )

        return result

    def validate_date_consistency(
        self,
        enrollment_date: str,
        visit_date: str,
    ) -> ValidationResult:
        """Validate date consistency in clinical trials."""
        result = ValidationResult()

        from datetime import datetime

        try:
            enroll = datetime.fromisoformat(enrollment_date)
            visit = datetime.fromisoformat(visit_date)

            if visit < enroll:
                result.add_error(
                    f"Visit date ({visit_date}) is before enrollment date ({enrollment_date}). "
                    "This is logically impossible."
                )
                result.add_recommendation(
                    "Review source documents to correct date error."
                )

        except ValueError as e:
            result.add_error(f"Invalid date format: {e}")

        return result

    def validate_bmi(
        self,
        weight_kg: float,
        height_cm: float,
    ) -> ValidationResult:
        """Validate BMI calculation and interpretation."""
        result = ValidationResult()

        # Validate inputs
        if weight_kg <= 0 or weight_kg > 300:
            result.add_error(f"Invalid weight: {weight_kg} kg")
        if height_cm <= 0 or height_cm > 250:
            result.add_error(f"Invalid height: {height_cm} cm")

        if not result.valid:
            return result

        # Calculate BMI
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)

        # Get WHO classification evidence
        bmi_entry = self.medical_standards.get_entry("anthro_bmi_categories")

        # Interpret BMI
        if bmi < 16:
            result.add_error(
                f"BMI {bmi:.1f} indicates severe underweight. Verify measurements."
            )
        elif bmi < 18.5:
            result.add_warning(
                f"BMI {bmi:.1f} indicates underweight (WHO classification)."
            )
            if bmi_entry:
                result.evidence.append(bmi_entry)
        elif 18.5 <= bmi < 25:
            pass  # Normal range
        elif 25 <= bmi < 30:
            result.add_warning(
                f"BMI {bmi:.1f} indicates overweight (WHO classification)."
            )
            if bmi_entry:
                result.evidence.append(bmi_entry)
        elif 30 <= bmi < 40:
            result.add_warning(
                f"BMI {bmi:.1f} indicates obesity (WHO classification)."
            )
            if bmi_entry:
                result.evidence.append(bmi_entry)
        elif bmi >= 40:
            result.add_error(
                f"BMI {bmi:.1f} indicates severe obesity or measurement error. Verify data."
            )

        return result

    def validate_lab_value(
        self,
        test: str,
        value: float,
        unit: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate laboratory test value."""
        result = ValidationResult()
        context = context or {}

        # Common lab value ranges
        ranges = {
            "glucose": {
                "fasting": (70, 100, "mg/dL"),
                "random": (70, 200, "mg/dL"),
            },
            "hba1c": {
                "normal": (4.0, 5.6, "%"),
            },
            "hemoglobin": {
                "male": (13.5, 17.5, "g/dL"),
                "female": (12.0, 15.5, "g/dL"),
            },
            "creatinine": {
                "male": (0.7, 1.3, "mg/dL"),
                "female": (0.6, 1.1, "mg/dL"),
            },
        }

        if test not in ranges:
            result.add_warning(f"Unknown lab test: {test}")
            return result

        # Get appropriate range
        test_ranges = ranges[test]

        # Select range based on context
        if len(test_ranges) == 1:
            range_key = list(test_ranges.keys())[0]
            min_val, max_val, ref_unit = test_ranges[range_key]
        else:
            # Context-specific range
            if context.get("fasting"):
                range_key = "fasting"
            elif context.get("sex") == "male":
                range_key = "male"
            elif context.get("sex") == "female":
                range_key = "female"
            else:
                range_key = list(test_ranges.keys())[0]

            if range_key not in test_ranges:
                range_key = list(test_ranges.keys())[0]

            min_val, max_val, ref_unit = test_ranges[range_key]

        # Check unit compatibility
        if unit != ref_unit:
            result.add_warning(
                f"Unit mismatch: provided {unit}, expected {ref_unit}. "
                "Value may need unit conversion."
            )

        # Validate range
        if value < min_val or value > max_val:
            result.add_error(
                f"{test} value {value}{unit} is outside normal range "
                f"({min_val}-{max_val}{ref_unit})"
            )

            # Provide clinical interpretation
            if test == "glucose" and value > max_val:
                if value >= 126:
                    result.add_warning(
                        "Glucose ≥126 mg/dL indicates diabetes (ADA criteria)"
                    )
                elif value >= 100:
                    result.add_warning(
                        "Glucose 100-125 mg/dL indicates prediabetes"
                    )

            elif test == "hba1c" and value > max_val:
                if value >= 6.5:
                    result.add_warning(
                        "HbA1c ≥6.5% indicates diabetes (ADA criteria)"
                    )
                elif value >= 5.7:
                    result.add_warning(
                        "HbA1c 5.7-6.4% indicates prediabetes"
                    )

        return result

    def validate_icd10_format(self, code: str) -> ValidationResult:
        """Validate ICD-10 code format."""
        result = ValidationResult()

        # ICD-10 format: Letter + 2 digits + optional decimal + 1-2 digits
        pattern = r'^[A-Z][0-9]{2}(\.[0-9]{1,2})?$'

        if not re.match(pattern, code):
            result.add_error(
                f"Invalid ICD-10 code format: '{code}'. "
                "Expected format: A00 or A00.0 or A00.00"
            )
            result.add_recommendation(
                "ICD-10 codes must start with a letter followed by 2 digits, "
                "optionally with a decimal point and 1-2 more digits."
            )

        return result

    def validate_data_completeness(
        self,
        required_fields: List[str],
        data: Dict[str, Any],
    ) -> ValidationResult:
        """Validate required fields are present and non-null."""
        result = ValidationResult()

        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                result.add_error(f"Required field '{field}' is missing or empty")

        if result.errors:
            result.add_recommendation(
                f"Complete all required fields: {', '.join(required_fields)}"
            )

        return result
