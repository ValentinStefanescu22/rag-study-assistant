# Eval: measures retrieval and answers on a fixed set of questions with known right pages.
#
#   cd backend && uv run python -m eval.run            retrieval + threshold sweep (~10 s)
#   cd backend && uv run python -m eval.run --answers  also full answers (a few minutes)
#
# Needs Ollama and your uploaded lectures, which is why it isn't part of pytest or CI:
# unit tests check our code with fakes; an eval checks how well the real system performs.

import argparse
import json
from pathlib import Path
from statistics import mean

from app import generate, retrieve

QUESTIONS = json.loads(Path(__file__).with_name("questions.json").read_text())
K = 5
THRESHOLDS = [round(0.50 + 0.025 * i, 3) for i in range(9)]  # 0.500 ... 0.700


def is_expected(chunk: dict, expect: dict) -> bool:
    return chunk["page_number"] in expect.get(chunk["filename"], [])


# Position (1 = first) of the first retrieved chunk on an expected page, or None if none is.
def rank_of_first_hit(chunks: list[dict], expect: dict) -> int | None:
    for rank, chunk in enumerate(chunks, start=1):
        if is_expected(chunk, expect):
            return rank
    return None


# hit@1: right page ranked first. hit@k: right page anywhere in the top k.
# MRR (mean reciprocal rank): 1 for first place, 1/2 for second, ... 0 if missing; averaged.
def retrieval_metrics(ranks: list[int | None], k: int = K) -> dict:
    return {
        "hit@1": mean(r == 1 for r in ranks),
        f"hit@{k}": mean(r is not None and r <= k for r in ranks),
        "MRR": mean(1 / r if r else 0 for r in ranks),
    }


# For each cut-off: share of on-topic questions that still reach the model (want 100%),
# and share of off-topic questions refused before the model (higher is better).
def threshold_sweep(on_topic_best: list[float], off_topic_best: list[float]) -> list[dict]:
    return [
        {
            "threshold": t,
            "on_topic_kept": mean(s >= t for s in on_topic_best),
            "off_topic_refused": mean(s < t for s in off_topic_best),
        }
        for t in THRESHOLDS
    ]


# Wrongly refusing a real question can't be undone later (the model never sees it), while
# an off-topic question that slips through still meets the model's NOT_FOUND rule.
# So: the highest cut-off that keeps every on-topic question.
def suggest_threshold(sweep: list[dict]) -> float:
    safe = [row["threshold"] for row in sweep if row["on_topic_kept"] == 1]
    return max(safe) if safe else min(row["threshold"] for row in sweep)


def pages(chunks: list[dict]) -> str:
    return ", ".join(f"{c['filename'][:2]} p{c['page_number']}" for c in chunks[:3])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", action="store_true", help="also run full answers (slow)")
    parser.add_argument("--threshold", type=float, help="try a different MIN_SIMILARITY for this run")
    args = parser.parse_args()
    if args.threshold is not None:
        generate.MIN_SIMILARITY = args.threshold  # answer() reads it at call time

    on_topic = [q for q in QUESTIONS if q["expect"]]
    off_topic = [q for q in QUESTIONS if not q["expect"]]
    print(f"{len(on_topic)} on-topic and {len(off_topic)} off-topic questions\n")

    results = {q["question"]: retrieve.search(q["question"], k=K) for q in QUESTIONS}
    best = {question: chunks[0]["similarity"] for question, chunks in results.items()}

    # 1. Retrieval: does the right page come back, and how high?
    ranks = [rank_of_first_hit(results[q["question"]], q["expect"]) for q in on_topic]
    print("RETRIEVAL (on-topic)")
    for name, value in retrieval_metrics(ranks).items():
        print(f"  {name:6} {value:.2f}")
    for q, rank in zip(on_topic, ranks):
        if rank != 1:
            where = f"rank {rank}" if rank else f"not in top {K}"
            print(f"  ✗ {q['question']}  ({where}; got {pages(results[q['question']])})")

    # 2. Threshold: which cut-off separates on-topic from off-topic best?
    sweep = threshold_sweep([best[q["question"]] for q in on_topic], [best[q["question"]] for q in off_topic])
    print("\nTHRESHOLD SWEEP (best chunk score vs cut-off)")
    print("  cut-off  on-topic kept  off-topic refused")
    for row in sweep:
        mark = "  <- current" if row["threshold"] == generate.MIN_SIMILARITY else ""
        print(f"  {row['threshold']:.3f}    {row['on_topic_kept']:>5.0%}          {row['off_topic_refused']:>5.0%}{mark}")
    print(f"  suggested: {suggest_threshold(sweep):.3f} (highest that keeps every on-topic question)")
    print("  lowest on-topic best score:", f"{min(best[q['question']] for q in on_topic):.3f}")
    print("  highest off-topic best score:", f"{max(best[q['question']] for q in off_topic):.3f}")

    if not args.answers:
        return

    # 3. Full answers: right refusals, and citations pointing at an expected page.
    print(f"\nANSWERS (MIN_SIMILARITY = {generate.MIN_SIMILARITY})")
    correct = 0
    for q in QUESTIONS:
        result = generate.answer(q["question"])
        if q["expect"]:
            cited_right = any(s["page_number"] in q["expect"].get(s["filename"], []) for s in result["sources"])
            ok = result["found"] and cited_right
            why = "refused" if not result["found"] else f"cited {[(s['filename'][:2], s['page_number']) for s in result['sources']]}"
        else:
            ok = not result["found"]
            why = "answered an off-topic question: " + result["answer"][:80]
        correct += ok
        if not ok:
            print(f"  ✗ {q['question']}  ({why})")
    print(f"  {correct}/{len(QUESTIONS)} correct ({correct / len(QUESTIONS):.0%})")


if __name__ == "__main__":
    main()
