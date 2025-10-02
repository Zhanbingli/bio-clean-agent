from __future__ import annotations

import json
import os
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional, Protocol, Tuple

from .utils.logging import get_logger


class LLMProviderError(RuntimeError):
    """Raised when an LLM backend cannot be constructed."""


@dataclass
class ModelDescriptor:
    key: str
    provider: str
    name: str
    description: str
    tags: Tuple[str, ...] = ()
    default_options: Dict[str, Any] = field(default_factory=dict)
    recommended: bool = False


@dataclass
class ModelConfig:
    choice: Optional[str] = None
    options: Dict[str, Any] = field(default_factory=dict)
    api_key: Optional[str] = None


@dataclass
class GenerationConfig:
    temperature: float = 0.1
    top_p: float = 0.9
    max_new_tokens: int = 768
    extra_options: Dict[str, Any] = field(default_factory=dict)

    def kwargs(self) -> Dict[str, Any]:
        payload = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_new_tokens": self.max_new_tokens,
        }
        payload.update(self.extra_options)
        return payload


class LLMRegistry:
    """Keeps track of chat-model providers and descriptors."""

    def __init__(self) -> None:
        self._builders: Dict[str, Callable[[ModelConfig], LLMInterface]] = {}
        self._descriptors: Dict[str, ModelDescriptor] = {}
        self._default_key: Optional[str] = None

    def register(self, descriptor: ModelDescriptor, builder: Callable[[ModelConfig], LLMInterface]) -> None:
        key = descriptor.key
        if key in self._builders:
            raise ValueError(f"Model key already registered: {key}")
        self._builders[key] = builder
        self._descriptors[key] = descriptor
        if descriptor.recommended or self._default_key is None:
            self._default_key = key

    def available_models(self) -> List[ModelDescriptor]:
        return list(self._descriptors.values())

    def describe(self, key: Optional[str] = None) -> ModelDescriptor:
        target = key or self._default_key
        if not target or target not in self._descriptors:
            raise LLMProviderError("No models registered in registry")
        return self._descriptors[target]

    def create(self, config: ModelConfig) -> Tuple[LLMInterface, ModelDescriptor]:
        key = config.choice
        if not key or key == "auto":
            key = self._resolve_auto_choice(config)
        if key not in self._builders:
            available = ", ".join(sorted(self._descriptors)) or "none"
            raise LLMProviderError(f"Unknown model choice '{key}'. Available: {available}")
        descriptor = self._descriptors[key]
        merged_options = {**descriptor.default_options, **config.options}
        instance = self._builders[key](
            ModelConfig(choice=key, options=merged_options, api_key=config.api_key)
        )
        return instance, descriptor

    def _resolve_auto_choice(self, config: ModelConfig) -> str:
        if config.api_key or os.getenv("OPENAI_API_KEY"):
            for descriptor in self._descriptors.values():
                if descriptor.provider == "openai":
                    return descriptor.key
        if self._default_key:
            return self._default_key
        raise LLMProviderError("Unable to auto-select model; registry has no defaults")


def build_default_registry() -> LLMRegistry:
    """Build registry with simulated (default) and optional OpenAI providers."""
    registry = LLMRegistry()

    # Simulated provider - always available for testing
    registry.register(
        ModelDescriptor(
            key="simulated",
            provider="simulated",
            name="Simulated Planner",
            description="Returns static plans for testing and demos.",
            tags=("offline", "fast"),
            recommended=True,
        ),
        lambda cfg: SimulatedLLM(cfg.options.get("canned_response")),
    )

    # OpenAI provider - only if credentials available
    def openai_builder(cfg: ModelConfig) -> LLMInterface:
        api_key = cfg.api_key or cfg.options.get("api_key") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMProviderError("OpenAI backend requires an API key (set OPENAI_API_KEY env var)")
        model_name = cfg.options.get("model") or cfg.options.get("model_name") or "gpt-4o-mini"
        return OpenAIChatLLM(
            model=model_name,
            api_key=api_key,
            organization=cfg.options.get("organization"),
            request_timeout=cfg.options.get("request_timeout", 60),
            extra_options={k: v for k, v in cfg.options.items() if k not in {"model", "model_name", "api_key", "organization"}},
        )

    registry.register(
        ModelDescriptor(
            key="openai",
            provider="openai",
            name="OpenAI GPT",
            description="Cloud-based GPT models via OpenAI API.",
            tags=("cloud", "high-quality"),
        ),
        openai_builder,
    )

    return registry


class LLMInterface(Protocol):
    """Minimal interface for chat-oriented large language models."""

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        ...


class SimulatedLLM:
    """Lightweight fake LLM for testing and offline development."""

    def __init__(self, canned_response: Optional[str] = None):
        self.canned_response = canned_response or json.dumps(
            {
                "dataset_type": "sequencing",
                "dataset_id": "demo",
                "reasoning": "Default simulated plan.",
                "parameters": {"quality_threshold": 20},
                "actions": [
                    {"step": "fastqc", "description": "Run FastQC"},
                    {"step": "trim", "description": "Run Cutadapt"},
                ],
            }
        )

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:  # noqa: D401
        return self.canned_response


class OpenAIChatLLM:
    """Wrapper around OpenAI Chat Completions API."""

    def __init__(
        self,
        model: str,
        api_key: str,
        organization: Optional[str] = None,
        request_timeout: int = 60,
        extra_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._logger = get_logger(__name__)
        self.model = model
        self._request_timeout = request_timeout
        self.extra_options = extra_options or {}
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            try:
                import openai  # type: ignore
            except ImportError as exc:  # pragma: no cover - dependency guard
                raise LLMProviderError(
                    "openai package is required for the OpenAI backend. Install with `pip install openai`."
                ) from exc
            self._use_legacy_client = True
            self._client = openai
            self._client.api_key = api_key
            if organization:
                self._client.organization = organization
        else:
            self._use_legacy_client = False
            self._client = OpenAI(api_key=api_key, organization=organization)

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        params = {**self.extra_options, **kwargs}
        temperature = params.get("temperature", 0.1)
        top_p = params.get("top_p", 0.9)
        max_new_tokens = params.get("max_new_tokens")
        if self._use_legacy_client:
            response = self._client.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_new_tokens,
                request_timeout=self._request_timeout,
            )
            content = response["choices"][0]["message"]["content"]
        else:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_new_tokens,
                timeout=self._request_timeout,
            )
            content = response.choices[0].message.content or ""
        self._logger.debug("OpenAI response snippet: %s", (content or "")[:200])
        return content or ""


@dataclass
class PlannerDiagnostics:
    raw_response: str = ""
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PlannerOutput:
    dataset_type: str = "sequencing"
    dataset_id: Optional[str] = None
    reasoning: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    diagnostics: PlannerDiagnostics = field(default_factory=PlannerDiagnostics)


DEFAULT_SYSTEM_PROMPT = """
You are an expert bioinformatics data-cleaning planner. You receive user goals about sequencing, transcriptomics, or metabolomics datasets. Reply with a compact JSON object containing:
- "dataset_type": one of "sequencing", "transcriptomics", "metabolomics";
- "dataset_id": short identifier if provided or null otherwise;
- "reasoning": concise reasoning (<80 words);
- "parameters": dictionary of key/value parameters relevant for cleaning;
- "actions": ordered list of steps with "step" and "description" fields.
Do not include any additional prose outside the JSON.
""".strip()

DEFAULT_FORMAT_INSTRUCTIONS = (
    "Return valid JSON with keys: dataset_type, dataset_id, reasoning, parameters, actions."
    " Each action must be an object containing step and description."
)


@dataclass
class PlannerConfig:
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    format_instructions: str = DEFAULT_FORMAT_INSTRUCTIONS
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    max_history_turns: int = 3
    auto_repair: bool = True
    enforce_json: bool = True
    repair_prompt: str = (
        "Your previous reply was not valid JSON. Rewrite it strictly as JSON following the schema"
        " for dataset_type, dataset_id, reasoning, parameters, and actions."
    )


class LLMPlanner:
    """LLM-backed planner that turns natural language into structured agent intents."""

    def __init__(
        self,
        llm: LLMInterface,
        config: Optional[PlannerConfig] = None,
        descriptor: Optional[ModelDescriptor] = None,
    ) -> None:
        self._logger = get_logger(__name__)
        self.llm = llm
        self.config = config or PlannerConfig()
        history_slots = self.config.max_history_turns * 2
        self._history: Deque[Dict[str, str]] = deque(maxlen=history_slots or None)
        self._descriptor = descriptor

    @property
    def descriptor(self) -> Optional[ModelDescriptor]:
        return self._descriptor

    def update_descriptor(self, descriptor: Optional[ModelDescriptor]) -> None:
        self._descriptor = descriptor

    def plan(
        self,
        user_request: str,
        context_hint: Optional[str] = None,
        extra_instructions: Optional[str] = None,
        generation_overrides: Optional[Dict[str, Any]] = None,
    ) -> PlannerOutput:
        user_message = self._compose_user_message(user_request, context_hint, extra_instructions)
        messages = self._build_messages(user_message)
        generation_kwargs = self.config.generation.kwargs()
        if generation_overrides:
            generation_kwargs.update(generation_overrides)
        raw_response = self.llm.generate(messages, **generation_kwargs)
        try:
            output, warnings = self._parse_payload(raw_response)
        except ValueError as exc:
            if not self.config.auto_repair:
                self._logger.error("Planner parsing failed: %s", exc)
                raise ValueError("Failed to parse planner response") from exc
            repair_messages = self._build_repair_messages(raw_response)
            repair_raw = self.llm.generate(repair_messages, **generation_kwargs)
            try:
                output, warnings = self._parse_payload(repair_raw)
                raw_response = repair_raw
                warnings.append("Planner output repaired after invalid JSON")
            except ValueError as repair_exc:
                self._logger.error("Planner repair attempt failed: %s", repair_exc)
                raise ValueError("Failed to parse planner response") from repair_exc
        output.diagnostics.raw_response = raw_response
        if self._descriptor:
            output.diagnostics.metadata.setdefault("model", {})
            output.diagnostics.metadata["model"].update(
                {
                    "key": self._descriptor.key,
                    "provider": self._descriptor.provider,
                    "name": self._descriptor.name,
                }
            )
        if warnings:
            output.diagnostics.warnings.extend(warnings)
        self._record_turn(user_message, raw_response)
        return output

    def _build_messages(self, latest_user: str) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": self.config.system_prompt}]
        if self.config.format_instructions:
            messages.append({"role": "system", "content": self.config.format_instructions})
        messages.extend(list(self._history))
        messages.append({"role": "user", "content": latest_user})
        return messages

    def _compose_user_message(
        self,
        request: str,
        context_hint: Optional[str],
        extra_instructions: Optional[str],
    ) -> str:
        parts = [f"User request: {request}"]
        if context_hint:
            parts.append(f"Context: {context_hint}")
        if extra_instructions:
            parts.append(f"Additional instructions: {extra_instructions}")
        return "\n".join(parts)

    def _parse_payload(self, payload: str) -> Tuple[PlannerOutput, List[str]]:
        content = self._extract_json(payload) if self.config.enforce_json else payload
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Planner response was not valid JSON: {exc}") from exc
        warnings: List[str] = []
        dataset_type = str(parsed.get("dataset_type") or "sequencing")
        dataset_id = parsed.get("dataset_id")
        if dataset_id is not None:
            dataset_id = str(dataset_id)
        parameters = parsed.get("parameters") or {}
        if not isinstance(parameters, dict):
            warnings.append("Planner parameters field was not a dict; reset to empty dict")
            parameters = {}
        actions_raw = parsed.get("actions") or []
        actions: List[Dict[str, Any]]
        if isinstance(actions_raw, list):
            actions = []
            for item in actions_raw:
                if isinstance(item, dict):
                    step = {"step": item.get("step"), "description": item.get("description", "")}
                    actions.append(step)
                else:
                    warnings.append("Planner action entry was not an object and was skipped")
        else:
            warnings.append("Planner actions field was not a list; defaulted to empty list")
            actions = []
        reasoning = str(parsed.get("reasoning", ""))
        output = PlannerOutput(
            dataset_type=dataset_type,
            dataset_id=dataset_id,
            reasoning=reasoning,
            parameters=parameters,
            actions=actions,
        )
        output.diagnostics.metadata["parsed"] = parsed
        return output, warnings

    def _record_turn(self, user_message: str, assistant_message: str) -> None:
        if self._history.maxlen is None or self._history.maxlen > 0:
            self._history.append({"role": "user", "content": user_message})
            self._history.append({"role": "assistant", "content": assistant_message})

    def _extract_json(self, payload: str) -> str:
        start = payload.find("{")
        end = payload.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("LLM response did not contain JSON object")
        return payload[start : end + 1]

    def _build_repair_messages(self, invalid_response: str) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = [{"role": "system", "content": self.config.system_prompt}]
        if self.config.format_instructions:
            messages.append({"role": "system", "content": self.config.format_instructions})
        messages.extend(list(self._history))
        messages.append({"role": "assistant", "content": invalid_response})
        messages.append({"role": "user", "content": self.config.repair_prompt})
        return messages


DEFAULT_LLM_REGISTRY = build_default_registry()


__all__ = [
    "GenerationConfig",
    "LLMInterface",
    "LLMPlanner",
    "LLMProviderError",
    "LLMRegistry",
    "ModelConfig",
    "ModelDescriptor",
    "OpenAIChatLLM",
    "PlannerConfig",
    "PlannerDiagnostics",
    "PlannerOutput",
    "SimulatedLLM",
    "build_default_registry",
    "DEFAULT_LLM_REGISTRY",
]
