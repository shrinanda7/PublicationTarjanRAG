"""FastAPI Application for Knowledge Graph RAG with Streaming API and Graph Inspection."""
import os
import json
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from backend.config import settings
from backend.pipeline.ingestion_manager import ingestion_manager, PaperMetadata
from backend.search.query_router import query_router
from backend.pipeline.neo4j_store import neo4j_store
from backend.core.compression import compressor
from backend.search.multi_paper_search import multi_paper_search
from backend.search.baseline_query import BASELINE_METHODS, baseline_query

logger = logging.getLogger("graphrag.api")

app = FastAPI(
    title="Knowledge-Graph RAG API",
    description="Research Paper Knowledge-Graph RAG with Tarjan Compression and Dynamic Traversal",
    version="1.0.0"
)

# Explicit origin allowlist; override for a deployed frontend via CORS_ALLOW_ORIGINS.
_allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    paper_id: str
    paper_title: Optional[str] = None
    question: str
    mode: str = "ours" # "ours", "dynamic", "static", "local", "auto"
    llm_budget: Optional[int] = None
    conversation_context: str = Field(default="", max_length=4000)

class MultiPaperQueryRequest(BaseModel):
    paper_ids: List[str] = Field(min_length=1, max_length=12)
    paper_titles: Dict[str, str] = Field(default_factory=dict)
    question: str = Field(min_length=3, max_length=4000)
    mode: str = "ours"
    conversation_context: str = Field(default="", max_length=4000)
    max_evidence_chunks: int = Field(default=10, ge=1, le=30)
    max_context_chars: int = Field(default=24000, ge=2000, le=60000)
    max_context_tokens: int = Field(default=settings.MAX_TOKEN_BUDGET, ge=256, le=32000)

class ConfigUpdateRequest(BaseModel):
    ENABLE_TARJAN_COMPRESSION: Optional[bool] = None
    ENABLE_BRIDGE_AWARE_PRUNING: Optional[bool] = None
    ENABLE_BUDGET_AWARE_TRAVERSAL: Optional[bool] = None
    ENABLE_CROSS_PAPER_LINKS: Optional[bool] = None
    ENABLE_EVIDENCE_RECOVERY: Optional[bool] = None
    ENABLE_QUERY_CONDITIONED_TRAVERSAL: Optional[bool] = None
    RELEVANCE_THRESHOLD: Optional[float] = None
    TOTAL_LLM_BUDGET: Optional[int] = None
    MAX_COMMUNITY_DEPTH: Optional[int] = None

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "Knowledge Graph RAG", "index_schema_version": 2}

@app.get("/api/papers", response_model=List[PaperMetadata])
async def list_papers():
    """List all preloaded landmark and uploaded research papers."""
    return ingestion_manager.get_all_papers()

@app.delete("/api/papers/{paper_id}")
async def delete_paper(paper_id: str):
    """Purge paper from catalog, disk, and Neo4j graph storage."""
    ingestion_manager.delete_paper(paper_id)
    return {"success": True, "message": f"Paper '{paper_id}' deleted successfully from backend."}

@app.post("/api/neo4j/clear")
async def clear_neo4j_database():
    """Purge all nodes and relationships from Neo4j Aura database."""
    res = neo4j_store.clear_all_graphs()
    return res

@app.post("/api/upload")
async def upload_paper(
    file: Optional[UploadFile] = File(None),
    preloaded_id: Optional[str] = Form(None),
    paper_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    content: Optional[str] = Form(None),
    filename: Optional[str] = Form(None)
):
    """Upload a PDF research paper or trigger ingestion of a preloaded landmark paper."""
    if file:
        # Never use a client-supplied filename as a filesystem path.
        original_name = Path(file.filename or "upload.pdf").name
        if Path(original_name).suffix.lower() != ".pdf":
            raise HTTPException(status_code=415, detail="Only PDF files are accepted")

        # UploadFile is spooled by Starlette; reject oversized payloads before saving.
        max_upload_bytes = 50 * 1024 * 1024
        if file.size is not None and file.size > max_upload_bytes:
            raise HTTPException(status_code=413, detail="PDF exceeds the 50 MiB upload limit")

        content = await file.read(max_upload_bytes + 1)
        if len(content) > max_upload_bytes:
            raise HTTPException(status_code=413, detail="PDF exceeds the 50 MiB upload limit")
        if not content.startswith(b"%PDF-"):
            raise HTTPException(status_code=415, detail="Uploaded file does not have a valid PDF signature")

        if paper_id and (not all(ch.isalnum() or ch in "_.-" for ch in paper_id) or ".." in paper_id):
            raise HTTPException(status_code=400, detail="Invalid paper identifier")

        # Keep the research backend paper namespace aligned with the UI catalog.
        safe_filename = f"upload_{uuid.uuid4().hex}.pdf"
        dest_path = settings.PAPERS_DIR / safe_filename
        dest_path.write_bytes(content)
        job_id = await ingestion_manager.start_ingestion(
            pdf_path=dest_path,
            paper_id=paper_id,
            title=title or Path(original_name).stem.replace("_", " ")
        )
        return {"job_id": job_id, "message": "Ingestion started for uploaded PDF"}

    elif content is not None:
        if len(content.encode("utf-8")) > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Extracted source text exceeds the 50 MiB limit")
        if len(content.strip()) < 20:
            raise HTTPException(status_code=422, detail="Extracted source text is too short to index")
        original_name = Path(filename or "document.txt").name[:240]
        if paper_id and (not all(ch.isalnum() or ch in "_.-" for ch in paper_id) or ".." in paper_id):
            raise HTTPException(status_code=400, detail="Invalid paper identifier")
        source_tag = paper_id or f"source_{uuid.uuid4().hex}"
        dest_path = settings.PAPERS_DIR / f"source_{source_tag}_{uuid.uuid4().hex}.txt"
        dest_path.write_text(content, encoding="utf-8")
        job_id = await ingestion_manager.start_ingestion(
            pdf_path=dest_path,
            paper_id=paper_id,
            title=title or Path(original_name).stem.replace("_", " "),
            source_text=content,
            source_filename=original_name,
        )
        return {"job_id": job_id, "message": "Ingestion started for extracted document text"}

    elif preloaded_id:
        # Paper identifiers are not paths or glob expressions.
        if not preloaded_id or not all(ch.isalnum() or ch in "_.-" for ch in preloaded_id) or ".." in preloaded_id:
            raise HTTPException(status_code=400, detail="Invalid preloaded paper identifier")
        target_path = None
        for p in settings.PAPERS_DIR.glob(f"*{preloaded_id}*.pdf"):
            target_path = p
            break

        if not target_path:
            # Check by exact name match
            target_path = settings.PAPERS_DIR / f"{preloaded_id}.pdf"

        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Preloaded paper {preloaded_id} not found")

        job_id = await ingestion_manager.start_ingestion(
            pdf_path=target_path,
            paper_id=target_path.stem,
            title=title or target_path.stem.split("_", 1)[-1].replace("_", " ")
        )
        return {"job_id": job_id, "message": f"Ingestion started for landmark paper {target_path.name}"}

    else:
        raise HTTPException(status_code=400, detail="Must provide either a file upload or preloaded_id")

@app.get("/api/jobs/{job_id}")
@app.get("/api/ingestion/status/{job_id}")
async def get_job_status(job_id: str):
    """Poll background ingestion progress."""
    status = ingestion_manager.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@app.get("/api/graph/{paper_id}")
async def get_paper_graph(paper_id: str):
    """Return both original knowledge graph and Tarjan-compressed quotient graph."""
    paper_data = neo4j_store.get_paper_graph(paper_id) or {}
    nodes = paper_data.get("nodes", [])
    edges = paper_data.get("edges", [])

    if not nodes:
        return {
            "status": "no_indexed_graph",
            "paper_id": paper_id,
            "original_graph": {**paper_data, "nodes": [], "edges": [], "node_count": 0, "edge_count": 0},
            "compressed_graph": {
                "nodes": [], "edges": [], "diagnostics": {},
                "compression_ratio": 0.0, "articulation_points": [],
                "bridges": [], "node_count": 0, "edge_count": 0,
            },
        }

    compressed = compressor.compress_graph(nodes, edges)

    return {
        "paper_id": paper_id,
        "original_graph": {
            **paper_data,
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        },
        "compressed_graph": {
            "nodes": compressed["nodes"],
            "edges": compressed["edges"],
            "diagnostics": compressed["diagnostics"],
            "compression_ratio": compressed["compression_ratio"],
            "articulation_points": compressed["articulation_points"],
            "bridges": compressed["bridges"],
            "node_count": len(compressed["nodes"]),
            "edge_count": len(compressed["edges"])
        }
    }

@app.post("/api/query")
async def execute_query(req: QueryRequest):
    """Synchronously execute RAG query and return answer with traversal trace."""
    title = req.paper_title or req.paper_id.split("_", 1)[-1].replace("_", " ")
    budget = req.llm_budget or settings.TOTAL_LLM_BUDGET

    res = await query_router.execute_query(
        question=req.question,
        paper_id=req.paper_id,
        paper_title=title,
        mode=req.mode,
        llm_budget=budget,
        conversation_context=req.conversation_context,
    )
    return res

@app.post("/api/query/multi-paper")
async def execute_multi_paper_query(req: MultiPaperQueryRequest):
    """Answer across indexed papers using Tarjan graph retrieval or a chunk baseline."""
    # Reject duplicates/blank IDs early and avoid arbitrary path-like identifiers.
    paper_ids = list(dict.fromkeys(pid.strip() for pid in req.paper_ids if pid and pid.strip()))
    if not paper_ids:
        raise HTTPException(status_code=422, detail="Provide at least one non-empty paper_id")
    for pid in paper_ids:
        if not all(ch.isalnum() or ch in "_.-" for ch in pid) or ".." in pid:
            raise HTTPException(status_code=422, detail=f"Invalid paper identifier: {pid!r}")
    if req.mode in BASELINE_METHODS:
        return await baseline_query.search(
            method=req.mode,
            question=req.question,
            paper_ids=paper_ids,
            paper_titles=req.paper_titles,
            max_evidence_chunks=req.max_evidence_chunks,
            max_context_chars=req.max_context_chars,
            max_context_tokens=req.max_context_tokens,
            conversation_context=req.conversation_context,
        )
    if req.mode != "ours":
        raise HTTPException(status_code=422, detail="Supported query modes are ours, bm25, dense, and hybrid.")
    return await multi_paper_search.search(
        question=req.question,
        paper_ids=paper_ids,
        paper_titles=req.paper_titles,
        max_evidence_chunks=req.max_evidence_chunks,
        max_context_chars=req.max_context_chars,
        max_context_tokens=req.max_context_tokens,
        conversation_context=req.conversation_context,
    )


@app.post("/api/query/stream")
async def execute_query_stream(req: QueryRequest):
    """Stream answer tokens and traversal trace events via Server-Sent Events (SSE)."""
    title = req.paper_title or req.paper_id.split("_", 1)[-1].replace("_", " ")
    budget = req.llm_budget or settings.TOTAL_LLM_BUDGET

    async def event_generator():
        # Execute the query logic
        result = await query_router.execute_query(
            question=req.question,
            paper_id=req.paper_id,
            paper_title=title,
            mode=req.mode,
            llm_budget=budget,
            conversation_context=req.conversation_context,
        )

        # 1. Yield graph topologies first
        yield f"event: topology\ndata: {json.dumps({'original_graph': result.get('original_graph'), 'compressed_graph': result.get('compressed_graph'), 'communities': result.get('communities')})}\n\n"
        await asyncio.sleep(0.05)

        # 2. Stream traversal trace steps sequentially for animation
        trace = result.get("trace", {})
        steps = trace.get("steps", [])
        for step in steps:
            yield f"event: trace_step\ndata: {json.dumps(step)}\n\n"
            await asyncio.sleep(0.04)

        # 3. Stream answer tokens
        full_answer = result.get("answer", "")
        words = full_answer.split(" ")
        for i in range(0, len(words), 3):
            chunk_tokens = " ".join(words[i:i+3]) + " "
            yield f"event: answer_token\ndata: {json.dumps({'token': chunk_tokens})}\n\n"
            await asyncio.sleep(0.02)

        # 4. Final summary event
        summary_payload = {
            "mode": result.get("mode"),
            "total_tokens": result.get("total_tokens"),
            "total_llm_calls": result.get("total_llm_calls"),
            "latency_ms": result.get("latency_ms"),
            "selected_reports": result.get("selected_reports", []),
            "bridge_kept_count": result.get("bridge_kept_count", 0),
            "ratings": trace.get("ratings", {})
        }
        yield f"event: complete\ndata: {json.dumps(summary_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/api/config")
async def get_config():
    """Get active ablation toggles and parameters."""
    return {
        "ENABLE_TARJAN_COMPRESSION": settings.ENABLE_TARJAN_COMPRESSION,
        "ENABLE_BRIDGE_AWARE_PRUNING": settings.ENABLE_BRIDGE_AWARE_PRUNING,
        "ENABLE_BUDGET_AWARE_TRAVERSAL": settings.ENABLE_BUDGET_AWARE_TRAVERSAL,
        "ENABLE_CROSS_PAPER_LINKS": settings.ENABLE_CROSS_PAPER_LINKS,
        "ENABLE_EVIDENCE_RECOVERY": settings.ENABLE_EVIDENCE_RECOVERY,
        "ENABLE_QUERY_CONDITIONED_TRAVERSAL": settings.ENABLE_QUERY_CONDITIONED_TRAVERSAL,
        "GIANT_SCC_THRESHOLD": settings.GIANT_SCC_THRESHOLD,
        "RELEVANCE_THRESHOLD": settings.RELEVANCE_THRESHOLD,
        "TOTAL_LLM_BUDGET": settings.TOTAL_LLM_BUDGET,
        "MAX_COMMUNITY_DEPTH": settings.MAX_COMMUNITY_DEPTH,
        "OLLAMA_SMALL_MODEL": settings.OLLAMA_SMALL_MODEL,
        "OLLAMA_LARGE_MODEL": settings.OLLAMA_LARGE_MODEL,
    }

@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    """Dynamically toggle ablations and update runtime parameters."""
    if req.ENABLE_TARJAN_COMPRESSION is not None:
        settings.ENABLE_TARJAN_COMPRESSION = req.ENABLE_TARJAN_COMPRESSION
    if req.ENABLE_BRIDGE_AWARE_PRUNING is not None:
        settings.ENABLE_BRIDGE_AWARE_PRUNING = req.ENABLE_BRIDGE_AWARE_PRUNING
    if req.ENABLE_BUDGET_AWARE_TRAVERSAL is not None:
        settings.ENABLE_BUDGET_AWARE_TRAVERSAL = req.ENABLE_BUDGET_AWARE_TRAVERSAL
    if req.ENABLE_CROSS_PAPER_LINKS is not None:
        settings.ENABLE_CROSS_PAPER_LINKS = req.ENABLE_CROSS_PAPER_LINKS
    if req.ENABLE_EVIDENCE_RECOVERY is not None:
        settings.ENABLE_EVIDENCE_RECOVERY = req.ENABLE_EVIDENCE_RECOVERY
    if req.ENABLE_QUERY_CONDITIONED_TRAVERSAL is not None:
        settings.ENABLE_QUERY_CONDITIONED_TRAVERSAL = req.ENABLE_QUERY_CONDITIONED_TRAVERSAL
    if req.RELEVANCE_THRESHOLD is not None:
        settings.RELEVANCE_THRESHOLD = req.RELEVANCE_THRESHOLD
    if req.TOTAL_LLM_BUDGET is not None:
        settings.TOTAL_LLM_BUDGET = req.TOTAL_LLM_BUDGET
    if req.MAX_COMMUNITY_DEPTH is not None:
        settings.MAX_COMMUNITY_DEPTH = req.MAX_COMMUNITY_DEPTH

    return await get_config()
