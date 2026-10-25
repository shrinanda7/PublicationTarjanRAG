"""Validation contract for frozen, human-reviewed evaluation annotations."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

VALID_CATEGORIES = {"single_paper", "multi_hop_single_paper", "multi_hop_cross_paper"}


def validate_record(record: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required = {"question_id", "paper_ids", "question", "category", "answerable", "gold_answers", "gold_evidence", "gold_paths", "required_hops", "annotation"}
    missing = sorted(required - record.keys())
    if missing:
        return [f"missing fields: {', '.join(missing)}"]
    qid = str(record.get("question_id", "<unknown>"))
    if not isinstance(record.get("question_id"), str) or not record["question_id"].strip():
        errors.append("question_id must be a non-empty string")
    if not isinstance(record["paper_ids"], list) or not record["paper_ids"]:
        errors.append("paper_ids must be a non-empty list")
        valid_paper_ids: List[str] = []
    else:
        valid_paper_ids = [paper_id for paper_id in record["paper_ids"] if isinstance(paper_id, str) and paper_id.strip()]
        if len(valid_paper_ids) != len(record["paper_ids"]):
            errors.append("paper_ids entries must be non-empty strings")
        if len(valid_paper_ids) != len(set(valid_paper_ids)):
            errors.append("paper_ids entries must be unique")
    if record["category"] == "single_paper" and len(valid_paper_ids) != 1:
        errors.append("single_paper questions must identify exactly one paper")
    if record["category"] == "multi_hop_single_paper" and len(valid_paper_ids) != 1:
        errors.append("multi_hop_single_paper questions must identify exactly one paper")
    if record["category"] == "multi_hop_cross_paper" and len(set(valid_paper_ids)) < 2:
        errors.append("multi_hop_cross_paper questions must require at least two papers")
    if not isinstance(record["question"], str) or not record["question"].strip():
        errors.append("question must be non-empty text")
    if not isinstance(record["category"], str) or record["category"] not in VALID_CATEGORIES:
        errors.append(f"category must be one of {sorted(VALID_CATEGORIES)}")
    if not isinstance(record["answerable"], bool):
        errors.append("answerable must be boolean")
    if not isinstance(record["gold_answers"], list) or any(not isinstance(answer, str) or not answer.strip() for answer in record["gold_answers"]):
        errors.append("gold_answers must be a list of non-empty acceptable answers")
    if record.get("answerable") is True and not record.get("gold_answers"):
        errors.append("answerable questions need at least one independently authored gold answer")
    if record.get("answerable") is False and record.get("gold_answers"):
        errors.append("unanswerable questions must not contain a positive gold answer")
    if not isinstance(record["gold_evidence"], list):
        errors.append("gold_evidence must be a list")
    else:
        paper_ids = set(valid_paper_ids)
        seen_evidence = set()
        for index, evidence in enumerate(record["gold_evidence"]):
            if (not isinstance(evidence, dict)
                    or any(not isinstance(evidence.get(field), str) or not evidence[field].strip()
                           for field in ("paper_id", "chunk_id", "quote"))):
                errors.append(f"gold_evidence[{index}] needs paper_id, chunk_id, and exact quote")
                continue
            if evidence["paper_id"] not in paper_ids:
                errors.append(f"gold_evidence[{index}] references a paper outside paper_ids")
            evidence_key = (str(evidence["paper_id"]), str(evidence["chunk_id"]), str(evidence["quote"]))
            if evidence_key in seen_evidence:
                errors.append(f"gold_evidence[{index}] duplicates an earlier evidence passage")
            seen_evidence.add(evidence_key)
    if record.get("answerable") is True and not record.get("gold_evidence"):
        errors.append("answerable questions need at least one exact supporting passage")
    if (record.get("category") == "multi_hop_cross_paper" and record.get("answerable") is True
            and len({e.get("paper_id") for e in record.get("gold_evidence", []) if isinstance(e, dict)}) < 2):
        errors.append("answerable cross-paper questions need supporting passages from at least two papers")
    if not isinstance(record["gold_paths"], list):
        errors.append("gold_paths must be a list")
    else:
        for path_index, path in enumerate(record["gold_paths"]):
            if not isinstance(path, dict) or not isinstance(path.get("nodes"), list) or not isinstance(path.get("edges"), list):
                errors.append(f"gold_paths[{path_index}] needs nodes and directed edges arrays")
                continue
            if len(path["nodes"]) != len(path["edges"]) + 1:
                errors.append(f"gold_paths[{path_index}] must have one more node than edge")
                continue
            if len(path["nodes"]) < 2 or not path["edges"]:
                errors.append(f"gold_paths[{path_index}] must contain at least one directed transition")
            if any(not isinstance(node, str) or not node.strip() for node in path["nodes"]):
                errors.append(f"gold_paths[{path_index}].nodes must contain non-empty node IDs")
            for edge_index, edge in enumerate(path["edges"]):
                if (not isinstance(edge, dict) or edge.get("source") != path["nodes"][edge_index]
                        or edge.get("target") != path["nodes"][edge_index + 1] or not edge.get("type")):
                    errors.append(f"gold_paths[{path_index}].edges[{edge_index}] must match adjacent nodes and include type")
                elif (not isinstance(edge.get("source"), str) or not edge["source"].strip()
                      or not isinstance(edge.get("target"), str) or not edge["target"].strip()
                      or not isinstance(edge.get("type"), str) or not edge["type"].strip()):
                    errors.append(f"gold_paths[{path_index}].edges[{edge_index}] source, target, and type must be non-empty strings")
    if isinstance(record["required_hops"], bool) or not isinstance(record["required_hops"], int) or record["required_hops"] < 0:
        errors.append("required_hops must be a non-negative integer")
    elif record["answerable"] is True:
        if (isinstance(record["category"], str)
                and record["category"] in {"multi_hop_single_paper", "multi_hop_cross_paper"}
                and record["required_hops"] < 1):
            errors.append("answerable multi-hop questions need required_hops >= 1")
        if record["required_hops"] > 0 and not record["gold_paths"]:
            errors.append("answerable questions with required_hops > 0 need at least one adjudicated gold path")
        if record["required_hops"] == 0 and record["gold_paths"]:
            errors.append("gold_paths must be empty when required_hops is zero")
        if isinstance(record.get("gold_paths"), list):
            for path_index, path in enumerate(record["gold_paths"]):
                if isinstance(path, dict) and isinstance(path.get("edges"), list) and len(path["edges"]) != record["required_hops"]:
                    errors.append(f"gold_paths[{path_index}] edge count must match required_hops")
    annotation = record.get("annotation")
    if not isinstance(annotation, dict) or annotation.get("status") != "validated":
        errors.append("annotation.status must be 'validated'")
    else:
        reviewers = annotation.get("reviewers")
        if (not isinstance(reviewers, list)
                or any(not isinstance(reviewer, str) or not reviewer.strip() for reviewer in reviewers)
                or len(set(reviewers)) < 2):
            errors.append("validated records need at least two independent reviewer IDs")
        if annotation.get("adjudicated") is not True:
            errors.append("validated records must explicitly record adjudicated=true")
    return [f"{qid}: {message}" for message in errors]


def validate_dataset(document: Dict[str, Any], chunk_manifest: Dict[str, Any] | None = None) -> List[str]:
    if not isinstance(document, dict):
        return ["dataset root must be an object"]
    errors: List[str] = []
    if document.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    if not isinstance(document.get("corpus_version"), str) or not document["corpus_version"].strip():
        errors.append("corpus_version must be a non-empty string")
    corpus_papers = document.get("corpus_papers")
    if not isinstance(corpus_papers, list) or not corpus_papers:
        errors.append("corpus_papers must freeze at least one paper")
        corpus_ids: set[str] = set()
    else:
        corpus_ids = set()
        for index, paper in enumerate(corpus_papers):
            if not isinstance(paper, dict):
                errors.append(f"corpus_papers[{index}] must be an object")
                continue
            raw_paper_id = paper.get("paper_id")
            paper_id = raw_paper_id if isinstance(raw_paper_id, str) else ""
            if (not paper_id.strip() or paper_id != paper_id.strip()
                    or not isinstance(paper.get("title"), str) or not paper["title"].strip()
                    or not isinstance(paper.get("citation"), str) or not paper["citation"].strip()):
                errors.append(f"corpus_papers[{index}] needs paper_id, title, and citation")
            digest = str(paper.get("sha256", ""))
            if not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
                errors.append(f"corpus_papers[{index}].sha256 must be a 64-character hexadecimal checksum")
            if not paper_id:
                continue
            if paper_id in corpus_ids:
                errors.append(f"duplicate corpus paper_id: {paper_id}")
            corpus_ids.add(paper_id)
    records = document.get("questions")
    if not isinstance(records, list) or not records:
        return errors + ["questions must be a non-empty list"]
    ids = [record.get("question_id") for record in records if isinstance(record, dict)]
    if len(ids) != len(records):
        errors.append("every questions entry must be an object")
    valid_ids = [qid for qid in ids if isinstance(qid, str) and qid.strip()]
    if len(valid_ids) != len(ids):
        errors.append("every question_id must be a non-empty string")
    if len(valid_ids) != len(set(valid_ids)):
        errors.append("question_id values must be unique")
    for record in records:
        if not isinstance(record, dict):
            continue
        errors.extend(validate_record(record))
        paper_ids = record.get("paper_ids")
        unknown_papers = set(item for item in paper_ids if isinstance(item, str)) - corpus_ids if isinstance(paper_ids, list) else set()
        if unknown_papers:
            errors.append(f"{record.get('question_id')}: paper_ids absent from corpus_papers: {sorted(unknown_papers)}")
        if chunk_manifest is not None:
            for index, evidence in enumerate(record.get("gold_evidence", [])):
                if not isinstance(evidence, dict):
                    continue
                paper_chunks = chunk_manifest.get(str(evidence.get("paper_id")), [])
                known = set(paper_chunks.keys()) if isinstance(paper_chunks, dict) else set(paper_chunks)
                if str(evidence.get("chunk_id")) not in known:
                    errors.append(f"{record.get('question_id')}: gold_evidence[{index}] references a chunk absent from the frozen manifest")
                elif isinstance(paper_chunks, dict):
                    quote = str(evidence.get("quote", ""))
                    content = str(paper_chunks.get(str(evidence.get("chunk_id")), ""))
                    if quote and quote not in content:
                        errors.append(f"{record.get('question_id')}: gold_evidence[{index}] quote does not exactly occur in its indexed chunk")
    return errors


def load_dataset(path: str | Path, chunk_manifest_path: str | Path | None = None) -> Dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    manifest = json.loads(Path(chunk_manifest_path).read_text(encoding="utf-8")) if chunk_manifest_path else None
    errors = validate_dataset(document, manifest)
    if errors:
        raise ValueError("Invalid gold dataset:\n- " + "\n- ".join(errors))
    return document
