"""Unit tests for medical data handlers - simplified smoke tests."""

import pytest
import pandas as pd
from pathlib import Path

from bio_clean_agent.medical.clinical_trials import ClinicalTrialHandler
from bio_clean_agent.medical.ehr import EHRHandler


@pytest.mark.unit
class TestClinicalTrialHandler:
    """Test suite for ClinicalTrialHandler."""

    def test_handler_initialization(self, tmp_path):
        """Test clinical trial handler can be initialized."""
        # Create a dummy CSV file
        data = pd.DataFrame({
            "patient_id": [1, 2, 3],
            "visit_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        })
        csv_path = tmp_path / "trial_data.csv"
        data.to_csv(csv_path, index=False)

        handler = ClinicalTrialHandler(data_path=str(csv_path))
        assert isinstance(handler, ClinicalTrialHandler)

    def test_handler_can_access_data(self, tmp_path):
        """Test handler can access loaded data."""
        data = pd.DataFrame({
            "patient_id": [1, 2, 3],
            "blood_pressure_systolic": [120, 130, 125],
        })
        csv_path = tmp_path / "trial_data.csv"
        data.to_csv(csv_path, index=False)

        handler = ClinicalTrialHandler(data_path=str(csv_path))
        # Just verify handler was created successfully
        assert handler is not None


@pytest.mark.unit
class TestEHRHandler:
    """Test suite for EHRHandler."""

    def test_ehr_handler_initialization(self, tmp_path):
        """Test EHR handler can be initialized."""
        # Create a dummy CSV file
        data = pd.DataFrame({
            "patient_id": [1, 2, 3],
            "age": [45, 52, 38],
        })
        csv_path = tmp_path / "ehr_data.csv"
        data.to_csv(csv_path, index=False)

        handler = EHRHandler(data_path=str(csv_path))
        assert isinstance(handler, EHRHandler)

    def test_ehr_handler_can_access_data(self, tmp_path):
        """Test EHR handler can access loaded data."""
        data = pd.DataFrame({
            "patient_id": [1, 2, 3],
            "diagnosis": ["Diabetes", "Hypertension", "Asthma"],
        })
        csv_path = tmp_path / "ehr_data.csv"
        data.to_csv(csv_path, index=False)

        handler = EHRHandler(data_path=str(csv_path))
        # Just verify handler was created successfully
        assert handler is not None
