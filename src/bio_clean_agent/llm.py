from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from .utils.logging import get_logger


class LLMInterface(Protocol):
    """Minimal interface for chat-oriented large language models."""

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        ...


class QwenNotAvailableError(RuntimeError):
    """Raised when the Qwen backend cannot be initialised."""


@dataclass
class QwenConfig:
    model_path: str
    device: str = "auto"
    dtype: Optional[str] = None
    max_new_tokens: int = 1024
    temperature: float = 0.1
    top_p: float = 0.9
    use_flash_attention: bool = True
    load_in_8bit: bool = False


class QwenLLM:
    """Wrapper around Qwen3 chat models via `transformers`."""

    def __init__(self, config: QwenConfig):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise QwenNotAvailableError(
                "transformers is required to load Qwen models. Install with `pip install bio-clean-agent[llm]`."
            ) from exc

        self._logger = get_logger(__name__)
        self.config = config
        tokenizer_kwargs: Dict[str, Any] = {}
        model_kwargs: Dict[str, Any] = {"trust_remote_code": True}

        if config.load_in_8bit:
            model_kwargs["load_in_8bit"] = True
        if config.dtype:
            import torch  # type: ignore

            dtype_map = {
                "float16": "float16",
                "bfloat16": "bfloat16",
                "float32": "float32",
            }
            dtype_string = dtype_map.get(config.dtype, config.dtype)
            model_kwargs["torch_dtype"] = getattr(torch, dtype_string)
        if config.use_flash_attention:
            model_kwargs["attn_implementation"] = "flash_attention_2"

        self.tokenizer = AutoTokenizer.from_pretrained(config.model_path, **tokenizer_kwargs)
        self.model = AutoModelForCausalLM.from_pretrained(
            config.model_path,
            device_map=config.device,
            **model_kwargs,
        )
        self.model.eval()
        self._logger.debug("Loaded Qwen model from %s", config.model_path)

    def generate(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        from torch import no_grad

        generate_kwargs = {
            "max_new_tokens": kwargs.get("max_new_tokens", self.config.max_new_tokens),
            "temperature": kwargs.get("temperature", self.config.temperature),
            "top_p": kwargs.get("top_p", self.config.top_p),
            "do_sample": kwargs.get("do_sample", False),
        }
        input_ids = self.tokenizer.apply_chat_template(messages, return_tensors="pt").to(self.model.device)
        with no_grad():
            output_ids = self.model.generate(input_ids, **generate_kwargs)
        result = self.tokenizer.decode(output_ids[0][input_ids.shape[-1]:], skip_special_tokens=True)
        self._logger.debug("Qwen response: %s", result[:200])
        return result


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


@dataclass
class PlannerOutput:
    dataset_type: str
    dataset_id: Optional[str]
    reasoning: str
    parameters: Dict[str, Any]
    actions: List[Dict[str, Any]]


class QwenPlanner:
    """LLM-backed planner that turns natural language into structured agent intents."""

    SYSTEM_PROMPT = """
You are an expert bioinformatics data-cleaning planner. You receive user goals about sequencing, transcriptomics, or metabolomics datasets. Reply with a compact JSON object containing:
- "dataset_type": one of "sequencing", "transcriptomics", "metabolomics";
- "dataset_id": short identifier if provided or null otherwise;
- "reasoning": concise reasoning (<80 words);
- "parameters": dictionary of key/value parameters relevant for cleaning;
- "actions": ordered list of steps with "step" and "description" fields.
Do not include any additional prose outside the JSON.
""".strip()

    def __init__(self, llm: LLMInterface):
        self._logger = get_logger(__name__)
        self.llm = llm

    def plan(self, user_request: str, context_hint: Optional[str] = None) -> PlannerOutput:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_message(user_request, context_hint)},
        ]
        raw = self.llm.generate(messages)
        try:
            parsed = json.loads(self._extract_json(raw))
        except json.JSONDecodeError as exc:
            self._logger.error("Planner failed to parse JSON: %s", raw)
            raise ValueError("Failed to parse planner response") from exc
        return PlannerOutput(
            dataset_type=parsed.get("dataset_type", "sequencing"),
            dataset_id=parsed.get("dataset_id"),
            reasoning=parsed.get("reasoning", ""),
            parameters=parsed.get("parameters", {}),
            actions=parsed.get("actions", []),
        )

    def _build_user_message(self, request: str, context_hint: Optional[str]) -> str:
        if context_hint:
            return f"User request: {request}\nContext: {context_hint}"
        return f"User request: {request}"

    def _extract_json(self, payload: str) -> str:
        start = payload.find("{")
        end = payload.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("LLM response did not contain JSON")
        return payload[start : end + 1]
