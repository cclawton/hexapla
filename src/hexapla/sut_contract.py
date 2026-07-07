"""System-under-test contracts for Hexapla benchmark runs.

A benchmark candidate can be a frontier model, a local model, or a composed
architecture hidden behind the same tiny interface: call(prompt) -> SUTResult.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Protocol

from .backend import Backend
from .config import Config


@dataclass(frozen=True)
class SUTResult:
    """Result returned by a system under test."""

    response: str
    latency_ms: float
    cost_usd: float
    trace_id: str
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "trace_id": self.trace_id,
            "raw": self.raw,
        }


class SystemUnderTest(Protocol):
    """Protocol every benchmark candidate must satisfy."""

    @property
    def name(self) -> str: ...

    @property
    def metadata(self) -> dict[str, Any]: ...

    def call(self, prompt: str, **kwargs: Any) -> SUTResult: ...


class EchoSUT:
    """Deterministic no-network SUT for smoke tests."""

    def __init__(self, name: str = "echo", prefix: str = "") -> None:
        self._name = name
        self.prefix = prefix

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> dict[str, Any]:
        return {"backend": "echo", "prefix": self.prefix}

    def call(self, prompt: str, **kwargs: Any) -> SUTResult:
        started = time.perf_counter()
        response = f"{self.prefix}{prompt}"
        return SUTResult(
            response=response,
            latency_ms=(time.perf_counter() - started) * 1000,
            cost_usd=0.0,
            trace_id=f"echo-{uuid.uuid4().hex[:12]}",
            raw={"kwargs": kwargs},
        )


class OpenRouterSUT:
    """OpenRouter-backed model candidate."""

    def __init__(self, name: str, model: str, config: Config) -> None:
        self._name = name
        self.model = model
        self.backend = Backend(model=model, config=config)

    @property
    def name(self) -> str:
        return self._name

    @property
    def metadata(self) -> dict[str, Any]:
        return {"backend": "openrouter", "model": self.model}

    def call(self, prompt: str, **kwargs: Any) -> SUTResult:
        started = time.perf_counter()
        cost_before = self.backend.cost_usd
        messages = [{"role": "user", "content": prompt}]
        result = self.backend.chat(
            messages,
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens"),
        )
        latency_ms = (time.perf_counter() - started) * 1000
        cost_delta = self.backend.cost_usd - cost_before
        return SUTResult(
            response=result.text,
            latency_ms=latency_ms,
            cost_usd=cost_delta,
            trace_id=f"openrouter-{uuid.uuid4().hex[:12]}",
            raw={"usage": result.usage.to_dict(), "model": self.model},
        )


def load_sut_contract(contract: dict[str, Any], config: Config) -> list[SystemUnderTest]:
    """Build SUT instances from a contract dictionary.

    Expected shape:
        {"candidates": [{"name": "glm", "type": "openrouter", "model": "..."}]}
    """

    candidates = contract.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("SUT contract must contain a non-empty 'candidates' list")

    suts: list[SystemUnderTest] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("Each candidate must be an object")
        candidate_type = candidate.get("type", "openrouter")
        name = candidate.get("name") or candidate.get("model")
        if not name:
            raise ValueError("Each candidate must define 'name' or 'model'")

        if candidate_type == "echo":
            suts.append(EchoSUT(name=name, prefix=candidate.get("prefix", "")))
        elif candidate_type == "openrouter":
            model = candidate.get("model")
            if not model:
                raise ValueError("OpenRouter candidates must define 'model'")
            suts.append(OpenRouterSUT(name=name, model=model, config=config))
        else:
            raise ValueError(f"Unsupported SUT type: {candidate_type}")

    return suts
