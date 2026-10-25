"""Deterministic metrics for answer, evidence, citation, and path evaluation.

These metrics consume explicit gold annotations; question hints are not gold.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Sequence


def _tokens(text: str) -> list[str]:
    # SQuAD-style normalization: lowercase, remove punctuation/articles,
    # then compare token sequences or multisets.
    return [token for token in re.findall(r"[a-z0-9]+", str(text or "").lower())
            if token not in {"a", "an", "the"}]


def exact_match(prediction: str, references: Sequence[str]) -> float | None:
    refs = [ref for ref in references if str(ref).strip()]
    if not refs:
        return None
    pred = " ".join(_tokens(prediction))
    return float(any(pred == " ".join(_tokens(ref)) for ref in refs))


def token_f1(prediction: str, reference: str) -> float:
    """Multiset token F1; repeated terms count up to reference frequency."""
    from collections import Counter

    pred_tokens, ref_tokens = _tokens(prediction), _tokens(reference)
    if not pred_tokens or not ref_tokens:
        return float(pred_tokens == ref_tokens)
    overlap = sum((Counter(pred_tokens) & Counter(ref_tokens)).values())
    if not overlap:
        return 0.0
    precision, recall = overlap / len(pred_tokens), overlap / len(ref_tokens)
    return 2 * precision * recall / (precision + recall)


def best_reference_f1(prediction: str, references: Sequence[str]) -> float | None:
    refs = [ref for ref in references if str(ref).strip()]
    return max((token_f1(prediction, ref) for ref in refs), default=None)


def evidence_metrics(retrieved: Sequence[str], gold: Sequence[str], k: int | None = None) -> Dict[str, Any]:
    """Compute Evidence Precision/Recall@K, MRR@K, and Hit@K.

    IDs should be paper-scoped (``paper_id::chunk_id``). Recall is None when
    the question has no gold evidence; it is never assigned an artificial 1.
    """
    ranked = list(retrieved[:k] if k is not None else retrieved)
    gold_set = set(gold)
    relevant = sum(item in gold_set for item in ranked)
    first_rank = next((rank for rank, item in enumerate(ranked, 1) if item in gold_set), None)
    return {
        "precision": relevant / len(ranked) if ranked else 0.0,
        "recall": relevant / len(gold_set) if gold_set else None,
        "mrr": 1 / first_rank if first_rank else 0.0,
        "hit": float(first_rank is not None),
        "retrieved_count": len(ranked),
        "gold_count": len(gold_set),
    }


def directed_path_survives(path_nodes: Sequence[str], quotient_graph: Dict[str, Any]) -> bool:
    """Check that each gold-path transition remains represented in quotient."""
    if len(path_nodes) < 2:
        return False
    original_to_component: Dict[str, str] = {}
    for node in quotient_graph.get("nodes", []):
        component_id = str(node.get("id", ""))
        if not component_id:
            continue
        for member in node.get("member_node_ids") or [component_id]:
            original_to_component[str(member)] = component_id
    mapped = [original_to_component.get(str(node)) for node in path_nodes]
    if any(component is None for component in mapped):
        return False
    edges = {(str(e.get("source")), str(e.get("target"))) for e in quotient_graph.get("edges", [])}
    return all(a == b or (a, b) in edges for a, b in zip(mapped, mapped[1:]))


def path_survival_metrics(gold_paths: Sequence[Sequence[str]], quotient_graph: Dict[str, Any]) -> Dict[str, Any]:
    """Return binary PSR and its complement RCFR; None when no gold paths."""
    if not gold_paths:
        return {"psr": None, "rcfr": None, "preserved_paths": 0, "gold_paths": 0}
    if any(len(path) < 2 for path in gold_paths):
        raise ValueError("gold paths must contain at least one directed transition")
    preserved = sum(directed_path_survives(path, quotient_graph) for path in gold_paths)
    psr = preserved / len(gold_paths)
    return {"psr": psr, "rcfr": 1.0 - psr, "preserved_paths": preserved, "gold_paths": len(gold_paths)}


def exact_path_recall(retrieved_paths: Sequence[Sequence[str]], gold_paths: Sequence[Sequence[str]]) -> float | None:
    if not gold_paths:
        return None
    if any(len(path) < 2 for path in gold_paths):
        raise ValueError("gold paths must contain at least one directed transition")
    retrieved = {tuple(path) for path in retrieved_paths}
    return sum(tuple(path) in retrieved for path in gold_paths) / len(gold_paths)


def citation_precision_recall(cited_evidence: Iterable[str], gold_support: Iterable[str]) -> Dict[str, float | None]:
    cited, gold = set(cited_evidence), set(gold_support)
    overlap = len(cited & gold)
    return {"precision": overlap / len(cited) if cited else 0.0, "recall": overlap / len(gold) if gold else None}


def abstention_accuracy(predicted_abstention: bool, answerable: bool) -> float:
    return float(bool(predicted_abstention) == (not bool(answerable)))
