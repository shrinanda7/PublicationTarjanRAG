"""Build and persist chunk vectors in the local SQLite vector index."""
from __future__ import annotations

import asyncio
import httpx
from typing import Any, Dict, List, Tuple

from backend.config import settings
from backend.core.llm_client import ollama_client
from backend.pipeline.local_research_store import local_research_store


async def index_chunk_embeddings(paper_id: str, chunks: List[Dict[str, Any]]) -> Tuple[int, str | None]:
    """Embed missing chunks; keep text indexing usable if the embedding service is offline."""
    semaphore = asyncio.Semaphore(8)
    missing = [
        chunk for chunk in chunks
        if not local_research_store.get_embedding(
            paper_id, str(chunk.get("chunk_id", "")), settings.OLLAMA_EMBED_MODEL, str(chunk.get("content", ""))
        )
    ]
    if not missing:
        return len(chunks), None

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{ollama_client.base_url}/api/tags")
            response.raise_for_status()
    except Exception as exc:
        count = len(chunks) - len(missing)
        return count, f"embedding service unavailable at {ollama_client.base_url}: {exc}"

    async def embed_one(chunk):
        async with semaphore:
            vector, log = await ollama_client.get_embedding(str(chunk["content"]), raise_on_error=True)
        if log.status != "success" or not vector:
            raise RuntimeError(f"Embedding failed for {chunk['chunk_id']}: {log.status}")
        local_research_store.save_embedding(paper_id, str(chunk["chunk_id"]), settings.OLLAMA_EMBED_MODEL, str(chunk["content"]), vector)

    try:
        await asyncio.gather(*(embed_one(chunk) for chunk in missing))
        return len(chunks), None
    except Exception as exc:
        count = sum(
            local_research_store.get_embedding(paper_id, str(chunk.get("chunk_id", "")), settings.OLLAMA_EMBED_MODEL, str(chunk.get("content", ""))) is not None
            for chunk in chunks
        )
        return count, f"Stored {count}/{len(chunks)} chunk embeddings; embedding service error: {exc}"
