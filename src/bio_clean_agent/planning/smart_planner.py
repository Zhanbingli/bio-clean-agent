"""Intelligent planner that reasons about data cleaning tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ..knowledge.medical_standards import MedicalStandards
from ..knowledge.evidence_base import EvidenceBase
from ..knowledge.validation_rules import ValidationRules


class TaskPriority(str, Enum):
    """Task execution priority based on data quality impact."""

    CRITICAL = "critical"  # Data integrity issues
    HIGH = "high"  # Significant quality problems
    MEDIUM = "medium"  # Standard cleaning operations
    LOW = "low"  # Optional enhancements


class StepType(str, Enum):
    """Types of cleaning steps."""

    VALIDATION = "validation"  # Check data quality
    CLEANING = "cleaning"  # Fix issues
    TRANSFORMATION = "transformation"  # Transform data
    VERIFICATION = "verification"  # Verify results


@dataclass
class PlanStep:
    """A single step in the execution plan."""

    id: str
    name: str
    description: str
    step_type: StepType
    priority: TaskPriority

    # Reasoning
    rationale: str  # Why this step is needed
    evidence_based: bool = False  # Based on scientific evidence
    evidence_summary: Optional[str] = None

    # Dependencies
    depends_on: List[str] = field(default_factory=list)
    required: bool = True

    # Execution
    estimated_duration: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Risk assessment
    risk_level: str = "low"  # low, medium, high
    reversible: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "step_type": self.step_type.value,
            "priority": self.priority.value,
            "rationale": self.rationale,
            "evidence_based": self.evidence_based,
            "evidence_summary": self.evidence_summary,
            "depends_on": self.depends_on,
            "required": self.required,
            "risk_level": self.risk_level,
            "reversible": self.reversible,
        }


@dataclass
class ExecutionPlan:
    """Complete execution plan with reasoning."""

    job_id: str
    data_type: str
    objectives: List[str]

    steps: List[PlanStep] = field(default_factory=list)

    # Analysis
    detected_issues: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Quality estimation
    estimated_quality_improvement: Optional[float] = None
    estimated_data_loss: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "data_type": self.data_type,
            "objectives": self.objectives,
            "steps": [step.to_dict() for step in self.steps],
            "detected_issues": self.detected_issues,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "estimated_quality_improvement": self.estimated_quality_improvement,
            "estimated_data_loss": self.estimated_data_loss,
            "total_steps": len(self.steps),
            "critical_steps": sum(
                1 for s in self.steps if s.priority == TaskPriority.CRITICAL
            ),
        }


class SmartPlanner:
    """
    Intelligent planner that creates scientifically-grounded execution plans.

    Unlike simple task execution, this planner:
    1. Analyzes data characteristics
    2. Consults knowledge base for best practices
    3. Reasons about task dependencies
    4. Prioritizes based on data quality impact
    5. Provides evidence-based recommendations
    """

    def __init__(self):
        self.medical_standards = MedicalStandards()
        self.evidence_base = EvidenceBase()
        self.validation_rules = ValidationRules()

    def create_plan(
        self,
        job_id: str,
        data_type: str,
        objectives: List[str],
        data_profile: Optional[Dict[str, Any]] = None,
    ) -> ExecutionPlan:
        """
        Create intelligent execution plan.

        Args:
            job_id: Job identifier
            data_type: Type of data (clinical_trial, ehr, etc.)
            objectives: User-specified goals
            data_profile: Initial data profiling results

        Returns:
            Comprehensive execution plan with reasoning
        """
        plan = ExecutionPlan(
            job_id=job_id,
            data_type=data_type,
            objectives=objectives,
        )

        # Step 1: Data profiling and validation
        self._add_profiling_steps(plan)

        # Step 2: Analyze objectives and detect issues
        if data_profile:
            self._analyze_data_profile(plan, data_profile)

        # Step 3: Create cleaning steps based on issues
        self._create_cleaning_steps(plan, objectives)

        # Step 4: Add verification steps
        self._add_verification_steps(plan)

        # Step 5: Optimize plan order
        self._optimize_plan_order(plan)

        # Step 6: Add quality estimates
        self._estimate_outcomes(plan)

        return plan

    def _add_profiling_steps(self, plan: ExecutionPlan) -> None:
        """Add initial data profiling and validation steps."""

        # Always start with data validation
        plan.steps.append(
            PlanStep(
                id="step_001_validate_structure",
                name="Validate Data Structure",
                description="Check file format, encoding, column structure",
                step_type=StepType.VALIDATION,
                priority=TaskPriority.CRITICAL,
                rationale="Ensure data is readable and structurally sound before processing",
                evidence_based=False,
                required=True,
                risk_level="low",
                reversible=True,
            )
        )

        # Profile data characteristics
        plan.steps.append(
            PlanStep(
                id="step_002_profile_data",
                name="Profile Data",
                description="Analyze data types, distributions, missing values, outliers",
                step_type=StepType.VALIDATION,
                priority=TaskPriority.HIGH,
                rationale="Understanding data characteristics guides appropriate cleaning methods",
                evidence_based=False,
                depends_on=["step_001_validate_structure"],
                required=True,
                risk_level="low",
                reversible=True,
            )
        )

    def _analyze_data_profile(
        self,
        plan: ExecutionPlan,
        profile: Dict[str, Any]
    ) -> None:
        """Analyze data profile and detect issues."""

        # Check missing data
        missing_values = profile.get("missing_values", {})
        for field, info in missing_values.items():
            missing_pct = info.get("percentage", 0)

            if missing_pct > 0:
                issue = {
                    "field": field,
                    "type": "missing_data",
                    "severity": "critical" if missing_pct > 20 else "medium",
                    "details": f"{missing_pct:.1f}% missing values",
                }
                plan.detected_issues.append(issue)

                # Get evidence-based recommendation
                recommendation = self.evidence_base.get_cleaning_recommendation(
                    "missing_data",
                    context={
                        "missing_rate": missing_pct / 100,
                        "mcar_assumption": missing_pct < 5,
                    },
                )

                if recommendation:
                    plan.recommendations.append(
                        f"{field}: {recommendation.statement}"
                    )

        # Check for potential outliers (simplified)
        numeric_summary = profile.get("numeric_summary", {})
        for field, stats in numeric_summary.items():
            # Simple outlier heuristic: large range
            min_val = stats.get("min", 0)
            max_val = stats.get("max", 0)
            mean_val = stats.get("mean", 0)

            if mean_val > 0:
                range_ratio = (max_val - min_val) / mean_val
                if range_ratio > 10:  # Arbitrary threshold
                    issue = {
                        "field": field,
                        "type": "potential_outliers",
                        "severity": "medium",
                        "details": f"Large value range detected",
                    }
                    plan.detected_issues.append(issue)

    def _create_cleaning_steps(
        self,
        plan: ExecutionPlan,
        objectives: List[str]
    ) -> None:
        """Create cleaning steps based on objectives and detected issues."""

        step_id_counter = 3  # Continue from profiling steps

        # Handle "remove duplicates" objective
        if any("duplicate" in obj.lower() for obj in objectives):
            step_id = f"step_{step_id_counter:03d}_remove_duplicates"
            step_id_counter += 1

            # Get evidence
            dup_entry = self.evidence_base.get_entry("duplicate_exact_matches")

            plan.steps.append(
                PlanStep(
                    id=step_id,
                    name="Remove Duplicate Records",
                    description="Identify and remove exact duplicate records",
                    step_type=StepType.CLEANING,
                    priority=TaskPriority.HIGH,
                    rationale=dup_entry.rationale if dup_entry else "Remove redundant data",
                    evidence_based=bool(dup_entry),
                    evidence_summary=dup_entry.statement if dup_entry else None,
                    depends_on=["step_002_profile_data"],
                    required=True,
                    risk_level="low",
                    reversible=False,  # Data is deleted
                )
            )

        # Handle "missing values" objective
        if any("missing" in obj.lower() for obj in objectives):
            for issue in plan.detected_issues:
                if issue["type"] == "missing_data":
                    step_id = f"step_{step_id_counter:03d}_handle_missing_{issue['field']}"
                    step_id_counter += 1

                    # Get evidence-based method
                    missing_pct = float(issue["details"].split("%")[0])
                    method_entry = self.evidence_base.get_cleaning_recommendation(
                        "missing_data",
                        context={"missing_rate": missing_pct / 100},
                    )

                    # Determine method based on missingness
                    if missing_pct < 5:
                        method = "delete"
                        desc = f"Delete rows with missing {issue['field']} (<5% missingness)"
                    elif missing_pct < 20:
                        method = "impute_median"
                        desc = f"Impute missing {issue['field']} with median value"
                    else:
                        method = "flag"
                        desc = f"Flag missing {issue['field']} for review (>20% missingness)"

                    plan.steps.append(
                        PlanStep(
                            id=step_id,
                            name=f"Handle Missing: {issue['field']}",
                            description=desc,
                            step_type=StepType.CLEANING,
                            priority=TaskPriority.HIGH if missing_pct < 20 else TaskPriority.MEDIUM,
                            rationale=method_entry.rationale if method_entry else "Address missing data",
                            evidence_based=bool(method_entry),
                            evidence_summary=method_entry.statement if method_entry else None,
                            depends_on=["step_002_profile_data"],
                            parameters={"method": method, "field": issue["field"]},
                            required=missing_pct < 20,
                            risk_level="medium" if method == "delete" else "low",
                            reversible=False if method == "delete" else True,
                        )
                    )

        # Handle "validate" objective
        if any("validat" in obj.lower() for obj in objectives):
            step_id = f"step_{step_id_counter:03d}_validate_ranges"
            step_id_counter += 1

            plan.steps.append(
                PlanStep(
                    id=step_id,
                    name="Validate Clinical Ranges",
                    description="Check if values are within clinically acceptable ranges",
                    step_type=StepType.VALIDATION,
                    priority=TaskPriority.HIGH,
                    rationale="Detect biologically implausible values that indicate data errors",
                    evidence_based=True,
                    evidence_summary="Values outside clinical reference ranges likely represent measurement or data entry errors",
                    depends_on=["step_002_profile_data"],
                    required=True,
                    risk_level="low",
                    reversible=True,
                )
            )

    def _add_verification_steps(self, plan: ExecutionPlan) -> None:
        """Add verification steps at the end."""

        # Final data quality check
        plan.steps.append(
            PlanStep(
                id=f"step_{len(plan.steps) + 1:03d}_final_verification",
                name="Final Quality Verification",
                description="Verify all cleaning operations completed successfully",
                step_type=StepType.VERIFICATION,
                priority=TaskPriority.HIGH,
                rationale="Ensure data quality improved and no unexpected issues introduced",
                evidence_based=False,
                depends_on=[s.id for s in plan.steps if s.step_type == StepType.CLEANING],
                required=True,
                risk_level="low",
                reversible=True,
            )
        )

    def _optimize_plan_order(self, plan: ExecutionPlan) -> None:
        """Optimize step execution order based on dependencies."""

        # Topological sort based on dependencies
        # For now, steps are already in reasonable order
        # In production, implement proper dependency resolution

        # Add warning if critical steps depend on optional steps
        for step in plan.steps:
            if step.priority == TaskPriority.CRITICAL:
                for dep_id in step.depends_on:
                    dep_step = next((s for s in plan.steps if s.id == dep_id), None)
                    if dep_step and not dep_step.required:
                        plan.warnings.append(
                            f"Critical step '{step.name}' depends on optional step '{dep_step.name}'"
                        )

    def _estimate_outcomes(self, plan: ExecutionPlan) -> None:
        """Estimate plan outcomes."""

        # Estimate quality improvement (simplified)
        num_cleaning_steps = sum(
            1 for s in plan.steps if s.step_type == StepType.CLEANING
        )
        plan.estimated_quality_improvement = min(0.95, 0.1 * num_cleaning_steps)

        # Estimate data loss (simplified)
        deletion_steps = [
            s for s in plan.steps
            if not s.reversible and s.step_type == StepType.CLEANING
        ]
        plan.estimated_data_loss = min(0.20, 0.05 * len(deletion_steps))

        # Add warning if significant data loss expected
        if plan.estimated_data_loss > 0.10:
            plan.warnings.append(
                f"Warning: Estimated data loss of {plan.estimated_data_loss * 100:.1f}%. "
                "Consider alternative methods to preserve more data."
            )
