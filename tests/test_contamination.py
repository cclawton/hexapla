from hexapla.contamination import (
    ContaminationResult,
    generate_perturbation,
    screen_contamination,
)
from hexapla.scoring import ScoreResult
from hexapla.sut_contract import SUTResult


class FakeSUT:
    name = "fake"
    metadata = {"backend": "fake"}

    def __init__(self):
        self.prompts = []

    def call(self, prompt, **kwargs):
        self.prompts.append(prompt)
        return SUTResult(response=f"response to {prompt}", latency_ms=1.0, cost_usd=0.0, trace_id="t")


def test_generate_perturbation_identity_returns_prompt():
    item = {"id": "q1", "prompt": "Name three bands."}

    assert generate_perturbation(item, "identity")["prompt"] == "Name three bands."


def test_generate_perturbation_order_shuffle_changes_order_for_sentences():
    item = {"id": "q1", "prompt": "First sentence. Second sentence. Third sentence."}

    perturbed = generate_perturbation(item, "order_shuffle")

    assert perturbed["id"] == "q1__order_shuffle"
    assert perturbed["prompt"] == "Third sentence. Second sentence. First sentence."


def test_screen_contamination_flags_high_score_variance():
    sut = FakeSUT()
    scores = iter([ScoreResult(1.0, "original"), ScoreResult(0.2, "perturbed")])

    def scorer(item, response):
        return next(scores)

    result = screen_contamination(
        item={"id": "q1", "prompt": "Question. Another."},
        sut=sut,
        scorer=scorer,
        operators=["identity", "order_shuffle"],
        threshold=0.2,
    )

    assert result == ContaminationResult(variance=0.8, flagged=True, scores=[1.0, 0.2])
    assert len(sut.prompts) == 2


def test_screen_contamination_handles_no_operators():
    sut = FakeSUT()
    result = screen_contamination(
        item={"id": "q1", "prompt": "Question"},
        sut=sut,
        scorer=lambda item, response: ScoreResult(0.5, "ok"),
        operators=[],
    )

    assert result.variance == 0.0
    assert result.flagged is False
    assert result.scores == []
