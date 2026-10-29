# The eval's own maths, checked on made-up numbers (the eval itself needs Ollama, so it
# isn't run here).

import pytest

from eval.run import rank_of_first_hit, retrieval_metrics, suggest_threshold, threshold_sweep


def test_rank_of_first_hit():
    chunks = [{"filename": "a.pdf", "page_number": 3}, {"filename": "a.pdf", "page_number": 7}]

    assert rank_of_first_hit(chunks, {"a.pdf": [7]}) == 2
    assert rank_of_first_hit(chunks, {"b.pdf": [3]}) is None  # right page number, wrong file


def test_retrieval_metrics():
    # First place, second place, missing.
    metrics = retrieval_metrics([1, 2, None], k=5)

    assert metrics["hit@1"] == pytest.approx(1 / 3)
    assert metrics["hit@5"] == pytest.approx(2 / 3)
    assert metrics["MRR"] == pytest.approx((1 + 1 / 2 + 0) / 3)


def test_sweep_and_suggestion():
    on_topic = [0.62, 0.70, 0.75]
    off_topic = [0.50, 0.58]

    sweep = {row["threshold"]: row for row in threshold_sweep(on_topic, off_topic)}

    assert sweep[0.6]["on_topic_kept"] == 1 and sweep[0.6]["off_topic_refused"] == 1
    assert sweep[0.625]["on_topic_kept"] == pytest.approx(2 / 3)  # 0.62 is now cut off
    assert suggest_threshold(list(sweep.values())) == 0.6  # highest that keeps all on-topic
