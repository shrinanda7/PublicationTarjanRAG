"""Score saved predictions against a validated, frozen gold dataset.

Prediction JSON is an object with ``run`` metadata and a ``predictions`` list.
Each prediction has ``question_id`` and may include ``answer``, ranked
``retrieved_evidence`` / ``citations`` IDs (``paper_id::chunk_id``),
``retrieved_paths`` (ordered node-ID arrays), ``quotient_graph``, and
``abstained``. This scorer is deterministic and makes no LLM judge calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List

from backend.evaluation.gold_dataset import load_dataset
from backend.evaluation.metrics import (
    abstention_accuracy,
    best_reference_f1,
    citation_precision_recall,
    evidence_metrics,
    exact_match,
    exact_path_recall,
    path_survival_metrics,
)


def _evidence_id(item: Dict[str, Any]) -> str:
    return f"{item['paper_id']}::{item['chunk_id']}"


def _mean(values: List[float | int | None]) -> float | None:
    present = [float(value) for value in values if value is not None]
    return statistics.mean(present) if present else None


def score_run(dataset: Dict[str, Any], run_document: Dict[str, Any], top_k: int = 5) -> Dict[str, Any]:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    run = run_document.get("run")
    records = run_document.get("predictions")
    if not isinstance(run, dict) or not isinstance(records, list):
        raise ValueError("prediction file needs run metadata object and predictions array")

    predictions: Dict[str, Dict[str, Any]] = {}
    for item in records:
        if not isinstance(item, dict) or not item.get("question_id"):
            raise ValueError("each prediction must be an object with question_id")
        qid = str(item["question_id"])
        if qid in predictions:
            raise ValueError(f"duplicate prediction question_id: {qid}")
        predictions[qid] = item

    gold_records = dataset["questions"]
    gold_ids = {str(item["question_id"]) for item in gold_records}
    if set(predictions) != gold_ids:
        raise ValueError(
            f"prediction IDs must exactly match gold IDs; missing={sorted(gold_ids - set(predictions))}, "
            f"unexpected={sorted(set(predictions) - gold_ids)}"
        )

    required_run_fields = (
        "run_id", "created_at_utc", "methods", "dataset_corpus_version", "model",
        "prompt_version", "temperature", "seed", "top_k", "max_evidence_chunks",
        "max_context_tokens_estimated", "token_estimator", "hardware_platform",
        "code_revision", "working_tree_clean", "git_status_sha256", "method_configuration",
    )
    missing_run_fields = [field for field in required_run_fields if run.get(field) is None]
    if not isinstance(run.get("methods"), list) or not run.get("methods"):
        missing_run_fields.append("nonempty_methods_list")
    elif len(run["methods"]) != 1:
        missing_run_fields.append("exactly_one_method_per_prediction_file")
    else:
        method = run["methods"][0]
        if method == "tarjan" or method in {"no_scc", "no_connector", "no_budget", "no_cross_paper_links", "no_evidence_recovery", "no_query_conditioned"}:
            if not isinstance(run.get("retrieval_flags"), dict):
                missing_run_fields.append("retrieval_flags")
        if method in {"dense", "hybrid"} and not run.get("embedding_model"):
            missing_run_fields.append("embedding_model")
        if method == "dynamic_community" and not run.get("selection_model"):
            missing_run_fields.append("selection_model")
    if run.get("dataset_corpus_version") != dataset.get("corpus_version"):
        missing_run_fields.append("dataset_corpus_version_matches_gold")
    if run.get("working_tree_clean") is not True:
        missing_run_fields.append("clean_committed_working_tree")
    if isinstance(run.get("seed"), bool) or not isinstance(run.get("seed"), int):
        missing_run_fields.append("integer_generation_seed")

    allowed_outcomes = {"ok", "no_evidence", "context_budget_exceeded"}
    operational_failures = []
    for qid, pred in predictions.items():
        status = pred.get("status")
        llm_status = pred.get("llm_status")
        failure = pred.get("error")
        if status not in allowed_outcomes:
            failure = failure or f"unexpected or missing prediction status: {status!r}"
        elif status == "ok" and llm_status != "success":
            failure = failure or f"status=ok requires llm_status=success, got {llm_status!r}"
        elif llm_status is not None and llm_status != "success":
            failure = failure or f"LLM call did not succeed: {llm_status!r}"
        if failure:
            operational_failures.append({"question_id": qid, "reason": str(failure)})
    execution_valid = not operational_failures
    metadata_complete = not missing_run_fields

    scored = []
    for gold in gold_records:
        qid = str(gold["question_id"])
        pred = predictions[qid]
        answer = str(pred.get("answer", ""))
        gold_answers = gold["gold_answers"]
        gold_evidence = {_evidence_id(item) for item in gold["gold_evidence"]}
        retrieved_evidence = [str(item) for item in pred.get("retrieved_evidence", [])]
        citations = [str(item) for item in pred.get("citations", [])]
        gold_paths = [item["nodes"] for item in gold["gold_paths"]]
        retrieved_paths = pred.get("retrieved_paths")
        graph_size_metrics = pred.get("graph_metrics") or {}
        is_abstained = bool(pred.get("abstained", False))

        evidence = evidence_metrics(retrieved_evidence, sorted(gold_evidence), top_k)
        citation = citation_precision_recall(citations, gold_evidence)
        graph_metrics = (
            path_survival_metrics(gold_paths, pred["quotient_graph"])
            if pred.get("quotient_graph") is not None
            else {"psr": None, "rcfr": None}
        )
        cross_paper_coverage = None
        if gold["category"] == "multi_hop_cross_paper":
            # Candidate scope may include papers not needed by the gold answer;
            # measure whether all gold-supporting papers were retrieved.
            required_papers = {str(item["paper_id"]) for item in gold["gold_evidence"]}
            retrieved_papers = {item.split("::", 1)[0] for item in retrieved_evidence[:top_k]}
            cross_paper_coverage = (
                len(required_papers & retrieved_papers) / len(required_papers)
                if required_papers else None
            )

        scored.append({
            "question_id": qid,
            "category": gold["category"],
            "answerable": gold["answerable"],
            "exact_match": exact_match(answer, gold_answers) if gold["answerable"] else None,
            "token_f1": best_reference_f1(answer, gold_answers) if gold["answerable"] else None,
            "evidence_precision_at_k": evidence["precision"],
            "evidence_recall_at_k": evidence["recall"],
            "evidence_mrr_at_k": evidence["mrr"],
            "evidence_hit_at_k": evidence["hit"],
            "gold_path_recall": exact_path_recall(retrieved_paths, gold_paths) if retrieved_paths is not None else None,
            "path_survival_rate": graph_metrics["psr"],
            "reasoning_chain_fracture_rate": graph_metrics["rcfr"],
            "citation_precision": citation["precision"],
            "citation_recall": citation["recall"],
            "abstention_accuracy": abstention_accuracy(is_abstained, gold["answerable"]),
            "cross_paper_evidence_coverage": cross_paper_coverage,
            "latency_ms": pred.get("latency_ms"),
            "retrieval_latency_ms": pred.get("retrieval_latency_ms"),
            "synthesis_latency_ms": pred.get("synthesis_latency_ms"),
            "llm_calls": pred.get("llm_calls"),
            "llm_tokens": pred.get("llm_tokens"),
            "retrieval_llm_calls": pred.get("retrieval_llm_calls"),
            "retrieval_tokens": pred.get("retrieval_tokens"),
            "embedding_calls": pred.get("embedding_calls"),
            "embedding_tokens": pred.get("embedding_tokens"),
            "embedding_latency_ms": pred.get("embedding_latency_ms"),
            "prompt_tokens": pred.get("prompt_tokens"),
            "completion_tokens": pred.get("completion_tokens"),
            "estimated_context_tokens": pred.get("estimated_context_tokens"),
            "context_token_budget": pred.get("context_token_budget"),
            "context_token_budget_utilization": pred.get("context_token_budget_utilization"),
            "original_node_count": graph_size_metrics.get("original_node_count"),
            "original_edge_count": graph_size_metrics.get("original_edge_count"),
            "quotient_node_count": graph_size_metrics.get("quotient_node_count"),
            "quotient_edge_count": graph_size_metrics.get("quotient_edge_count"),
            "node_compression_ratio": graph_size_metrics.get("node_compression_ratio"),
            "edge_compression_ratio": graph_size_metrics.get("edge_compression_ratio"),
            "node_reduction_fraction": graph_size_metrics.get("node_reduction_fraction"),
            "edge_reduction_fraction": graph_size_metrics.get("edge_reduction_fraction"),
        })

    metric_names = [key for key in scored[0] if key not in {"question_id", "category", "answerable"}]
    summary = {metric: _mean([item[metric] for item in scored]) for metric in metric_names}
    by_category = {}
    for category in sorted({item["category"] for item in scored}):
        category_records = [item for item in scored if item["category"] == category]
        by_category[category] = {
            metric: _mean([item[metric] for item in category_records])
            for metric in metric_names
        }

    dataset_fingerprint = hashlib.sha256(
        json.dumps(dataset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "scorer_version": "1.1",
        "top_k": top_k,
        "dataset_corpus_version": dataset["corpus_version"],
        "dataset_sha256": dataset_fingerprint,
        "run": run,
        "valid_for_analysis": execution_valid and metadata_complete,
        "validity": {
            "execution_valid": execution_valid,
            "metadata_complete": metadata_complete,
            "operational_failure_count": len(operational_failures),
            "operational_failures": operational_failures,
            "missing_or_invalid_run_metadata": sorted(set(missing_run_fields)),
        },
        "question_count": len(scored),
        "summary": summary,
        "by_category": by_category,
        "per_question": scored,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold_dataset", help="Validated frozen gold dataset JSON")
    parser.add_argument("predictions", help="Saved prediction JSON")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output", help="Output JSON path; defaults to stdout")
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.gold_dataset)
        run_document = json.loads(Path(args.predictions).read_text(encoding="utf-8"))
        result = score_run(dataset, run_document, args.top_k)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
