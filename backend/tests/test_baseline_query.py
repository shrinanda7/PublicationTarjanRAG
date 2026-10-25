import pytest

import backend.search.baseline_query as baseline_query_module
from backend.core.llm_client import LLMCallLog
from backend.pipeline.neo4j_store import neo4j_store


@pytest.mark.asyncio
async def test_bm25_baseline_query_retrieves_evidence_and_uses_shared_synthesis(monkeypatch):
    chunks = {
        "paper_a": [{"chunk_id": "c1", "content": "BM25 ranks lexical matches.", "page": 2}],
        "paper_b": [{"chunk_id": "c2", "content": "Dense embeddings rank semantic matches.", "page": 4}],
    }
    monkeypatch.setattr(neo4j_store, "get_chunks_by_ids", lambda pid, ids=None: chunks.get(pid, []))

    def fake_rank(question, candidates):
        assert question == "Compare retrieval methods"
        assert {item["paper_id"] for item in candidates} == {"paper_a", "paper_b"}
        return {
            "method": "bm25",
            "parameters": {"k1": 1.2, "b": 0.75},
            "ranked": [
                {**candidates[0], "score": 1.0, "rank": 1},
                {**candidates[1], "score": 0.5, "rank": 2},
            ],
            "telemetry": {"retrieval_latency_ms": 2.0, "embedding_calls": 0},
        }

    monkeypatch.setattr(baseline_query_module, "rank_bm25", fake_rank)

    async def fake_synthesis(question, selected, **kwargs):
        assert len(selected) == 2
        assert kwargs["conversation_context"] == "prior context"
        return "BM25 is lexical and dense is semantic [E1, E2].", LLMCallLog(
            call_type="generate", model="test", total_tokens=20,
            prompt_tokens=14, completion_tokens=6, status="success",
        ), "prompt"

    monkeypatch.setattr(baseline_query_module, "synthesize_evidence", fake_synthesis)
    result = await baseline_query_module.baseline_query.search(
        method="bm25",
        question="Compare retrieval methods",
        paper_ids=["paper_a", "paper_b"],
        paper_titles={"paper_a": "Paper A", "paper_b": "Paper B"},
        conversation_context="prior context",
    )

    assert result["status"] == "ok"
    assert result["mode"] == "bm25"
    assert [item["paper_id"] for item in result["evidence"]] == ["paper_a", "paper_b"]
    assert [step["chunk_id"] for step in result["trace"]["steps"]] == ["c1", "c2"]
    assert result["retrieval_trace"]["budget"]["context_tokens_budget"] > 0
    assert result["prompt_tokens"] == 14


@pytest.mark.asyncio
async def test_dense_baseline_returns_clear_retrieval_error_when_embeddings_are_unavailable(monkeypatch):
    monkeypatch.setattr(neo4j_store, "get_chunks_by_ids", lambda *args, **kwargs: [
        {"chunk_id": "c1", "content": "A source passage."},
    ])

    async def fail_embedding(*args, **kwargs):
        raise RuntimeError("embedding service unavailable")

    monkeypatch.setattr(baseline_query_module, "rank_dense", fail_embedding)
    result = await baseline_query_module.baseline_query.search(
        method="dense", question="A question", paper_ids=["paper_a"],
    )

    assert result["status"] == "retrieval_error"
    assert result["mode"] == "dense"
    assert "embedding service unavailable" in result["answer"]
    assert result["evidence"] == []
