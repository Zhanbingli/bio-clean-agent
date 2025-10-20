"""Interactive session manager for Claude Code-style CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

import pandas as pd

from ..medical.clinical_trials_enhanced import EnhancedClinicalTrialHandler
from ..quality.assessment import DataQualityAssessor
from .tools import ToolRegistry, ToolCategory


class InteractiveSession:
    """
    Interactive session that maintains state across user interactions.

    Similar to Claude Code's stateful conversation.
    """

    def __init__(self, user_id: str = "user"):
        self.user_id = user_id
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Tool registry
        self.tools = ToolRegistry()

        # Session state
        self.handler: Optional[EnhancedClinicalTrialHandler] = None
        self.data_loaded = False
        self.current_file: Optional[Path] = None

        # Conversation history
        self.history: List[Dict[str, Any]] = []

        # Statistics
        self.stats = {
            "session_start": datetime.now().isoformat(),
            "commands_executed": 0,
            "tools_used": {},
            "data_operations": 0
        }

    def add_message(self, role: str, content: str, tool_calls: Optional[List] = None) -> None:
        """Add a message to conversation history."""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "tool_calls": tool_calls or []
        })

    def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool and return results.

        This method handles the actual implementation of tools.
        """
        # Update stats
        self.stats["commands_executed"] += 1
        self.stats["tools_used"][tool_name] = self.stats["tools_used"].get(tool_name, 0) + 1

        # Route to appropriate handler
        if tool_name == "load_data":
            return self._handle_load_data(**kwargs)
        elif tool_name == "show_data":
            return self._handle_show_data(**kwargs)
        elif tool_name == "describe_data":
            return self._handle_describe_data()
        elif tool_name == "show_columns":
            return self._handle_show_columns()
        elif tool_name == "show_missing":
            return self._handle_show_missing()
        elif tool_name == "assess_quality":
            return self._handle_assess_quality()
        elif tool_name == "detect_issues":
            return self._handle_detect_issues()
        elif tool_name == "remove_duplicates":
            return self._handle_remove_duplicates(**kwargs)
        elif tool_name == "handle_missing":
            return self._handle_handle_missing(**kwargs)
        elif tool_name == "validate_ranges":
            return self._handle_validate_ranges(**kwargs)
        elif tool_name == "save_data":
            return self._handle_save_data(**kwargs)
        elif tool_name == "export_audit":
            return self._handle_export_audit(**kwargs)
        elif tool_name == "export_lineage":
            return self._handle_export_lineage(**kwargs)
        elif tool_name == "show_stats":
            return self._handle_show_stats()
        elif tool_name == "list_tools":
            return self._handle_list_tools(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

    def _ensure_data_loaded(self) -> Optional[str]:
        """Check if data is loaded, return error message if not."""
        if not self.data_loaded or self.handler is None:
            return "No data loaded. Please use 'load_data' tool first."
        return None

    # Tool implementations
    def _handle_load_data(self, file_path: str, data_type: str = "clinical_trial") -> Dict:
        """Load data from file."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {file_path}"
                }

            # Initialize handler
            self.handler = EnhancedClinicalTrialHandler(
                data_path=path,
                user_id=self.user_id
            )

            # Load data
            df = self.handler.load_data()
            self.data_loaded = True
            self.current_file = path
            self.stats["data_operations"] += 1

            # Return summary
            return {
                "success": True,
                "message": f"Loaded data from {file_path}",
                "summary": {
                    "file": str(path),
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
                    "preview": df.head(3).to_dict(orient="records")
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load data: {str(e)}"
            }

    def _handle_show_data(self, n: int = 5) -> Dict:
        """Show first N rows."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            df = self.handler.df
            preview = df.head(n)

            return {
                "success": True,
                "data": preview.to_string(index=False),
                "rows_shown": len(preview),
                "total_rows": len(df)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_describe_data(self) -> Dict:
        """Show statistical summary."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            df = self.handler.df
            desc = df.describe(include='all')

            return {
                "success": True,
                "description": desc.to_string(),
                "summary": {
                    "total_records": len(df),
                    "total_fields": len(df.columns),
                    "numeric_fields": len(df.select_dtypes(include='number').columns),
                    "categorical_fields": len(df.select_dtypes(include='object').columns)
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_show_columns(self) -> Dict:
        """Show column information."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            df = self.handler.df
            columns_info = {
                col: {
                    "dtype": str(dtype),
                    "non_null": int(df[col].count()),
                    "null": int(df[col].isnull().sum()),
                    "unique": int(df[col].nunique())
                }
                for col, dtype in df.dtypes.items()
            }

            return {
                "success": True,
                "columns": columns_info,
                "total_columns": len(df.columns)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_show_missing(self) -> Dict:
        """Show missing value statistics."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            df = self.handler.df
            missing_info = {}

            for col in df.columns:
                missing_count = df[col].isnull().sum()
                if missing_count > 0:
                    missing_info[col] = {
                        "count": int(missing_count),
                        "percentage": float(missing_count / len(df) * 100)
                    }

            total_missing = sum(info["count"] for info in missing_info.values())

            return {
                "success": True,
                "missing_by_column": missing_info,
                "total_missing": total_missing,
                "columns_with_missing": len(missing_info)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_assess_quality(self) -> Dict:
        """Assess data quality."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            quality = self.handler.assess_data_quality()

            return {
                "success": True,
                "quality_score": quality.overall_score,
                "quality_level": quality.data_quality_level,
                "dimensions": {
                    "completeness": quality.completeness_score,
                    "validity": quality.validity_score,
                    "consistency": quality.consistency_score,
                    "uniqueness": quality.uniqueness_score
                },
                "details": quality.to_dict()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_detect_issues(self) -> Dict:
        """Detect data quality issues."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            issues = self.handler.detect_issues_with_evidence()

            return {
                "success": True,
                "issues_count": len(issues),
                "issues": [
                    {
                        "severity": issue["severity"].value,
                        "category": issue["category"],
                        "field": issue.get("field"),
                        "message": issue.get("message"),
                        "count": issue.get("count"),
                        "evidence": issue.get("evidence"),
                        "recommendation": issue.get("recommendation")
                    }
                    for issue in issues
                ]
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_remove_duplicates(self, keep: str = "first", subset: Optional[List] = None) -> Dict:
        """Remove duplicates."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            removed = self.handler.clean_duplicates_with_lineage(keep=keep, subset=subset)
            self.stats["data_operations"] += 1

            return {
                "success": True,
                "removed_count": removed,
                "message": f"Removed {removed} duplicate records",
                "current_records": len(self.handler.df)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_handle_missing(self, column: str, auto_select: bool = True) -> Dict:
        """Handle missing values."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            affected, method, evidence_id = self.handler.handle_missing_values_evidence_based(
                column, auto_select=auto_select
            )
            self.stats["data_operations"] += 1

            return {
                "success": True,
                "column": column,
                "records_affected": affected,
                "method_used": method,
                "evidence_id": evidence_id,
                "message": f"Handled {affected} missing values in '{column}' using {method} method"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_validate_ranges(self, field: str, action: str = "flag") -> Dict:
        """Validate value ranges."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            # Get reference range from knowledge base
            ref_range = self.handler.medical_standards.get_reference_range(field)

            if not ref_range:
                return {
                    "success": False,
                    "error": f"No reference range found for field '{field}'"
                }

            min_val = ref_range.get("min")
            max_val = ref_range.get("max")

            df = self.handler.df
            if field not in df.columns:
                return {
                    "success": False,
                    "error": f"Field '{field}' not found in data"
                }

            # Check out of range
            out_of_range = ((df[field] < min_val) | (df[field] > max_val)).sum()

            return {
                "success": True,
                "field": field,
                "out_of_range_count": int(out_of_range),
                "reference_range": (min_val, max_val),
                "action_taken": action,
                "message": f"Found {out_of_range} values outside range ({min_val}-{max_val})"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_save_data(self, output_path: str) -> Dict:
        """Save cleaned data."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            path = Path(output_path)
            self.handler.save_cleaned_data(path)

            return {
                "success": True,
                "output_path": str(path),
                "records_saved": len(self.handler.df),
                "message": f"Data saved to {path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_export_audit(self, output_path: str) -> Dict:
        """Export audit trail."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            path = Path(output_path)
            self.handler.export_audit_trail(path)

            return {
                "success": True,
                "output_path": str(path),
                "audit_entries": len(self.handler.audit_trail),
                "message": f"Audit trail exported to {path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_export_lineage(self, output_path: str) -> Dict:
        """Export data lineage."""
        error = self._ensure_data_loaded()
        if error:
            return {"success": False, "error": error}

        try:
            path = Path(output_path)
            self.handler.export_lineage(path)

            return {
                "success": True,
                "output_path": str(path),
                "lineage_entries": len(self.handler.lineage),
                "message": f"Data lineage exported to {path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _handle_show_stats(self) -> Dict:
        """Show session statistics."""
        stats = self.stats.copy()

        if self.handler:
            stats["data_info"] = {
                "current_file": str(self.current_file) if self.current_file else None,
                "records": len(self.handler.df),
                "columns": len(self.handler.df.columns),
                "operations_performed": len(self.handler.audit_trail),
                "lineage_tracked": len(self.handler.lineage)
            }

        return {
            "success": True,
            "stats": stats
        }

    def _handle_list_tools(self, category: Optional[str] = None) -> Dict:
        """List available tools."""
        try:
            cat_enum = ToolCategory(category) if category else None
            tools = self.tools.list_tools(cat_enum)

            return {
                "success": True,
                "tools": [
                    {
                        "name": t.name,
                        "category": t.category.value,
                        "description": t.description,
                        "parameters": [
                            {
                                "name": p.name,
                                "type": p.type,
                                "required": p.required,
                                "description": p.description
                            }
                            for p in t.parameters
                        ]
                    }
                    for t in tools
                ],
                "total_tools": len(tools)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_context_summary(self) -> str:
        """Get a summary of current context for LLM."""
        if not self.data_loaded:
            return "No data loaded yet."

        summary_parts = [
            f"Data loaded from: {self.current_file}",
            f"Records: {len(self.handler.df)}",
            f"Columns: {len(self.handler.df.columns)}",
            f"Operations performed: {len(self.handler.audit_trail)}"
        ]

        if self.handler.current_quality:
            quality = self.handler.current_quality
            summary_parts.append(
                f"Quality Score: {quality.overall_score:.2%} ({quality.data_quality_level})"
            )

        return "\n".join(summary_parts)
