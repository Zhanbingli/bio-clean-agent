"""LLM-powered Interactive REPL - True AI Agent with DeepSeek."""

from __future__ import annotations

import sys
import json
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.prompt import Prompt, Confirm
    from rich.status import Status
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from .session import InteractiveSession
from .llm_engine import LLMEngine, ConversationManager


class LLMPoweredREPL:
    """
    LLM-Powered Interactive REPL.

    Features:
    - Natural language understanding via LLM (DeepSeek/OpenAI)
    - Intelligent tool calling
    - Context-aware conversations
    - Beautiful terminal UI
    """

    def __init__(
        self,
        user_id: str = "user",
        llm_provider: str = "deepseek",
        enable_llm: bool = True
    ):
        self.session = InteractiveSession(user_id)
        self.console = Console() if RICH_AVAILABLE else None
        self.running = True
        self.enable_llm = enable_llm

        # Initialize LLM
        self.llm_engine: Optional[LLMEngine] = None
        self.conversation: Optional[ConversationManager] = None

        if enable_llm:
            self._initialize_llm(llm_provider)

    def _initialize_llm(self, provider: str) -> None:
        """Initialize LLM engine."""
        try:
            # Create LLM engine from environment
            self.llm_engine = LLMEngine.from_env(provider)

            # Create conversation manager with tools
            tools_schema = self.session.tools.get_tools_schema()
            self.conversation = ConversationManager(
                self.llm_engine,
                tools_schema
            )

            if self.console:
                self.console.print(f"[green]✓ LLM initialized: {provider}[/green]")

        except Exception as e:
            if self.console:
                self.console.print(
                    f"[yellow]⚠ LLM initialization failed: {e}[/yellow]"
                )
                self.console.print(
                    "[dim]Falling back to rule-based mode[/dim]"
                )
            self.enable_llm = False

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

                # Process with LLM or fallback
                if self.enable_llm and self.conversation:
                    self._process_with_llm(user_input)
                else:
                    self._process_with_rules(user_input)

            except KeyboardInterrupt:
                if self._confirm_exit():
                    break
                continue
            except EOFError:
                break
            except Exception as e:
                self._print_error(f"Error: {str(e)}")

        self._show_goodbye()

    def _process_with_llm(self, user_input: str) -> None:
        """Process input using LLM."""
        # Show thinking indicator
        if self.console:
            with Status("[bold cyan]🤔 Thinking...", console=self.console):
                response = self.conversation.process_user_input(
                    user_input,
                    tool_executor=self.session,
                    max_iterations=5
                )
        else:
            print("\n🤔 Thinking...")
            response = self.conversation.process_user_input(
                user_input,
                tool_executor=self.session,
                max_iterations=5
            )

        # Display response
        if self.console:
            self.console.print(f"\n[bold blue]Assistant:[/bold blue]")
            self.console.print(Panel(
                Markdown(response),
                border_style="blue",
                padding=(1, 2)
            ))
        else:
            print(f"\nAssistant: {response}")

    def _process_with_rules(self, user_input: str) -> None:
        """Fallback to rule-based processing."""
        # Use the rule-based parsing from original REPL
        from .repl import InteractiveREPL
        temp_repl = InteractiveREPL(self.session.user_id)
        temp_repl.session = self.session
        temp_repl.console = self.console
        temp_repl._process_input(user_input)

    def _show_welcome(self) -> None:
        """Show welcome message."""
        if self.console:
            llm_status = (
                f"[green]✓ LLM Enabled: {self.llm_engine.config.model}[/green]"
                if self.enable_llm
                else "[yellow]⚠ Rule-based mode (LLM not available)[/yellow]"
            )

            welcome_text = f"""
# 🧬 Bio Clean Agent - AI-Powered Interactive CLI

{llm_status}

Welcome to the intelligent data cleaning assistant!

**Quick Start:**
- Ask me anything in natural language
- I'll understand your intent and call the right tools
- Use `/help` to see available commands
- Press Ctrl+C to exit

**Example requests:**
- "Load the clinical trial data from trial_data.csv"
- "Can you show me what the data looks like?"
- "Assess the quality and tell me what issues you find"
- "Clean the data by removing duplicates and handling missing values"
- "Save the cleaned data to output.csv"

**Pro tip:** Just talk naturally - I understand context! 💡
            """

            self.console.print(Panel(
                Markdown(welcome_text),
                title="[bold cyan]Welcome[/bold cyan]",
                border_style="cyan",
                box=box.DOUBLE
            ))
        else:
            print("\n" + "="*60)
            print("Bio Clean Agent - AI-Powered CLI")
            if self.enable_llm:
                print(f"LLM: {self.llm_engine.config.model}")
            else:
                print("Mode: Rule-based")
            print("="*60)
            print("\nType your requests in natural language")
            print("Type '/help' for commands or '/exit' to quit\n")

    def _get_user_input(self) -> str:
        """Get user input."""
        if self.console:
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

        elif cmd == "/llm":
            self._show_llm_info()

        elif cmd == "/tools":
            self._show_tools()

        elif cmd == "/stats":
            result = self.session.execute_tool("show_stats")
            self._display_stats(result)

        elif cmd == "/status":
            self._show_status()

        elif cmd == "/history":
            self._show_history()

        elif cmd == "/clear":
            if self.console:
                self.console.clear()
            else:
                print("\n" * 50)

        elif cmd == "/reset":
            if self.conversation:
                self.conversation.clear_history()
            self._print_info("Conversation history cleared")

        else:
            self._print_error(f"Unknown command: {command}")
            self._print_info("Type '/help' for available commands")

    def _show_help(self) -> None:
        """Show help."""
        if self.console:
            help_text = """
# Available Commands

**Slash Commands:**
- `/help` - Show this help
- `/llm` - Show LLM information
- `/tools` - List available tools
- `/stats` - Session statistics
- `/status` - Current status
- `/history` - Conversation history
- `/reset` - Clear conversation (keep session data)
- `/clear` - Clear screen
- `/exit` - Exit

**Natural Language Examples:**
- "Load data from my_data.csv and show me a preview"
- "What's the quality of this data?"
- "Find any issues and recommend cleaning strategies"
- "Remove all duplicates and handle missing values in age column"
- "Save the cleaned data and export the audit trail"
- "Show me statistics about this cleaning session"
            """

            self.console.print(Panel(
                Markdown(help_text),
                title="[bold cyan]Help[/bold cyan]",
                border_style="cyan"
            ))
        else:
            print("\nAvailable Commands:")
            print("  /help - Show help")
            print("  /llm - LLM info")
            print("  /tools - List tools")
            print("  /exit - Exit\n")

    def _show_llm_info(self) -> None:
        """Show LLM information."""
        if not self.enable_llm:
            self._print_info("LLM is not enabled. Running in rule-based mode.")
            return

        if self.console:
            table = Table(title="🤖 LLM Information", box=box.ROUNDED)
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Provider", self.llm_engine.config.provider.value)
            table.add_row("Model", self.llm_engine.config.model)
            table.add_row("Temperature", str(self.llm_engine.config.temperature))
            table.add_row("Max Tokens", str(self.llm_engine.config.max_tokens))

            if self.conversation:
                table.add_row(
                    "Messages in Context",
                    str(len(self.conversation.messages))
                )

            self.console.print("\n")
            self.console.print(table)
        else:
            print(f"\nLLM Provider: {self.llm_engine.config.provider.value}")
            print(f"Model: {self.llm_engine.config.model}")

    def _show_tools(self) -> None:
        """Show available tools."""
        tools = self.session.tools.list_tools()

        if self.console:
            by_category = {}
            for tool in tools:
                cat = tool.category.value
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(tool)

            for category, cat_tools in by_category.items():
                table = Table(
                    title=f"📦 {category.replace('_', ' ').title()}",
                    box=box.ROUNDED
                )
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

    def _show_status(self) -> None:
        """Show current status."""
        status_parts = []

        # LLM status
        if self.enable_llm:
            status_parts.append(f"✓ LLM: {self.llm_engine.config.model}")
        else:
            status_parts.append("⚠ LLM: Disabled")

        # Data status
        if self.session.data_loaded:
            status_parts.append("✓ Data loaded")
            status_parts.append(self.session.get_context_summary())
        else:
            status_parts.append("⚠ No data loaded")

        status_content = "\n".join(status_parts)

        if self.console:
            self.console.print(Panel(
                status_content,
                title="Session Status",
                border_style="blue"
            ))
        else:
            print(f"\n{status_content}")

    def _show_history(self) -> None:
        """Show conversation history."""
        if not self.enable_llm or not self.conversation:
            self._print_info("Conversation history only available in LLM mode")
            return

        messages = self.conversation.get_conversation_history()

        if self.console:
            for msg in messages[-10:]:  # Last 10
                if msg.role == "system":
                    continue

                role_color = (
                    "green" if msg.role == "user"
                    else "blue" if msg.role == "assistant"
                    else "yellow"
                )

                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                self.console.print(f"[{role_color}]{msg.role}:[/{role_color}] {content}\n")
        else:
            for msg in messages[-10:]:
                if msg.role != "system":
                    print(f"{msg.role}: {msg.content}\n")

    def _display_stats(self, result: Dict) -> None:
        """Display session statistics."""
        if not result.get("success"):
            self._print_error(result.get("error", "Failed to get stats"))
            return

        stats = result.get("stats", {})

        if self.console:
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
                table.add_row("Operations", str(data_info.get("operations_performed", 0)))

            self.console.print("\n")
            self.console.print(table)
        else:
            print("\nSession Statistics:")
            print(json.dumps(stats, indent=2))

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
            return Confirm.ask(
                "\n[yellow]Are you sure you want to exit?[/yellow]",
                default=True
            )
        else:
            response = input("\nExit? (y/n): ")
            return response.lower() in ["y", "yes"]

    def _show_goodbye(self) -> None:
        """Show goodbye message."""
        if self.console:
            self.console.print(
                "\n[bold cyan]👋 Goodbye! Thanks for using Bio Clean Agent.[/bold cyan]\n"
            )
        else:
            print("\n👋 Goodbye!\n")
