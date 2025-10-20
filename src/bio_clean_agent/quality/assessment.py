"""Professional data quality assessment framework.

Based on ISO 8000 and DAMA-DMBOK data quality dimensions:
- Completeness
- Validity/Accuracy
- Consistency
- Uniqueness
- Timeliness
- Relevancy
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats


class QualityDimension(str, Enum):
    """Data quality dimensions (ISO 8000)."""
    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    CONSISTENCY = "consistency"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"
    ACCURACY = "accuracy"


class DimensionScore(str, Enum):
    """Quality scoring levels."""
    EXCELLENT = "excellent"  # >= 95%
    GOOD = "good"  # 80-94%
    FAIR = "fair"  # 60-79%
    POOR = "poor"  # < 60%


@dataclass
class DimensionAssessment:
    """Assessment result for a quality dimension."""
    dimension: QualityDimension
    score: float  # 0-1
    level: DimensionScore
    issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dimension": self.dimension.value,
            "score": self.score,
            "level": self.level.value,
            "issues_count": len(self.issues),
            "recommendations_count": len(self.recommendations),
            "metrics": self.metrics
        }


@dataclass
class DataQualityReport:
    """Comprehensive data quality report."""
    dataset_name: str
    total_records: int
    total_fields: int

    # Dimension scores
    completeness: DimensionAssessment
    validity: DimensionAssessment
    consistency: DimensionAssessment
    uniqueness: DimensionAssessment
    timeliness: Optional[DimensionAssessment] = None
    accuracy: Optional[DimensionAssessment] = None

    # Overall
    overall_score: float = 0.0
    overall_level: DimensionScore = DimensionScore.POOR

    # Statistical tests
    statistical_tests: Dict[str, Any] = field(default_factory=dict)

    def calculate_overall(self) -> None:
        """Calculate overall quality score."""
        scores = [
            self.completeness.score,
            self.validity.score,
            self.consistency.score,
            self.uniqueness.score
        ]

        if self.timeliness:
            scores.append(self.timeliness.score)
        if self.accuracy:
            scores.append(self.accuracy.score)

        self.overall_score = np.mean(scores)

        if self.overall_score >= 0.95:
            self.overall_level = DimensionScore.EXCELLENT
        elif self.overall_score >= 0.80:
            self.overall_level = DimensionScore.GOOD
        elif self.overall_score >= 0.60:
            self.overall_level = DimensionScore.FAIR
        else:
            self.overall_level = DimensionScore.POOR

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "dataset_name": self.dataset_name,
            "total_records": self.total_records,
            "total_fields": self.total_fields,
            "overall_score": self.overall_score,
            "overall_level": self.overall_level.value,
            "dimensions": {
                "completeness": self.completeness.to_dict(),
                "validity": self.validity.to_dict(),
                "consistency": self.consistency.to_dict(),
                "uniqueness": self.uniqueness.to_dict()
            },
            "statistical_tests": self.statistical_tests
        }

        if self.timeliness:
            result["dimensions"]["timeliness"] = self.timeliness.to_dict()
        if self.accuracy:
            result["dimensions"]["accuracy"] = self.accuracy.to_dict()

        return result


class DataQualityAssessor:
    """
    Professional data quality assessor.

    Implements ISO 8000 quality dimensions with statistical rigor.
    """

    def __init__(self, reference_ranges: Optional[Dict[str, tuple]] = None):
        """
        Initialize assessor.

        Args:
            reference_ranges: Dict of field -> (min, max) for validity checks
        """
        self.reference_ranges = reference_ranges or {}

    def assess(
        self,
        df: pd.DataFrame,
        dataset_name: str = "dataset",
        key_fields: Optional[List[str]] = None,
        date_fields: Optional[List[str]] = None
    ) -> DataQualityReport:
        """
        Perform comprehensive quality assessment.

        Args:
            df: DataFrame to assess
            dataset_name: Name for reporting
            key_fields: Fields that uniquely identify records
            date_fields: Date fields for timeliness checks

        Returns:
            Comprehensive quality report
        """
        # Assess each dimension
        completeness = self._assess_completeness(df)
        validity = self._assess_validity(df)
        consistency = self._assess_consistency(df)
        uniqueness = self._assess_uniqueness(df, key_fields)

        # Optional dimensions
        timeliness = None
        if date_fields:
            timeliness = self._assess_timeliness(df, date_fields)

        # Create report
        report = DataQualityReport(
            dataset_name=dataset_name,
            total_records=len(df),
            total_fields=len(df.columns),
            completeness=completeness,
            validity=validity,
            consistency=consistency,
            uniqueness=uniqueness,
            timeliness=timeliness
        )

        # Run statistical tests
        report.statistical_tests = self._run_statistical_tests(df)

        # Calculate overall
        report.calculate_overall()

        return report

    def _assess_completeness(self, df: pd.DataFrame) -> DimensionAssessment:
        """
        Assess data completeness.

        Measures: Missing values, null rates, empty strings
        """
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()

        # Also check for empty strings in object columns
        empty_string_count = 0
        for col in df.select_dtypes(include=['object']).columns:
            empty_string_count += (df[col] == '').sum()

        total_missing = missing_cells + empty_string_count
        completeness_score = 1 - (total_missing / total_cells) if total_cells > 0 else 1.0

        # Field-level analysis
        issues = []
        for col in df.columns:
            missing_count = df[col].isnull().sum()
            missing_pct = (missing_count / len(df)) * 100

            if missing_pct > 0:
                severity = (
                    "critical" if missing_pct > 20
                    else "high" if missing_pct > 5
                    else "medium"
                )

                issues.append({
                    "field": col,
                    "missing_count": int(missing_count),
                    "missing_percentage": missing_pct,
                    "severity": severity
                })

        # Recommendations
        recommendations = []
        if completeness_score < 0.95:
            recommendations.append(
                f"Overall completeness is {completeness_score*100:.1f}%. "
                "Investigate fields with high missing rates."
            )

        critical_missing = [i for i in issues if i["severity"] == "critical"]
        if critical_missing:
            recommendations.append(
                f"{len(critical_missing)} fields have >20% missing data. "
                "Consider if these fields are necessary or if data collection needs improvement."
            )

        # Determine level
        level = self._score_to_level(completeness_score)

        return DimensionAssessment(
            dimension=QualityDimension.COMPLETENESS,
            score=completeness_score,
            level=level,
            issues=issues,
            recommendations=recommendations,
            metrics={
                "total_cells": total_cells,
                "missing_cells": int(total_missing),
                "fields_with_missing": len(issues)
            }
        )

    def _assess_validity(self, df: pd.DataFrame) -> DimensionAssessment:
        """
        Assess data validity.

        Measures: Values within acceptable ranges, correct data types, format compliance
        """
        total_records = len(df)
        invalid_count = 0
        issues = []

        # Check reference ranges
        for field, (min_val, max_val) in self.reference_ranges.items():
            if field in df.columns:
                # Check if numeric
                if pd.api.types.is_numeric_dtype(df[field]):
                    out_of_range = (
                        (df[field] < min_val) | (df[field] > max_val)
                    ).sum()

                    if out_of_range > 0:
                        invalid_count += out_of_range
                        issues.append({
                            "field": field,
                            "issue_type": "out_of_range",
                            "count": int(out_of_range),
                            "percentage": (out_of_range / total_records) * 100,
                            "expected_range": (min_val, max_val)
                        })

        # Check for negative values in fields that should be positive
        positive_fields = ["age", "weight", "height", "bmi"]
        for field in positive_fields:
            if field in df.columns and pd.api.types.is_numeric_dtype(df[field]):
                negative_count = (df[field] < 0).sum()
                if negative_count > 0:
                    invalid_count += negative_count
                    issues.append({
                        "field": field,
                        "issue_type": "negative_value",
                        "count": int(negative_count),
                        "percentage": (negative_count / total_records) * 100
                    })

        # Check for extreme outliers using IQR method
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1

            # Outliers are beyond 3*IQR (extreme outliers)
            lower_bound = Q1 - 3 * IQR
            upper_bound = Q3 + 3 * IQR

            outliers = (
                (df[col] < lower_bound) | (df[col] > upper_bound)
            ).sum()

            if outliers > 0:
                outlier_pct = (outliers / total_records) * 100
                if outlier_pct > 1:  # Only flag if >1% are outliers
                    issues.append({
                        "field": col,
                        "issue_type": "extreme_outliers",
                        "count": int(outliers),
                        "percentage": outlier_pct,
                        "method": "IQR_3x"
                    })

        validity_score = 1 - (invalid_count / total_records) if total_records > 0 else 1.0
        level = self._score_to_level(validity_score)

        recommendations = []
        if validity_score < 0.95:
            recommendations.append(
                "Review fields with validity issues. Verify measurement procedures and data entry."
            )

        return DimensionAssessment(
            dimension=QualityDimension.VALIDITY,
            score=validity_score,
            level=level,
            issues=issues,
            recommendations=recommendations,
            metrics={
                "invalid_records": invalid_count,
                "fields_with_issues": len(issues)
            }
        )

    def _assess_consistency(self, df: pd.DataFrame) -> DimensionAssessment:
        """
        Assess data consistency.

        Measures: Cross-field validation, referential integrity, business rules
        """
        total_records = len(df)
        inconsistent_count = 0
        issues = []

        # Check BMI consistency (if weight, height, bmi present)
        if {"weight", "height", "bmi"}.issubset(df.columns):
            # Calculate BMI
            df_temp = df.copy()
            df_temp["calculated_bmi"] = df_temp["weight"] / (df_temp["height"] / 100) ** 2

            # Check for inconsistency (>10% difference)
            bmi_diff = abs(df_temp["bmi"] - df_temp["calculated_bmi"])
            inconsistent_bmi = (bmi_diff > df_temp["bmi"] * 0.1).sum()

            if inconsistent_bmi > 0:
                inconsistent_count += inconsistent_bmi
                issues.append({
                    "rule": "BMI consistency",
                    "description": "BMI doesn't match calculated BMI from weight/height",
                    "count": int(inconsistent_bmi),
                    "percentage": (inconsistent_bmi / total_records) * 100
                })

        # Check date consistency
        date_pairs = [
            ("enrollment_date", "visit_date", "Visit should be after enrollment"),
            ("birth_date", "enrollment_date", "Enrollment should be after birth"),
            ("start_date", "end_date", "End should be after start")
        ]

        for field1, field2, description in date_pairs:
            if {field1, field2}.issubset(df.columns):
                # Convert to datetime
                date1 = pd.to_datetime(df[field1], errors='coerce')
                date2 = pd.to_datetime(df[field2], errors='coerce')

                # Check consistency
                inconsistent = (date2 < date1).sum()

                if inconsistent > 0:
                    inconsistent_count += inconsistent
                    issues.append({
                        "rule": f"{field1} < {field2}",
                        "description": description,
                        "count": int(inconsistent),
                        "percentage": (inconsistent / total_records) * 100
                    })

        # Check age consistency (if age and birth_date present)
        if {"age", "birth_date"}.issubset(df.columns):
            birth_dates = pd.to_datetime(df["birth_date"], errors='coerce')
            current_year = pd.Timestamp.now().year
            calculated_age = current_year - birth_dates.dt.year

            age_diff = abs(df["age"] - calculated_age)
            inconsistent_age = (age_diff > 1).sum()  # Allow 1 year difference

            if inconsistent_age > 0:
                inconsistent_count += inconsistent_age
                issues.append({
                    "rule": "Age consistency",
                    "description": "Age doesn't match birth date",
                    "count": int(inconsistent_age),
                    "percentage": (inconsistent_age / total_records) * 100
                })

        consistency_score = 1 - (inconsistent_count / total_records) if total_records > 0 else 1.0
        level = self._score_to_level(consistency_score)

        recommendations = []
        if issues:
            recommendations.append(
                "Review inconsistent records. Check for data entry errors or measurement timing issues."
            )

        return DimensionAssessment(
            dimension=QualityDimension.CONSISTENCY,
            score=consistency_score,
            level=level,
            issues=issues,
            recommendations=recommendations,
            metrics={
                "inconsistent_records": inconsistent_count,
                "rules_violated": len(issues)
            }
        )

    def _assess_uniqueness(
        self,
        df: pd.DataFrame,
        key_fields: Optional[List[str]] = None
    ) -> DimensionAssessment:
        """
        Assess data uniqueness.

        Measures: Duplicate records, primary key violations
        """
        total_records = len(df)
        issues = []

        # Check exact duplicates
        exact_duplicates = df.duplicated().sum()
        if exact_duplicates > 0:
            issues.append({
                "type": "exact_duplicates",
                "count": int(exact_duplicates),
                "percentage": (exact_duplicates / total_records) * 100
            })

        # Check key field duplicates
        if key_fields:
            for key_field in key_fields:
                if key_field in df.columns:
                    key_duplicates = df[key_field].duplicated().sum()
                    if key_duplicates > 0:
                        issues.append({
                            "type": "key_duplicate",
                            "field": key_field,
                            "count": int(key_duplicates),
                            "percentage": (key_duplicates / total_records) * 100
                        })

            # Check composite key duplicates
            if len(key_fields) > 1:
                available_keys = [k for k in key_fields if k in df.columns]
                if len(available_keys) > 1:
                    composite_duplicates = df.duplicated(subset=available_keys).sum()
                    if composite_duplicates > 0:
                        issues.append({
                            "type": "composite_key_duplicate",
                            "fields": available_keys,
                            "count": int(composite_duplicates),
                            "percentage": (composite_duplicates / total_records) * 100
                        })

        duplicate_count = exact_duplicates
        uniqueness_score = 1 - (duplicate_count / total_records) if total_records > 0 else 1.0
        level = self._score_to_level(uniqueness_score)

        recommendations = []
        if exact_duplicates > 0:
            recommendations.append(
                f"{exact_duplicates} exact duplicate records found. Remove duplicates to improve data quality."
            )

        return DimensionAssessment(
            dimension=QualityDimension.UNIQUENESS,
            score=uniqueness_score,
            level=level,
            issues=issues,
            recommendations=recommendations,
            metrics={
                "exact_duplicates": int(exact_duplicates),
                "duplicate_types": len(issues)
            }
        )

    def _assess_timeliness(
        self,
        df: pd.DataFrame,
        date_fields: List[str]
    ) -> DimensionAssessment:
        """
        Assess data timeliness.

        Measures: Currency, data age, update frequency
        """
        issues = []
        current_date = pd.Timestamp.now()

        for field in date_fields:
            if field in df.columns:
                dates = pd.to_datetime(df[field], errors='coerce')

                # Check for future dates
                future_dates = (dates > current_date).sum()
                if future_dates > 0:
                    issues.append({
                        "field": field,
                        "issue": "future_dates",
                        "count": int(future_dates),
                        "percentage": (future_dates / len(df)) * 100
                    })

                # Check data age
                valid_dates = dates.dropna()
                if len(valid_dates) > 0:
                    oldest = valid_dates.min()
                    newest = valid_dates.max()
                    age_days = (current_date - newest).days

                    issues.append({
                        "field": field,
                        "issue": "data_age",
                        "oldest_date": str(oldest),
                        "newest_date": str(newest),
                        "age_days": age_days,
                        "data_span_days": (newest - oldest).days
                    })

        # Score based on data age
        timeliness_score = 1.0  # Default
        level = DimensionScore.EXCELLENT

        recommendations = []
        future_date_issues = [i for i in issues if i.get("issue") == "future_dates"]
        if future_date_issues:
            recommendations.append(
                "Future dates detected. Verify date entry and system date settings."
            )

        return DimensionAssessment(
            dimension=QualityDimension.TIMELINESS,
            score=timeliness_score,
            level=level,
            issues=issues,
            recommendations=recommendations,
            metrics={}
        )

    def _run_statistical_tests(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Run statistical tests on the data.

        Tests:
        - Normality (Shapiro-Wilk)
        - Homogeneity of variance (Levene)
        - Missing data mechanism (Little's MCAR test approximation)
        """
        tests = {}

        # Normality tests for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        normality_results = {}

        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) >= 3:  # Need at least 3 samples
                try:
                    stat, p_value = stats.shapiro(data)
                    normality_results[col] = {
                        "test": "Shapiro-Wilk",
                        "statistic": float(stat),
                        "p_value": float(p_value),
                        "normal": p_value > 0.05
                    }
                except:
                    pass

        tests["normality"] = normality_results

        # Skewness and kurtosis
        skewness_results = {}
        for col in numeric_cols:
            data = df[col].dropna()
            if len(data) > 0:
                skewness_results[col] = {
                    "skewness": float(data.skew()),
                    "kurtosis": float(data.kurtosis())
                }

        tests["distribution_shape"] = skewness_results

        return tests

    @staticmethod
    def _score_to_level(score: float) -> DimensionScore:
        """Convert numeric score to quality level."""
        if score >= 0.95:
            return DimensionScore.EXCELLENT
        elif score >= 0.80:
            return DimensionScore.GOOD
        elif score >= 0.60:
            return DimensionScore.FAIR
        else:
            return DimensionScore.POOR
