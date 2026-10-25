from backend.search.evidence_synthesis import (
    build_evidence_prompt,
    estimate_prompt_tokens,
    select_budgeted_chunks,
)


def test_conversation_context_is_labeled_as_reference_and_not_evidence():
    prompt = build_evidence_prompt(
        "What did it achieve?",
        [{"paper_id": "p1", "paper_title": "Paper", "chunk_id": "c1", "content": "The model achieved 91%."}],
        "Previous question: What model?\nPrevious answer: Model A.",
    )

    assert "RECENT CONVERSATION CONTEXT" in prompt
    assert "it is not evidence" in prompt
    assert "Previous answer: Model A." in prompt
    assert "CURRENT QUESTION:\nWhat did it achieve?" in prompt
    assert "[E1] Paper: Paper" in prompt


def test_conversation_context_is_bounded_and_counted_in_prompt_budget():
    oversized = "x" * 5000
    without_history = estimate_prompt_tokens("Question?", [])
    with_history = estimate_prompt_tokens("Question?", [], oversized)

    assert with_history > without_history
    assert len(build_evidence_prompt("Question?", [], oversized)) <= len(build_evidence_prompt("Question?", [], "x" * 4000))
    selected, budget = select_budgeted_chunks(
        "Question?", [{"paper_id": "p1", "chunk_id": "c1", "content": "Evidence."}],
        max_context_tokens=400,
        conversation_context=oversized,
    )
    assert selected == []
    assert budget["estimated_prompt_tokens"] > 400

