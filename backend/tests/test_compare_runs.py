import pytest
import json

from backend.evaluation.compare_runs import _load_runs, compare_runs


def _scored(values):
    return {
        "valid_for_analysis": True,
        "dataset_sha256": "f" * 64,
        "per_question": [
            {"question_id": f"q{i}", "category": "single_paper" if i < 3 else "multi_hop_cross_paper", "evidence_recall_at_k": score}
            for i, score in enumerate(values, 1)
        ],
    }


def test_compare_runs_uses_paired_questions_and_is_deterministic():
    runs = {
        "bm25": [_scored([0.0, 0.0, 1.0]), _scored([0.0, 0.0, 1.0])],
        "tarjan": [_scored([1.0, 1.0, 1.0]), _scored([1.0, 1.0, 1.0])],
    }
    first = compare_runs(runs, "f" * 64, bootstrap_samples=1000, seed=17)
    second = compare_runs(runs, "f" * 64, bootstrap_samples=1000, seed=17)

    comparison = first["comparisons"][0]
    assert comparison["reference_method"] == "bm25"
    assert comparison["comparison_method"] == "tarjan"
    assert comparison["paired_question_count"] == 3
    assert comparison["bootstrap_strata"] == {"multi_hop_cross_paper": 1, "single_paper": 2}
    assert comparison["mean_paired_difference"] == pytest.approx(2 / 3)
    assert comparison["bootstrap_ci_95"][0] <= 2 / 3 <= comparison["bootstrap_ci_95"][1]
    assert comparison["paired_sign_flip_p_value"] == pytest.approx(0.5)
    assert first == second


def test_run_loader_rejects_reusing_a_seed_as_a_repeat(tmp_path):
    def write_score(name, run_id, seed):
        path = tmp_path / name
        path.write_text(json.dumps({
            "valid_for_analysis": True,
            "dataset_sha256": "f" * 64,
            "run": {"run_id": run_id, "seed": seed, "methods": ["bm25"]},
            "per_question": [],
        }), encoding="utf-8")
        return path

    first = write_score("first.json", "run-1", 11)
    second = write_score("second.json", "run-2", 11)
    with pytest.raises(ValueError, match="distinct seeds"):
        _load_runs([f"bm25={first}", f"bm25={second}"])


def test_run_loader_rejects_unmatched_context_or_generation_configuration(tmp_path):
    def write_score(name, method, run_id, seed, context_budget):
        path = tmp_path / name
        path.write_text(json.dumps({
            "valid_for_analysis": True,
            "dataset_sha256": "f" * 64,
            "run": {
                "run_id": run_id, "seed": seed, "methods": [method],
                "model": "model-a", "prompt_version": "prompt-v1", "temperature": 0.1,
                "top_k": 50, "max_evidence_chunks": 10, "max_context_chars": 24000,
                "max_context_tokens_estimated": context_budget,
                "token_estimator": "character-v1", "hardware_platform": "test-host",
            },
            "per_question": [],
        }), encoding="utf-8")
        return path

    bm25_first = write_score("bm25-1.json", "bm25", "b1", 1, 8000)
    bm25_second = write_score("bm25-2.json", "bm25", "b2", 2, 8000)
    tarjan_first = write_score("tarjan-1.json", "tarjan", "t1", 1, 8000)
    tarjan_second = write_score("tarjan-2.json", "tarjan", "t2", 2, 16000)

    with pytest.raises(ValueError, match="matched experiment settings"):
        _load_runs([
            f"bm25={bm25_first}", f"bm25={bm25_second}",
            f"tarjan={tarjan_first}", f"tarjan={tarjan_second}",
        ])
