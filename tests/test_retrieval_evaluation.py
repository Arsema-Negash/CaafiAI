from pathlib import Path

import pytest

from app.ai.evaluate_retrieval import evaluate_cases, load_cases

DRAFT_DATASET = Path(__file__).resolve().parents[1] / "evaluation" / "retrieval_cases.json"


CASES = [
    {"id": "child_fever", "query": "fever in a child", "expected_topic": "Fever", "expected_population": "Child"},
    {"id": "adult_chest", "query": "chest pain in an adult", "expected_topic": "Chest pain", "expected_population": "Adult"},
]


def test_draft_dataset_loads_and_stays_marked_for_clinical_review():
    dataset, cases = load_cases(DRAFT_DATASET)
    assert dataset["status"] == "draft_needs_clinical_review"
    assert len(cases) >= 15
    adult_cough = next(case for case in cases if case["id"] == "adult_cough")
    assert adult_cough["expected_topic"] == "Breathing difficulty"


def test_evaluation_calculates_topic_population_and_joint_hits():
    fixtures = {
        "fever in a child": [
            {"id": 1, "topic": "Other", "population": "Adult", "page": 1},
            {"id": 2, "topic": "Fever", "population": "Child", "page": 135},
        ],
        "chest pain in an adult": [
            {"id": 3, "topic": "Chest pain", "population": "Adult", "page": 30},
        ],
    }

    report = evaluate_cases(CASES, lambda query, top_k: fixtures[query][:top_k], ks=(1, 2))
    metrics = report["metrics"]

    assert metrics["case_count"] == 2
    assert metrics["cutoffs"]["1"]["joint_topic_population_hit_rate_at_1"] == pytest.approx(0.5)
    assert metrics["cutoffs"]["2"]["joint_topic_population_hit_rate_at_2"] == pytest.approx(1.0)
    assert metrics["joint_mean_reciprocal_rank"] == pytest.approx(0.75)
    assert report["cases"][0]["joint_first_rank"] == 2


def test_evaluation_reports_no_match_without_crashing():
    report = evaluate_cases(
        CASES[:1],
        lambda query, top_k: [{"topic": "Other", "population": "Adult"}],
        ks=(3,),
    )
    assert report["metrics"]["cases_with_no_joint_label_match"] == ["child_fever"]
    assert report["metrics"]["joint_mean_reciprocal_rank"] == 0.0


def test_evaluation_rejects_empty_cases():
    with pytest.raises(ValueError, match="At least one"):
        evaluate_cases([], lambda query, top_k: [])


def test_evaluation_handles_fewer_results_than_cutoff():
    report = evaluate_cases(
        CASES[:1],
        lambda query, top_k: [],
        ks=(3,),
    )
    assert report["cases"][0]["hits"]["joint_hit_at_3"] is False
    assert report["metrics"]["joint_mean_reciprocal_rank"] == 0.0


def test_load_cases_rejects_missing_fields(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text('{"cases":[{"id":"x","query":"q","expected_topic":"Fever"}]}', encoding="utf-8")
    with pytest.raises(ValueError, match="missing required fields"):
        load_cases(path)


def test_load_cases_rejects_duplicate_ids(tmp_path):
    path = tmp_path / "cases.json"
    path.write_text(
        '{"cases":['
        '{"id":"same","query":"q1","expected_topic":"Fever","expected_population":"Child"},'
        '{"id":"same","query":"q2","expected_topic":"Fever","expected_population":"Adult"}'
        ']}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate"):
        load_cases(path)
