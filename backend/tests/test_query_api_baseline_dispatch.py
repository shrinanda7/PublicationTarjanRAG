import pytest

import backend.main as main_module
from backend.main import MultiPaperQueryRequest


@pytest.mark.asyncio
async def test_multi_paper_api_dispatches_baseline_methods(monkeypatch):
    calls = []

    async def fake_search(**kwargs):
        calls.append(kwargs)
        return {"status": "ok", "mode": kwargs["method"], "answer": "test answer"}

    monkeypatch.setattr(main_module.baseline_query, "search", fake_search)
    request = MultiPaperQueryRequest(
        paper_ids=["paper_a"],
        question="What does the paper say?",
        mode="bm25",
    )

    result = await main_module.execute_multi_paper_query(request)

    assert result["status"] == "ok"
    assert calls[0]["method"] == "bm25"
    assert calls[0]["paper_ids"] == ["paper_a"]
