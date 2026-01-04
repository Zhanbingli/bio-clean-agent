from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from .base import Pipeline, PipelineStep, StepResult, ToolExecutor
from ..medical.clinical_trials_enhanced import EnhancedClinicalTrialHandler


class ClinicalTrialCleaningPipeline(Pipeline):
    name = "clinical_trial_cleaning"
    dataset_type = "clinical"

    def __init__(self, output_dir: str | Path, executor: ToolExecutor = None):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.executor = executor  # Not heavily used by the handler yet, but good for consistency
        self.handler: EnhancedClinicalTrialHandler | None = None

        # Define steps
        self.add_step(PipelineStep("initialize", "Initialize Clinical Handler", self.initialize))
        self.add_step(PipelineStep("load_data", "Load and Validate Data", self.load_data))
        self.add_step(PipelineStep("assess_quality_initial", "Initial Quality Assessment", self.assess_quality_initial))
        self.add_step(PipelineStep("detect_issues", "Detect Data Issues", self.detect_issues))
        self.add_step(PipelineStep("clean_duplicates", "Clean Duplicates", self.clean_duplicates))
        self.add_step(PipelineStep("handle_missing", "Handle Missing Values", self.handle_missing))
        self.add_step(PipelineStep("assess_quality_final", "Final Quality Assessment", self.assess_quality_final))
        self.add_step(PipelineStep("save_results", "Save Results and Reports", self.save_results))

    def validate_context(self, context: Dict) -> None:
        if "dataset" not in context:
            raise ValueError("Clinical pipeline requires 'dataset' in context")
        dataset = context["dataset"]
        if not dataset.raw_paths:
            raise ValueError("Clinical dataset must contain at least one raw path (the data file)")

        # Ensure input exists
        input_file = Path(dataset.raw_paths[0])
        if not input_file.exists():
            # Check capabilities/params if we should skip strict check (usually strict for local files)
            allow_missing = context.get("parameters", {}).get("allow_missing_inputs", False)
            if not allow_missing:
                raise FileNotFoundError(f"Input file not found: {input_file}")

        context.setdefault("workdir", str(self.output_dir))
        Path(context["workdir"]).mkdir(parents=True, exist_ok=True)
        context["input_file"] = str(input_file)

    def initialize(self, context: Dict) -> StepResult:
        input_file = context["input_file"]
        try:
            self.handler = EnhancedClinicalTrialHandler(
                data_path=input_file,
                user_id=context.get("parameters", {}).get("user_id", "system")
            )
            return StepResult(name="initialize", success=True, details={"input_file": input_file})
        except Exception as e:
            return StepResult(name="initialize", success=False, error=str(e))

    def load_data(self, context: Dict) -> StepResult:
        if not self.handler:
            return StepResult(name="load_data", success=False, error="Handler not initialized")
        try:
            df = self.handler.load_data()
            details = {
                "rows": len(df),
                "columns": list(df.columns)
            }
            return StepResult(name="load_data", success=True, details=details)
        except Exception as e:
            return StepResult(name="load_data", success=False, error=str(e))

    def assess_quality_initial(self, context: Dict) -> StepResult:
        if not self.handler:
            return StepResult(name="assess_quality_initial", success=False, error="Handler not initialized")
        try:
            metrics = self.handler.assess_data_quality()
            context["initial_quality"] = metrics
            return StepResult(name="assess_quality_initial", success=True, details=metrics.to_dict())
        except Exception as e:
            return StepResult(name="assess_quality_initial", success=False, error=str(e))

    def detect_issues(self, context: Dict) -> StepResult:
        if not self.handler:
            return StepResult(name="detect_issues", success=False, error="Handler not initialized")
        try:
            issues = self.handler.detect_issues_with_evidence()
            details = {
                "issue_count": len(issues),
                "issues_summary": self._summarize_issues(issues)
            }
            return StepResult(name="detect_issues", success=True, details=details)
        except Exception as e:
            return StepResult(name="detect_issues", success=False, error=str(e))

    def clean_duplicates(self, context: Dict) -> StepResult:
        if not self.handler:
            return StepResult(name="clean_duplicates", success=False, error="Handler not initialized")
        try:
            params = context.get("parameters", {})
            keep = params.get("duplicate_keep_strategy", "first")
            removed = self.handler.clean_duplicates_with_lineage(keep=keep)
            return StepResult(name="clean_duplicates", success=True, details={"removed_count": removed})
        except Exception as e:
            return StepResult(name="clean_duplicates", success=False, error=str(e))

    def handle_missing(self, context: Dict) -> StepResult:
        if not self.handler:
            return StepResult(name="handle_missing", success=False, error="Handler not initialized")
        try:
            # We can iterate over critical fields if defined in params, or standard vital signs
            # For this pipeline, let's process standard vitals + weight
            key_fields = ["systolic_bp", "diastolic_bp", "heart_rate", "temperature", "weight"]

            # Also check if user provided specific fields to handle
            params = context.get("parameters", {})
            user_fields = params.get("missing_value_fields")
            if user_fields:
                key_fields = user_fields

            results = {}
            total_handled = 0

            for field in key_fields:
                try:
                    # In a real pipeline, we might want to be more careful, but here we try simple auto-handling
                    affected, method, _ = self.handler.handle_missing_values_evidence_based(
                        field,
                        auto_select=True
                    )
                    if affected > 0:
                        results[field] = {"method": method, "affected": affected}
                        total_handled += affected
                except ValueError:
                    # Column might not exist
                    pass
                except Exception as e:
                    results[field] = {"error": str(e)}

            return StepResult(name="handle_missing", success=True, details={"handled_count": total_handled, "field_details": results})
        except Exception as e:
            return StepResult(name="handle_missing", success=False, error=str(e))

    def assess_quality_final(self, context: Dict) -> StepResult:
        if not self.handler:
            return StepResult(name="assess_quality_final", success=False, error="Handler not initialized")
        try:
            metrics = self.handler.assess_data_quality()
            context["final_quality"] = metrics

            # Compare with initial
            initial = context.get("initial_quality")
            improvement = 0.0
            if initial:
                improvement = metrics.overall_score - initial.overall_score

            details = metrics.to_dict()
            details["improvement_score"] = improvement
            return StepResult(name="assess_quality_final", success=True, details=details)
        except Exception as e:
            return StepResult(name="assess_quality_final", success=False, error=str(e))

    def save_results(self, context: Dict) -> StepResult:
        if not self.handler:
            return StepResult(name="save_results", success=False, error="Handler not initialized")
        try:
            output_path = Path(context["workdir"])

            # Save data
            cleaned_file = output_path / "cleaned_data.csv"
            self.handler.save_cleaned_data(cleaned_file)

            # Save artifacts
            self.handler.export_audit_trail(output_path / "audit_trail.json")
            self.handler.export_lineage(output_path / "data_lineage.json")

            report = self.handler.generate_quality_report()
            # We can save this report as json too
            import json
            with open(output_path / "quality_report.json", "w") as f:
                json.dump(report, f, indent=2)

            return StepResult(name="save_results", success=True, details={"output_dir": str(output_path)})
        except Exception as e:
            return StepResult(name="save_results", success=False, error=str(e))

    def _summarize_issues(self, issues: list) -> Dict[str, int]:
        from collections import Counter
        return dict(Counter(i['severity'] for i in issues))
