"""Shared evidence synthesis for the chunk-retrieval baselines exposed in the UI."""
from __future__ import annotations

import time
from typing import Any, Dict, List

from backend.config import settings
from backend.evaluation.baseline_retrieval import rank_bm25, rank_dense, rank_hybrid
from backend.pipeline.neo4j_store import neo4j_store
from backend.search.evidence_synthesis import select_budgeted_chunks, synthesize_evidence


BASELINE_METHODS = {"bm25", "dense", "hybrid"}


class BaselineQuery:
    async def search(
        self,
        *,
        method: str,
        question: str,
        paper_ids: List[str],
        paper_titles: Dict[str, str] | None = None,
        max_evidence_chunks: int = 10,
        max_context_chars: int = 24000,
        max_context_tokens: int | None = None,
        conversation_context: str = "",
    ) -> Dict[str, Any]:
        started = time.perf_counter()
        if method not in BASELINE_METHODS:
            return self._error("unsupported_baseline", f"Unknown retrieval baseline: {method}", started)

        paper_titles = paper_titles or {}
        chunks: List[Dict[str, Any]] = []
        missing_papers: List[str] = []
        for paper_id in dict.fromkeys(str(pid).strip() for pid in paper_ids if str(pid).strip()):
            paper_chunks = neo4j_store.get_chunks_by_ids(paper_id, []) or []
            usable = [chunk for chunk in paper_chunks if chunk.get("chunk_id") and chunk.get("content")]
            if not usable:
                missing_papers.append(paper_id)
                continue
            for chunk in usable:
                chunks.append({
                    **chunk,
                    "paper_id": paper_id,
                    "paper_title": paper_titles.get(paper_id, paper_id),
                })

        if not chunks:
            return self._error(
                "no_indexed_chunks",
                "No indexed source chunks are available for the selected papers.",
                started,
                mode=method,
                missing_paper_ids=missing_papers,
            )

        try:
            if method == "bm25":
                ranking = rank_bm25(question, chunks)
            elif method == "dense":
                ranking = await rank_dense(question, chunks)
            else:
                ranking = await rank_hybrid(question, chunks)
        except Exception as exc:
            return self._error(
                "retrieval_error",
                f"{method} retrieval failed: {type(exc).__name__}: {exc}",
                started,
                mode=method,
                missing_paper_ids=missing_papers,
            )

        max_tokens = max_context_tokens if max_context_tokens is not None else settings.MAX_TOKEN_BUDGET
        selected, budget = select_budgeted_chunks(
            question,
            ranking.get("ranked", []),
            max_evidence_chunks=max_evidence_chunks,
            max_context_chars=max_context_chars,
            max_context_tokens=max_tokens,
            conversation_context=conversation_context,
        )
        trace = {
            "method": method,
            "ranker": ranking.get("method", method),
            "ranker_parameters": ranking.get("parameters", {}),
            "selected_evidence": [
                {"paper_id": item["paper_id"], "chunk_id": item["chunk_id"], "rank": item.get("rank"), "score": item.get("score")}
                for item in selected
            ],
            "budget": budget,
            "retrieval_telemetry": ranking.get("telemetry", {}),
            "missing_paper_ids": missing_papers,
        }
        if not selected:
            telemetry = ranking.get("telemetry", {})
            return {
                "status": "no_evidence",
                "mode": method,
                "answer": "No relevant source chunks were retrieved within the configured context budget.",
                "paper_ids": paper_ids,
                "missing_paper_ids": missing_papers,
                "evidence": [],
                "retrieval_trace": trace,
                "trace": {"mode": method, "steps": [], "retrieval": trace, "total_llm_calls": 0, "total_tokens": 0},
                "total_llm_calls": 0,
                "total_tokens": 0,
                "embedding_calls": int(telemetry.get("embedding_calls", 0)),
                "embedding_tokens": int(telemetry.get("embedding_tokens", 0)),
                "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            }

        answer, log, _ = await synthesize_evidence(
            question,
            selected,
            conversation_context=conversation_context,
        )
        llm_ok = log.status == "success" and bool(answer.strip())
        if not llm_ok:
            answer = "Answer generation failed. The retrieved evidence is shown for inspection; no answer has been fabricated."
        evidence = [
            {
                "evidence_id": f"E{index}",
                "paper_id": item["paper_id"],
                "paper_title": item.get("paper_title", item["paper_id"]),
                "chunk_id": item["chunk_id"],
                "section": item.get("section"),
                "page": item.get("page"),
                "content": item["content"],
                "score": item.get("score"),
                "rank": item.get("rank"),
            }
            for index, item in enumerate(selected, 1)
        ]
        steps = [
            {
                "action": "EVIDENCE",
                "paper_id": item["paper_id"],
                "chunk_id": item["chunk_id"],
                "rank": item.get("rank"),
                "score": item.get("score"),
            }
            for item in evidence
        ]
        telemetry = ranking.get("telemetry", {})
        trace["synthesis"] = {
            "status": log.status,
            "model": log.model,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "latency_ms": log.latency_ms,
        }
        return {
            "status": "ok" if llm_ok else "llm_error",
            "mode": method,
            "answer": answer,
            "paper_ids": paper_ids,
            "missing_paper_ids": missing_papers,
            "evidence": evidence,
            "retrieval_trace": trace,
            "trace": {
                "mode": method,
                "steps": steps,
                "retrieval": trace,
                "total_llm_calls": 1 if llm_ok else 0,
                "total_tokens": int(log.total_tokens or 0),
                "latency_ms": log.latency_ms,
            },
            "embedding_calls": telemetry.get("embedding_calls", 0),
            "embedding_tokens": telemetry.get("embedding_tokens", 0),
            "embedding_latency_ms": telemetry.get("embedding_latency_ms", 0.0),
            "retrieval_latency_ms": telemetry.get("retrieval_latency_ms", 0.0),
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_llm_calls": 1 if llm_ok else 0,
            "total_tokens": int(telemetry.get("embedding_tokens", 0)) + int(log.total_tokens or 0),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            "llm_status": log.status,
            "engine": f"{method.upper()} + shared evidence synthesis",
        }

    @staticmethod
    def _error(status: str, message: str, started: float, **extra: Any) -> Dict[str, Any]:
        return {
            "status": status,
            "mode": extra.pop("mode", "baseline"),
            "answer": message,
            "evidence": [],
            "trace": {"steps": [], "total_llm_calls": 0, "total_tokens": 0},
            "total_llm_calls": 0,
            "total_tokens": 0,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
            **extra,
        }


baseline_query = BaselineQuery()
