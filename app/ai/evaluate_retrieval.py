"""Evaluate clinical guideline retrieval against a draft, metadata-labeled query set.

This measures whether retrieved chunks match expected topic/population metadata.
It does not establish clinical relevance or clinical safety. The draft cases must be
reviewed by a qualified clinician before results are used as clinical evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES = PROJECT_ROOT / "evaluation" / "retrieval_cases.json"
DEFAULT_KS = (3, 5)


def load_cases(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Load and minimally validate an evaluation dataset."""
    try:
        dataset = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Evaluation dataset not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in evaluation dataset {path}: {exc}") from exc

    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Evaluation dataset must contain a non-empty 'cases' list.")

    seen_ids: set[str] = set()
    required = ("id", "query", "expected_topic", "expected_population")
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"Case {index} must be a JSON object.")
        missing = [field for field in required if not str(case.get(field, "")).strip()]
        if missing:
            raise ValueError(f"Case {index} is missing required fields: {', '.join(missing)}")
        case_id = str(case["id"])
        if case_id in seen_ids:
            raise ValueError(f"Duplicate evaluation case id: {case_id}")
        seen_ids.add(case_id)
    return dataset, cases


def evaluate_cases(
    cases: list[dict[str, Any]],
    search_fn: Callable[..., list[dict[str, Any]]],
    ks: tuple[int, ...] = DEFAULT_KS,
) -> dict[str, Any]:
    """Calculate topic/population label-hit metrics and per-case diagnostics."""
    if not cases:
        raise ValueError("At least one evaluation case is required.")
    if not ks or any(not isinstance(k, int) or k < 1 for k in ks):
        raise ValueError("All evaluation cutoffs must be positive integers.")

    ordered_ks = tuple(sorted(set(ks)))
    per_case: list[dict[str, Any]] = []
    topic_ranks: list[int | None] = []
    population_ranks: list[int | None] = []
    joint_ranks: list[int | None] = []

    for case in cases:
        results = search_fn(case["query"], top_k=max(ordered_ks))
        expected_topic = case["expected_topic"]
        expected_population = case["expected_population"]

        topic_rank = next(
            (rank for rank, result in enumerate(results, start=1)
             if result.get("topic") == expected_topic),
            None,
        )
        population_rank = next(
            (rank for rank, result in enumerate(results, start=1)
             if result.get("population") == expected_population),
            None,
        )
        joint_rank = next(
            (rank for rank, result in enumerate(results, start=1)
             if result.get("topic") == expected_topic
             and result.get("population") == expected_population),
            None,
        )
        topic_ranks.append(topic_rank)
        population_ranks.append(population_rank)
        joint_ranks.append(joint_rank)

        result_summaries = [
            {
                "rank": rank,
                "id": result.get("id"),
                "topic": result.get("topic"),
                "population": result.get("population"),
                "page": result.get("page"),
                "semantic_score": result.get("score"),
                "ranking_score": result.get("ranking_score"),
            }
            for rank, result in enumerate(results, start=1)
        ]
        hits = {}
        for k in ordered_ks:
            hits[f"topic_hit_at_{k}"] = topic_rank is not None and topic_rank <= k
            hits[f"population_hit_at_{k}"] = population_rank is not None and population_rank <= k
            hits[f"joint_hit_at_{k}"] = joint_rank is not None and joint_rank <= k
        per_case.append({
            "id": case["id"],
            "query": case["query"],
            "expected_topic": expected_topic,
            "expected_population": expected_population,
            "topic_first_rank": topic_rank,
            "population_first_rank": population_rank,
            "joint_first_rank": joint_rank,
            "hits": hits,
            "top_results": result_summaries,
        })

    def hit_rate(ranks: list[int | None], k: int) -> float:
        return sum(rank is not None and rank <= k for rank in ranks) / len(ranks)

    metrics: dict[str, Any] = {
        "case_count": len(cases),
        "metrics_note": (
            "Label-hit rates measure agreement with provisional topic/population metadata only; "
            "they are not clinical relevance, answer correctness, or safety metrics."
        ),
        "cutoffs": {},
    }
    for k in ordered_ks:
        metrics["cutoffs"][str(k)] = {
            f"topic_label_hit_rate_at_{k}": round(hit_rate(topic_ranks, k), 4),
            f"population_label_hit_rate_at_{k}": round(hit_rate(population_ranks, k), 4),
            f"joint_topic_population_hit_rate_at_{k}": round(hit_rate(joint_ranks, k), 4),
        }
    metrics["joint_mean_reciprocal_rank"] = round(
        sum(1 / rank for rank in joint_ranks if rank is not None) / len(cases),
        4,
    )
    metrics["cases_with_no_joint_label_match"] = [
        case["id"] for case in per_case if case["joint_first_rank"] is None
    ]
    return {"metrics": metrics, "cases": per_case}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_CASES, help="Path to evaluation JSON")
    parser.add_argument("--output", type=Path, help="Optional path to write the full JSON report")
    parser.add_argument("--ks", type=int, nargs="+", default=list(DEFAULT_KS), help="Top-k cutoffs (default: 3 5)")
    args = parser.parse_args()

    try:
        dataset, cases = load_cases(args.dataset)
        from app.ai.retrieval import search_clinical_guidelines
        report = evaluate_cases(cases, search_clinical_guidelines, tuple(args.ks))
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report["dataset"] = {
        "name": dataset.get("dataset_name"),
        "version": dataset.get("dataset_version"),
        "status": dataset.get("status"),
        "source_guideline": dataset.get("source_guideline"),
    }
    print(json.dumps(report["metrics"], indent=2, ensure_ascii=False))
    print("\nPer-case details:")
    for case in report["cases"]:
        print(
            f"- {case['id']}: joint rank={case['joint_first_rank']}; "
            f"expected={case['expected_topic']} / {case['expected_population']}"
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nFull report written to: {args.output}")

    print(
        "\nIMPORTANT: This draft dataset is not clinically validated. "
        "Have a qualified clinician review all cases and expected labels."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
