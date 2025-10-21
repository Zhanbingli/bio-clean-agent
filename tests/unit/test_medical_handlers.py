"""Unit tests for medical data handlers."""

import pytest
import pandas as pd
from pathlib import Path

from bio_clean_agent.medical.clinical_trials import ClinicalTrialHandler
from bio_clean_agent.medical.ehr import EHRHandler


@pytest.mark.unit
class TestClinicalTrialHandler:
    """Test suite for ClinicalTrialHandler."""

    def test_handler_initialization(self):
        """Test clinical trial handler can be initialized."""
        handler = ClinicalTrialHandler()
        assert isinstance(handler, ClinicalTrialHandler)

    def test_load_clinical_trial_data(self, tmp_path):
        """Test loading clinical trial data."""
        # Create sample CSV
        data = pd.DataFrame(
            {
                "patient_id": [1, 2, 3],
                "visit_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
                "blood_pressure_systolic": [120, 130, 125],
                "blood_pressure_diastolic": [80, 85, 82],
                "heart_rate": [70, 75, 72],
            }
        )

        csv_path = tmp_path / "trial_data.csv"
        data.to_csv(csv_path, index=False)

        handler = ClinicalTrialHandler()
        loaded_data = handler.load(str(csv_path))

        assert isinstance(loaded_data, pd.DataFrame)
        assert len(loaded_data) == 3
        assert "patient_id" in loaded_data.columns

    def test_detect_issues(self, tmp_path):
        """Test detecting issues in clinical trial data."""
        # Create data with issues
        data = pd.DataFrame(
            {
                "patient_id": [1, 1, 2],  # Duplicate patient_id
                "visit_date": ["2024-01-01", "2024-01-01", None],  # Missing date
                "blood_pressure_systolic": [120, 250, 125],  # Invalid BP
                "heart_rate": [70, 75, 72],
            }
        )

        csv_path = tmp_path / "trial_data.csv"
        data.to_csv(csv_path, index=False)

        handler = ClinicalTrialHandler()
        loaded_data = handler.load(str(csv_path))
        issues = handler.detect_issues(loaded_data)

        assert len(issues) > 0
        # Should detect duplicates, missing values, and invalid ranges

    def test_assess_quality(self, tmp_path):
        """Test quality assessment of clinical trial data."""
        data = pd.DataFrame(
            {
                "patient_id": [1, 2, 3, 4, 5],
                "visit_date": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                ],
                "blood_pressure_systolic": [120, 130, 125, 128, 122],
                "heart_rate": [70, 75, 72, 74, 71],
            }
        )

        csv_path = tmp_path / "trial_data.csv"
        data.to_csv(csv_path, index=False)

        handler = ClinicalTrialHandler()
        loaded_data = handler.load(str(csv_path))
        quality = handler.assess_quality(loaded_data)

        assert "score" in quality
        assert 0 <= quality["score"] <= 1


@pytest.mark.unit
class TestEHRHandler:
    """Test suite for EHRHandler."""

    def test_ehr_handler_initialization(self):
        """Test EHR handler can be initialized."""
        handler = EHRHandler()
        assert isinstance(handler, EHRHandler)

    def test_phi_detection(self):
        """Test PHI field detection."""
        handler = EHRHandler()

        phi_fields = [
            "patient_name",
            "ssn",
            "email",
            "phone",
            "address",
            "medical_record_number",
        ]

        for field in phi_fields:
            assert handler.is_phi_field(field) is True

        # Non-PHI fields
        assert handler.is_phi_field("age") is False
        assert handler.is_phi_field("diagnosis") is False

    def test_mask_phi_data(self, tmp_path):
        """Test masking PHI data."""
        data = pd.DataFrame(
            {
                "patient_id": [1, 2, 3],
                "patient_name": ["John Doe", "Jane Smith", "Bob Johnson"],
                "email": ["john@example.com", "jane@example.com", "bob@example.com"],
                "age": [45, 52, 38],
                "diagnosis": ["Diabetes", "Hypertension", "Asthma"],
            }
        )

        csv_path = tmp_path / "ehr_data.csv"
        data.to_csv(csv_path, index=False)

        handler = EHRHandler()
        loaded_data = handler.load(str(csv_path))
        masked_data = handler.mask_phi(loaded_data)

        # PHI fields should be masked
        assert masked_data["patient_name"].iloc[0] != "John Doe"
        assert masked_data["email"].iloc[0] != "john@example.com"

        # Non-PHI fields should remain unchanged
        assert masked_data["age"].iloc[0] == 45
        assert masked_data["diagnosis"].iloc[0] == "Diabetes"

    def test_hash_phi_data(self):
        """Test hashing PHI data for anonymization."""
        handler = EHRHandler()

        original = "John Doe"
        hashed = handler.hash_phi_value(original)

        # Hash should be consistent
        assert handler.hash_phi_value(original) == hashed

        # Different values should hash differently
        assert handler.hash_phi_value("Jane Smith") != hashed

    def test_detect_phi_in_content(self):
        """Test detecting PHI patterns in content."""
        handler = EHRHandler()

        # Email pattern
        text_with_email = "Contact patient at john.doe@example.com"
        assert handler.contains_phi(text_with_email) is True

        # SSN pattern
        text_with_ssn = "Patient SSN: 123-45-6789"
        assert handler.contains_phi(text_with_ssn) is True

        # Clean text
        clean_text = "Patient has diabetes and hypertension"
        assert handler.contains_phi(clean_text) is False
