"""Shared evidence-only answer generation for Tarjan-RAG and retrieval baselines."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

from backend.config import settings
from backend.core.llm_client import LLMCallLog, ollama_client


SYSTEM_PROMPT = (
    "You are a careful research assistant. Ground every factual claim in supplied source chunks, "
    "cite evidence IDs, distinguish inference from evidence, and state uncertainty."
)

PROMPT_INSTRUCTIONS = (
    "Answer the exact research question in about 150–250 words when the evidence supports that depth; stay shorter for simple questions and never pad. Use 2–4 clear paragraphs and up to three compact evidence bullets if useful. "
    "For cross-paper questions, name what the papers concretely share (topic, method, data, or result) and distinguish topical similarity from a demonstrated direct scholarly relationship. "
    "Separate each paper's own methods and results from methods mentioned in related work or background; never attribute cited prior work to the current paper's authors. "
    "For every substantive claim, cite evidence IDs exactly like [E1] or [E2, E4]. Never invent a result, citation, paper detail, or causal relationship. "
    "If evidence from a selected paper is absent, say so briefly; do not imply that the paper itself has no relevant content. "
    "Do not add headings such as Multi-hop Synthesis, Key Takeaway, Agreement, Disagreement, Uncertainty, or Graph Connections. Do not claim a graph path or relation was verified.\n\n"
)


def build_evidence_prompt(
    question: str,
    chunks: Sequence[Dict[str, Any]],
    conversation_context: str = "",
) -> str:
    blocks = []
    for index, chunk in enumerate(chunks, 1):
        title = str(chunk.get("paper_title", chunk.get("paper_id", "unknown")))
        paper_id = str(chunk.get("paper_id", "unknown"))
        chunk_id = str(chunk.get("chunk_id", "unknown"))
        section = chunk.get("section", "unknown")
        page = chunk.get("page", "unknown")
        content = str(chunk.get("content", ""))
        blocks.append(
            f"[E{index}] Paper: {title} (paper_id={paper_id}); Chunk={chunk_id}; "
            f"Section={section}; Page={page}\n{content}"
        )
    history = str(conversation_context or "").strip()[:4000]
    context_section = (
        f"RECENT CONVERSATION CONTEXT (use only to resolve references in the current question; it is not evidence):\n{history}\n\n"
        if history else ""
    )
    return (
        PROMPT_INSTRUCTIONS
        + context_section
        + f"CURRENT QUESTION:\n{question}\n\nEVIDENCE:\n"
        + "\n\n".join(blocks)
    )


def estimate_prompt_tokens(
    question: str,
    chunks: Sequence[Dict[str, Any]],
    conversation_context: str = "",
) -> int:
    """Character-based upper estimate; replace with the selected model tokenizer for publication runs."""
    return (len(build_evidence_prompt(question, chunks, conversation_context)) + 2) // 3 + 120


def select_budgeted_chunks(
    question: str,
    ranked_chunks: Sequence[Dict[str, Any]],
    *,
    max_evidence_chunks: int = 10,
    max_context_chars: int = 24000,
    max_context_tokens: int | None = None,
    conversation_context: str = "",
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Greedily accept ranked chunks under shared character and token estimates."""
    token_budget = max(0, int(max_context_tokens if max_context_tokens is not None else settings.MAX_TOKEN_BUDGET))
    char_budget = max(0, int(max_context_chars))
    chunk_budget = max(0, int(max_evidence_chunks))
    selected: List[Dict[str, Any]] = []
    seen = set()
    used_chars = 0
    fixed_tokens = estimate_prompt_tokens(question, [], conversation_context)
    for raw in ranked_chunks:
        if len(selected) >= chunk_budget:
            break
        key = (str(raw.get("paper_id", "")), str(raw.get("chunk_id", "")))
        if not all(key) or key in seen:
            continue
        content = str(raw.get("content", ""))
        if not content:
            continue
        candidate = [*selected, raw]
        if used_chars + len(content) > char_budget:
            continue
        if estimate_prompt_tokens(question, candidate, conversation_context) > token_budget:
            continue
        selected.append(dict(raw))
        seen.add(key)
        used_chars += len(content)
    used_tokens = estimate_prompt_tokens(question, selected, conversation_context)
    return selected, {
        "evidence_content_chars_used": used_chars,
        "context_chars_budget": char_budget,
        "context_tokens_budget": token_budget,
        "evidence_chunk_budget": chunk_budget,
        "fixed_prompt_tokens_estimated": fixed_tokens,
        "estimated_prompt_tokens": used_tokens,
        "token_budget_utilization": used_tokens / token_budget if token_budget else None,
        "token_estimator": "ceil(prompt_characters/3) + 120 system/framing allowance",
    }


async def synthesize_evidence(
    question: str,
    chunks: Sequence[Dict[str, Any]],
    *,
    seed: int | None = None,
    conversation_context: str = "",
) -> Tuple[str, LLMCallLog, str]:
    """Generate with one shared prompt/model/temperature across retrieval methods."""
    prompt = build_evidence_prompt(question, chunks, conversation_context)
    answer, log = await ollama_client.generate(
        prompt=prompt,
        model=settings.OLLAMA_LARGE_MODEL,
        system=SYSTEM_PROMPT,
        temperature=0.1,
        seed=seed,
    )
    return answer, log, prompt
