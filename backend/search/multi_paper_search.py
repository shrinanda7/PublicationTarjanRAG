"""Cross-paper graph retrieval with provenance-preserving multi-hop evidence.

Automatic identity links require exact normalized names. Semantic cross-paper
relations enter the traversable graph only from human-reviewed bridge records
whose quotes match indexed source chunks.
"""
from __future__ import annotations

import re
import time
import logging
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

import networkx as nx

from backend.config import settings
from backend.core.compression import compressor
from backend.pipeline.neo4j_store import neo4j_store
from backend.search.evidence_synthesis import estimate_prompt_tokens, synthesize_evidence
from backend.search.quotient_traversal import select_quotient_subgraph
from backend.search.cross_paper_bridges import build_validated_bridge_edges, load_bridge_records
from backend.search.baseline_query import baseline_query

logger = logging.getLogger("graphrag.multi_paper")


def _norm(value: Any) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _terms(value: str) -> Set[str]:
    stop = {"the", "and", "for", "with", "from", "that", "this", "what", "how", "why", "paper", "across", "between", "compare", "explain", "does", "are", "was", "were", "into", "their", "using"}
    return {t for t in re.findall(r"[a-z0-9]+", value.lower()) if len(t) > 2 and t not in stop}


def _strip_model_graph_connections(answer: str) -> str:
    """Remove model-authored graph claims; the service adds verified output later."""
    return re.sub(
        r"(?:^|\n)#{1,4}\s*[^\n]*\bGraph Connections\b[^\n]*[\s\S]*?(?=\n#{1,4}\s|$)",
        "\n",
        answer,
        count=1,
        flags=re.IGNORECASE,
    ).strip()


def _verified_traversed_relations(
    selected_edges: List[Dict[str, Any]],
    original_nodes: List[Dict[str, Any]],
    original_edges: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Return reviewed semantic relations represented by selected quotient edges.

    Exact-name identity links and extracted-but-unreviewed relations are not
    presented as verified Graph Connections. Every returned edge must exist in
    the original graph and cite source chunks present in that graph.
    """
    nodes_by_id = {str(node.get("id")): node for node in original_nodes if node.get("id")}
    known_chunks = {
        (str(node.get("paper_id", "")), str(chunk_id))
        for node in original_nodes
        for chunk_id in node.get("source_chunk_ids", [])
        if node.get("paper_id") and chunk_id is not None
    }
    original_keys = {
        (str(edge.get("source")), str(edge.get("target")), str(edge.get("type")), str(edge.get("paper_id", "")))
        for edge in original_edges
    }
    seen = set()
    verified = []
    for quotient_edge in selected_edges:
        for relation in quotient_edge.get("original_relations", []):
            source = str(relation.get("source", ""))
            target = str(relation.get("target", ""))
            relation_type = str(relation.get("type", ""))
            paper_id = str(relation.get("paper_id", ""))
            key = (source, target, relation_type, paper_id)
            if key in seen or key not in original_keys:
                continue
            if source not in nodes_by_id or target not in nodes_by_id:
                continue
            if relation.get("validation_status") != "validated":
                continue
            if relation.get("provenance") not in {"paper_extraction", "llm_extracted", "human_validated_bridge"}:
                continue
            source_chunk_ids = {str(cid) for cid in relation.get("source_chunk_ids", [])}
            evidence = relation.get("source_evidence")
            if not isinstance(evidence, list) or not evidence:
                continue
            normalized_evidence = []
            for item in evidence:
                if not isinstance(item, dict):
                    normalized_evidence = []
                    break
                evidence_paper = str(item.get("paper_id", ""))
                chunk_id = str(item.get("chunk_id", ""))
                if not evidence_paper or not chunk_id or chunk_id not in source_chunk_ids:
                    normalized_evidence = []
                    break
                if (evidence_paper, chunk_id) not in known_chunks:
                    normalized_evidence = []
                    break
                normalized_evidence.append({"paper_id": evidence_paper, "chunk_id": chunk_id})
            if not normalized_evidence:
                continue
            verified.append({"edge": relation, "source_evidence": normalized_evidence})
            seen.add(key)
    return verified


class MultiPaperSearch:
    """Retrieve connected, query-relevant evidence across several indexed papers."""

    async def search(
        self,
        question: str,
        paper_ids: List[str],
        paper_titles: Dict[str, str] | None = None,
        max_evidence_chunks: int = 10,
        max_context_chars: int = 24000,
        max_context_tokens: int | None = None,
        seed: int | None = None,
        conversation_context: str = "",
    ) -> Dict[str, Any]:
        started = time.time()
        paper_titles = paper_titles or {}
        max_evidence_chunks = max(0, int(max_evidence_chunks))
        max_context_chars = max(0, int(max_context_chars))
        max_context_tokens = max(0, int(max_context_tokens if max_context_tokens is not None else settings.MAX_TOKEN_BUDGET))
        conversation_context = str(conversation_context or "").strip()[:4000]
        # Keep order stable and bound graph fan-out for predictable latency.
        paper_ids = list(dict.fromkeys(str(p).strip() for p in paper_ids if str(p).strip()))
        if not paper_ids:
            return self._error("paper_ids must contain at least one paper ID", started)
        if len(paper_ids) > 12:
            return self._error("At most 12 papers can be queried in one request", started)

        merged_nodes: List[Dict[str, Any]] = []
        merged_edges: List[Dict[str, Any]] = []
        chunks_by_paper: Dict[str, List[Dict[str, Any]]] = {}
        paper_meta: Dict[str, Dict[str, Any]] = {}
        name_index: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        node_ids_by_paper: Dict[str, Dict[str, str]] = {}
        nodes_by_namespaced_id: Dict[str, Dict[str, Any]] = {}
        missing: List[str] = []
        generic_entity_names = {"method", "model", "graph", "paper", "approach", "result", "dataset", "experiment", "framework", "network", "system", "layer", "module", "baseline", "performance", "architecture", "algorithm", "embedding"}

        for paper_id in paper_ids:
            graph_data = neo4j_store.get_paper_graph(paper_id, compressed=False) or {}
            nodes = graph_data.get("nodes") or []
            edges = graph_data.get("edges") or []
            if not nodes:
                missing.append(paper_id)
                continue
            title = paper_titles.get(paper_id) or paper_id.replace("_", " ")
            paper_meta[paper_id] = {"title": title, "storage_mode": graph_data.get("storage_mode", "unknown"), "durable": bool(graph_data.get("durable", False))}
            chunks_by_paper[paper_id] = neo4j_store.get_chunks_by_ids(paper_id, []) or []
            id_map: Dict[str, str] = {}
            for node in nodes:
                original_id = str(node.get("id", ""))
                if not original_id:
                    continue
                global_id = f"{paper_id}::{original_id}"
                id_map[original_id] = global_id
                copied = dict(node)
                copied["id"] = global_id
                copied["original_node_id"] = original_id
                copied["paper_id"] = paper_id
                copied["paper_title"] = title
                copied["source_chunk_ids"] = [str(x) for x in node.get("source_chunk_ids", []) if x is not None]
                merged_nodes.append(copied)
                nodes_by_namespaced_id[global_id] = copied
                canonical = _norm(node.get("name", ""))
                # Avoid extremely generic labels creating noisy cross-paper hubs.
                if (len(canonical) >= 4 and len(canonical.split()) <= 8
                        and canonical not in generic_entity_names):
                    name_index[canonical].append(copied)
            for edge in edges:
                source = id_map.get(str(edge.get("source", "")))
                target = id_map.get(str(edge.get("target", "")))
                if not source or not target or source == target:
                    continue
                copied_edge = dict(edge)
                copied_edge.update({"source": source, "target": target, "paper_id": paper_id})
                copied_edge.setdefault("provenance", "llm_extracted")
                copied_edge.setdefault("validation_status", "unreviewed")
                copied_edge["source_evidence"] = [
                    {"paper_id": paper_id, "chunk_id": str(cid)}
                    for cid in copied_edge.get("source_chunk_ids", [])
                ]
                merged_edges.append(copied_edge)
            node_ids_by_paper[paper_id] = id_map

        if not merged_nodes:
            # A paper can have durable source chunks before graph extraction has
            # completed (or when extraction produced no entities). Use those
            # chunks to answer from evidence instead of treating graph absence
            # as paper absence.
            chunk_fallback = await baseline_query.search(
                method="bm25",
                question=question,
                paper_ids=paper_ids,
                paper_titles=paper_titles,
                max_evidence_chunks=max_evidence_chunks,
                max_context_chars=max_context_chars,
                max_context_tokens=max_context_tokens,
                conversation_context=conversation_context,
            )
            if chunk_fallback.get("status") not in {"no_indexed_chunks", "retrieval_error"}:
                chunk_fallback["graph_fallback"] = "bm25_source_chunks"
                chunk_fallback["missing_graph_paper_ids"] = missing
                chunk_fallback["engine"] = "BM25 source chunks + shared evidence synthesis (graph unavailable)"
                return chunk_fallback

            missing_label = ", ".join(missing or paper_ids)
            return {
                "status": "no_indexed_graph", "mode": "multi_paper",
                "answer": f"No indexed knowledge graph is available for these paper IDs: {missing_label}. In Research Corpus, click ‘Index selected for research’ and wait for ingestion to finish, then retry. The graph and chunks are now stored in local SQLite when Neo4j is unavailable.",
                "paper_ids": paper_ids, "missing_paper_ids": missing, "evidence": [], "selected_node_ids": [],
                "trace": {"steps": [], "total_llm_calls": 0, "total_tokens": 0}, "total_llm_calls": 0,
                "total_tokens": 0, "latency_ms": round((time.time()-started)*1000, 2),
            }

        # Exact-name cross-paper identity links only; no guessed semantic edges.
        cross_links = 0
        if settings.ENABLE_CROSS_PAPER_LINKS:
            for canonical, matches in name_index.items():
                by_paper: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
                for node in matches:
                    by_paper[node["paper_id"]].append(node)
                paper_keys = sorted(by_paper)
                if len(paper_keys) < 2:
                    continue
                # Cap ambiguous homonyms to avoid a quadratic, high-degree hub.
                candidates = [nodes_for_paper[0] for pid in paper_keys for nodes_for_paper in [by_paper[pid]]]
                if len(candidates) > 8:
                    candidates = candidates[:8]
                for i, left in enumerate(candidates):
                    for right in candidates[i + 1:]:
                        if left["paper_id"] == right["paper_id"]:
                            continue
                        provenance = sorted(set(left.get("source_chunk_ids", [])) | set(right.get("source_chunk_ids", [])))
                        source_evidence = [
                            {"paper_id": str(left["paper_id"]), "chunk_id": str(cid)}
                            for cid in left.get("source_chunk_ids", [])
                        ] + [
                            {"paper_id": str(right["paper_id"]), "chunk_id": str(cid)}
                            for cid in right.get("source_chunk_ids", [])
                        ]
                        identity_edge = {"type": "SAME_ENTITY_NAME", "weight": 0.5, "source_chunk_ids": provenance, "source_evidence": source_evidence, "cross_paper": True, "provenance": "normalized_exact_name_match", "validation_status": "identity_match_only"}
                        merged_edges.append({"source": left["id"], "target": right["id"], **identity_edge})
                        merged_edges.append({"source": right["id"], "target": left["id"], **identity_edge})
                        cross_links += 2

        bridge_file = settings.BASE_DIR / "data" / "evaluation" / "cross_paper_bridges.json"
        bridge_records, bridge_file_error = load_bridge_records(bridge_file) if settings.ENABLE_CROSS_PAPER_LINKS else ([], None)
        reviewed_edges, rejected_bridge_ids = build_validated_bridge_edges(
            bridge_records,
            paper_ids=paper_ids,
            node_ids_by_paper=node_ids_by_paper,
            nodes_by_namespaced_id=nodes_by_namespaced_id,
            chunks_by_paper=chunks_by_paper,
        )
        merged_edges.extend(reviewed_edges)
        cross_links += len(reviewed_edges)

        compressed = compressor.compress_graph(merged_nodes, merged_edges)
        selection = select_quotient_subgraph(
            question=question,
            compressed_graph=compressed,
            max_seeds=5,
            max_selected_nodes=24,
            max_path_nodes=12,
            bridge_aware=settings.ENABLE_BRIDGE_AWARE_PRUNING,
            budget_aware=settings.ENABLE_BUDGET_AWARE_TRAVERSAL,
            query_conditioned=settings.ENABLE_QUERY_CONDITIONED_TRAVERSAL,
        )
        verified_graph_relations = _verified_traversed_relations(
            selection.get("edges", []), merged_nodes, merged_edges
        )

        # Resolve graph-derived chunk references without losing paper namespaces.
        requested_chunks: Dict[str, Set[str]] = defaultdict(set)
        node_by_id = {str(n["id"]): n for n in compressed.get("nodes", [])}
        selected_node_ids = [str(x) for x in selection.get("selected_node_ids", [])]
        for selected_id in selected_node_ids:
            node = node_by_id.get(selected_id, {})
            members = node.get("member_nodes", [])
            if not members:
                members = [node]
            for member in members:
                pid = member.get("paper_id")
                if not pid:
                    # Singleton compressed nodes keep the paper_id on the node.
                    pid = node.get("paper_id")
                if not pid:
                    continue
                for cid in member.get("source_chunk_ids", []):
                    requested_chunks[str(pid)].add(str(cid))
            # Edge provenance belongs to the paper(s) attached to its source nodes;
            # node provenance remains the authoritative chunk map.

        # Candidate evidence: graph-linked chunks, then lexical backfill.
        candidates: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for pid in (paper_ids if settings.ENABLE_EVIDENCE_RECOVERY else []):
            available = chunks_by_paper.get(pid, [])
            wanted = requested_chunks.get(pid, set())
            for chunk in available:
                cid = str(chunk.get("chunk_id", ""))
                if cid and cid in wanted and chunk.get("content"):
                    item = dict(chunk)
                    item.update({"paper_id": pid, "paper_title": paper_meta.get(pid, {}).get("title", pid)})
                    candidates[(pid, cid)] = item

        query_terms = _terms(question)
        # Score all available chunks for lexical backfill and relevance ordering.
        scored: List[Tuple[float, Dict[str, Any]]] = []
        for pid in paper_ids:
            for raw in chunks_by_paper.get(pid, []):
                cid = str(raw.get("chunk_id", ""))
                content = str(raw.get("content", "")).strip()
                if not cid or not content:
                    continue
                item = candidates.get((pid, cid))
                if item is None:
                    item = dict(raw)
                    item.update({"paper_id": pid, "paper_title": paper_meta.get(pid, {}).get("title", pid)})
                text = " ".join([content, str(item.get("section", ""))])
                terms = _terms(text)
                overlap = len(query_terms & terms) / max(len(query_terms), 1)
                # Graph-linked chunks receive a small, explicit structural prior.
                structural_prior = 0.15 if (pid, cid) in candidates else 0.0
                scored.append((overlap + structural_prior, item))
        scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("paper_id")), str(pair[1].get("chunk_id"))))
        selected_chunks: List[Dict[str, Any]] = []
        seen: Set[Tuple[str, str]] = set()
        used_content_chars = 0
        fixed_prompt_tokens = estimate_prompt_tokens(question, [], conversation_context)
        used_prompt_tokens = fixed_prompt_tokens

        def try_add_chunk(chunk: Dict[str, Any]) -> bool:
            nonlocal used_content_chars, used_prompt_tokens
            if len(selected_chunks) >= max_evidence_chunks:
                return False
            key = (str(chunk["paper_id"]), str(chunk["chunk_id"]))
            if key in seen:
                return False
            content = str(chunk.get("content", ""))
            if used_content_chars + len(content) > max_context_chars:
                return False
            if estimate_prompt_tokens(question, [*selected_chunks, chunk], conversation_context) > max_context_tokens:
                return False
            selected_chunks.append(chunk)
            seen.add(key)
            used_content_chars += len(content)
            used_prompt_tokens = estimate_prompt_tokens(question, selected_chunks, conversation_context)
            return True

        # Guarantee representation from multiple papers when relevant chunks exist.
        relevant_by_paper: Dict[str, List[Tuple[float, Dict[str, Any]]]] = defaultdict(list)
        for score, chunk in scored:
            if score > 0:
                relevant_by_paper[str(chunk["paper_id"])].append((score, chunk))
        for pid in paper_ids:
            if relevant_by_paper.get(pid):
                _, chunk = relevant_by_paper[pid][0]
                try_add_chunk(chunk)
        for score, chunk in scored:
            if len(selected_chunks) >= max_evidence_chunks:
                break
            if score <= 0:
                continue
            try_add_chunk(chunk)

        # Broad cross-paper prompts such as "compare both papers" carry no
        # useful lexical terms. Still provide representative text from each
        # selected paper so synthesis can compare evidence instead of returning
        # a misleading zero-match response.
        comparative_prompt = bool(re.search(
            r"\b(compare|comparison|contrast|relationship|related|similarit(?:y|ies)|difference(?:s)?)\b",
            question,
            flags=re.IGNORECASE,
        ))
        if not selected_chunks and comparative_prompt and len(paper_ids) > 1:
            for pid in paper_ids:
                representative = next(
                    (item for _, item in scored if str(item.get("paper_id")) == pid),
                    None,
                )
                if representative is not None:
                    try_add_chunk(representative)

        if not selected_chunks:
            has_lexical_match = any(score > 0 for score, _ in scored)
            reason = "context_budget_exceeded" if has_lexical_match else "no_relevant_chunk"
            retrieval_trace = {
                "seed_node_ids": selection.get("seed_node_ids", []),
                "selected_node_ids": selected_node_ids,
                "selected_edges": selection.get("edges", []),
                "verified_graph_relations": [],
                "evidence_content_chars_used": 0,
                "context_chars_budget": max_context_chars,
                "context_tokens_budget": max_context_tokens,
                "estimated_prompt_tokens": fixed_prompt_tokens,
                "token_estimator": "ceil(prompt_characters/3) + 120 system/framing allowance",
                "token_budget_utilization": min(fixed_prompt_tokens / max_context_tokens, 1.0) if max_context_tokens else None,
                "evidence_chunk_budget": max_evidence_chunks,
                "fallback_modes": [reason],
            }
            return {
                "status": "context_budget_exceeded" if has_lexical_match else "no_evidence",
                "mode": "multi_paper",
                "answer": "Relevant source chunks were found, but none fit within the configured context budget. Increase the budget or reduce the question/context overhead." if has_lexical_match else "The selected papers are indexed, but no source chunks matched the query. Try a more specific question or verify that chunk text was persisted.",
                "paper_ids": paper_ids, "missing_paper_ids": missing, "selected_node_ids": selected_node_ids,
                "cross_paper_links": cross_links, "evidence": [], "retrieval_trace": retrieval_trace,
                "trace": {"steps": [], "total_llm_calls": 0, "total_tokens": 0, "retrieval": retrieval_trace},
                "total_llm_calls": 0, "total_tokens": 0, "latency_ms": round((time.time()-started)*1000, 2),
            }

        estimated_prompt_tokens = estimate_prompt_tokens(question, selected_chunks, conversation_context)
        if estimated_prompt_tokens > max_context_tokens:
            # Guard the prompt actually sent, even if the chunk estimator changes.
            return {
                "status": "context_budget_exceeded", "mode": "multi_paper",
                "answer": "The assembled evidence prompt exceeds the configured estimated context-token budget. No answer was generated.",
                "paper_ids": paper_ids, "missing_paper_ids": missing, "selected_node_ids": selected_node_ids,
                "evidence": [], "retrieval_trace": {"context_tokens_budget": max_context_tokens, "estimated_prompt_tokens": estimated_prompt_tokens, "token_estimator": "ceil(prompt_characters/3) + 120 system/framing allowance", "fallback_modes": ["context_budget_exceeded"]},
                "trace": {"steps": [], "total_llm_calls": 0, "total_tokens": 0},
                "total_llm_calls": 0, "total_tokens": 0, "latency_ms": round((time.time()-started)*1000, 2),
            }
        answer, log, prompt = await synthesize_evidence(
            question, selected_chunks, seed=seed,
            conversation_context=conversation_context,
        )
        llm_failed = not bool(answer and answer.strip()) or log.status not in {"success", "mock"}
        if llm_failed:
            answer = "Answer generation failed because the configured LLM endpoint did not return a valid response. The retrieved evidence is included for inspection; no answer has been fabricated."
        else:
            answer = _strip_model_graph_connections(answer)
        connection_lines = []
        for item in verified_graph_relations:
            edge = item["edge"]
            source = next((n for n in merged_nodes if str(n.get("id")) == str(edge.get("source"))), {})
            target = next((n for n in merged_nodes if str(n.get("id")) == str(edge.get("target"))), {})
            refs = ", ".join(f"{e['paper_id']}::{e['chunk_id']}" for e in item["source_evidence"])
            connection_lines.append(
                f"- **{source.get('name', edge.get('source'))}** —{edge.get('type')}→ "
                f"**{target.get('name', edge.get('target'))}** (source: {refs})"
            )
        if connection_lines:
            answer = f"{answer.rstrip()}\n\n**Verified graph links**\n" + "\n".join(connection_lines)
        trace_steps = []
        for seed in selection.get("seed_node_ids", []):
            trace_steps.append({"action": "SEED", "node_id": str(seed), "score": selection.get("scores", {}).get(str(seed)), "reason": "Query-conditioned lexical overlap seed" if settings.ENABLE_QUERY_CONDITIONED_TRAVERSAL else "Query-independent stable-order seed"})
        for node_id in selected_node_ids:
            selected_node = node_by_id.get(node_id, {})
            trace_steps.append({"action": "SELECT", "node_id": node_id, "member_node_ids": selected_node.get("member_node_ids", []), "source_chunk_ids": selected_node.get("source_chunk_ids", []), "reason": "Selected quotient node/path for evidence retrieval"})
        for edge in selection.get("edges", []):
            relations = edge.get("original_relations", [])
            relation_states = sorted({str(r.get("validation_status", "unknown")) for r in relations})
            trace_steps.append({"action": "SELECT_EDGE", "source": str(edge.get("source")), "target": str(edge.get("target")), "type": str(edge.get("type", "RELATED_TO")), "original_relations": relations, "validation_statuses": relation_states, "reason": "Directed quotient edge selected; relation-level validation remains as listed"})
        for idx, chunk in enumerate(selected_chunks, 1):
            trace_steps.append({"action": "EVIDENCE", "node_id": str(chunk.get("chunk_id")), "paper_id": str(chunk.get("paper_id")), "reason": f"Evidence [{idx}] selected from source chunk"})
        graph_linked_keys = set(candidates)
        selected_keys = {(str(chunk.get("paper_id")), str(chunk.get("chunk_id"))) for chunk in selected_chunks}
        lexical_fallback_count = len(selected_keys - graph_linked_keys)
        fallback_modes = []
        if lexical_fallback_count:
            fallback_modes.append("lexical_chunk_backfill")
        if any(not bool(meta.get("durable")) for meta in paper_meta.values()):
            fallback_modes.append("in_memory_store")
        if llm_failed:
            fallback_modes.append("llm_generation_failure")
        retrieval_trace = {
            "seed_node_ids": selection.get("seed_node_ids", []),
            "selected_node_ids": selected_node_ids,
            "selected_edges": selection.get("edges", []),
            "verified_graph_relations": [
                {"source": item["edge"].get("source"), "target": item["edge"].get("target"), "type": item["edge"].get("type"), "source_evidence": item["source_evidence"]}
                for item in verified_graph_relations
            ],
            "selected_evidence": [{"paper_id": str(c.get("paper_id")), "chunk_id": str(c.get("chunk_id"))} for c in selected_chunks],
            "cross_paper_links_enabled": settings.ENABLE_CROSS_PAPER_LINKS,
            "reviewed_cross_paper_bridge_count": len(reviewed_edges),
            "rejected_cross_paper_bridge_ids": rejected_bridge_ids,
            "cross_paper_bridge_file_error": bridge_file_error,
            "evidence_recovery_enabled": settings.ENABLE_EVIDENCE_RECOVERY,
            "query_conditioned_traversal_enabled": settings.ENABLE_QUERY_CONDITIONED_TRAVERSAL,
            "evidence_content_chars_used": used_content_chars,
            "context_chars_budget": max_context_chars,
            "context_tokens_budget": max_context_tokens,
            "fixed_prompt_tokens_estimated": fixed_prompt_tokens,
            "estimated_prompt_tokens": estimated_prompt_tokens,
            "token_estimator": "ceil(prompt_characters/3) + 120 system/framing allowance",
            "token_budget_utilization": estimated_prompt_tokens / max_context_tokens if max_context_tokens else None,
            "evidence_chunk_budget": max_evidence_chunks,
            "graph_linked_chunk_count": len(selected_keys & graph_linked_keys),
            "lexical_fallback_chunk_count": lexical_fallback_count,
            "fallback_modes": fallback_modes,
        }
        return {
            "status": "llm_error" if llm_failed else "ok", "mode": "multi_paper", "question": question,
            "paper_ids": paper_ids, "paper_titles": {pid: meta["title"] for pid, meta in paper_meta.items()},
            "missing_paper_ids": missing, "cross_paper_links": cross_links,
            "reviewed_cross_paper_bridge_count": len(reviewed_edges),
            "original_graph": {"nodes": merged_nodes, "edges": merged_edges},
            "compressed_graph": {"nodes": compressed["nodes"], "edges": compressed["edges"], "diagnostics": compressed["diagnostics"], "compression_ratio": compressed["compression_ratio"], "articulation_points": compressed["articulation_points"], "bridges": compressed["bridges"]},
            "selected_node_ids": selected_node_ids,
            "selected_edges": selection.get("edges", []),
            "retrieval_trace": retrieval_trace,
            "evidence": [{"evidence_id": f"E{i}", "paper_id": c["paper_id"], "paper_title": c["paper_title"], "chunk_id": c["chunk_id"], "section": c.get("section"), "page": c.get("page"), "content": c["content"]} for i, c in enumerate(selected_chunks, 1)],
            "answer": answer, "trace": {"mode": "multi_paper", "steps": trace_steps, "selected_node_ids": selected_node_ids, "total_llm_calls": 1 if log.status == "success" else 0, "total_tokens": log.total_tokens, "latency_ms": log.latency_ms, "retrieval": retrieval_trace},
            "total_llm_calls": 1 if log.status == "success" else 0,
            "prompt_tokens": log.prompt_tokens,
            "completion_tokens": log.completion_tokens,
            "total_tokens": log.total_tokens,
            "latency_ms": round((time.time()-started)*1000, 2), "llm_status": log.status,
        }

    @staticmethod
    def _error(message: str, started: float) -> Dict[str, Any]:
        return {"status": "invalid_request", "mode": "multi_paper", "answer": message, "evidence": [], "trace": {"steps": [], "total_llm_calls": 0, "total_tokens": 0}, "total_llm_calls": 0, "total_tokens": 0, "latency_ms": round((time.time()-started)*1000, 2)}


multi_paper_search = MultiPaperSearch()
