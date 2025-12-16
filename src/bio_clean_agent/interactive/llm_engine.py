"""LLM engine for intelligent conversation and tool calling.

Supports:
- DeepSeek API
- OpenAI API
- Custom LLM providers
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv()
class LLMProvider(str, Enum):
    """Supported LLM providers."""
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider
    api_key: str
    model: str
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000


@dataclass
class Message:
    """Chat message."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None


class LLMEngine:
    """
    LLM Engine for intelligent conversation.

    Handles:
    - Multiple LLM providers
    - Function/tool calling
    - Conversation history
    - Error handling and retries
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize LLM client based on provider."""
        if self.config.provider == LLMProvider.DEEPSEEK:
            self._initialize_deepseek()
        elif self.config.provider == LLMProvider.OPENAI:
            self._initialize_openai()
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _initialize_deepseek(self) -> None:
        """Initialize DeepSeek client."""
        try:
            from openai import OpenAI

            # DeepSeek API is compatible with OpenAI SDK
            self.client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url or "https://api.deepseek.com"
            )
        except ImportError:
            raise ImportError(
                "OpenAI SDK required for DeepSeek. Install with: pip install openai"
            )

    def _initialize_openai(self) -> None:
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
        except ImportError:
            raise ImportError(
                "OpenAI SDK required. Install with: pip install openai"
            )

    def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto"
    ) -> Dict[str, Any]:
        """
        Send chat request to LLM.

        Args:
            messages: Conversation history
            tools: Available tools/functions
            tool_choice: "auto", "none", or specific tool

        Returns:
            Response with content and/or tool calls
        """
        try:
            # Convert messages to API format
            api_messages = [
                self._message_to_dict(msg) for msg in messages
            ]

            # Build request
            request_params = {
                "model": self.config.model,
                "messages": api_messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }

            # Add tools if provided
            if tools:
                request_params["tools"] = tools
                request_params["tool_choice"] = tool_choice

            # Call LLM
            response = self.client.chat.completions.create(**request_params)

            # Parse response
            message = response.choices[0].message

            result = {
                "content": message.content,
                "tool_calls": None,
                "finish_reason": response.choices[0].finish_reason
            }

            # Extract tool calls if present
            if hasattr(message, "tool_calls") and message.tool_calls:
                result["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]

            return result

        except Exception as e:
            return {
                "error": str(e),
                "content": None,
                "tool_calls": None
            }

    def _message_to_dict(self, msg: Message) -> Dict[str, Any]:
        """Convert Message to API dict format."""
        msg_dict = {
            "role": msg.role,
            "content": msg.content
        }

        if msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls

        if msg.tool_call_id:
            msg_dict["tool_call_id"] = msg.tool_call_id

        if msg.name:
            msg_dict["name"] = msg.name

        return msg_dict

    @staticmethod
    def from_env(provider: str = "deepseek") -> "LLMEngine":
        """
        Create LLM engine from environment variables.

        Environment variables:
            DEEPSEEK_API_KEY - DeepSeek API key
            OPENAI_API_KEY - OpenAI API key
            LLM_MODEL - Model name (optional)
            LLM_BASE_URL - Base URL (optional)
        """
        provider_enum = LLMProvider(provider.lower())

        # Get API key
        if provider_enum == LLMProvider.DEEPSEEK:
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                raise ValueError(
                    "DEEPSEEK_API_KEY environment variable not set. "
                    "Get your key at: https://platform.deepseek.com"
                )
            default_model = "deepseek-chat"
            default_base_url = "https://api.deepseek.com"

        elif provider_enum == LLMProvider.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set")
            default_model = "gpt-4"
            default_base_url = None

        else:
            raise ValueError(f"Unsupported provider: {provider}")

        # Get model and base URL
        model = os.getenv("LLM_MODEL", default_model)
        base_url = os.getenv("LLM_BASE_URL", default_base_url)

        config = LLMConfig(
            provider=provider_enum,
            api_key=api_key,
            model=model,
            base_url=base_url
        )

        return LLMEngine(config)


class ConversationManager:
    """
    Manages conversation with LLM including tool calling.

    Implements the full tool calling loop:
    1. User input → LLM
    2. LLM decides which tools to call
    3. Execute tools
    4. Send results back to LLM
    5. LLM generates final response
    """

    def __init__(self, llm_engine: LLMEngine, tools_schema: List[Dict]):
        self.llm = llm_engine
        self.tools_schema = tools_schema
        self.messages: List[Message] = []
        self._add_system_message()

    def _add_system_message(self) -> None:
        """Add system prompt."""
        system_prompt = """You are a professional data cleaning assistant for medical and clinical trial data.

Your capabilities:
- Load and inspect datasets
- Assess data quality using ISO 8000 standards
- Detect data quality issues with scientific evidence
- Clean data (remove duplicates, handle missing values)
- Validate values against medical reference ranges
- Export cleaned data and audit trails

Guidelines:
1. Always provide clear explanations
2. Reference scientific evidence when available
3. Suggest appropriate cleaning strategies based on data characteristics
4. Warn about potential data loss or bias
5. Follow medical data handling best practices

When a user asks you to perform a task:
1. Determine which tools to call
2. Call the necessary tools in the correct order
3. Interpret the results
4. Provide a clear summary to the user

Available tools:
- load_data: Load dataset from file
- show_data: Display data preview
- describe_data: Statistical summary
- show_columns: Column information
- show_missing: Missing value analysis
- assess_quality: Comprehensive quality assessment
- detect_issues: Detect quality issues with evidence
- remove_duplicates: Remove duplicate records
- handle_missing: Handle missing values (evidence-based)
- validate_ranges: Validate against medical ranges
- save_data: Save cleaned data
- export_audit: Export audit trail
- export_lineage: Export data lineage
- show_stats: Session statistics

Be helpful, professional, and thorough in your responses."""

        self.messages.append(Message(
            role="system",
            content=system_prompt
        ))

    def process_user_input(
        self,
        user_input: str,
        tool_executor: Any,
        max_iterations: int = 5
    ) -> str:
        """
        Process user input with tool calling loop.

        Args:
            user_input: User's message
            tool_executor: Object with execute_tool(name, **params) method
            max_iterations: Max tool calling iterations

        Returns:
            Final assistant response
        """
        # Add user message
        self.messages.append(Message(
            role="user",
            content=user_input
        ))

        iteration = 0
        while iteration < max_iterations:
            iteration += 1

            # Call LLM
            response = self.llm.chat(
                messages=self.messages,
                tools=self.tools_schema,
                tool_choice="auto"
            )

            # Check for errors
            if "error" in response:
                error_msg = f"LLM Error: {response['error']}"
                self.messages.append(Message(
                    role="assistant",
                    content=error_msg
                ))
                return error_msg

            # If no tool calls, we're done
            if not response.get("tool_calls"):
                final_content = response.get("content", "")
                self.messages.append(Message(
                    role="assistant",
                    content=final_content
                ))
                return final_content

            # Execute tool calls
            tool_calls = response["tool_calls"]

            # Add assistant message with tool calls
            self.messages.append(Message(
                role="assistant",
                content=response.get("content") or "",
                tool_calls=tool_calls
            ))

            # Execute each tool
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]

                try:
                    # Parse arguments
                    args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError:
                    args = {}

                # Execute tool
                result = tool_executor.execute_tool(tool_name, **args)

                # Add tool result message
                self.messages.append(Message(
                    role="tool",
                    content=json.dumps(result, ensure_ascii=False),
                    tool_call_id=tool_call["id"],
                    name=tool_name
                ))

            # Continue loop to let LLM process tool results

        # Max iterations reached
        final_msg = "I've completed the requested operations. You can ask for more details or request additional actions."
        self.messages.append(Message(
            role="assistant",
            content=final_msg
        ))
        return final_msg

    def get_conversation_history(self) -> List[Message]:
        """Get conversation history."""
        return self.messages.copy()

    def clear_history(self, keep_system: bool = True) -> None:
        """Clear conversation history."""
        if keep_system:
            # Keep only system message
            self.messages = [self.messages[0]]
        else:
            self.messages = []
            self._add_system_message()
