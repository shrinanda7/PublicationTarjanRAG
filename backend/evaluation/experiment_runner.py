"""Run validated gold questions with matched retrieval and answer synthesis."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import re
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from backend.config import settings
from backend.core.clustering import clusterer
from backend.core.compression import compressor
from backend.evaluation.baseline_retrieval import rank_bm25, rank_dense, rank_hybrid
from backend.evaluation.gold_dataset import load_dataset
from backend.pipeline.neo4j_store import neo4j_store
from backend.search.evidence_synthesis import select_budgeted_chunks, synthesize_evidence
from backend.search.dynamic_search import dynamic_search
from backend.search.local_search import local_search
from backend.search.multi_paper_search import multi_paper_search


ABLATION_FLAGS = {
    "no_scc": "ENABLE_TARJAN_COMPRESSION",
    "no_connector": "ENABLE_BRIDGE_AWARE_PRUNING",
    "no_budget": "ENABLE_BUDGET_AWARE_TRAVERSAL",
    "no_cross_paper_links": "ENABLE_CROSS_PAPER_LINKS",
    "no_evidence_recovery": "ENABLE_EVIDENCE_RECOVERY",
    "no_query_conditioned": "ENABLE_QUERY_CONDITIONED_TRAVERSAL",
}
BASELINE_RETRIEVAL_FLAGS = {flag: True for flag in ABLATION_FLAGS.values()}
METHODS = {"tarjan", "local", "bm25", "dense", "hybrid", *ABLATION_FLAGS}
COMMUNITY_METHODS = {"static_community", "dynamic_community"}
METHODS.update(COMMUNITY_METHODS)


def _git_metadata() -> Dict[str, Any]:
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            check=True, timeout=3,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            capture_output=True, text=True, check=True, timeout=3,
        ).stdout
        return {
            "code_revision": revision,
            "working_tree_clean": not bool(status.strip()),
            "git_status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
        }
    except (OSError, subprocess.SubprocessError):
        return {"code_revision": None, "working_tree_clean": False, "git_status_sha256": None}


def _citation_ids(answer: str, evidence: List[Dict[str, Any]]) -> List[str]:
    matches = set()
    for group in re.findall(r"\[(E\d+(?:\s*,\s*E\d+)*)\]", answer, flags=re.IGNORECASE):
        matches.update(re.findall(r"E\d+", group, flags=re.IGNORECASE))
    return [
        f"{item['paper_id']}::{item['chunk_id']}"
        for item in evidence
        if str(item.get("evidence_id", "")).upper() in {match.upper() for match in matches}
    ]


def _selected_original_paths(
    result: Dict[str, Any], *, max_nodes: int = 8, max_paths: int = 1000,
) -> List[List[str]]:
    """Enumerate bounded directed paths represented by the selected quotient subgraph.

    Paths are returned in original graph node IDs so they can be compared with
    independently annotated gold paths. Edges within a selected SCC are allowed;
    cross-component transitions must occur in the selected quotient edge set.
    """
    original = result.get("original_graph") or {}
    compressed = result.get("compressed_graph") or {}
    selected_ids = {str(value) for value in result.get("selected_node_ids", [])}
    selected_components = {
        str(node.get("id")): node for node in compressed.get("nodes", [])
        if str(node.get("id")) in selected_ids
    }
    original_to_component: Dict[str, str] = {}
    for component_id, node in selected_components.items():
        for member_id in node.get("member_node_ids") or [component_id]:
            original_to_component[str(member_id)] = component_id
    if not original_to_component:
        return []

    selected_edges = result.get("selected_edges") or []
    allowed_cross_component_edges = {
        (str(edge.get("source")), str(edge.get("target"))) for edge in selected_edges
    }
    adjacency: Dict[str, set[str]] = defaultdict(set)
    for edge in original.get("edges", []):
        source, target = str(edge.get("source", "")), str(edge.get("target", ""))
        source_component = original_to_component.get(source)
        target_component = original_to_component.get(target)
        if source_component is None or target_component is None:
            continue
        if source_component == target_component or (source_component, target_component) in allowed_cross_component_edges:
            adjacency[source].add(target)

    paths: List[List[str]] = []
    for start in sorted(adjacency):
        stack: List[tuple[str, List[str]]] = [(start, [start])]
        while stack and len(paths) < max_paths:
            current, path = stack.pop()
            if len(path) >= max_nodes:
                continue
            for neighbor in sorted(adjacency.get(current, set()), reverse=True):
                if neighbor in path:
                    continue
                extended = [*path, neighbor]
                paths.append(extended)
                if len(paths) >= max_paths:
                    break
                stack.append((neighbor, extended))
        if len(paths) >= max_paths:
            break
    return paths


async def _rank(method: str, question: str, chunks: List[Dict[str, Any]], top_k: int) -> Dict[str, Any]:
    if method == "bm25":
        return rank_bm25(question, chunks, top_k=top_k)
    if method == "dense":
        return await rank_dense(question, chunks, top_k=top_k)
    return await rank_hybrid(question, chunks, top_k=top_k)


async def _rank_community(
    method: str,
    question: str,
    paper_id: str,
    paper_title: str,
    *,
    seed: int | None = None,
) -> Dict[str, Any]:
    """Select source chunks through static or dynamically rated graph communities."""
    started = time.perf_counter()
    graph_data = neo4j_store.get_paper_graph(paper_id, compressed=False) or {}
    nodes, edges = graph_data.get("nodes", []), graph_data.get("edges", [])
    if not nodes:
        return {
            "method": method,
            "ranked": [],
            "status": "no_indexed_graph",
            "telemetry": {"retrieval_latency_ms": round((time.perf_counter() - started) * 1000, 2)},
        }
    old_scc = settings.ENABLE_TARJAN_COMPRESSION
    settings.ENABLE_TARJAN_COMPRESSION = True
    try:
        quotient = compressor.compress_graph(nodes, edges)
    finally:
        settings.ENABLE_TARJAN_COMPRESSION = old_scc
    communities = clusterer.build_hierarchy(quotient["nodes"], quotient["edges"], paper_id)
    quotient_nodes = {str(node.get("id")): node for node in quotient["nodes"]}
    for community in communities.values():
        descriptions = []
        for member_id in community.member_node_ids:
            node = quotient_nodes.get(str(member_id), {})
            descriptions.append(f"{node.get('name', '')}: {node.get('description', '')}")
        community.summary = " ".join(descriptions)[:4000]

    if method == "static_community":
        selected = [community for community in communities.values() if community.level == 1]
        if not selected:
            selected = list(communities.values())
        selection_trace = {
            "steps": [{"action": "SELECT", "node_or_comm_id": community.id, "reason": "Select every Level-1 community"} for community in selected],
            "ratings": {}, "llm_statuses": [], "total_llm_calls": 0, "total_tokens": 0,
        }
    else:
        result = await dynamic_search.search(
            question=question,
            paper_id=paper_id,
            paper_title=paper_title,
            communities=communities,
            selection_only=True,
            seed=seed,
        )
        selection_trace = result.get("trace", {})
        if any(status != "success" for status in selection_trace.get("llm_statuses", [])):
            raise RuntimeError(f"Dynamic community rating failed: {selection_trace.get('llm_statuses')}")
        selected_ids = set(result.get("selected_reports", []))
        selected = [community for community in communities.values() if community.id in selected_ids]

    scores = selection_trace.get("ratings", {})
    chunk_scores: Dict[str, float] = {}
    for community in selected:
        score = float(scores.get(community.id, 1.0 if method == "static_community" else 0.0))
        for node_id in community.member_node_ids:
            node = quotient_nodes.get(str(node_id), {})
            for chunk_id in node.get("source_chunk_ids", []):
                key = str(chunk_id)
                chunk_scores[key] = max(chunk_scores.get(key, 0.0), score)

    chunks = neo4j_store.get_chunks_by_ids(paper_id, sorted(chunk_scores)) or []
    ranked = [
        {
            **chunk,
            "paper_id": paper_id,
            "paper_title": paper_title,
            "score": chunk_scores[str(chunk.get("chunk_id", ""))],
        }
        for chunk in chunks
        if str(chunk.get("chunk_id", "")) in chunk_scores and chunk.get("content")
    ]
    ranked.sort(key=lambda item: (-item["score"], str(item["chunk_id"])))
    return {
        "method": method,
        "ranked": ranked,
        "selected_communities": [community.id for community in selected],
        "trace": selection_trace,
        "telemetry": {
            "retrieval_llm_calls": int(selection_trace.get("total_llm_calls", 0)),
            "retrieval_tokens": int(selection_trace.get("total_tokens", 0)),
            "retrieval_latency_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }


async def run_experiment(
    dataset: Dict[str, Any],
    methods: List[str],
    *,
    top_k: int = 50,
    max_evidence_chunks: int = 10,
    max_context_chars: int = 24000,
    max_context_tokens: int | None = None,
    seed: int = 2026,
) -> Dict[str, Any]:
    unknown = set(methods) - METHODS
    if unknown:
        raise ValueError(f"Unknown methods: {sorted(unknown)}")
    if len(methods) != 1:
        raise ValueError("Run one method per prediction file so the deterministic scorer receives one prediction per question")
    if top_k < 1 or max_evidence_chunks < 0:
        raise ValueError("top_k must be positive and max_evidence_chunks non-negative")
    context_tokens = int(max_context_tokens if max_context_tokens is not None else settings.MAX_TOKEN_BUDGET)
    paper_info = {str(p["paper_id"]): p for p in dataset["corpus_papers"]}
    predictions: List[Dict[str, Any]] = []
    telemetry: Dict[str, Any] = {
        method: {
            "embedding_calls": 0, "embedding_tokens": 0, "embedding_latency_ms": 0.0,
            "retrieval_llm_calls": 0, "retrieval_tokens": 0, "retrieval_latency_ms": 0.0,
            "answer_llm_calls": 0, "answer_tokens": 0, "synthesis_latency_ms": 0.0,
            "end_to_end_latency_ms": 0.0, "question_count": 0,
        }
        for method in methods
    }
    for gold in dataset["questions"]:
        qid = str(gold["question_id"])
        for method in methods:
            question_started = time.perf_counter()
            record: Dict[str, Any] = {
                "question_id": qid,
                "method": method,
                "status": "error",
                "answer": "",
                "retrieved_evidence": [],
                "citations": [],
                "abstained": False,
                "retrieved_paths": None,
                "quotient_graph": None,
            }
            try:
                candidate_chunks: List[Dict[str, Any]] = []
                for pid in gold["paper_ids"]:
                    paper = paper_info[pid]
                    paper_chunks = neo4j_store.get_chunks_by_ids(pid, []) or []
                    if not paper_chunks:
                        raise RuntimeError(f"No indexed source chunks are available for paper {pid!r}")
                    for chunk in paper_chunks:
                        if chunk.get("content"):
                            candidate_chunks.append({
                                **chunk,
                                "paper_id": pid,
                                "paper_title": paper["title"],
                            })
                if method == "tarjan" or method in ABLATION_FLAGS:
                    previous_flags = {
                        flag: getattr(settings, flag)
                        for flag in ABLATION_FLAGS.values()
                    }
                    for flag, value in BASELINE_RETRIEVAL_FLAGS.items():
                        setattr(settings, flag, value)
                    override = ABLATION_FLAGS.get(method)
                    if override:
                        setattr(settings, override, False)
                    try:
                        result = await multi_paper_search.search(
                            gold["question"], gold["paper_ids"],
                            {pid: paper_info[pid]["title"] for pid in gold["paper_ids"]},
                            max_evidence_chunks=max_evidence_chunks,
                            max_context_chars=max_context_chars,
                            max_context_tokens=context_tokens,
                            seed=seed,
                        )
                    finally:
                        for flag, value in previous_flags.items():
                            setattr(settings, flag, value)
                    evidence = result.get("evidence", [])
                    answer = str(result.get("answer", ""))
                    record["retrieval_trace"] = result.get("retrieval_trace")
                    if result.get("compressed_graph"):
                        graph = result["compressed_graph"]
                        original_graph = result.get("original_graph") or {}
                        original_node_count = len(original_graph.get("nodes", []))
                        original_edge_count = len(original_graph.get("edges", []))
                        quotient_node_count = len(graph.get("nodes", []))
                        quotient_edge_count = len(graph.get("edges", []))
                        record["graph_metrics"] = {
                            "original_node_count": original_node_count,
                            "original_edge_count": original_edge_count,
                            "quotient_node_count": quotient_node_count,
                            "quotient_edge_count": quotient_edge_count,
                            "node_compression_ratio": quotient_node_count / original_node_count if original_node_count else None,
                            "edge_compression_ratio": quotient_edge_count / original_edge_count if original_edge_count else None,
                            "node_reduction_fraction": 1.0 - quotient_node_count / original_node_count if original_node_count else None,
                            "edge_reduction_fraction": 1.0 - quotient_edge_count / original_edge_count if original_edge_count else None,
                        }
                        record["quotient_graph"] = {
                            "nodes": graph.get("nodes", []),
                            # PSR/RCFR measures compression preservation before
                            # query-time selection, so it must use every quotient edge.
                            "edges": graph.get("edges", []),
                        }
                        record["selected_quotient_graph"] = {
                            "nodes": [
                                node for node in graph.get("nodes", [])
                                if str(node.get("id")) in {str(item) for item in result.get("selected_node_ids", [])}
                            ],
                            "edges": result.get("selected_edges", []),
                        }
                        record["retrieved_paths"] = _selected_original_paths(result)
                    record["status"] = str(result.get("status", "error"))
                    record["llm_status"] = result.get("llm_status")
                    if record["llm_status"] != "success" and record["status"] == "ok":
                        record["status"] = "llm_error"
                    record["llm_calls"] = result.get("total_llm_calls", 0)
                    record["prompt_tokens"] = result.get("prompt_tokens", 0)
                    record["completion_tokens"] = result.get("completion_tokens", 0)
                    record["llm_tokens"] = result.get("total_tokens", 0)
                    record["latency_ms"] = result.get("latency_ms")
                    total_latency = float(result.get("latency_ms") or 0.0)
                    synthesis_latency = float((result.get("trace") or {}).get("latency_ms") or 0.0)
                    record["synthesis_latency_ms"] = synthesis_latency
                    record["retrieval_latency_ms"] = max(0.0, total_latency - synthesis_latency)
                    if override:
                        record["ablation"] = {"disabled_flag": override}
                else:
                    ranking: Dict[str, Any]
                    if method in COMMUNITY_METHODS:
                        per_paper = [
                            await _rank_community(method, gold["question"], pid, paper_info[pid]["title"], seed=seed)
                            for pid in gold["paper_ids"]
                        ]
                        missing_graphs = [pid for pid, result in zip(gold["paper_ids"], per_paper) if result.get("status") == "no_indexed_graph"]
                        if missing_graphs:
                            raise RuntimeError(f"No indexed graph is available for community retrieval on papers: {missing_graphs}")
                        ranked_chunks = [chunk for result in per_paper for chunk in result.get("ranked", [])]
                        ranked_chunks.sort(key=lambda item: (-float(item.get("score", 0.0)), str(item.get("paper_id", "")), str(item.get("chunk_id", ""))))
                        ranking = {
                            "method": method,
                            "ranked": ranked_chunks,
                            "paper_traces": {str(pid): result.get("trace") for pid, result in zip(gold["paper_ids"], per_paper)},
                            "selected_communities": {str(pid): result.get("selected_communities", []) for pid, result in zip(gold["paper_ids"], per_paper)},
                            "telemetry": {
                                "retrieval_llm_calls": sum(result.get("telemetry", {}).get("retrieval_llm_calls", 0) for result in per_paper),
                                "retrieval_tokens": sum(result.get("telemetry", {}).get("retrieval_tokens", 0) for result in per_paper),
                                "retrieval_latency_ms": round(sum(result.get("telemetry", {}).get("retrieval_latency_ms", 0.0) for result in per_paper), 2),
                            },
                        }
                    elif method == "local":
                        local_candidates = []
                        local_traces = {}
                        local_latencies = []
                        for pid in gold["paper_ids"]:
                            result = await local_search.search(
                                gold["question"], pid, paper_info[pid]["title"],
                                top_k_chunks=top_k, generate_answer=False,
                            )
                            if result.get("status") == "no_indexed_graph":
                                raise RuntimeError(f"No indexed graph is available for local retrieval on paper {pid!r}")
                            local_traces[pid] = result.get("retrieval_trace")
                            local_latencies.append(float((result.get("trace") or {}).get("latency_ms") or 0.0))
                            local_candidates.extend(result.get("retrieved_evidence", []))
                        ranked_chunks = sorted(
                            local_candidates,
                            key=lambda item: (-float(item.get("score", 0.0)), str(item.get("paper_id", "")), str(item.get("chunk_id", ""))),
                        )
                        ranking = {
                            "method": "lexical_local_graph",
                            "ranked": ranked_chunks,
                            "telemetry": {"retrieval_latency_ms": round(sum(local_latencies), 2)},
                            "paper_traces": local_traces,
                        }
                    else:
                        ranking = await _rank(method, gold["question"], candidate_chunks, top_k)
                        ranked_chunks = [item for item in ranking.get("ranked", [])]
                    for key, value in ranking.get("telemetry", {}).items():
                        telemetry[method][key] = telemetry[method].get(key, 0) + (value or 0)
                    record["retrieval_llm_calls"] = ranking.get("telemetry", {}).get("retrieval_llm_calls", 0)
                    record["retrieval_tokens"] = ranking.get("telemetry", {}).get("retrieval_tokens", 0)
                    record["retrieval_latency_ms"] = ranking.get("telemetry", {}).get("retrieval_latency_ms", 0.0)
                    record["embedding_calls"] = ranking.get("telemetry", {}).get("embedding_calls", 0)
                    record["embedding_tokens"] = ranking.get("telemetry", {}).get("embedding_tokens", 0)
                    record["embedding_latency_ms"] = ranking.get("telemetry", {}).get("embedding_latency_ms", 0.0)
                    record["selected_communities"] = ranking.get("selected_communities")
                    selected, budget = select_budgeted_chunks(
                        gold["question"], ranked_chunks,
                        max_evidence_chunks=max_evidence_chunks,
                        max_context_chars=max_context_chars,
                        max_context_tokens=context_tokens,
                    )
                    if not selected:
                        answer = "No retrieved source chunks fit the configured context budget."
                        record["status"] = "no_evidence"
                        record["retrieval_trace"] = {"budget": budget, "ranker": ranking.get("method"), "paper_traces": ranking.get("paper_traces")}
                        evidence = []
                    else:
                        answer, log, _ = await synthesize_evidence(gold["question"], selected, seed=seed)
                        evidence = [
                            {"evidence_id": f"E{i}", **chunk}
                            for i, chunk in enumerate(selected, 1)
                        ]
                        record["status"] = "ok" if log.status == "success" and answer.strip() else "llm_error"
                        record["llm_status"] = log.status
                        record["llm_calls"] = 1 if log.status == "success" else 0
                        record["prompt_tokens"] = log.prompt_tokens
                        record["completion_tokens"] = log.completion_tokens
                        record["llm_tokens"] = log.total_tokens
                        record["synthesis_latency_ms"] = log.latency_ms
                        record["retrieval_trace"] = {"budget": budget, "ranker": ranking.get("method"), "ranker_parameters": ranking.get("parameters"), "retrieval_telemetry": ranking.get("telemetry"), "paper_traces": ranking.get("paper_traces")}
                record["answer"] = answer
                record["retrieved_evidence"] = [f"{item['paper_id']}::{item['chunk_id']}" for item in evidence]
                record["citations"] = _citation_ids(answer, evidence)
                record["abstained"] = bool(re.search(r"\b(insufficient evidence|cannot be determined|not enough evidence)\b", answer, re.I))
                retrieval_trace = record.get("retrieval_trace") or {}
                budget_trace = retrieval_trace.get("budget") or retrieval_trace
                record["estimated_context_tokens"] = budget_trace.get("estimated_prompt_tokens")
                record["context_token_budget"] = budget_trace.get("context_tokens_budget")
                record["context_token_budget_utilization"] = budget_trace.get("token_budget_utilization")
            except Exception as exc:  # preserve complete gold coverage and expose operational failures
                record["error"] = f"{type(exc).__name__}: {exc}"
            elapsed_ms = round((time.perf_counter() - question_started) * 1000, 2)
            record["latency_ms"] = elapsed_ms
            record["end_to_end_latency_ms"] = elapsed_ms
            telemetry[method]["answer_llm_calls"] += int(record.get("llm_calls", 0) or 0)
            telemetry[method]["answer_tokens"] += int(record.get("llm_tokens", 0) or 0)
            telemetry[method]["synthesis_latency_ms"] += float(record.get("synthesis_latency_ms", 0.0) or 0.0)
            telemetry[method]["end_to_end_latency_ms"] += elapsed_ms
            telemetry[method]["question_count"] += 1
            predictions.append(record)
    method = methods[0]
    retrieval_flags = None
    if method == "tarjan" or method in ABLATION_FLAGS:
        retrieval_flags = {
            **BASELINE_RETRIEVAL_FLAGS,
            **({ABLATION_FLAGS[method]: False} if method in ABLATION_FLAGS else {}),
        }
    elif method in COMMUNITY_METHODS:
        retrieval_flags = {"ENABLE_TARJAN_COMPRESSION": True}
    method_configuration: Dict[str, Any] = {"method": method}
    if method in ABLATION_FLAGS:
        method_configuration["ablation"] = {"disabled_flag": ABLATION_FLAGS[method]}
    elif method == "bm25":
        method_configuration["bm25"] = {"k1": 1.2, "b": 0.75}
    elif method == "hybrid":
        method_configuration["hybrid_rrf"] = {"sparse_weight": 1.0, "dense_weight": 1.0, "rrf_k": 60}
    elif method == "local":
        method_configuration["local_graph"] = {"k_hops": 2, "top_k_seeds": 4, "lexical_entity_matching": True}
    elif method == "static_community":
        method_configuration["community_selection"] = {"selection": "all_level_1_quotient_communities"}
    elif method == "dynamic_community":
        method_configuration["community_selection"] = {
            "selection": "llm_rated_top_down",
            "relevance_threshold": settings.RELEVANCE_THRESHOLD,
            "max_depth": settings.MAX_COMMUNITY_DEPTH,
            "rating_model": settings.OLLAMA_SMALL_MODEL,
        }
    return {
        "run": {
            "run_id": str(uuid.uuid4()),
            "methods": methods,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            **_git_metadata(),
            "dataset_corpus_version": dataset["corpus_version"],
            "model": settings.OLLAMA_LARGE_MODEL,
            "embedding_model": settings.OLLAMA_EMBED_MODEL if any(m in methods for m in ("dense", "hybrid")) else None,
            "selection_model": settings.OLLAMA_SMALL_MODEL if "dynamic_community" in methods else None,
            "prompt_version": "evidence_synthesis_v1",
            "temperature": 0.1,
            "seed": seed,
            "top_k": top_k,
            "max_evidence_chunks": max_evidence_chunks,
            "max_context_chars": max_context_chars,
            "max_context_tokens_estimated": context_tokens,
            "token_estimator": "ceil(prompt_characters/3) + 120 system/framing allowance",
            "hardware_platform": platform.platform(),
            "retrieval_telemetry": telemetry,
            "retrieval_flags": retrieval_flags,
            "method_configuration": method_configuration,
            "ablation_override": ({"disabled_flag": ABLATION_FLAGS[method]} if method in ABLATION_FLAGS else None),
        },
        "predictions": predictions,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold_dataset", help="Validated, frozen gold dataset JSON")
    parser.add_argument("output", help="Output predictions JSON")
    parser.add_argument("--method", choices=sorted(METHODS), default="tarjan")
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--max-evidence-chunks", type=int, default=10)
    parser.add_argument("--max-context-chars", type=int, default=24000)
    parser.add_argument("--max-context-tokens", type=int)
    parser.add_argument("--seed", type=int, default=2026, help="Ollama generation seed for repeatable per-run sampling")
    parser.add_argument("--chunk-manifest", help="Optional frozen chunk manifest JSON for exact quote checks")
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.gold_dataset, args.chunk_manifest)
        output = asyncio.run(run_experiment(
            dataset, [args.method], top_k=args.top_k,
            max_evidence_chunks=args.max_evidence_chunks,
            max_context_chars=args.max_context_chars,
            max_context_tokens=args.max_context_tokens,
            seed=args.seed,
        ))
        Path(args.output).write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Wrote {len(output['predictions'])} predictions to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
