"""Decision management system for agent execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..api.jobs import DecisionPoint


@dataclass
class DecisionContext:
    """Context information for making a decision."""

    job_id: str
    step_name: str
    question: str
    options: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    default_option: Optional[str] = None


class DecisionStrategy(ABC):
    """Base class for decision-making strategies."""

    @abstractmethod
    def decide(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Make a decision based on the context.

        Args:
            context: Decision context with question and options

        Returns:
            The chosen option as a dictionary
        """
        pass


class DecisionManager:
    """
    Manages decision-making during job execution.

    This replaces back-and-forth chatbot conversations with
    structured decision points that only appear when necessary.
    """

    def __init__(self, strategy: DecisionStrategy):
        self.strategy = strategy
        self._pending_decisions: Dict[str, DecisionPoint] = {}

    def request_decision(
        self,
        job_id: str,
        step_name: str,
        question: str,
        options: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        default_option: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Request a decision from the user or auto-decide based on strategy.

        Example usage:
        ```python
        choice = decision_manager.request_decision(
            job_id="abc-123",
            step_name="handle_missing_values",
            question="How should we handle missing values in column 'age'?",
            options=[
                {
                    "id": "drop",
                    "label": "Drop rows with missing values",
                    "impact": "May lose 15% of data"
                },
                {
                    "id": "impute_mean",
                    "label": "Impute with mean value",
                    "impact": "Preserves all rows"
                },
                {
                    "id": "impute_median",
                    "label": "Impute with median value",
                    "impact": "More robust to outliers"
                }
            ],
            metadata={"column": "age", "missing_count": 150},
            default_option="impute_median"
        )
        ```

        Args:
            job_id: ID of the current job
            step_name: Name of the step requiring decision
            question: Clear question to present to user
            options: List of available options with metadata
            metadata: Additional context for the decision
            default_option: Default option ID if user doesn't respond

        Returns:
            The chosen option dictionary
        """
        context = DecisionContext(
            job_id=job_id,
            step_name=step_name,
            question=question,
            options=options,
            metadata=metadata or {},
            default_option=default_option,
        )

        return self.strategy.decide(context)

    def set_strategy(self, strategy: DecisionStrategy) -> None:
        """Change the decision-making strategy."""
        self.strategy = strategy


# Example decision scenarios for medical data cleaning
class MedicalDataDecisions:
    """Common decision scenarios for medical data cleaning."""

    @staticmethod
    def missing_value_strategy(
        column_name: str,
        missing_count: int,
        total_count: int,
        column_type: str,
    ) -> DecisionContext:
        """Decision for handling missing values."""
        missing_pct = (missing_count / total_count) * 100

        options = []

        # Option 1: Drop rows (if missing % is low)
        if missing_pct < 5:
            options.append({
                "id": "drop",
                "label": f"Drop rows with missing {column_name}",
                "impact": f"Remove {missing_count} rows ({missing_pct:.1f}%)",
                "recommended": missing_pct < 1,
            })

        # Option 2: Imputation (for numeric)
        if column_type in {"int", "float"}:
            options.extend([
                {
                    "id": "impute_mean",
                    "label": "Impute with mean",
                    "impact": "Preserves all rows, assumes normal distribution",
                    "recommended": False,
                },
                {
                    "id": "impute_median",
                    "label": "Impute with median",
                    "impact": "Robust to outliers",
                    "recommended": True,
                },
            ])

        # Option 3: Keep as missing
        options.append({
            "id": "keep_missing",
            "label": "Keep as missing (NaN)",
            "impact": "Preserve data integrity, handle in analysis",
            "recommended": missing_pct > 20,
        })

        return DecisionContext(
            job_id="",  # Will be filled by caller
            step_name="handle_missing_values",
            question=f"Column '{column_name}' has {missing_count} missing values ({missing_pct:.1f}%). How should we handle this?",
            options=options,
            metadata={
                "column": column_name,
                "missing_count": missing_count,
                "total_count": total_count,
                "missing_percentage": missing_pct,
                "column_type": column_type,
            },
            default_option=next(
                (opt["id"] for opt in options if opt.get("recommended")),
                options[0]["id"] if options else None
            ),
        )

    @staticmethod
    def outlier_detection(
        column_name: str,
        outlier_count: int,
        outlier_values: List[float],
    ) -> DecisionContext:
        """Decision for handling outliers."""
        options = [
            {
                "id": "remove",
                "label": "Remove outliers",
                "impact": f"Remove {outlier_count} records",
                "recommended": False,
            },
            {
                "id": "cap",
                "label": "Cap at percentile boundaries",
                "impact": "Replace with 5th/95th percentile values",
                "recommended": True,
            },
            {
                "id": "flag",
                "label": "Flag but keep",
                "impact": "Add 'is_outlier' column for reference",
                "recommended": False,
            },
        ]

        preview = ", ".join(str(v) for v in outlier_values[:5])
        if len(outlier_values) > 5:
            preview += "..."

        return DecisionContext(
            job_id="",
            step_name="handle_outliers",
            question=f"Detected {outlier_count} outliers in '{column_name}' (e.g., {preview}). How should we handle these?",
            options=options,
            metadata={
                "column": column_name,
                "outlier_count": outlier_count,
                "outlier_values": outlier_values,
            },
            default_option="cap",
        )

    @staticmethod
    def duplicate_records(
        duplicate_count: int,
        total_count: int,
        key_columns: List[str],
    ) -> DecisionContext:
        """Decision for handling duplicate records."""
        dup_pct = (duplicate_count / total_count) * 100

        options = [
            {
                "id": "drop_all",
                "label": "Drop all duplicate records",
                "impact": f"Remove {duplicate_count} records ({dup_pct:.1f}%)",
                "recommended": dup_pct < 5,
            },
            {
                "id": "keep_first",
                "label": "Keep first occurrence only",
                "impact": "Preserve original data order",
                "recommended": True,
            },
            {
                "id": "keep_last",
                "label": "Keep last occurrence only",
                "impact": "May preserve most recent data",
                "recommended": False,
            },
            {
                "id": "flag",
                "label": "Flag duplicates but keep all",
                "impact": "Manual review required",
                "recommended": dup_pct > 20,
            },
        ]

        key_cols_str = ", ".join(key_columns)

        return DecisionContext(
            job_id="",
            step_name="handle_duplicates",
            question=f"Found {duplicate_count} duplicate records ({dup_pct:.1f}%) based on columns: {key_cols_str}",
            options=options,
            metadata={
                "duplicate_count": duplicate_count,
                "total_count": total_count,
                "key_columns": key_columns,
                "duplicate_percentage": dup_pct,
            },
            default_option="keep_first",
        )
