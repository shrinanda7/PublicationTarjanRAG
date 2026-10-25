import pytest

from backend.core.llm_client import LLMCallLog
from backend.config import settings
from backend.evaluation import experiment_runner


def test_selected_original_paths_are_directed_and_respect_selected_quotient_edges():
    result = {
        "selected_node_ids": ["A", "B"],
        "compressed_graph": {"nodes": [
            {"id": "A", "member_node_ids": ["a1", "a2"]},
            {"id": "B", "member_node_ids": ["b1"]},
            {"id": "C", "member_node_ids": ["c1"]},
        ]},
        "selected_edges": [{"source": "A", "target": "B"}],
        "original_graph": {"edges": [
            {"source": "a1", "target": "a2"},
            {"source": "a2", "target": "a1"},
            {"source": "a2", "target": "b1"},
            {"source": "b1", "target": "c1"},
        ]},
    }

    paths = experiment_runner._selected_original_paths(result)

    assert ["a1", "a2"] in paths
    assert ["a2", "b1"] in paths
    assert ["a1", "a2", "b1"] in paths
    assert all("c1" not in path for path in paths)


@pytest.mark.asyncio
async def test_local_graph_runner_uses_shared_synthesis_and_exports_citations(monkeypatch):
    dataset = {
        "corpus_version": "test-v1",
        "corpus_papers": [{"paper_id": "p1", "title": "Paper One"}],
        "questions": [{"question_id": "q1", "paper_ids": ["p1"], "question": "What is the result?"}],
    }

    monkeypatch.setattr(
        experiment_runner.neo4j_store,
        "get_chunks_by_ids",
        lambda paper_id, chunk_ids: [{"chunk_id": "c1", "content": "The result is 42."}],
    )

    async def local_retrieve(question, paper_id, paper_title, **kwargs):
        assert kwargs["generate_answer"] is False
        return {
            "status": "retrieved",
            "retrieved_evidence": [{
                "paper_id": paper_id,
                "chunk_id": "c1",
                "content": "The result is 42.",
                "score": 1.0,
            }],
            "retrieval_trace": {"selection_mode": "lexical_graph_neighborhood_retrieval_only"},
        }

    synthesis_calls = []

    async def synthesize(question, chunks, *, seed=None):
        assert seed == 2026
        synthesis_calls.append((question, chunks))
        return (
            "The result is 42 [E1].",
            LLMCallLog(call_type="generate", model="test-model", total_tokens=10, status="success"),
            "matched prompt",
        )

    monkeypatch.setattr(experiment_runner.local_search, "search", local_retrieve)
    monkeypatch.setattr(experiment_runner, "synthesize_evidence", synthesize)
    result = await experiment_runner.run_experiment(dataset, ["local"])

    prediction = result["predictions"][0]
    assert prediction["status"] == "ok"
    assert prediction["retrieved_evidence"] == ["p1::c1"]
    assert prediction["citations"] == ["p1::c1"]
    assert len(synthesis_calls) == 1
    assert result["run"]["prompt_version"] == "evidence_synthesis_v1"


@pytest.mark.asyncio
@pytest.mark.parametrize("method,flag", sorted(experiment_runner.ABLATION_FLAGS.items()))
async def test_ablation_runner_changes_one_flag_and_restores_it(monkeypatch, method, flag):
    dataset = {
        "corpus_version": "test-v1",
        "corpus_papers": [{"paper_id": "p1", "title": "Paper One"}],
        "questions": [{"question_id": "q1", "paper_ids": ["p1"], "question": "What is the result?"}],
    }
    monkeypatch.setattr(
        experiment_runner.neo4j_store,
        "get_chunks_by_ids",
        lambda paper_id, chunk_ids: [{"chunk_id": "c1", "content": "The result is 42."}],
    )
    original = {name: getattr(settings, name) for name in experiment_runner.ABLATION_FLAGS.values()}
    observed = []

    async def search(*args, **kwargs):
        observed.append({name: getattr(settings, name) for name in original})
        return {
            "status": "ok", "answer": "The result is 42 [E1].", "llm_status": "success",
            "evidence": [{"evidence_id": "E1", "paper_id": "p1", "chunk_id": "c1", "content": "The result is 42."}],
            "total_llm_calls": 1, "total_tokens": 10,
        }

    monkeypatch.setattr(experiment_runner.multi_paper_search, "search", search)
    result = await experiment_runner.run_experiment(dataset, [method])

    expected = {name: True for name in original}
    expected[flag] = False
    assert observed == [expected]
    assert {name: getattr(settings, name) for name in original} == original
    assert result["run"]["ablation_override"] == {"disabled_flag": flag}
    assert result["run"]["retrieval_flags"] == expected
    assert result["predictions"][0]["status"] == "ok"


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["static_community", "dynamic_community"])
async def test_community_runner_recovers_selected_source_chunks(monkeypatch, method):
    dataset = {
        "corpus_version": "test-v1",
        "corpus_papers": [{"paper_id": "p1", "title": "Paper One"}],
        "questions": [{"question_id": "q1", "paper_ids": ["p1"], "question": "What is attention?"}],
    }
    graph = {
        "nodes": [{
            "id": "e1", "name": "Attention", "type": "Method",
            "description": "Self-attention mechanism", "source_chunk_ids": ["c1"],
        }],
        "edges": [],
    }
    chunk = {"chunk_id": "c1", "content": "Attention uses self-attention.", "section": "Method", "page": 2}
    monkeypatch.setattr(experiment_runner.neo4j_store, "get_paper_graph", lambda paper_id, compressed=False: graph)
    monkeypatch.setattr(experiment_runner.neo4j_store, "get_chunks_by_ids", lambda paper_id, chunk_ids: [chunk])

    async def select_communities(question, paper_id, paper_title, communities, **kwargs):
        selected = [community for community in communities.values() if community.level == 1]
        return {
            "status": "selected",
            "selected_reports": [community.id for community in selected],
            "trace": {
                "ratings": {community.id: 90.0 for community in selected},
                "llm_statuses": ["success"], "total_llm_calls": 1, "total_tokens": 5,
            },
        }

    monkeypatch.setattr(experiment_runner.dynamic_search, "search", select_communities)

    async def synthesize(question, chunks, *, seed=None):
        assert seed == 2026
        assert any(item["chunk_id"] == "c1" for item in chunks)
        return (
            "Attention uses self-attention [E1].",
            LLMCallLog(call_type="generate", model="test-model", total_tokens=10, status="success"),
            "matched prompt",
        )

    monkeypatch.setattr(experiment_runner, "synthesize_evidence", synthesize)
    result = await experiment_runner.run_experiment(dataset, [method])
    prediction = result["predictions"][0]

    assert prediction["status"] == "ok"
    assert prediction["retrieved_evidence"] == ["p1::c1"]
    assert prediction["citations"] == ["p1::c1"]
    assert prediction["selected_communities"]["p1"]
    if method == "dynamic_community":
        assert prediction["retrieval_llm_calls"] == 1
        assert result["run"]["selection_model"]


@pytest.mark.asyncio
async def test_runner_treats_missing_indexed_chunks_as_operational_error(monkeypatch):
    dataset = {
        "corpus_version": "test-v1",
        "corpus_papers": [{"paper_id": "p1", "title": "Paper One"}],
        "questions": [{"question_id": "q1", "paper_ids": ["p1"], "question": "What is the result?"}],
    }
    monkeypatch.setattr(experiment_runner.neo4j_store, "get_chunks_by_ids", lambda paper_id, chunk_ids: [])

    result = await experiment_runner.run_experiment(dataset, ["bm25"])
    prediction = result["predictions"][0]

    assert prediction["status"] == "error"
    assert "No indexed source chunks" in prediction["error"]
