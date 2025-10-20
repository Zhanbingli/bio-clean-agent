"""Tool registry and execution system for interactive CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
from enum import Enum
import pandas as pd
from pathlib import Path


class ToolCategory(str, Enum):
    """Tool categories."""
    DATA_LOADING = "data_loading"
    DATA_INSPECTION = "data_inspection"
    DATA_CLEANING = "data_cleaning"
    QUALITY_ASSESSMENT = "quality_assessment"
    VALIDATION = "validation"
    EXPORT = "export"
    SYSTEM = "system"


@dataclass
class ToolParameter:
    """Tool parameter definition."""
    name: str
    type: str  # "string", "number", "boolean", "array"
    description: str
    required: bool = False
    default: Any = None
    choices: Optional[List[Any]] = None


@dataclass
class Tool:
    """Tool definition."""
    name: str
    category: ToolCategory
    description: str
    parameters: List[ToolParameter]
    function: Callable
    returns: str  # Description of return value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for LLM."""
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.type,
                        "description": p.description,
                        **({"enum": p.choices} if p.choices else {}),
                        **({"default": p.default} if p.default is not None else {})
                    }
                    for p in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required]
            },
            "returns": self.returns
        }


class ToolRegistry:
    """Registry of available tools for the agent."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_default_tools()

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)

    def list_tools(self, category: Optional[ToolCategory] = None) -> List[Tool]:
        """List all tools, optionally filtered by category."""
        if category:
            return [t for t in self.tools.values() if t.category == category]
        return list(self.tools.values())

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """Get all tools as schema for LLM."""
        return [tool.to_dict() for tool in self.tools.values()]

    def execute(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool with given parameters."""
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }

        try:
            # Validate required parameters
            required_params = [p.name for p in tool.parameters if p.required]
            missing = [p for p in required_params if p not in kwargs]
            if missing:
                return {
                    "success": False,
                    "error": f"Missing required parameters: {', '.join(missing)}"
                }

            # Execute tool
            result = tool.function(**kwargs)

            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }

    def _register_default_tools(self) -> None:
        """Register default tools."""

        # DATA LOADING
        self.register(Tool(
            name="load_data",
            category=ToolCategory.DATA_LOADING,
            description="Load clinical trial data from CSV or Excel file",
            parameters=[
                ToolParameter("file_path", "string", "Path to data file", required=True),
                ToolParameter("data_type", "string", "Type of data",
                             choices=["clinical_trial", "ehr", "genomics", "general"])
            ],
            function=self._load_data,
            returns="Dictionary with data summary (rows, columns, preview)"
        ))

        # DATA INSPECTION
        self.register(Tool(
            name="show_data",
            category=ToolCategory.DATA_INSPECTION,
            description="Display first N rows of the dataset",
            parameters=[
                ToolParameter("n", "number", "Number of rows to show", default=5)
            ],
            function=self._show_data,
            returns="String representation of data head"
        ))

        self.register(Tool(
            name="describe_data",
            category=ToolCategory.DATA_INSPECTION,
            description="Show statistical summary of the dataset",
            parameters=[],
            function=self._describe_data,
            returns="Statistical summary as string"
        ))

        self.register(Tool(
            name="show_columns",
            category=ToolCategory.DATA_INSPECTION,
            description="List all column names and their data types",
            parameters=[],
            function=self._show_columns,
            returns="Dictionary of column names and types"
        ))

        self.register(Tool(
            name="show_missing",
            category=ToolCategory.DATA_INSPECTION,
            description="Show missing value statistics for each column",
            parameters=[],
            function=self._show_missing,
            returns="Dictionary of missing value counts and percentages"
        ))

        # QUALITY ASSESSMENT
        self.register(Tool(
            name="assess_quality",
            category=ToolCategory.QUALITY_ASSESSMENT,
            description="Perform comprehensive ISO 8000 quality assessment",
            parameters=[],
            function=self._assess_quality,
            returns="Quality report with scores for all dimensions"
        ))

        self.register(Tool(
            name="detect_issues",
            category=ToolCategory.QUALITY_ASSESSMENT,
            description="Detect data quality issues with scientific evidence",
            parameters=[],
            function=self._detect_issues,
            returns="List of detected issues with severity and recommendations"
        ))

        # DATA CLEANING
        self.register(Tool(
            name="remove_duplicates",
            category=ToolCategory.DATA_CLEANING,
            description="Remove duplicate records with lineage tracking",
            parameters=[
                ToolParameter("keep", "string", "Which duplicate to keep",
                             choices=["first", "last"], default="first"),
                ToolParameter("subset", "array", "Columns to check for duplicates",
                             required=False)
            ],
            function=self._remove_duplicates,
            returns="Number of duplicates removed"
        ))

        self.register(Tool(
            name="handle_missing",
            category=ToolCategory.DATA_CLEANING,
            description="Handle missing values with evidence-based strategy",
            parameters=[
                ToolParameter("column", "string", "Column name", required=True),
                ToolParameter("auto_select", "boolean",
                             "Auto-select best method based on data", default=True)
            ],
            function=self._handle_missing,
            returns="Records affected, method used, and evidence ID"
        ))

        self.register(Tool(
            name="validate_ranges",
            category=ToolCategory.VALIDATION,
            description="Validate values are within acceptable medical ranges",
            parameters=[
                ToolParameter("field", "string", "Field to validate", required=True),
                ToolParameter("action", "string", "Action to take",
                             choices=["flag", "cap", "remove"], default="flag")
            ],
            function=self._validate_ranges,
            returns="Number of out-of-range values found"
        ))

        # EXPORT
        self.register(Tool(
            name="save_data",
            category=ToolCategory.EXPORT,
            description="Save cleaned data to file",
            parameters=[
                ToolParameter("output_path", "string", "Output file path", required=True)
            ],
            function=self._save_data,
            returns="Success message with file path"
        ))

        self.register(Tool(
            name="export_audit",
            category=ToolCategory.EXPORT,
            description="Export audit trail for regulatory compliance",
            parameters=[
                ToolParameter("output_path", "string", "Output file path", required=True)
            ],
            function=self._export_audit,
            returns="Success message with file path"
        ))

        self.register(Tool(
            name="export_lineage",
            category=ToolCategory.EXPORT,
            description="Export data lineage tracking",
            parameters=[
                ToolParameter("output_path", "string", "Output file path", required=True)
            ],
            function=self._export_lineage,
            returns="Success message with file path"
        ))

        # SYSTEM
        self.register(Tool(
            name="show_stats",
            category=ToolCategory.SYSTEM,
            description="Show current session statistics",
            parameters=[],
            function=self._show_stats,
            returns="Session statistics dictionary"
        ))

        self.register(Tool(
            name="list_tools",
            category=ToolCategory.SYSTEM,
            description="List all available tools",
            parameters=[
                ToolParameter("category", "string", "Filter by category", required=False)
            ],
            function=self._list_tools_func,
            returns="List of available tools"
        ))

    # Tool implementation functions (placeholders for context)
    def _load_data(self, file_path: str, data_type: str = "clinical_trial") -> Dict:
        """Load data - actual implementation in session."""
        return {"status": "delegated_to_session"}

    def _show_data(self, n: int = 5) -> str:
        return "delegated_to_session"

    def _describe_data(self) -> str:
        return "delegated_to_session"

    def _show_columns(self) -> Dict:
        return {"status": "delegated_to_session"}

    def _show_missing(self) -> Dict:
        return {"status": "delegated_to_session"}

    def _assess_quality(self) -> Dict:
        return {"status": "delegated_to_session"}

    def _detect_issues(self) -> List:
        return []

    def _remove_duplicates(self, keep: str = "first", subset: Optional[List] = None) -> int:
        return 0

    def _handle_missing(self, column: str, auto_select: bool = True) -> tuple:
        return (0, "none", None)

    def _validate_ranges(self, field: str, action: str = "flag") -> int:
        return 0

    def _save_data(self, output_path: str) -> str:
        return "delegated_to_session"

    def _export_audit(self, output_path: str) -> str:
        return "delegated_to_session"

    def _export_lineage(self, output_path: str) -> str:
        return "delegated_to_session"

    def _show_stats(self) -> Dict:
        return {"status": "delegated_to_session"}

    def _list_tools_func(self, category: Optional[str] = None) -> List[Dict]:
        """List tools."""
        cat_enum = ToolCategory(category) if category else None
        tools = self.list_tools(cat_enum)
        return [
            {
                "name": t.name,
                "category": t.category.value,
                "description": t.description
            }
            for t in tools
        ]
