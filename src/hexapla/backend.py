"""Model backend — thin OpenRouter client with cost tracking.

Backend-agnostic: the loop never touches the API directly.
All it sees is `chat(messages) -> (text, usage)`.

Pricing is per-model, loaded from a simple table. Update PRICING
when you add models or OpenRouter changes rates.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI

from .config import Config

logger = logging.getLogger(__name__)

# --- Pricing table (USD per 1M tokens) ---------------------------------------
# Source: OpenRouter pricing pages. Update as needed.
# Format: "model-slug": (input_per_1m, output_per_1m)
PRICING: dict[str, tuple[float, float]] = {
    "z-ai/glm-5.2": (0.50, 2.00),
    "anthropic/claude-sonnet-4": (3.00, 15.00),
    "anthropic/claude-sonnet-4.5": (3.00, 15.00),
    "anthropic/claude-opus-4.8": (5.00, 25.00),
    "openai/gpt-4o": (2.50, 10.00),
    "openai/gpt-4o-mini": (0.15, 0.60),
    "google/gemini-2.5-flash": (0.15, 0.60),
    "google/gemini-2.5-pro": (1.25, 5.00),
}


def get_pricing(model: str) -> tuple[float, float]:
    """Return (input_per_1m, output_per_1m) for a model, or (0, 0) if unknown."""
    if model in PRICING:
        return PRICING[model]
    # Try prefix match (e.g. "z-ai/glm-5.2-32b" → "z-ai/glm-5.2")
    for key in PRICING:
        if model.startswith(key):
            return PRICING[key]
    logger.warning("No pricing data for %s — cost tracking will show $0", model)
    return (0.0, 0.0)


@dataclass
class Usage:
    """Cumulative token + cost tracking for a single model backend."""

    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    api_calls: int = 0

    def add(self, usage_dict: dict[str, int]) -> None:
        pt = usage_dict.get("prompt_tokens", 0)
        ct = usage_dict.get("completion_tokens", 0)
        self.prompt_tokens += pt
        self.completion_tokens += ct
        self.total_tokens += pt + ct
        self.api_calls += 1

        in_rate, out_rate = get_pricing(self.model)
        self.cost_usd += (pt / 1_000_000 * in_rate) + (ct / 1_000_000 * out_rate)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "api_calls": self.api_calls,
        }


@dataclass
class ChatResult:
    """What the loop sees from a single model call."""

    text: str
    usage: Usage


class Backend:
    """Thin wrapper around OpenRouter (OpenAI-compatible API).

    Keeps a running Usage per backend instance.
    The loop creates one Backend for the actor and one for the verifier
    so costs are tracked separately.
    """

    def __init__(self, model: str, config: Config) -> None:
        self.model = model
        self.config = config
        self.usage = Usage(model=model)
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            default_headers={
                "HTTP-Referer": config.site_header,
                "X-Title": config.app_name,
            },
        )

    def chat(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> ChatResult:
        """Send messages, return (text, usage_delta). Raises on API error."""
        # Always set max_tokens — prevents OpenRouter pre-allocating
        # 65k tokens per request and burning through credits.
        if max_tokens is None:
            max_tokens = self.config.max_tokens

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp = self._client.chat.completions.create(**kwargs)

        text = resp.choices[0].message.content or ""
        if resp.usage:
            self.usage.add(
                {
                    "prompt_tokens": resp.usage.prompt_tokens,
                    "completion_tokens": resp.usage.completion_tokens,
                }
            )
        return ChatResult(text=text, usage=self.usage)

    @property
    def cost_usd(self) -> float:
        return self.usage.cost_usd
