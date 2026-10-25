"""Load human-reviewed, chunk-grounded cross-paper graph bridges."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple


def build_validated_bridge_edges(
    records: Iterable[Dict[str, Any]],
    *,
    paper_ids: Iterable[str],
    node_ids_by_paper: Mapping[str, Mapping[str, str]],
    nodes_by_namespaced_id: Mapping[str, Dict[str, Any]],
    chunks_by_paper: Mapping[str, List[Dict[str, Any]]],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Accept only reviewed bridges whose endpoints and quoted evidence exist.

    `node_ids_by_paper` maps original graph node IDs to namespaced IDs. Each
    supporting quote must match an indexed chunk linked to the corresponding
    endpoint node. Invalid records are rejected individually and their IDs are
    returned for telemetry.
    """
    selected = set(map(str, paper_ids))
    chunk_text = {
        (str(paper_id), str(chunk.get("chunk_id"))): str(chunk.get("content", ""))
        for paper_id, chunks in chunks_by_paper.items()
        for chunk in chunks
        if chunk.get("chunk_id") and chunk.get("content")
    }
    edges: List[Dict[str, Any]] = []
    rejected: List[str] = []
    seen = set()
    for index, raw in enumerate(records):
        if not isinstance(raw, dict):
            rejected.append(str(index))
            continue
        bridge_id = str(raw.get("bridge_id") or index)
        source_paper = str(raw.get("source_paper_id", ""))
        target_paper = str(raw.get("target_paper_id", ""))
        source = node_ids_by_paper.get(source_paper, {}).get(str(raw.get("source_node_id", "")))
        target = node_ids_by_paper.get(target_paper, {}).get(str(raw.get("target_node_id", "")))
        relation = str(raw.get("relation_type", "")).strip().upper()
        reviewers = raw.get("reviewer_ids")
        evidence = raw.get("evidence")
        key = (source, target, relation)
        valid = (
            raw.get("validation_status") == "human_validated"
            and source_paper in selected and target_paper in selected
            and source_paper != target_paper and source and target and source != target
            and source in nodes_by_namespaced_id and target in nodes_by_namespaced_id
            and relation and relation.replace("_", "").isalnum()
            and isinstance(reviewers, list) and any(str(reviewer).strip() for reviewer in reviewers)
            and isinstance(evidence, list) and len(evidence) >= 2
            and key not in seen
        )
        normalized_evidence = []
        if valid:
            endpoint_chunks = {
                (source_paper, str(chunk_id))
                for chunk_id in nodes_by_namespaced_id[source].get("source_chunk_ids", [])
            } | {
                (target_paper, str(chunk_id))
                for chunk_id in nodes_by_namespaced_id[target].get("source_chunk_ids", [])
            }
            for item in evidence:
                if not isinstance(item, dict):
                    valid = False
                    break
                evidence_paper = str(item.get("paper_id", ""))
                chunk_id = str(item.get("chunk_id", ""))
                quote = str(item.get("quote", "")).strip()
                text = chunk_text.get((evidence_paper, chunk_id), "")
                if (
                    (evidence_paper, chunk_id) not in endpoint_chunks
                    or not quote or quote not in text
                ):
                    valid = False
                    break
                normalized_evidence.append({
                    "paper_id": evidence_paper,
                    "chunk_id": chunk_id,
                    "quote": quote,
                })
            valid = valid and {item["paper_id"] for item in normalized_evidence} >= {source_paper, target_paper}
        if not valid:
            rejected.append(bridge_id)
            continue
        seen.add(key)
        chunk_ids = sorted({item["chunk_id"] for item in normalized_evidence})
        edges.append({
            "source": source,
            "target": target,
            "type": relation,
            "relation_description": str(raw.get("relation_description", "")).strip(),
            "paper_id": "__cross_paper__",
            "weight": 1.0,
            "cross_paper": True,
            "bridge_id": bridge_id,
            "reviewer_ids": [str(reviewer).strip() for reviewer in reviewers if str(reviewer).strip()],
            "source_chunk_ids": chunk_ids,
            "source_evidence": normalized_evidence,
            "provenance": "human_validated_bridge",
            "validation_status": "validated",
        })
    return edges, rejected


def load_bridge_records(path: Path) -> Tuple[List[Dict[str, Any]], str | None]:
    """Read the optional annotation file, failing closed on malformed input."""
    if not path.exists():
        return [], None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or not isinstance(payload.get("bridges"), list):
            return [], "root must be an object with a bridges array"
        return payload["bridges"], None
    except (OSError, json.JSONDecodeError) as exc:
        return [], f"{type(exc).__name__}: {exc}"
