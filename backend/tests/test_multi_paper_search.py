"""Regression tests for provenance-preserving multi-paper graph retrieval."""
import pytest
import importlib

from backend.search.multi_paper_search import multi_paper_search
from backend.pipeline.neo4j_store import neo4j_store
from backend.core.llm_client import ollama_client, LLMCallLog

multi_paper_search_module = importlib.import_module("backend.search.multi_paper_search")


@pytest.mark.asyncio
async def test_multi_paper_query_builds_cross_paper_links_and_cites_evidence(monkeypatch):
    graphs = {
        "paper_a": {
            "nodes": [
                {"id": "rag", "name": "Retrieval Augmented Generation", "type": "Method", "description": "Combines retrieval with generation", "source_chunk_ids": ["a1"]},
                {"id": "dense", "name": "Dense Retrieval", "type": "Method", "description": "Retrieves semantically similar passages", "source_chunk_ids": ["a2"]},
            ],
            "edges": [{"source": "rag", "target": "dense", "type": "USES", "weight": 1.0, "source_chunk_ids": ["a1"]}],
        },
        "paper_b": {
            "nodes": [
                {"id": "rag2", "name": "Retrieval Augmented Generation", "type": "Method", "description": "Uses a retriever and generator", "source_chunk_ids": ["b1"]},
                {"id": "graph", "name": "Graph Retrieval", "type": "Method", "description": "Uses graph paths for evidence", "source_chunk_ids": ["b2"]},
            ],
            "edges": [{"source": "rag2", "target": "graph", "type": "USES", "weight": 1.0, "source_chunk_ids": ["b1"]}],
        },
    }
    chunks = {
        "paper_a": [
            {"chunk_id": "a1", "content": "Retrieval augmented generation combines external evidence with a language model.", "section": "Introduction", "page": 1},
            {"chunk_id": "a2", "content": "Dense retrieval selects semantically similar passages using vector representations.", "section": "Method", "page": 3},
        ],
        "paper_b": [
            {"chunk_id": "b1", "content": "Retrieval augmented generation can combine graph retrieval with evidence traversal.", "section": "Overview", "page": 2},
            {"chunk_id": "b2", "content": "Graph retrieval follows connected entity paths to support multi-hop questions.", "section": "Method", "page": 4},
        ],
    }
    monkeypatch.setattr(neo4j_store, "get_paper_graph", lambda pid, compressed=False: graphs.get(pid, {"nodes": [], "edges": []}))
    monkeypatch.setattr(neo4j_store, "get_chunks_by_ids", lambda pid, ids=None: [c for c in chunks.get(pid, []) if not ids or c["chunk_id"] in ids])

    async def fake_generate(prompt, **kwargs):
        assert "[E1]" in prompt
        assert "paper_a" in prompt or "Paper A" in prompt
        assert "paper_b" in prompt or "Paper B" in prompt
        return "The papers connect retrieval-augmented generation with dense and graph retrieval [E1, E2].\n\n### Graph Connections\n\n- Invented relation A → B", LLMCallLog(call_type="generate", model="test", total_tokens=42, status="success")

    monkeypatch.setattr(ollama_client, "generate", fake_generate)
    result = await multi_paper_search.search(
        question="How does retrieval augmented generation connect dense retrieval and graph retrieval for multi-hop evidence?",
        paper_ids=["paper_a", "paper_b"],
        paper_titles={"paper_a": "Paper A", "paper_b": "Paper B"},
    )
    assert result["status"] == "ok"
    assert result["cross_paper_links"] >= 2
    assert {item["paper_id"] for item in result["evidence"]} == {"paper_a", "paper_b"}
    assert "[E1" in result["answer"]
    assert "Graph Connections" not in result["answer"]
    assert "No validated, provenance-backed relations" not in result["answer"]
    assert "Invented relation A" not in result["answer"]
    assert any(step["action"] == "SELECT" for step in result["trace"]["steps"])
    assert any(step["action"] == "SELECT_EDGE" for step in result["trace"]["steps"])


@pytest.mark.asyncio
async def test_multi_paper_query_reports_missing_papers_without_fabricating_graph(monkeypatch):
    monkeypatch.setattr(neo4j_store, "get_paper_graph", lambda pid, compressed=False: {"nodes": [], "edges": []})
    result = await multi_paper_search.search("compare methods", ["not_indexed"])
    assert result["status"] == "no_indexed_graph"
    assert result["missing_paper_ids"] == ["not_indexed"]
    assert result["evidence"] == []
    assert result["total_llm_calls"] == 0


@pytest.mark.asyncio
async def test_multi_paper_token_budget_blocks_oversized_evidence_before_llm(monkeypatch):
    monkeypatch.setattr(neo4j_store, "get_paper_graph", lambda *args, **kwargs: {
        "nodes": [{"id": "gcn", "name": "GraphSAGE aggregation", "type": "Method", "source_chunk_ids": ["c1"]}],
        "edges": [],
    })
    monkeypatch.setattr(neo4j_store, "get_chunks_by_ids", lambda *args, **kwargs: [{
        "chunk_id": "c1", "section": "Method", "page": 1,
        "content": "GraphSAGE aggregation " + ("detail " * 3000),
    }])
    async def forbidden_generate(*args, **kwargs):
        raise AssertionError("LLM must not be called when no evidence fits the budget")
    monkeypatch.setattr(ollama_client, "generate", forbidden_generate)

    result = await multi_paper_search.search(
        "How does GraphSAGE aggregation work?", ["paper_a"], max_context_tokens=400,
    )
    assert result["status"] == "context_budget_exceeded"
    assert result["evidence"] == []
    assert result["retrieval_trace"]["estimated_prompt_tokens"] <= 400
    assert "context_budget_exceeded" in result["retrieval_trace"]["fallback_modes"]


@pytest.mark.asyncio
async def test_multi_paper_token_budget_records_prompt_usage(monkeypatch):
    monkeypatch.setattr(neo4j_store, "get_paper_graph", lambda *args, **kwargs: {
        "nodes": [{"id": "gcn", "name": "GraphSAGE aggregation", "type": "Method", "source_chunk_ids": ["c1"]}],
        "edges": [],
    })
    content = "GraphSAGE aggregation combines sampled neighborhood information."
    monkeypatch.setattr(neo4j_store, "get_chunks_by_ids", lambda *args, **kwargs: [{
        "chunk_id": "c1", "section": "Method", "page": 1, "content": content,
    }])
    async def fake_generate(prompt, **kwargs):
        assert content in prompt
        return "It combines neighborhood information [E1].", LLMCallLog(call_type="generate", model="test", total_tokens=30, status="success")
    monkeypatch.setattr(ollama_client, "generate", fake_generate)

    result = await multi_paper_search.search(
        "How does GraphSAGE aggregation work?", ["paper_a"], max_context_tokens=500,
    )
    assert result["status"] == "ok"
    trace = result["retrieval_trace"]
    assert trace["estimated_prompt_tokens"] <= trace["context_tokens_budget"] == 500
    assert trace["token_budget_utilization"] <= 1.0


@pytest.mark.asyncio
async def test_reviewed_bridge_connects_disconnected_paper_graphs_with_verified_path(monkeypatch):
    graphs = {
        "paper_a": {"nodes": [{"id": "a", "name": "Treatment A", "type": "Method", "description": "Original treatment", "source_chunk_ids": ["a1"]}], "edges": []},
        "paper_b": {"nodes": [{"id": "b", "name": "Treatment B", "type": "Method", "description": "Extended treatment", "source_chunk_ids": ["b1"]}], "edges": []},
    }
    chunks = {
        "paper_a": [{"chunk_id": "a1", "content": "Treatment A proposes the retrieval method.", "page": 1}],
        "paper_b": [{"chunk_id": "b1", "content": "Treatment B extends the retrieval method proposed earlier.", "page": 2}],
    }
    monkeypatch.setattr(neo4j_store, "get_paper_graph", lambda pid, compressed=False: graphs.get(pid, {"nodes": [], "edges": []}))
    monkeypatch.setattr(neo4j_store, "get_chunks_by_ids", lambda pid, ids=None: [c for c in chunks.get(pid, []) if not ids or c["chunk_id"] in ids])
    monkeypatch.setattr(multi_paper_search_module.settings, "ENABLE_CROSS_PAPER_LINKS", True)
    monkeypatch.setattr(multi_paper_search_module, "load_bridge_records", lambda _path: ([{
        "bridge_id": "a-extends-b",
        "source_paper_id": "paper_a",
        "source_node_id": "a",
        "target_paper_id": "paper_b",
        "target_node_id": "b",
        "relation_type": "EXTENDS",
        "relation_description": "Paper B extends the method in paper A.",
        "evidence": [
            {"paper_id": "paper_a", "chunk_id": "a1", "quote": chunks["paper_a"][0]["content"]},
            {"paper_id": "paper_b", "chunk_id": "b1", "quote": chunks["paper_b"][0]["content"]},
        ],
        "reviewer_ids": ["reviewer_1", "reviewer_2"],
        "validation_status": "human_validated",
    }], None))

    async def fake_generate(prompt, **kwargs):
        assert "Treatment A proposes" in prompt
        assert "Treatment B extends" in prompt
        return "Paper B extends the earlier method [E1, E2].", LLMCallLog(call_type="generate", model="test", total_tokens=22, status="success")

    monkeypatch.setattr(ollama_client, "generate", fake_generate)
    result = await multi_paper_search.search(
        question="How does Treatment A extend Treatment B?",
        paper_ids=["paper_a", "paper_b"],
    )

    assert result["status"] == "ok"
    assert result["reviewed_cross_paper_bridge_count"] == 1
    assert result["retrieval_trace"]["reviewed_cross_paper_bridge_count"] == 1
    assert result["retrieval_trace"]["verified_graph_relations"][0]["type"] == "EXTENDS"
    assert any(edge.get("cross_paper") and edge.get("type") == "EXTENDS" for edge in result["original_graph"]["edges"])
