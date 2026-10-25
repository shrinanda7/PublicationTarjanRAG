from backend.evaluation.metrics import (
    abstention_accuracy,
    best_reference_f1,
    directed_path_survives,
    evidence_metrics,
    exact_match,
    path_survival_metrics,
)
from backend.evaluation.gold_dataset import validate_dataset
from backend.evaluation.score_run import score_run


def test_answer_metrics_use_best_reference_and_normalized_exact_match():
    assert exact_match("The GCN method!", ["GCN method"]) == 1.0
    assert exact_match("wrong", []) is None
    assert best_reference_f1("GCN uses spectral convolution", ["GCN uses spectral filters", "GCN uses convolution"]) > 0.5


def test_evidence_metrics_have_explicit_empty_gold_semantics():
    result = evidence_metrics(["p1::c2", "p1::c1"], ["p1::c1"], k=1)
    assert result == {"precision": 0.0, "recall": 0.0, "mrr": 0.0, "hit": 0.0, "retrieved_count": 1, "gold_count": 1}
    assert evidence_metrics([], [])["recall"] is None


def test_path_survival_respects_direction_and_scc_mapping():
    quotient = {
        "nodes": [
            {"id": "SCC1", "member_node_ids": ["A", "B"]},
            {"id": "C", "member_node_ids": ["C"]},
        ],
        "edges": [{"source": "SCC1", "target": "C"}],
    }
    assert directed_path_survives(["A", "B", "C"], quotient)
    assert not directed_path_survives(["C", "B", "A"], quotient)
    assert not directed_path_survives(["A"], quotient)
    assert path_survival_metrics([["A", "B", "C"], ["C", "B", "A"]], quotient) == {
        "psr": 0.5, "rcfr": 0.5, "preserved_paths": 1, "gold_paths": 2
    }
    assert path_survival_metrics([], quotient)["psr"] is None


def test_path_metrics_reject_zero_transition_gold_paths():
    import pytest
    from backend.evaluation.metrics import exact_path_recall

    with pytest.raises(ValueError, match="at least one directed transition"):
        path_survival_metrics([["A"]], {"nodes": [{"id": "A"}], "edges": []})
    with pytest.raises(ValueError, match="at least one directed transition"):
        exact_path_recall([], [["A"]])


def test_unanswerable_questions_require_correct_abstention():
    assert abstention_accuracy(True, False) == 1.0
    assert abstention_accuracy(False, False) == 0.0


def test_gold_dataset_rejects_draft_hint_only_questions():
    document = {
        "schema_version": "1.0",
        "corpus_version": "draft",
        "corpus_papers": [],
        "questions": [{"question_id": "q1", "question": "A question?"}],
    }
    errors = validate_dataset(document)
    assert any("missing fields" in error for error in errors)
    assert any("corpus_papers" in error for error in errors)


def test_gold_dataset_reports_malformed_annotation_types_without_crashing():
    document = {
        "schema_version": "1.0", "corpus_version": "draft",
        "corpus_papers": [{"paper_id": "p1", "title": "Paper", "citation": "Author (2020)", "sha256": "a" * 64}],
        "questions": [{
            "question_id": "q1", "paper_ids": [{"bad": "id"}], "question": "A question?",
            "category": "multi_hop_cross_paper", "answerable": True, "gold_answers": [None],
            "gold_evidence": [], "gold_paths": [], "required_hops": True,
            "annotation": {"status": "validated", "reviewers": ["reviewer", []], "adjudicated": True},
        }],
    }
    errors = validate_dataset(document)
    assert any("paper_ids entries must be non-empty strings" in error for error in errors)
    assert any("gold_answers must be a list" in error for error in errors)
    assert any("required_hops must be a non-negative integer" in error for error in errors)
    assert any("at least two independent reviewer IDs" in error for error in errors)


def test_gold_dataset_rejects_chunk_and_quote_mismatch():
    document = {
        "schema_version": "1.0",
        "corpus_version": "v1",
        "corpus_papers": [{"paper_id": "p1", "title": "Paper", "citation": "Author (2020)", "sha256": "a" * 64}],
        "questions": [{
            "question_id": "q1", "paper_ids": ["p1"], "question": "What method?",
            "category": "single_paper", "answerable": True, "gold_answers": ["Method X"],
            "gold_evidence": [{"paper_id": "p1", "chunk_id": "c1", "quote": "missing quote"}],
            "gold_paths": [], "required_hops": 0,
            "annotation": {"status": "validated", "reviewers": ["r1", "r2"], "adjudicated": True},
        }],
    }
    errors = validate_dataset(document, {"p1": {"c1": "Actual source text."}})
    assert any("quote does not exactly occur" in error for error in errors)


def test_gold_dataset_rejects_duplicate_scope_and_inconsistent_hop_paths():
    from backend.evaluation.gold_dataset import validate_record

    record = {
        "question_id": "q-path",
        "paper_ids": ["p1", "p1"],
        "question": "How is the mechanism connected to its result?",
        "category": "multi_hop_single_paper",
        "answerable": True,
        "gold_answers": ["A supported answer"],
        "gold_evidence": [{"paper_id": "p1", "chunk_id": "c1", "quote": "support"}],
        "gold_paths": [{"nodes": ["A", "B"], "edges": [{"source": "A", "target": "B", "type": "USES"}]}],
        "required_hops": 2,
        "annotation": {"status": "validated", "reviewers": ["r1", "r2"], "adjudicated": True},
    }
    errors = validate_record(record)
    assert any("paper_ids entries must be unique" in error for error in errors)
    assert any("edge count must match required_hops" in error for error in errors)


def test_gold_dataset_rejects_zero_transition_paths():
    from backend.evaluation.gold_dataset import validate_record

    record = {
        "question_id": "q-empty-path", "paper_ids": ["p1"],
        "question": "What method is described?", "category": "single_paper",
        "answerable": True, "gold_answers": ["Method X"],
        "gold_evidence": [{"paper_id": "p1", "chunk_id": "c1", "quote": "Method X."}],
        "gold_paths": [{"nodes": ["n1"], "edges": []}], "required_hops": 0,
        "annotation": {"status": "validated", "reviewers": ["r1", "r2"], "adjudicated": True},
    }
    errors = validate_record(record)
    assert any("at least one directed transition" in error for error in errors)
    assert any("gold_paths must be empty when required_hops is zero" in error for error in errors)


def test_gold_dataset_malformed_category_is_reported_without_crashing():
    from backend.evaluation.gold_dataset import validate_record

    record = {
        "question_id": "q-malformed",
        "paper_ids": ["p1"],
        "question": "What is supported?",
        "category": [],
        "answerable": True,
        "gold_answers": ["Answer"],
        "gold_evidence": [{"paper_id": "p1", "chunk_id": "c1", "quote": "support"}],
        "gold_paths": [],
        "required_hops": 0,
        "annotation": {"status": "validated", "reviewers": ["r1", "r2"], "adjudicated": True},
    }
    assert any("category must be one of" in error for error in validate_record(record))


def test_gold_dataset_rejects_non_object_root_without_crashing():
    assert validate_dataset([]) == ["dataset root must be an object"]


def test_saved_run_scorer_checks_complete_question_alignment_and_reports_metrics():
    dataset = {
        "schema_version": "1.0", "corpus_version": "v1",
        "corpus_papers": [
            {"paper_id": "p1", "title": "One", "citation": "A (2020)", "sha256": "a" * 64},
            {"paper_id": "p2", "title": "Two", "citation": "B (2021)", "sha256": "b" * 64},
            {"paper_id": "p3", "title": "Candidate only", "citation": "C (2022)", "sha256": "c" * 64},
        ],
        "questions": [{
            "question_id": "q1", "paper_ids": ["p1", "p2", "p3"], "question": "What connects them?",
            "category": "multi_hop_cross_paper", "answerable": True,
            "gold_answers": ["Shared method"],
            "gold_evidence": [
                {"paper_id": "p1", "chunk_id": "c1", "quote": "support one"},
                {"paper_id": "p2", "chunk_id": "c2", "quote": "support two"},
            ],
            "gold_paths": [{"nodes": ["A", "B"], "edges": [{"source": "A", "target": "B", "type": "USES"}]}],
            "required_hops": 1,
            "annotation": {"status": "validated", "reviewers": ["r1", "r2"], "adjudicated": True},
        }],
    }
    predictions = {"run": {
        "run_id": "run-1", "created_at_utc": "2026-10-19T00:00:00Z",
        "methods": ["tarjan"], "dataset_corpus_version": "v1",
        "model": "test-model", "prompt_version": "v1", "temperature": 0.0, "seed": 1,
        "top_k": 5, "max_evidence_chunks": 10,
        "max_context_tokens_estimated": 1000,
        "token_estimator": "test", "hardware_platform": "test",
        "code_revision": "abc123", "working_tree_clean": True,
        "git_status_sha256": "0" * 64,
        "method_configuration": {"method": "tarjan"},
        "retrieval_flags": {"ENABLE_TARJAN_COMPRESSION": True},
    }, "predictions": [{
        "question_id": "q1", "answer": "The Shared method!",
        "retrieved_evidence": ["p1::c1", "p2::c2"], "citations": ["p1::c1", "p2::c2"],
        "retrieved_paths": [["A", "B"]],
        "quotient_graph": {"nodes": [{"id": "A"}, {"id": "B"}], "edges": [{"source": "A", "target": "B"}]},
        "abstained": False, "status": "ok", "llm_status": "success",
        "latency_ms": 100.0, "retrieval_latency_ms": 60.0, "synthesis_latency_ms": 40.0,
        "llm_calls": 1, "llm_tokens": 20, "retrieval_llm_calls": 2,
        "retrieval_tokens": 12, "embedding_calls": 3, "embedding_tokens": 18,
        "embedding_latency_ms": 25.0,
        "prompt_tokens": 14, "completion_tokens": 6,
        "estimated_context_tokens": 500, "context_token_budget": 1000,
        "context_token_budget_utilization": 0.5,
        "graph_metrics": {
            "original_node_count": 10, "original_edge_count": 20,
            "quotient_node_count": 5, "quotient_edge_count": 8,
            "node_compression_ratio": 0.5, "edge_compression_ratio": 0.4,
            "node_reduction_fraction": 0.5, "edge_reduction_fraction": 0.6,
        },
    }]}
    result = score_run(dataset, predictions, top_k=2)
    assert result["summary"]["evidence_recall_at_k"] == 1.0
    assert result["summary"]["gold_path_recall"] == 1.0
    assert result["summary"]["path_survival_rate"] == 1.0
    assert result["summary"]["cross_paper_evidence_coverage"] == 1.0
    assert result["summary"]["latency_ms"] == 100.0
    assert result["summary"]["retrieval_latency_ms"] == 60.0
    assert result["summary"]["llm_tokens"] == 20.0
    assert result["summary"]["embedding_tokens"] == 18.0
    assert result["summary"]["prompt_tokens"] == 14.0
    assert result["summary"]["completion_tokens"] == 6.0
    assert result["summary"]["context_token_budget_utilization"] == 0.5
    assert result["summary"]["node_reduction_fraction"] == 0.5
    assert result["summary"]["edge_reduction_fraction"] == 0.6
    assert len(result["dataset_sha256"]) == 64
    assert result["valid_for_analysis"] is True

    predictions["predictions"][0]["status"] = "llm_error"
    failed_result = score_run(dataset, predictions, top_k=2)
    assert failed_result["valid_for_analysis"] is False
    assert failed_result["validity"]["operational_failure_count"] == 1

    predictions["predictions"] = []
    try:
        score_run(dataset, predictions)
    except ValueError as error:
        assert "prediction IDs must exactly match" in str(error)
    else:
        raise AssertionError("incomplete run should be rejected")
