from hexapla.config import Config
from hexapla.sut_contract import (
    EchoSUT,
    OpenRouterSUT,
    SUTResult,
    load_sut_contract,
)


def test_sut_result_serializes_to_dict():
    result = SUTResult(
        response="answer",
        latency_ms=12.5,
        cost_usd=0.001,
        trace_id="trace-1",
        raw={"x": 1},
    )

    assert result.to_dict() == {
        "response": "answer",
        "latency_ms": 12.5,
        "cost_usd": 0.001,
        "trace_id": "trace-1",
        "raw": {"x": 1},
    }


def test_echo_sut_implements_contract_without_network():
    sut = EchoSUT(name="echo", prefix="PFX: ")

    result = sut.call("hello")

    assert sut.name == "echo"
    assert sut.metadata["backend"] == "echo"
    assert result.response == "PFX: hello"
    assert result.latency_ms >= 0
    assert result.cost_usd == 0.0
    assert result.trace_id.startswith("echo-")


def test_load_sut_contract_supports_echo_and_openrouter_candidates():
    contract = {
        "candidates": [
            {"name": "local-smoke", "type": "echo", "prefix": "A: "},
            {"name": "glm", "type": "openrouter", "model": "z-ai/glm-5.2"},
        ]
    }

    suts = load_sut_contract(contract, Config(api_key="test-key"))

    assert [sut.name for sut in suts] == ["local-smoke", "glm"]
    assert isinstance(suts[0], EchoSUT)
    assert isinstance(suts[1], OpenRouterSUT)
    assert suts[1].metadata["model"] == "z-ai/glm-5.2"


def test_load_sut_contract_rejects_missing_candidates():
    try:
        load_sut_contract({}, Config(api_key="test-key"))
    except ValueError as exc:
        assert "candidates" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_load_sut_contract_rejects_unknown_type():
    try:
        load_sut_contract({"candidates": [{"name": "bad", "type": "wat"}]}, Config(api_key="test-key"))
    except ValueError as exc:
        assert "Unsupported SUT type" in str(exc)
    else:
        raise AssertionError("expected ValueError")
