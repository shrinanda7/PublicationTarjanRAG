import pytest

import backend.search.query_router as query_router_module


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["ours", "local"])
async def test_core_graph_modes_skip_community_report_generation(monkeypatch, mode):
    graph = {
        "nodes": [{"id": "n1", "name": "Method", "type": "Method", "description": "A method", "source_chunk_ids": ["c1"]}],
        "edges": [],
    }
    monkeypatch.setattr(query_router_module.neo4j_store, "get_paper_graph", lambda paper_id: graph)

    async def unexpected_report_generation(*args, **kwargs):
        raise AssertionError("core graph modes must not generate hierarchical reports")

    monkeypatch.setattr(query_router_module.report_generator, "generate_reports_for_hierarchy", unexpected_report_generation)
    calls = []

    async def fake_search(**kwargs):
        calls.append(kwargs)
        assert kwargs["question"] == "What method is described?"
        assert kwargs["conversation_context"] == "Prior turn for reference only."
        if mode == "ours":
            assert kwargs["communities"] == {}
        return {"mode": mode, "answer": "retrieved", "trace": {"steps": []}}

    engine = query_router_module.ours_search if mode == "ours" else query_router_module.local_search
    monkeypatch.setattr(engine, "search", fake_search)

    result = await query_router_module.query_router.execute_query(
        question="What method is described?",
        paper_id="p1",
        paper_title="Paper One",
        mode=mode,
        conversation_context="Prior turn for reference only.",
    )

    assert result["mode"] == mode
    assert len(calls) == 1
