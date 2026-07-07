"""Configuration — loaded from environment / .env file."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class Config:
    # API
    api_key: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY", ""))
    base_url: str = field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        )
    )
    site_header: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_SITE", "https://github.com/cclawton/react-harness")
    )
    app_name: str = field(
        default_factory=lambda: os.getenv("OPENROUTER_APP_NAME", "react-harness")
    )

    # Models
    actor_model: str = field(default_factory=lambda: os.getenv("ACTOR_MODEL", "z-ai/glm-5.2"))
    verifier_model: str = field(
        default_factory=lambda: os.getenv("VERIFIER_MODEL", "z-ai/glm-5.2")
    )

    # Bounded termination
    max_turns: int = field(default_factory=lambda: int(os.getenv("MAX_TURNS", "30")))
    max_cost_usd: float = field(
        default_factory=lambda: float(os.getenv("MAX_COST_USD", "2.00"))
    )
    max_wall_clock_seconds: int = field(
        default_factory=lambda: int(os.getenv("MAX_WALL_CLOCK_SECONDS", "3600"))
    )

    # Max output tokens per API call — prevents OpenRouter pre-allocating
    # huge token budgets that eat into credit balance.
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096")))

    # Working directory for tool execution
    workdir: Path = field(default_factory=lambda: Path.cwd())

    # Run output
    runs_dir: Path = field(default_factory=lambda: PROJECT_ROOT / "runs")
