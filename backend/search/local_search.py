"""Lexical local-graph baseline with source-chunk recovery and budgeted synthesis."""
import math
import re
import time
from typing import Any, Dict, List, Set, Tuple

from backend.config import settings
from backend.core.llm_client import ollama_client
from backend.pipeline.neo4j_store import neo4j_store
from backend.search.traversal_tracer import TraversalTrace


STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "what", "how", "why",
    "does", "do", "of", "in", "on", "for", "and", "or", "to", "with",
    "by", "this", "that", "it", "its", "from", "paper", "explain", "describe",
}


def _terms(text: str) -> Set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", str(text or "").lower())
        if len(token) > 1 and token not in STOP_WORDS
    }


def _estimate_tokens(text: str) -> int:
    """Conservative character approximation; not a model-specific tokenizer."""
    return (len(text) + 2) // 3


class LocalSearch:
    """Match lexical entity seeds, expand their local graph, then recover chunks."""

    PROMPT = """You are answering a specific research question about '{paper_title}'.

Recent conversation context (reference only, not evidence):
{conversation_context}

Current question: {question}

Local graph context (extracted relations are unreviewed):
{graph_context}

Retrieved source chunks:
{chunk_context}

Use only the source chunks as evidence for factual claims. Graph relations are navigation hints, not independently verified facts. Cite source chunks exactly with [Source: paper_id::chunk_id]. If the sources do not answer the question, state what is missing."""

    async def search(
        self,
        question: str,
        paper_id: str,
        paper_title: str,
        k_hops: int = 2,
        top_k_seeds: int = 4,
        top_k_chunks: int = 5,
        generate_answer: bool = True,
        conversation_context: str = "",
    ) -> Dict[str, Any]:
        start_time = time.time()
        trace = TraversalTrace(mode="local")
        paper_data = neo4j_store.get_paper_graph(paper_id) or {}
        nodes = paper_data.get("nodes", [])
        edges = paper_data.get("edges", [])
        chunks = paper_data.get("chunks") or neo4j_store.get_chunks_by_ids(paper_id, [])

        if not nodes:
            return self._finish(trace, start_time, "no_indexed_graph", f"No indexed knowledge graph found for paper '{paper_title}'.")

        query_terms = _terms(question)
        node_scores: List[Tuple[float, Dict[str, Any]]] = []
        for node in nodes:
            name_score = len(query_terms & _terms(node.get("name", "")))
            description_score = len(query_terms & _terms(node.get("description", "")))
            type_score = len(query_terms & _terms(node.get("type", "")))
            score = name_score * 2.0 + description_score * 0.5 + type_score * 0.25
            node_scores.append((score, node))
        node_scores.sort(key=lambda item: (-item[0], str(item[1].get("id", ""))))
        seed_nodes = [node for score, node in node_scores if score > 0][:max(0, top_k_seeds)]
        if not seed_nodes:
            trace.add_step("NO_EVIDENCE", paper_id, level=0, reason="No graph entity matched the query lexically; no arbitrary seed was selected.")
            return self._finish(trace, start_time, "no_evidence", "No query-matched graph entity or source evidence was found. Try a more specific question.")

        for score, node in node_scores:
            if node in seed_nodes:
                trace.add_step("VISIT", str(node.get("id")), level=0, score=score, reason=f"Lexical seed match for '{node.get('name', '')}'.")
                trace.add_step("SELECT", str(node.get("id")), level=0, score=score, reason="Selected as a local-graph search seed.")

        # Expand an undirected local neighborhood for a standard local-graph baseline.
        visited = {str(node.get("id")) for node in seed_nodes}
        frontier = set(visited)
        traversed_edges: List[Dict[str, Any]] = []
        for hop in range(1, max(0, k_hops) + 1):
            next_frontier: Set[str] = set()
            for edge in edges:
                source, target = str(edge.get("source", "")), str(edge.get("target", ""))
                if source in frontier and target not in visited:
                    visited.add(target)
                    next_frontier.add(target)
                    traversed_edges.append({**edge, "walked_from": source, "walked_to": target, "walk_direction": "forward"})
                    trace.add_step("EXPAND", source, target_id=target, level=hop, reason=f"Local neighborhood expansion along extracted edge type {edge.get('type', 'unknown')}.")
                elif target in frontier and source not in visited:
                    visited.add(source)
                    next_frontier.add(source)
                    traversed_edges.append({**edge, "walked_from": target, "walked_to": source, "walk_direction": "reverse"})
                    trace.add_step("EXPAND", target, target_id=source, level=hop, reason=f"Local neighborhood expansion along extracted edge type {edge.get('type', 'unknown')}.")
            frontier = next_frontier
            if not frontier:
                break
        trace.traversed_edges = traversed_edges

        node_map = {str(node.get("id")): node for node in nodes}
        graph_lines = []
        for node_id in sorted(visited):
            node = node_map.get(node_id)
            if node:
                graph_lines.append(f"- Entity: {node.get('name', node_id)} ({node.get('type', 'Concept')}): {node.get('description', '')}")
        for edge in traversed_edges:
            source = node_map.get(str(edge.get("source")), {})
            target = node_map.get(str(edge.get("target")), {})
            graph_lines.append(
                f"- Unreviewed extracted relation: {source.get('name', edge.get('source'))} "
                f"-[{edge.get('type', 'RELATED_TO')}]-> {target.get('name', edge.get('target'))}"
            )
        graph_context = "\n".join(graph_lines) or "No local graph context was selected."

        graph_chunk_ids = {
            str(chunk_id)
            for node_id in visited
            for chunk_id in node_map.get(node_id, {}).get("source_chunk_ids", [])
        }
        ranked_chunks = []
        for chunk in chunks:
            chunk_id = str(chunk.get("chunk_id", ""))
            content = str(chunk.get("content", "")).strip()
            if not chunk_id or not content:
                continue
            overlap = len(query_terms & _terms(f"{chunk.get('section', '')} {content}"))
            graph_prior = 0.25 if chunk_id in graph_chunk_ids else 0.0
            score = overlap + graph_prior
            if score > 0:
                ranked_chunks.append((score, chunk))
        ranked_chunks.sort(key=lambda item: (-item[0], str(item[1].get("chunk_id", ""))))

        context_budget = max(0, int(settings.MAX_TOKEN_BUDGET))
        conversation_context = str(conversation_context or "").strip()[:4000]
        empty_prompt = self.PROMPT.format(
            paper_title=paper_title,
            question=question,
            graph_context=graph_context,
            chunk_context="",
            conversation_context=conversation_context or "None supplied.",
        )
        used_tokens = _estimate_tokens(empty_prompt) + 80
        selected_chunks: List[Dict[str, Any]] = []
        chunk_lines: List[str] = []
        for _, chunk in ranked_chunks:
            if len(selected_chunks) >= max(0, top_k_chunks):
                break
            chunk_id = str(chunk.get("chunk_id"))
            content = str(chunk.get("content", "")).strip()
            block = (
                f"[Source: {paper_id}::{chunk_id}] Section: {chunk.get('section') or 'unknown'}, "
                f"Page: {chunk.get('page') if chunk.get('page') is not None else 'unknown'}\n{content[:1200]}"
            )
            cost = _estimate_tokens(block) + (_estimate_tokens("\n\n") if chunk_lines else 0)
            if generate_answer and used_tokens + cost > context_budget:
                trace.add_step("BUDGET_PRUNE", chunk_id, level=0, reason="Source chunk omitted because it exceeded the estimated prompt-token budget.")
                continue
            selected_chunks.append(chunk)
            chunk_lines.append(block)
            used_tokens += cost
            trace.add_step("EVIDENCE", chunk_id, level=0, score=next((score for score, item in ranked_chunks if item is chunk), 0), reason="Recovered from the original paper chunk store.")

        if not selected_chunks:
            trace.add_step("NO_EVIDENCE", "source_chunks", level=0, reason="No relevant source chunk fit the context budget.")
            return self._finish(trace, start_time, "no_evidence", "The local graph selected no source evidence that fits the context budget. No answer was generated.")

        if not generate_answer:
            score_by_chunk = {str(chunk.get("chunk_id")): score for score, chunk in ranked_chunks}
            return self._finish(
                trace, start_time, "retrieved", "",
                extras={
                    "retrieved_evidence": [
                        {
                            "paper_id": paper_id,
                            "chunk_id": str(chunk.get("chunk_id")),
                            "section": chunk.get("section"),
                            "page": chunk.get("page"),
                            "content": str(chunk.get("content", "")),
                            "score": score_by_chunk.get(str(chunk.get("chunk_id")), 0.0),
                        }
                        for chunk in selected_chunks
                    ],
                    "retrieval_trace": {
                        "seed_node_ids": [str(node.get("id")) for node in seed_nodes],
                        "selected_node_ids": sorted(visited),
                        "selected_evidence": [str(chunk.get("chunk_id")) for chunk in selected_chunks],
                        "selection_mode": "lexical_graph_neighborhood_retrieval_only",
                        "fallback_modes": [],
                    },
                },
            )

        chunk_context = "\n\n".join(chunk_lines)
        prompt = self.PROMPT.format(
            paper_title=paper_title,
            question=question,
            graph_context=graph_context,
            chunk_context=chunk_context,
            conversation_context=conversation_context or "None supplied.",
        )
        estimated_prompt_tokens = _estimate_tokens(prompt) + 80
        if estimated_prompt_tokens > context_budget:
            return self._finish(trace, start_time, "context_budget_exceeded", "The assembled local-search prompt exceeds the estimated context-token budget. No answer was generated.")

        answer, call_log = await ollama_client.generate(
            prompt=prompt,
            model=settings.OLLAMA_LARGE_MODEL,
            system="Use retrieved source chunks for factual support. Treat extracted graph relations as unreviewed navigation hints.",
            temperature=0.1,
        )
        trace.total_tokens += call_log.total_tokens
        trace.total_llm_calls += 1
        if not answer or call_log.status != "success":
            answer = "Answer generation failed. Retrieved source evidence:\n\n" + chunk_context

        return self._finish(
            trace, start_time, "ok", answer,
            extras={
                "retrieved_evidence": [
                    {"paper_id": paper_id, "chunk_id": str(chunk.get("chunk_id")), "section": chunk.get("section"), "page": chunk.get("page")}
                    for chunk in selected_chunks
                ],
                "retrieval_trace": {
                    "seed_node_ids": [str(node.get("id")) for node in seed_nodes],
                    "selected_node_ids": sorted(visited),
                    "selected_evidence": [str(chunk.get("chunk_id")) for chunk in selected_chunks],
                    "estimated_prompt_tokens": estimated_prompt_tokens,
                    "context_tokens_budget": context_budget,
                    "token_estimator": "ceil(prompt_characters/3) + 80 system allowance",
                    "fallback_modes": [],
                },
            },
        )

    @staticmethod
    def _finish(
        trace: TraversalTrace,
        started: float,
        status: str,
        answer: str,
        extras: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        trace.latency_ms = round((time.time() - started) * 1000.0, 2)
        result = {
            "status": status,
            "mode": "local",
            "answer": answer,
            "trace": trace.model_dump(),
            "total_tokens": trace.total_tokens,
            "total_llm_calls": trace.total_llm_calls,
            "latency_ms": trace.latency_ms,
        }
        if extras:
            result.update(extras)
        return result


local_search = LocalSearch()
