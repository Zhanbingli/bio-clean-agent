"""Unit tests for data quality assessment."""

import pytest
import pandas as pd

from bio_clean_agent.quality.assessment import (
    DataQualityAssessor,
    QualityDimension,
    DimensionScore,
)


@pytest.mark.unit
class TestQualityDimension:
    """Test suite for QualityDimension enum."""

    def test_quality_dimensions_exist(self):
        """Test all quality dimensions are defined."""
        assert hasattr(QualityDimension, 'COMPLETENESS')
        assert hasattr(QualityDimension, 'VALIDITY')
        assert hasattr(QualityDimension, 'CONSISTENCY')


@pytest.mark.unit
class TestDimensionScore:
    """Test suite for DimensionScore enum."""

    def test_score_levels_exist(self):
        """Test score levels are defined."""
        assert hasattr(DimensionScore, 'EXCELLENT')
        assert hasattr(DimensionScore, 'GOOD')
        assert hasattr(DimensionScore, 'FAIR')
        assert hasattr(DimensionScore, 'POOR')


@pytest.mark.unit
class TestDataQualityAssessor:
    """Test suite for DataQualityAssessor."""

    def test_assessor_initialization(self):
        """Test assessor can be initialized."""
        assessor = DataQualityAssessor()
        assert isinstance(assessor, DataQualityAssessor)

    def test_assessor_with_reference_ranges(self):
        """Test assessor with custom reference ranges."""
        ranges = {"age": (0, 120), "score": (0, 100)}
        assessor = DataQualityAssessor(reference_ranges=ranges)
        assert assessor.reference_ranges == ranges

    def test_assess_simple_data(self):
        """Test assessing simple clean data."""
        data = pd.DataFrame({
            "A": [1, 2, 3, 4, 5],
            "B": [10, 20, 30, 40, 50],
        })

        assessor = DataQualityAssessor()
        report = assessor.assess(data, dataset_name="test_data")

        assert report is not None
        assert hasattr(report, 'overall_score')

    def test_assess_data_with_missing_values(self):
        """Test assessing data with missing values."""
        data = pd.DataFrame({
            "A": [1, 2, None, 4, 5],
            "B": [10, None, 30, 40, 50],
        })

        assessor = DataQualityAssessor()
        report = assessor.assess(data, dataset_name="test_data")

        # Should detect missing values
        assert report is not None

    def test_assess_with_key_fields(self):
        """Test assessing with specified key fields."""
        data = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50],
        })

        assessor = DataQualityAssessor()
        report = assessor.assess(data, key_fields=["id"])

        assert report is not None
