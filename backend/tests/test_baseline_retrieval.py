import pytest

from backend.core.llm_client import LLMCallLog
from backend.evaluation.baseline_retrieval import rank_bm25, rank_dense, rank_hybrid


DOCS = [
    {"paper_id": "p1", "chunk_id": "c1", "content": "graph retrieval uses graph paths and graph traversal"},
    {"paper_id": "p2", "chunk_id": "c2", "content": "dense retrieval ranks semantic document vectors"},
    {"paper_id": "p3", "chunk_id": "c3", "content": "unrelated optimization details"},
]


def test_bm25_is_deterministic_and_ignores_nonmatching_documents():
    first = rank_bm25("graph retrieval", DOCS)
    second = rank_bm25("graph retrieval", list(reversed(DOCS)))
    assert [item["chunk_id"] for item in first["ranked"]] == ["c1", "c2"]
    assert [item["chunk_id"] for item in first["ranked"]] == [item["chunk_id"] for item in second["ranked"]]
    assert first["parameters"] == {"k1": 1.2, "b": 0.75}
    assert first["telemetry"]["retrieval_latency_ms"] >= 0


@pytest.mark.asyncio
async def test_dense_baseline_uses_cosine_and_records_embedding_cost():
    vectors = {
        "graph retrieval": [1.0, 0.0],
        DOCS[0]["content"]: [0.8, 0.2],
        DOCS[1]["content"]: [0.0, 1.0],
        DOCS[2]["content"]: [-1.0, 0.0],
    }

    async def embed(text, **kwargs):
        return vectors[text], LLMCallLog(call_type="embedding", model="test-embed", total_tokens=4, status="success")

    result = await rank_dense("graph retrieval", DOCS, embedder=embed)
    assert result["ranked"][0]["chunk_id"] == "c1"
    assert result["ranked"][0]["score"] > result["ranked"][1]["score"]
    assert result["telemetry"]["embedding_calls"] == 4
    assert result["telemetry"]["embedding_tokens"] == 16
    assert result["telemetry"]["retrieval_latency_ms"] >= result["telemetry"]["embedding_latency_ms"]


@pytest.mark.asyncio
async def test_hybrid_uses_equal_weight_rrf_not_raw_incomparable_scores():
    vectors = {
        "graph retrieval": [1.0, 0.0],
        DOCS[0]["content"]: [0.0, 1.0],
        DOCS[1]["content"]: [1.0, 0.0],
        DOCS[2]["content"]: [-1.0, 0.0],
    }

    async def embed(text, **kwargs):
        return vectors[text], LLMCallLog(call_type="embedding", model="test-embed", total_tokens=2, status="success")

    result = await rank_hybrid("graph retrieval", DOCS, embedder=embed)
    assert result["method"] == "hybrid_rrf"
    assert result["parameters"] == {"sparse_weight": 1.0, "dense_weight": 1.0, "rrf_k": 60}
    assert [item["chunk_id"] for item in result["ranked"][:2]] == ["c1", "c2"]
    assert {item["chunk_id"] for item in result["ranked"]} == {"c1", "c2", "c3"}
    assert result["telemetry"]["embedding_calls"] == 4
