
import json
from pathlib import Path

from app.services.rag.retrieval import search_evidence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_PATH = PROJECT_ROOT / "evaluation" / "retrieval_benchmark.json"

TOP_K = 5


def evaluate_retrieval():
    with BENCHMARK_PATH.open(encoding="utf-8") as file:
        benchmark_data = json.load(file)

    video_id = benchmark_data["video_id"]
    questions = benchmark_data["benchmark"]

    recalls = []
    reciprocal_ranks = []
    hits = []

    print("\nVIDIQ AI - RETRIEVAL EVALUATION")
    print("=" * 55)

    for question in questions:
        question_id = question["id"]
        query = question["question"]
        expected_ids = set(question["expected_evidence_ids"])
        expected_type = question["expected_type"]

        results = search_evidence(
            query=query,
            top_k=TOP_K,
            video_id=video_id,
        )

        retrieved_ids = [
            item["evidence_id"] for item in results
        ]

        print(f"\n{question_id}: {query}")
        print(f"Retrieved: {retrieved_ids}")

        # Unanswerable questions are handled separately.
        if expected_type == "insufficient_evidence":
            print("Result: UNANSWERABLE CASE - NOT SCORED")
            continue

        relevant_ranks = [
            rank
            for rank, evidence_id in enumerate(
                retrieved_ids, start=1
            )
            if evidence_id in expected_ids
        ]

        relevant_count = len(
            set(retrieved_ids) & expected_ids
        )

        recall = relevant_count / len(expected_ids)

        reciprocal_rank = (
            1 / relevant_ranks[0]
            if relevant_ranks
            else 0.0
        )

        hit = 1 if relevant_ranks else 0

        recalls.append(recall)
        reciprocal_ranks.append(reciprocal_rank)
        hits.append(hit)

        print(f"Expected IDs: {sorted(expected_ids)}")
        print(f"Recall@{TOP_K}: {recall:.2f}")
        print(f"Reciprocal Rank: {reciprocal_rank:.2f}")
        print(f"Hit@{TOP_K}: {hit}")

    print("\n" + "=" * 55)
    print("OVERALL RESULTS")

    if not recalls:
        print("No answerable questions available for evaluation.")
        return

    print(f"Evaluated questions: {len(recalls)}")
    print(f"Mean Recall@{TOP_K}: {sum(recalls) / len(recalls):.3f}")
    print(
        f"MRR@{TOP_K}: "
        f"{sum(reciprocal_ranks) / len(reciprocal_ranks):.3f}"
    )
    print(f"Hit Rate@{TOP_K}: {sum(hits) / len(hits):.3f}")


if __name__ == "__main__":
    evaluate_retrieval()
