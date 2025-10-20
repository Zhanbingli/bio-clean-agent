"""Interactive REPL (Read-Eval-Print Loop) - Claude Code style CLI interface."""

from __future__ import annotations

import sys
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.markdown import Markdown
    from rich.prompt import Prompt, Confirm
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .session import InteractiveSession
from .tools import ToolCategory


class InteractiveREPL:
    """
    Interactive REPL for Bio Clean Agent.

    Features:
    - Beautiful terminal UI with Rich
    - Tool execution with visual feedback
    - Conversation history
    - Context-aware suggestions
    - Similar UX to Claude Code
    """

    def __init__(self, user_id: str = "user"):
        self.session = InteractiveSession(user_id)
        self.console = Console() if RICH_AVAILABLE else None
        self.running = True

    def start(self) -> None:
        """Start the interactive REPL."""
        self._show_welcome()

        while self.running:
            try:
                # Get user input
                user_input = self._get_user_input()

                if not user_input or user_input.strip() == "":
                    continue

                # Handle special commands
                if user_input.startswith("/"):
                    self._handle_command(user_input)
                    continue

                # Process as natural language
                self._process_input(user_input)

            except KeyboardInterrupt:
                if self._confirm_exit():
                    break
                continue
            except EOFError:
                break
            except Exception as e:
                self._print_error(f"Error: {str(e)}")

        self._show_goodbye()

    def _show_welcome(self) -> None:
        """Show welcome message."""
        if self.console:
            welcome_text = """
# 🧬 Bio Clean Agent - Interactive CLI

Welcome to the interactive data cleaning assistant!

**Quick Start:**
- Type your requests in natural language
- Use `/help` to see available commands
- Use `/tools` to list all tools
- Press Ctrl+C to exit

**Example requests:**
- "Load data from trial_data.csv"
- "Show me the first 10 rows"
- "Assess data quality"
- "Remove duplicates and handle missing values"
            """

            self.console.print(Panel(
                Markdown(welcome_text),
                title="[bold cyan]Welcome[/bold cyan]",
                border_style="cyan",
                box=box.DOUBLE
            ))
        else:
            print("\n" + "="*60)
            print("Bio Clean Agent - Interactive CLI")
            print("="*60)
            print("\nType '/help' for available commands")
            print("Type '/exit' to quit\n")

    def _get_user_input(self) -> str:
        """Get user input with rich prompt."""
        if self.console:
            # Show context if data is loaded
            context = ""
            if self.session.data_loaded:
                context = f" [{len(self.session.handler.df)} rows]"

            return Prompt.ask(
                f"\n[bold green]You{context}[/bold green]",
                default=""
            )
        else:
            return input("\nYou: ")

    def _handle_command(self, command: str) -> None:
        """Handle slash commands."""
        cmd = command.lower().strip()

        if cmd in ["/exit", "/quit", "/q"]:
            self.running = False

        elif cmd == "/help":
            self._show_help()

        elif cmd == "/tools":
            self._show_tools()

        elif cmd.startswith("/tool "):
            # Show specific tool info
            tool_name = cmd.replace("/tool ", "").strip()
            self._show_tool_info(tool_name)

        elif cmd == "/stats":
            self._show_stats()

        elif cmd == "/history":
            self._show_history()

        elif cmd == "/clear":
            if self.console:
                self.console.clear()
            else:
                print("\n" * 50)

        elif cmd == "/status":
            self._show_status()

        else:
            self._print_error(f"Unknown command: {command}")
            self._print_info("Type '/help' to see available commands")

    def _process_input(self, user_input: str) -> None:
        """
        Process natural language input.

        This simulates what would happen with an LLM:
        1. Parse user intent
        2. Determine which tools to use
        3. Execute tools
        4. Show results
        """
        self.session.add_message("user", user_input)

        # Simple rule-based routing (in production, this would be LLM)
        intent = self._parse_intent(user_input)

        if intent:
            self._execute_intent(intent)
        else:
            self._print_info(
                "I understand you want to work with data, but I need more specific instructions.\n"
                "Try: 'load data from [file]', 'show data', 'assess quality', etc."
            )

    def _parse_intent(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse user intent from text (simplified version).

        In production, this would use an LLM.
        """
        text_lower = text.lower()

        # Load data
        if "load" in text_lower and ("data" in text_lower or "file" in text_lower):
            # Extract file path
            import re
            # Look for file path patterns
            file_match = re.search(r'[\w\./\\-]+\.(?:csv|xlsx|xls)', text)
            if file_match:
                return {
                    "tool": "load_data",
                    "params": {"file_path": file_match.group(0)}
                }

        # Show data
        if any(word in text_lower for word in ["show", "display", "view"]) and "data" in text_lower:
            # Extract number if present
            import re
            num_match = re.search(r'(\d+)\s+rows?', text_lower)
            n = int(num_match.group(1)) if num_match else 5
            return {
                "tool": "show_data",
                "params": {"n": n}
            }

        # Describe
        if any(word in text_lower for word in ["describe", "summary", "statistics"]):
            return {"tool": "describe_data", "params": {}}

        # Columns
        if "columns" in text_lower or "fields" in text_lower:
            return {"tool": "show_columns", "params": {}}

        # Missing values
        if "missing" in text_lower and not any(word in text_lower for word in ["handle", "fix", "clean"]):
            return {"tool": "show_missing", "params": {}}

        # Quality assessment
        if "quality" in text_lower or "assess" in text_lower:
            return {"tool": "assess_quality", "params": {}}

        # Detect issues
        if "issues" in text_lower or "problems" in text_lower or "detect" in text_lower:
            return {"tool": "detect_issues", "params": {}}

        # Remove duplicates
        if "duplicate" in text_lower and any(word in text_lower for word in ["remove", "delete", "clean"]):
            return {"tool": "remove_duplicates", "params": {"keep": "first"}}

        # Handle missing
        if "missing" in text_lower and any(word in text_lower for word in ["handle", "fix", "clean", "fill"]):
            # Extract column name
            import re
            # Try to find column name in quotes or after "in"
            col_match = re.search(r'["\'](\w+)["\']|in\s+(\w+)', text_lower)
            if col_match:
                column = col_match.group(1) or col_match.group(2)
                return {
                    "tool": "handle_missing",
                    "params": {"column": column, "auto_select": True}
                }

        # Save data
        if "save" in text_lower or "export" in text_lower:
            if "audit" in text_lower:
                import re
                file_match = re.search(r'[\w\./\\-]+\.json', text)
                file_path = file_match.group(0) if file_match else "output/audit.json"
                return {"tool": "export_audit", "params": {"output_path": file_path}}
            elif "lineage" in text_lower:
                import re
                file_match = re.search(r'[\w\./\\-]+\.json', text)
                file_path = file_match.group(0) if file_match else "output/lineage.json"
                return {"tool": "export_lineage", "params": {"output_path": file_path}}
            else:
                import re
                file_match = re.search(r'[\w\./\\-]+\.(?:csv|xlsx)', text)
                file_path = file_match.group(0) if file_match else "output/cleaned_data.csv"
                return {"tool": "save_data", "params": {"output_path": file_path}}

        # Stats
        if "stats" in text_lower or "statistics" in text_lower and "session" in text_lower:
            return {"tool": "show_stats", "params": {}}

        return None

    def _execute_intent(self, intent: Dict[str, Any]) -> None:
        """Execute parsed intent."""
        tool_name = intent["tool"]
        params = intent.get("params", {})

        # Show what we're doing
        self._print_tool_call(tool_name, params)

        # Execute tool
        result = self.session.execute_tool(tool_name, **params)

        # Display result
        self._display_result(tool_name, result)

        # Add to history
        self.session.add_message("assistant", f"Executed {tool_name}", tool_calls=[intent])

    def _print_tool_call(self, tool_name: str, params: Dict) -> None:
        """Print tool call in progress."""
        if self.console:
            params_str = json.dumps(params, indent=2) if params else "{}"
            self.console.print(
                f"\n[dim]🔧 Calling tool: [bold]{tool_name}[/bold][/dim]"
            )
            if params:
                self.console.print(f"[dim]   Parameters: {params_str}[/dim]")
        else:
            print(f"\n🔧 Calling tool: {tool_name}")
            if params:
                print(f"   Parameters: {params}")

    def _display_result(self, tool_name: str, result: Dict[str, Any]) -> None:
        """Display tool execution result."""
        if not result.get("success"):
            self._print_error(result.get("error", "Unknown error"))
            return

        if self.console:
            # Format output based on tool
            if tool_name == "load_data":
                self._display_load_result(result)
            elif tool_name == "show_data":
                self._display_show_data(result)
            elif tool_name == "describe_data":
                self._display_describe(result)
            elif tool_name == "show_columns":
                self._display_columns(result)
            elif tool_name == "show_missing":
                self._display_missing(result)
            elif tool_name == "assess_quality":
                self._display_quality(result)
            elif tool_name == "detect_issues":
                self._display_issues(result)
            elif tool_name in ["remove_duplicates", "handle_missing"]:
                self._display_cleaning_result(result)
            elif tool_name in ["save_data", "export_audit", "export_lineage"]:
                self._display_export_result(result)
            elif tool_name == "show_stats":
                self._display_stats(result)
            else:
                self._display_generic(result)
        else:
            # Plain text output
            print(f"\n✓ Success")
            print(json.dumps(result, indent=2))

    def _display_load_result(self, result: Dict) -> None:
        """Display load data result."""
        summary = result.get("summary", {})

        table = Table(title="📂 Data Loaded Successfully", box=box.ROUNDED)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("File", str(summary.get("file")))
        table.add_row("Rows", str(summary.get("rows")))
        table.add_row("Columns", str(summary.get("columns")))

        self.console.print("\n")
        self.console.print(table)

        # Show column names
        columns = summary.get("column_names", [])
        self.console.print(f"\n[bold]Columns:[/bold] {', '.join(columns)}")

    def _display_show_data(self, result: Dict) -> None:
        """Display data preview."""
        self.console.print(f"\n[bold]Data Preview[/bold] (showing {result['rows_shown']} of {result['total_rows']} rows)\n")
        self.console.print(Panel(result["data"], border_style="blue"))

    def _display_describe(self, result: Dict) -> None:
        """Display statistical summary."""
        self.console.print("\n[bold]Statistical Summary[/bold]\n")
        self.console.print(Panel(result["description"], border_style="blue"))

    def _display_columns(self, result: Dict) -> None:
        """Display columns information."""
        table = Table(title="📊 Columns Information", box=box.ROUNDED)
        table.add_column("Column", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Non-Null", style="yellow")
        table.add_column("Null", style="red")
        table.add_column("Unique", style="magenta")

        for col, info in result["columns"].items():
            table.add_row(
                col,
                info["dtype"],
                str(info["non_null"]),
                str(info["null"]),
                str(info["unique"])
            )

        self.console.print("\n")
        self.console.print(table)

    def _display_missing(self, result: Dict) -> None:
        """Display missing values."""
        if not result.get("missing_by_column"):
            self.console.print("\n[green]✓ No missing values found![/green]")
            return

        table = Table(title="🔍 Missing Values", box=box.ROUNDED)
        table.add_column("Column", style="cyan")
        table.add_column("Count", style="red")
        table.add_column("Percentage", style="yellow")

        for col, info in result["missing_by_column"].items():
            table.add_row(
                col,
                str(info["count"]),
                f"{info['percentage']:.1f}%"
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print(f"\n[bold]Total missing values:[/bold] {result['total_missing']}")

    def _display_quality(self, result: Dict) -> None:
        """Display quality assessment."""
        score = result["quality_score"]
        level = result["quality_level"]

        # Color based on level
        color = "green" if score >= 0.9 else "yellow" if score >= 0.75 else "red"

        self.console.print(f"\n[bold]Overall Quality Score:[/bold] [{color}]{score:.1%}[/{color}] ({level})")

        # Dimensions table
        table = Table(title="📈 Quality Dimensions", box=box.ROUNDED)
        table.add_column("Dimension", style="cyan")
        table.add_column("Score", style="green")
        table.add_column("Bar", style="blue")

        for dim, score in result["dimensions"].items():
            bar_length = int(score * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            table.add_row(dim.capitalize(), f"{score:.1%}", bar)

        self.console.print("\n")
        self.console.print(table)

    def _display_issues(self, result: Dict) -> None:
        """Display detected issues."""
        issues = result.get("issues", [])

        if not issues:
            self.console.print("\n[green]✓ No issues detected![/green]")
            return

        self.console.print(f"\n[bold]Detected {result['issues_count']} issues:[/bold]\n")

        for i, issue in enumerate(issues, 1):
            severity = issue["severity"]
            color = "red" if severity == "critical" else "yellow" if severity == "high" else "blue"

            panel_content = f"""**Severity:** [{color}]{severity.upper()}[/{color}]
**Category:** {issue['category']}
**Field:** {issue.get('field', 'N/A')}
**Count:** {issue.get('count', 'N/A')}

{issue.get('message', '')}

**Recommendation:** {issue.get('recommendation', 'N/A')}
"""
            if issue.get('evidence'):
                panel_content += f"\n**Evidence:** {issue['evidence']}"

            self.console.print(Panel(
                Markdown(panel_content),
                title=f"Issue {i}",
                border_style=color
            ))

    def _display_cleaning_result(self, result: Dict) -> None:
        """Display cleaning operation result."""
        self.console.print(f"\n[green]✓ {result.get('message', 'Operation completed')}[/green]")

        if "records_affected" in result:
            self.console.print(f"   Records affected: {result['records_affected']}")
        if "method_used" in result:
            self.console.print(f"   Method: {result['method_used']}")
        if "evidence_id" in result and result["evidence_id"]:
            self.console.print(f"   Evidence: {result['evidence_id']}")

    def _display_export_result(self, result: Dict) -> None:
        """Display export result."""
        self.console.print(f"\n[green]✓ {result.get('message', 'Export completed')}[/green]")
        self.console.print(f"   File: {result.get('output_path')}")

    def _display_stats(self, result: Dict) -> None:
        """Display session statistics."""
        stats = result.get("stats", {})

        table = Table(title="📊 Session Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Session Start", stats.get("session_start", "N/A"))
        table.add_row("Commands Executed", str(stats.get("commands_executed", 0)))

        if "data_info" in stats:
            data_info = stats["data_info"]
            table.add_row("Current File", data_info.get("current_file", "N/A"))
            table.add_row("Records", str(data_info.get("records", 0)))
            table.add_row("Columns", str(data_info.get("columns", 0)))
            table.add_row("Operations Performed", str(data_info.get("operations_performed", 0)))

        self.console.print("\n")
        self.console.print(table)

    def _display_generic(self, result: Dict) -> None:
        """Generic result display."""
        self.console.print(f"\n[green]✓ Success[/green]")
        self.console.print(Panel(json.dumps(result, indent=2), border_style="green"))

    def _show_help(self) -> None:
        """Show help message."""
        if self.console:
            help_text = """
# Available Commands

**Slash Commands:**
- `/help` - Show this help message
- `/tools` - List all available tools
- `/tool <name>` - Show details for a specific tool
- `/stats` - Show session statistics
- `/status` - Show current session status
- `/history` - Show conversation history
- `/clear` - Clear screen
- `/exit` or `/quit` - Exit the program

**Natural Language Examples:**
- "Load data from trial_data.csv"
- "Show me the first 10 rows"
- "Describe the data"
- "What columns do I have?"
- "Show missing values"
- "Assess data quality"
- "Detect issues"
- "Remove duplicates"
- "Handle missing values in systolic_bp"
- "Save data to cleaned.csv"
- "Export audit trail"
            """

            self.console.print(Panel(
                Markdown(help_text),
                title="[bold cyan]Help[/bold cyan]",
                border_style="cyan"
            ))
        else:
            print("\nAvailable Commands:")
            print("  /help - Show help")
            print("  /tools - List tools")
            print("  /exit - Exit\n")

    def _show_tools(self) -> None:
        """Show available tools."""
        tools = self.session.tools.list_tools()

        if self.console:
            # Group by category
            by_category = {}
            for tool in tools:
                cat = tool.category.value
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(tool)

            for category, cat_tools in by_category.items():
                table = Table(title=f"📦 {category.replace('_', ' ').title()}", box=box.ROUNDED)
                table.add_column("Tool", style="cyan")
                table.add_column("Description", style="white")

                for tool in cat_tools:
                    table.add_row(tool.name, tool.description)

                self.console.print("\n")
                self.console.print(table)
        else:
            print("\nAvailable Tools:")
            for tool in tools:
                print(f"  {tool.name} - {tool.description}")

    def _show_tool_info(self, tool_name: str) -> None:
        """Show detailed information about a tool."""
        tool = self.session.tools.get_tool(tool_name)

        if not tool:
            self._print_error(f"Tool not found: {tool_name}")
            return

        if self.console:
            info = f"""
**Category:** {tool.category.value}
**Description:** {tool.description}
**Returns:** {tool.returns}

**Parameters:**
"""
            for param in tool.parameters:
                required = "✓" if param.required else ""
                info += f"\n- `{param.name}` ({param.type}) {required}\n  {param.description}"
                if param.default is not None:
                    info += f"\n  Default: {param.default}"

            self.console.print(Panel(
                Markdown(info),
                title=f"[bold cyan]Tool: {tool_name}[/bold cyan]",
                border_style="cyan"
            ))
        else:
            print(f"\nTool: {tool_name}")
            print(f"Description: {tool.description}")

    def _show_stats(self) -> None:
        """Show session stats."""
        result = self.session.execute_tool("show_stats")
        self._display_stats(result)

    def _show_status(self) -> None:
        """Show current status."""
        if self.console:
            status = "✓ Data loaded" if self.session.data_loaded else "⚠ No data loaded"
            color = "green" if self.session.data_loaded else "yellow"

            content = f"[{color}]{status}[/{color}]\n\n"

            if self.session.data_loaded:
                content += self.session.get_context_summary()

            self.console.print(Panel(content, title="Session Status", border_style="blue"))
        else:
            print(f"\nStatus: {'Data loaded' if self.session.data_loaded else 'No data loaded'}")
            if self.session.data_loaded:
                print(self.session.get_context_summary())

    def _show_history(self) -> None:
        """Show conversation history."""
        if not self.session.history:
            self._print_info("No history yet")
            return

        if self.console:
            for msg in self.session.history[-10:]:  # Last 10 messages
                role = msg["role"]
                content = msg["content"]
                timestamp = msg["timestamp"].split("T")[1].split(".")[0]  # HH:MM:SS

                color = "green" if role == "user" else "blue"
                self.console.print(f"\n[dim]{timestamp}[/dim] [{color}]{role}:[/{color}] {content}")
        else:
            for msg in self.session.history[-10:]:
                print(f"{msg['role']}: {msg['content']}")

    def _print_error(self, message: str) -> None:
        """Print error message."""
        if self.console:
            self.console.print(f"\n[red]✗ {message}[/red]")
        else:
            print(f"\n✗ Error: {message}")

    def _print_info(self, message: str) -> None:
        """Print info message."""
        if self.console:
            self.console.print(f"\n[blue]ℹ {message}[/blue]")
        else:
            print(f"\nℹ {message}")

    def _confirm_exit(self) -> bool:
        """Confirm exit."""
        if self.console:
            return Confirm.ask("\n[yellow]Are you sure you want to exit?[/yellow]", default=True)
        else:
            response = input("\nAre you sure you want to exit? (y/n): ")
            return response.lower() in ["y", "yes"]

    def _show_goodbye(self) -> None:
        """Show goodbye message."""
        if self.console:
            self.console.print("\n[bold cyan]👋 Goodbye! Thanks for using Bio Clean Agent.[/bold cyan]\n")
        else:
            print("\n👋 Goodbye!\n")
