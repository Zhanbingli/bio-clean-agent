"""Decision-making strategies for different execution modes."""

from __future__ import annotations

from typing import Any, Dict

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from .manager import DecisionContext, DecisionStrategy


class AutoApproveStrategy(DecisionStrategy):
    """Automatically approve all decisions using defaults or first option."""

    def decide(self, context: DecisionContext) -> Dict[str, Any]:
        """Auto-approve using default or first option."""
        if context.default_option:
            # Find the option with matching ID
            for option in context.options:
                if option.get("id") == context.default_option:
                    return option

        # Fall back to first option
        return context.options[0] if context.options else {}


class InteractiveStrategy(DecisionStrategy):
    """
    Prompt user for decision in terminal.

    This is NOT a chatbot - it's a structured decision point.
    """

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def decide(self, context: DecisionContext) -> Dict[str, Any]:
        """Present options and get user choice."""
        self._display_decision_prompt(context)

        # Build choice mapping
        choice_map = {str(i + 1): opt for i, opt in enumerate(context.options)}

        # Add default option
        default_key = None
        if context.default_option:
            for key, opt in choice_map.items():
                if opt.get("id") == context.default_option:
                    default_key = key
                    break

        # Get user choice
        while True:
            choice = Prompt.ask(
                "[bold cyan]Select option[/]",
                choices=list(choice_map.keys()),
                default=default_key,
            )

            if choice in choice_map:
                selected = choice_map[choice]
                self.console.print(
                    f"[green]✓[/] Selected: {selected.get('label', 'Unknown')}",
                )
                return selected

    def _display_decision_prompt(self, context: DecisionContext) -> None:
        """Display the decision prompt in a structured way."""
        # Header
        self.console.print(
            Panel(
                f"[bold yellow]⚠ Decision Required[/]\n\n{context.question}",
                title=f"Step: {context.step_name}",
                border_style="yellow",
            )
        )

        # Options table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("#", width=3, style="cyan")
        table.add_column("Option", style="white")
        table.add_column("Impact", style="dim")
        table.add_column("Recommended", width=12, style="green")

        for idx, option in enumerate(context.options, start=1):
            is_default = option.get("id") == context.default_option
            is_recommended = option.get("recommended", False)

            table.add_row(
                str(idx),
                option.get("label", "Unknown"),
                option.get("impact", ""),
                "✓" if (is_recommended or is_default) else "",
            )

        self.console.print(table)
        self.console.print()


class NotifyAndWaitStrategy(DecisionStrategy):
    """
    Notify user and wait for external decision resolution.

    This is useful for web-based or asynchronous workflows where
    the user will resolve the decision through an API or UI.
    """

    def __init__(self, timeout_seconds: int = 300):
        self.timeout_seconds = timeout_seconds
        self._pending_decisions: Dict[str, Dict[str, Any]] = {}

    def decide(self, context: DecisionContext) -> Dict[str, Any]:
        """
        Store decision and wait for external resolution.

        In a real implementation, this would:
        1. Emit an event/notification
        2. Wait for decision via API
        3. Return the user's choice

        For now, we'll return the default option.
        """
        decision_id = f"{context.job_id}:{context.step_name}"

        # Store pending decision
        self._pending_decisions[decision_id] = {
            "context": context,
            "resolved": False,
            "choice": None,
        }

        # TODO: In production, this would:
        # - Send notification (email, webhook, etc.)
        # - Wait for resolution via API
        # - Return the resolved choice

        # For now, return default
        if context.default_option:
            for option in context.options:
                if option.get("id") == context.default_option:
                    return option

        return context.options[0] if context.options else {}

    def resolve(self, decision_id: str, choice: Dict[str, Any]) -> None:
        """Externally resolve a pending decision."""
        if decision_id in self._pending_decisions:
            self._pending_decisions[decision_id]["resolved"] = True
            self._pending_decisions[decision_id]["choice"] = choice


class LLMAssistedStrategy(DecisionStrategy):
    """
    Use LLM to suggest a decision based on context and best practices.

    The LLM analyzes the situation and recommends an option, but
    this is NOT a chatbot - it's a structured analysis and recommendation.
    """

    def __init__(self, planner=None, auto_approve: bool = False):
        self.planner = planner
        self.auto_approve = auto_approve
        self.console = Console()

    def decide(self, context: DecisionContext) -> Dict[str, Any]:
        """Use LLM to analyze and recommend a decision."""
        if not self.planner:
            # Fall back to default
            return self._get_default_option(context)

        # Build analysis prompt
        prompt = self._build_analysis_prompt(context)

        try:
            # Get LLM recommendation
            response = self.planner.llm.complete(prompt)

            # Parse recommendation (simplified)
            # In production, use structured output
            recommended_id = self._parse_recommendation(response, context)

            # Find the recommended option
            for option in context.options:
                if option.get("id") == recommended_id:
                    if self.auto_approve:
                        return option
                    else:
                        # Show LLM reasoning and confirm
                        return self._confirm_llm_choice(context, option, response)

        except Exception as e:
            self.console.print(f"[red]LLM analysis failed: {e}[/]")

        # Fall back to default
        return self._get_default_option(context)

    def _build_analysis_prompt(self, context: DecisionContext) -> str:
        """Build prompt for LLM analysis."""
        options_text = "\n".join(
            f"- {opt.get('id')}: {opt.get('label')} (Impact: {opt.get('impact', 'Unknown')})"
            for opt in context.options
        )

        metadata_text = "\n".join(
            f"- {k}: {v}" for k, v in context.metadata.items()
        )

        return f"""Analyze the following data cleaning decision and recommend the best option:

Question: {context.question}

Context:
{metadata_text}

Available Options:
{options_text}

Based on medical data best practices, which option would you recommend?
Respond with just the option ID (e.g., "impute_median").
"""

    def _parse_recommendation(self, response: str, context: DecisionContext) -> str:
        """Parse LLM response to extract recommended option ID."""
        # Simple parsing - look for option IDs in response
        response_lower = response.lower()
        for option in context.options:
            option_id = option.get("id", "").lower()
            if option_id in response_lower:
                return option.get("id", "")

        # Fall back to default
        return context.default_option or context.options[0].get("id", "")

    def _confirm_llm_choice(
        self,
        context: DecisionContext,
        recommended_option: Dict[str, Any],
        llm_reasoning: str
    ) -> Dict[str, Any]:
        """Show LLM recommendation and ask for confirmation."""
        self.console.print(
            Panel(
                f"[bold]LLM Recommendation:[/]\n{llm_reasoning}",
                border_style="cyan",
            )
        )

        confirmed = Confirm.ask(
            f"Accept recommendation: {recommended_option.get('label')}?",
            default=True
        )

        if confirmed:
            return recommended_option
        else:
            # Fall back to interactive
            interactive = InteractiveStrategy(console=self.console)
            return interactive.decide(context)

    def _get_default_option(self, context: DecisionContext) -> Dict[str, Any]:
        """Get default option."""
        if context.default_option:
            for option in context.options:
                if option.get("id") == context.default_option:
                    return option
        return context.options[0] if context.options else {}
