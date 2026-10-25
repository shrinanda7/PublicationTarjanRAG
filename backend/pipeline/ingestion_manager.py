"""Background Ingestion Job Manager with fine-grained status and progress states."""
import os
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from backend.config import settings
from backend.pipeline.pdf_extractor import pdf_extractor
from backend.pipeline.chunker import chunker
from backend.pipeline.extractor import extractor
from backend.pipeline.entity_merging import entity_merger
from backend.pipeline.neo4j_store import neo4j_store
from backend.pipeline.local_research_store import local_research_store
from backend.pipeline.embedding_index import index_chunk_embeddings

logger = logging.getLogger("graphrag.ingestion")

class JobStatus(BaseModel):
    job_id: str
    paper_id: str
    paper_title: str
    state: str = "QUEUED"  # QUEUED, EXTRACTING_PDF, CHUNKING, EXTRACTING_ENTITIES, MERGING_ENTITIES, STORING_GRAPH, COMPLETED, FAILED
    progress: int = 0      # 0 to 100
    message: str = "Job created"
    num_chunks: int = 0
    num_embeddings: int = 0
    embedding_error: Optional[str] = None
    num_entities: int = 0
    num_relations: int = 0
    error: Optional[str] = None
    storage_mode: Optional[str] = None  # "neo4j", "in_memory", "failed"
    durable: bool = False

class PaperMetadata(BaseModel):
    paper_id: str
    title: str
    filename: str
    file_size_kb: int
    is_preloaded: bool
    status: str = "ready" # pending, processing, ready, failed
    num_entities: int = 0
    num_relations: int = 0
    num_communities: int = 0
    storage_mode: Optional[str] = None  # "neo4j", "in_memory", "failed"
    durable: bool = False

class IngestionManager:
    """Orchestrates document ingestion background tasks and status tracking."""

    def __init__(self):
        self.jobs: Dict[str, JobStatus] = {}
        self.papers: Dict[str, PaperMetadata] = {}
        self._deleted_papers = set()
        self._init_preloaded_papers()

    def _init_preloaded_papers(self):
        """Register the 10 preloaded landmark research papers in the catalog."""
        if not settings.PAPERS_DIR.exists():
            return

        for pdf_file in settings.PAPERS_DIR.glob("*.pdf"):
            paper_id = pdf_file.stem
            if paper_id in self._deleted_papers or paper_id in self.papers:
                continue
            clean_title = pdf_file.stem.split("_", 1)[-1].replace("_", " ")
            size_kb = pdf_file.stat().st_size // 1024
            self.papers[paper_id] = PaperMetadata(
                paper_id=paper_id,
                title=clean_title,
                filename=pdf_file.name,
                file_size_kb=size_kb,
                is_preloaded=True,
                status="ready"
            )

    def get_all_papers(self) -> List[PaperMetadata]:
        return list(self.papers.values())

    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        return self.jobs.get(job_id)

    def delete_paper(self, paper_id: str) -> bool:
        """Purge paper from catalog, disk PDF files, and Neo4j graph storage."""
        self._deleted_papers.add(paper_id)
        removed = self.papers.pop(paper_id, None)
        try:
            neo4j_store.clear_paper_graph(paper_id)
        except Exception as e:
            logger.warning(f"Error purging paper {paper_id} from Neo4j: {e}")

        # Delete uploaded source files regardless of their supported format.
        for f in settings.PAPERS_DIR.glob(f"*{paper_id}*.*"):
            try:
                f.unlink(missing_ok=True)
            except Exception:
                pass
        return removed is not None or True

    async def start_ingestion(
        self,
        pdf_path: Path,
        paper_id: Optional[str] = None,
        title: Optional[str] = None,
        require_durable: bool = False,
        source_text: Optional[str] = None,
        source_filename: Optional[str] = None,
    ) -> str:
        """Start async ingestion job."""
        job_id = str(uuid.uuid4())[:8]
        pid = paper_id or pdf_path.stem
        ptype = title or pdf_path.stem.replace("_", " ")

        status = JobStatus(job_id=job_id, paper_id=pid, paper_title=ptype, state="QUEUED", progress=5)
        self.jobs[job_id] = status

        # Spawn background task
        asyncio.create_task(self._run_pipeline(job_id, pdf_path, pid, ptype, require_durable=require_durable, source_text=source_text, source_filename=source_filename))
        return job_id

    async def _run_pipeline(
        self,
        job_id: str,
        pdf_path: Path,
        paper_id: str,
        title: str,
        require_durable: bool = False,
        source_text: Optional[str] = None,
        source_filename: Optional[str] = None,
    ):
        status = self.jobs[job_id]
        try:
            # 1. Extract PDF or use text extracted by the primary document loader.
            status.state = "EXTRACTING_PDF" if source_text is None else "EXTRACTING_TEXT"
            status.progress = 15
            if source_text is None:
                status.message = "Extracting structured text and section headings from PDF..."
                sections = pdf_extractor.extract_from_pdf(pdf_path)
            else:
                status.message = "Preparing extracted document or webpage text..."
                sections = [{"title": source_filename or "Document text", "page": 1, "end_page": 1, "text": source_text}]

            # 2. Chunking
            status.state = "CHUNKING"
            status.progress = 30
            status.message = f"Partitioning {len(sections)} sections into semantic chunks..."
            chunks = chunker.chunk_sections(paper_id, sections)
            status.num_chunks = len(chunks)
            local_research_store.upsert_chunks(paper_id, chunks)
            if not chunks:
                raise RuntimeError("PDF text extraction produced no source chunks; check that the PDF contains readable text or OCR it first.")
            status.message = f"Created {len(chunks)} source chunks; building persistent dense vectors..."
            status.num_embeddings, status.embedding_error = await index_chunk_embeddings(paper_id, chunks)

            # 3. Entity & Relation Extraction
            status.state = "EXTRACTING_ENTITIES"
            status.progress = 50
            status.message = f"Extracting entities & directed relations from {len(chunks)} chunks..."

            raw_entities: List[Dict[str, Any]] = []
            raw_relations: List[Dict[str, Any]] = []

            # Process every chunk through the same extraction path. Limiting deep
            # extraction to four structurally selected chunks silently dropped
            # relations and made graph coverage depend on section labels. The
            # extractor itself has provider fallbacks; this small delay spaces
            # requests to reduce rate-limit pressure.
            for c in chunks:
                extracted = await extractor.extract_from_chunk(c)
                raw_entities.extend(extracted.get("entities", []))
                raw_relations.extend(extracted.get("relations", []))
                await asyncio.sleep(0.15)

            # 4. Entity Merging & Deduplication
            status.state = "MERGING_ENTITIES"
            status.progress = 75
            status.message = "Canonical entity resolution and alias merging..."
            merged_ents, merged_rels = entity_merger.merge_graph(raw_entities, raw_relations)
            status.num_entities = len(merged_ents)
            status.num_relations = len(merged_rels)

            # 5. Graph Persistence (Neo4j / fallback)
            status.state = "STORING_GRAPH"
            status.progress = 90
            status.message = f"Persisting {len(merged_ents)} entities and {len(merged_rels)} relations to graph..."
            persist_res = neo4j_store.save_entities_and_relations(
                paper_id,
                merged_ents,
                merged_rels,
                chunks,
                allow_memory_fallback=not require_durable
            )

            # Explicit check: Failed persistence must NOT report success
            if not persist_res.success or persist_res.storage_mode == "failed":
                status.state = "FAILED"
                status.progress = 90
                status.error = persist_res.error or "Graph persistence failed"
                status.message = f"Persistence failure: {persist_res.error or 'Failed to persist graph'}"
                status.storage_mode = "failed"
                status.durable = False
                logger.error(f"Ingestion job {job_id} failed persistence: {persist_res.error}")
                return

            if persist_res.storage_mode == "in_memory" and require_durable:
                status.state = "FAILED"
                status.progress = 90
                status.error = "Durable graph storage was required, but only in-memory storage was available"
                status.message = status.error
                status.storage_mode = "in_memory"
                status.durable = False
                return

            status.state = "COMPLETED"
            status.progress = 100
            status.storage_mode = persist_res.storage_mode
            status.durable = bool(persist_res.durable)
            store_label = {"neo4j": "Neo4j", "sqlite": "local SQLite", "in_memory": "memory"}.get(persist_res.storage_mode, persist_res.storage_mode)
            durable_label = "durably stored" if persist_res.durable else "not durably stored"
            status.message = (
                f"Graph {durable_label} in {store_label} with {len(merged_ents)} entities and {len(merged_rels)} relations. "
                f"{status.num_chunks} chunks saved locally and {status.num_embeddings} embeddings indexed."
            )
            if status.embedding_error:
                status.message += f" Dense indexing warning: {status.embedding_error}"

            file_size = (pdf_path.stat().st_size // 1024) if pdf_path.exists() else (len(source_text.encode("utf-8")) // 1024 if source_text else 0)
            self.papers[paper_id] = PaperMetadata(
                paper_id=paper_id,
                title=title,
                filename=source_filename or pdf_path.name,
                file_size_kb=file_size,
                is_preloaded=False,
                status="ready",
                num_entities=len(merged_ents),
                num_relations=len(merged_rels),
                storage_mode=persist_res.storage_mode,
                durable=bool(persist_res.durable)
            )
        except Exception as e:
            logger.error(f"Ingestion job {job_id} failed: {e}", exc_info=True)
            status.state = "FAILED"
            status.error = str(e)
            status.message = f"Ingestion error: {e}"
            status.storage_mode = "failed"
            status.durable = False

ingestion_manager = IngestionManager()
