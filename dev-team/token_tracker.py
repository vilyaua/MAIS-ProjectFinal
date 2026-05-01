"""Lightweight token usage tracker for cost logging.

Tracks cumulative tokens and cost per pipeline run.
Uses LangChain callback to capture token counts from each LLM call.
"""

import logging
import threading
from dataclasses import dataclass, field

from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger("tokens")

# Pricing per 1M tokens (estimated, May 2026)
MODEL_PRICING = {
    "gpt-5.5": {"input": 3.00, "output": 12.00},
    "gpt-5.4": {"input": 2.50, "output": 10.00},
    "gpt-4.1": {"input": 2.00, "output": 8.00},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
}

# Fallback pricing for unknown models
DEFAULT_PRICING = {"input": 2.00, "output": 8.00}


def _get_pricing(model_name: str) -> dict:
    for key, pricing in MODEL_PRICING.items():
        if key in model_name:
            return pricing
    return DEFAULT_PRICING


@dataclass
class TokenUsage:
    """Accumulated token usage for a pipeline run."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    calls: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add(self, input_tokens: int, output_tokens: int, model: str = "") -> None:
        pricing = _get_pricing(model)
        cost = (
            input_tokens * pricing["input"] / 1_000_000
            + output_tokens * pricing["output"] / 1_000_000
        )
        with self._lock:
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.total_tokens += input_tokens + output_tokens
            self.total_cost += cost
            self.calls += 1

    def summary(self) -> str:
        return (
            f"tokens: {self.total_tokens:,} "
            f"(in: {self.input_tokens:,}, out: {self.output_tokens:,}) | "
            f"cost: ${self.total_cost:.4f} | calls: {self.calls}"
        )

    def snapshot(self) -> dict:
        """Return a snapshot of current values for delta calculation."""
        return {
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_cost": self.total_cost,
            "calls": self.calls,
        }

    def delta_summary(self, prev: dict) -> str:
        """Return a summary of the delta since a previous snapshot."""
        dt = self.total_tokens - prev["total_tokens"]
        di = self.input_tokens - prev["input_tokens"]
        do_ = self.output_tokens - prev["output_tokens"]
        dc = self.total_cost - prev["total_cost"]
        dn = self.calls - prev["calls"]
        return f"tokens: {dt:,} (in: {di:,}, out: {do_:,}) | cost: ${dc:.4f} | calls: {dn}"

    def reset(self) -> None:
        with self._lock:
            self.input_tokens = 0
            self.output_tokens = 0
            self.total_tokens = 0
            self.total_cost = 0.0
            self.calls = 0


class TokenTrackingHandler(BaseCallbackHandler):
    """LangChain callback handler that tracks token usage."""

    def __init__(self, usage: TokenUsage):
        self.usage = usage
        self._call_count = 0

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._call_count += 1
        model = serialized.get("kwargs", {}).get("model_name", "?")
        logger.info("LLM call #%d started (model=%s)", self._call_count, model)

    def on_llm_end(self, response, **kwargs):
        # Try llm_output first (aggregated usage)
        llm_output = response.llm_output or {}
        token_usage = llm_output.get("token_usage") or {}
        model = llm_output.get("model_name", "")

        input_tokens = token_usage.get("prompt_tokens", 0)
        output_tokens = token_usage.get("completion_tokens", 0)

        if input_tokens or output_tokens:
            self.usage.add(input_tokens, output_tokens, model)
            logger.info(
                "LLM call #%d done: in=%d out=%d model=%s | running total: %d",
                self._call_count,
                input_tokens,
                output_tokens,
                model,
                self.usage.total_tokens,
            )
            return

        # Fallback: check per-generation info
        for generations in response.generations:
            for gen in generations:
                info = gen.generation_info or {}
                tu = info.get("token_usage") or {}
                m = info.get("model_name", model)

                inp = tu.get("prompt_tokens", 0)
                out = tu.get("completion_tokens", 0)

                if inp or out:
                    self.usage.add(inp, out, m)
                    logger.info(
                        "LLM call #%d done (gen): in=%d out=%d model=%s | running total: %d",
                        self._call_count,
                        inp,
                        out,
                        m,
                        self.usage.total_tokens,
                    )
                    return

        # Nothing captured
        logger.warning(
            "LLM call #%d done: NO token data. llm_output keys=%s",
            self._call_count,
            list(llm_output.keys()),
        )

    def on_llm_error(self, error, **kwargs):
        logger.warning("LLM call #%d ERROR: %s", self._call_count, str(error)[:100])


# Global usage tracker — reset per pipeline run
pipeline_usage = TokenUsage()
