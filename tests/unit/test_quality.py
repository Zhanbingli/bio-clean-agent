"""Unit tests for data quality assessment."""

import pytest
import pandas as pd
import numpy as np

from bio_clean_agent.quality.assessment import (
    QualityAssessment,
    QualityDimension,
    QualityScore,
    assess_data_quality,
)


@pytest.mark.unit
class TestQualityDimension:
    """Test suite for QualityDimension."""

    def test_quality_dimension_creation(self):
        """Test quality dimension can be created."""
        dimension = QualityDimension(
            name="completeness", score=0.95, issues=[], recommendations=[]
        )

        assert dimension.name == "completeness"
        assert dimension.score == 0.95

    def test_quality_dimension_with_issues(self):
        """Test quality dimension with issues."""
        issues = ["Missing values in column A", "Missing values in column B"]
        dimension = QualityDimension(
            name="completeness", score=0.80, issues=issues, recommendations=[]
        )

        assert len(dimension.issues) == 2
        assert "column A" in dimension.issues[0]


@pytest.mark.unit
class TestQualityScore:
    """Test suite for QualityScore."""

    def test_quality_score_excellent(self):
        """Test excellent quality score."""
        score = QualityScore(value=0.96)

        assert score.value == 0.96
        assert score.grade == "EXCELLENT"

    def test_quality_score_good(self):
        """Test good quality score."""
        score = QualityScore(value=0.85)

        assert score.value == 0.85
        assert score.grade == "GOOD"

    def test_quality_score_fair(self):
        """Test fair quality score."""
        score = QualityScore(value=0.70)

        assert score.value == 0.70
        assert score.grade == "FAIR"

    def test_quality_score_poor(self):
        """Test poor quality score."""
        score = QualityScore(value=0.50)

        assert score.value == 0.50
        assert score.grade == "POOR"


@pytest.mark.unit
class TestQualityAssessment:
    """Test suite for QualityAssessment."""

    def test_assess_completeness(self):
        """Test completeness assessment."""
        # Create sample data
        data = pd.DataFrame(
            {
                "A": [1, 2, 3, 4, 5],
                "B": [1, 2, None, 4, 5],
                "C": [1, None, None, 4, 5],
            }
        )

        assessment = QualityAssessment(data)
        completeness = assessment.assess_completeness()

        # Overall completeness should be (15-3)/15 = 0.80
        assert completeness.score == pytest.approx(0.80, rel=0.01)
        assert len(completeness.issues) > 0

    def test_assess_uniqueness(self):
        """Test uniqueness assessment."""
        data = pd.DataFrame(
            {
                "id": [1, 2, 3, 4, 5, 5],  # One duplicate
                "value": [10, 20, 30, 40, 50, 50],
            }
        )

        assessment = QualityAssessment(data)
        uniqueness = assessment.assess_uniqueness(id_column="id")

        # Should detect duplicate
        assert uniqueness.score < 1.0
        assert len(uniqueness.issues) > 0

    def test_assess_validity(self):
        """Test validity assessment."""
        data = pd.DataFrame(
            {
                "age": [25, 30, -5, 150, 40],  # -5 and 150 are invalid
                "email": [
                    "test@example.com",
                    "invalid-email",
                    "test2@example.com",
                    "test3@example.com",
                    "another@test.com",
                ],
            }
        )

        assessment = QualityAssessment(data)
        validity = assessment.assess_validity(
            constraints={"age": {"min": 0, "max": 120}}
        )

        # Should detect invalid ages
        assert validity.score < 1.0

    def test_assess_consistency(self):
        """Test consistency assessment."""
        data = pd.DataFrame(
            {
                "start_date": pd.to_datetime(
                    ["2024-01-01", "2024-02-01", "2024-03-01"]
                ),
                "end_date": pd.to_datetime(
                    ["2024-01-31", "2024-01-15", "2024-03-31"]
                ),  # Second row inconsistent
            }
        )

        assessment = QualityAssessment(data)
        consistency = assessment.assess_consistency()

        # Should detect inconsistent dates
        assert len(consistency.issues) > 0

    def test_overall_quality_score(self):
        """Test overall quality score calculation."""
        data = pd.DataFrame(
            {"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50], "C": [100, 200, 300, 400, 500]}
        )

        assessment = QualityAssessment(data)
        overall_score = assessment.get_overall_score()

        assert isinstance(overall_score, QualityScore)
        assert 0 <= overall_score.value <= 1


@pytest.mark.unit
class TestAssessDataQuality:
    """Test suite for assess_data_quality function."""

    def test_assess_complete_data(self):
        """Test assessing complete, high-quality data."""
        data = pd.DataFrame(
            {"A": [1, 2, 3, 4, 5], "B": [10, 20, 30, 40, 50], "C": [100, 200, 300, 400, 500]}
        )

        result = assess_data_quality(data)

        assert result["overall_score"] >= 0.9
        assert "dimensions" in result
        assert "completeness" in result["dimensions"]

    def test_assess_data_with_issues(self):
        """Test assessing data with quality issues."""
        data = pd.DataFrame(
            {
                "A": [1, 2, None, 4, 5],  # Missing value
                "B": [10, 20, 30, 30, 50],  # Duplicate
                "C": [100, 200, 300, 400, -50],  # Invalid value
            }
        )

        result = assess_data_quality(data, constraints={"C": {"min": 0}})

        assert result["overall_score"] < 0.9
        assert len(result["issues"]) > 0
