"""Chunk-level dense, BM25, and hybrid retrieval baselines.

These rankers do not call an answer model. Callers can feed the returned ranked
chunks into the same synthesis and budget policy as Tarjan-RAG. Dense retrieval
uses the configured Ollama embedding model for both query and document chunks;
hybrid retrieval uses equal-weight reciprocal-rank fusion (RRF, k=60).
"""
from __future__ import annotations

import math
import re
import time
import asyncio
from collections import Counter
from typing import Any, Dict, List, Sequence

from backend.config import settings
from backend.core.llm_client import ollama_client
from backend.pipeline.local_research_store import local_research_store


def _tokens(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", str(text or "").lower())


def _documents(chunks: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    docs = []
    seen = set()
    for chunk in chunks:
        paper_id = str(chunk.get("paper_id", ""))
        chunk_id = str(chunk.get("chunk_id", ""))
        content = str(chunk.get("content", "")).strip()
        key = (paper_id, chunk_id)
        if not paper_id or not chunk_id or not content or key in seen:
            continue
        seen.add(key)
        docs.append({**chunk, "paper_id": paper_id, "chunk_id": chunk_id, "content": content})
    return docs


def rank_bm25(
    question: str,
    chunks: Sequence[Dict[str, Any]],
    *,
    top_k: int | None = None,
    k1: float = 1.2,
    b: float = 0.75,
) -> Dict[str, Any]:
    """Rank chunks with Robertson-Sparck Jones BM25 using k1=1.2, b=0.75."""
    started = time.perf_counter()
    if k1 <= 0 or not 0 <= b <= 1:
        raise ValueError("BM25 requires k1 > 0 and b in [0, 1]")
    docs = _documents(chunks)
    query_terms = _tokens(question)
    token_lists = [_tokens(doc["content"]) for doc in docs]
    doc_freq = Counter(term for tokens in token_lists for term in set(tokens))
    avg_len = sum(map(len, token_lists)) / len(token_lists) if token_lists else 0.0
    n_docs = len(docs)
    ranked = []
    for doc, tokens in zip(docs, token_lists):
        freqs = Counter(tokens)
        score = 0.0
        for term in query_terms:
            frequency = freqs[term]
            if frequency == 0:
                continue
            df = doc_freq[term]
            idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (1.0 - b + b * len(tokens) / max(avg_len, 1e-12))
            score += idf * frequency * (k1 + 1.0) / denominator
        if score > 0:
            ranked.append({**doc, "score": score})
    ranked.sort(key=lambda item: (-item["score"], item["paper_id"], item["chunk_id"]))
    if top_k is not None:
        ranked = ranked[:max(0, top_k)]
    for index, item in enumerate(ranked, 1):
        item["rank"] = index
    return {
        "method": "bm25",
        "parameters": {"k1": k1, "b": b},
        "ranked": ranked,
        "telemetry": {
            "embedding_calls": 0,
            "embedding_tokens": 0,
            "embedding_latency_ms": 0.0,
            "retrieval_latency_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }


def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
    if not left or len(left) != len(right):
        raise ValueError("Embedding vectors must be non-empty and have matching dimensions")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


async def rank_dense(
    question: str,
    chunks: Sequence[Dict[str, Any]],
    *,
    top_k: int | None = None,
    embedder=None,
) -> Dict[str, Any]:
    """Rank chunks by cosine similarity from the same configured embedding model."""
    docs = _documents(chunks)
    if not docs:
        return {"method": "dense", "model": settings.OLLAMA_EMBED_MODEL, "ranked": [], "telemetry": {"embedding_calls": 0, "embedding_tokens": 0, "embedding_latency_ms": 0.0, "retrieval_latency_ms": 0.0}}
    embed = embedder or ollama_client.get_embedding
    started = time.perf_counter()
    query_vector, query_log = await embed(question, raise_on_error=True)
    if query_log.status not in {"success", "mock"} or not query_vector:
        raise RuntimeError(f"Query embedding failed: {query_log.status}")
    if query_log.status == "mock":
        raise RuntimeError("Dense baseline refuses mock embeddings; configure the real embedding service")
    total_tokens = int(query_log.total_tokens or 0)
    total_embedding_latency_ms = float(query_log.latency_ms or 0.0)
    calls = 1
    semaphore = asyncio.Semaphore(8)

    async def embed_document(doc):
        async with semaphore:
            return await embed(doc["content"], raise_on_error=True)

    cached_vectors = [
        local_research_store.get_embedding(doc["paper_id"], doc["chunk_id"], settings.OLLAMA_EMBED_MODEL, doc["content"])
        if embedder is None else None
        for doc in docs
    ]
    missing_indices = [index for index, vector in enumerate(cached_vectors) if not vector]
    fresh_embeddings = await asyncio.gather(*(embed_document(docs[index]) for index in missing_indices))
    for index, (vector, log) in zip(missing_indices, fresh_embeddings):
        cached_vectors[index] = vector
        if log.status != "success" or not vector:
            raise RuntimeError(f"Document embedding failed for {docs[index]['paper_id']}::{docs[index]['chunk_id']}: {log.status}")
        if embedder is None:
            local_research_store.save_embedding(docs[index]["paper_id"], docs[index]["chunk_id"], settings.OLLAMA_EMBED_MODEL, docs[index]["content"], vector)
    ranked = []
    logs_by_index = dict(zip(missing_indices, fresh_embeddings))
    for index, (doc, vector) in enumerate(zip(docs, cached_vectors)):
        if index in logs_by_index:
            _, log = logs_by_index[index]
            calls += 1
            total_tokens += int(log.total_tokens or 0)
            total_embedding_latency_ms += float(log.latency_ms or 0.0)
        ranked.append({**doc, "score": _cosine(query_vector, vector)})
    ranked.sort(key=lambda item: (-item["score"], item["paper_id"], item["chunk_id"]))
    if top_k is not None:
        ranked = ranked[:max(0, top_k)]
    for index, item in enumerate(ranked, 1):
        item["rank"] = index
    return {
        "method": "dense",
        "model": settings.OLLAMA_EMBED_MODEL,
        "ranked": ranked,
        "telemetry": {
            "embedding_calls": calls,
            "embedding_tokens": total_tokens,
            "embedding_latency_ms": round(total_embedding_latency_ms, 2),
            "retrieval_latency_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    }


async def rank_hybrid(
    question: str,
    chunks: Sequence[Dict[str, Any]],
    *,
    top_k: int | None = None,
    rrf_k: int = 60,
    embedder=None,
) -> Dict[str, Any]:
    """Equal-weight reciprocal-rank fusion of BM25 and dense rankings."""
    if rrf_k <= 0:
        raise ValueError("rrf_k must be positive")
    sparse = rank_bm25(question, chunks)
    dense = await rank_dense(question, chunks, embedder=embedder)
    scores: Dict[tuple[str, str], float] = {}
    docs: Dict[tuple[str, str], Dict[str, Any]] = {}
    for result in (sparse, dense):
        for item in result["ranked"]:
            key = (item["paper_id"], item["chunk_id"])
            docs[key] = item
            scores[key] = scores.get(key, 0.0) + 1.0 / (rrf_k + item["rank"])
    ranked = [
        {**docs[key], "score": score}
        for key, score in scores.items()
    ]
    ranked.sort(key=lambda item: (-item["score"], item["paper_id"], item["chunk_id"]))
    if top_k is not None:
        ranked = ranked[:max(0, top_k)]
    for index, item in enumerate(ranked, 1):
        item["rank"] = index
    return {
        "method": "hybrid_rrf",
        "parameters": {"sparse_weight": 1.0, "dense_weight": 1.0, "rrf_k": rrf_k},
        "model": settings.OLLAMA_EMBED_MODEL,
        "ranked": ranked,
        "telemetry": {
            **dense["telemetry"],
            "retrieval_latency_ms": round(
                float(dense["telemetry"].get("retrieval_latency_ms", 0.0))
                + float(sparse["telemetry"].get("retrieval_latency_ms", 0.0)),
                2,
            ),
        },
    }
