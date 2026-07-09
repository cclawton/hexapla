import json
from pathlib import Path

from hexapla.config import Config
from hexapla.sut_contract import EchoSUT, OpenRouterSUT, load_sut_contract


CONFIG_DIR = Path("configs")


def test_echo_config_example_loads_without_network():
    contract = json.loads((CONFIG_DIR / "echo.example.json").read_text(encoding="utf-8"))

    suts = load_sut_contract(contract, Config(api_key=""))

    assert len(suts) == 1
    assert isinstance(suts[0], EchoSUT)
    assert suts[0].name == "echo-baseline"


def test_openrouter_config_example_contains_no_secrets_and_loads_candidate():
    text = (CONFIG_DIR / "openrouter.example.json").read_text(encoding="utf-8")
    contract = json.loads(text)

    assert "OPENROUTER_API_KEY" not in text
    assert "sk-" not in text
    suts = load_sut_contract(contract, Config(api_key="test-key"))

    assert len(suts) == 1
    assert isinstance(suts[0], OpenRouterSUT)
    assert suts[0].name == "cheap-openrouter-smoke"
    assert suts[0].metadata["model"]
