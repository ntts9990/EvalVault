import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

from evalvault.adapters.outbound.kg.parallel_kg_builder import ParallelKGBuilder
from evalvault.config.settings import Settings, get_settings

router = APIRouter(tags=["knowledge"])

DATA_DIR = Path("data/raw")
KG_OUTPUT_DIR = Path("data/kg")
DATA_DIR.mkdir(parents=True, exist_ok=True)
KG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# In-memory job tracking (similar to runs)
KG_JOBS: dict[str, dict[str, Any]] = {}


def _normalize_tokens(raw_tokens: str | None) -> set[str]:
    if not raw_tokens:
        return set()
    return {token.strip() for token in raw_tokens.split(",") if token.strip()}


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header:
        return None
    prefix = "bearer "
    if auth_header.lower().startswith(prefix):
        return auth_header[len(prefix) :].strip()
    return None


def _require_knowledge_read_token(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    read_tokens = _normalize_tokens(settings.knowledge_read_tokens)
    write_tokens = _normalize_tokens(settings.knowledge_write_tokens)
    if not read_tokens and not write_tokens:
        return
    token = _extract_bearer_token(request)
    if token is None or token not in (read_tokens | write_tokens):
        raise HTTPException(status_code=403, detail="Invalid or missing knowledge read token")


def _require_knowledge_write_token(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    write_tokens = _normalize_tokens(settings.knowledge_write_tokens)
    if not write_tokens:
        return
    token = _extract_bearer_token(request)
    if token is None or token not in write_tokens:
        raise HTTPException(status_code=403, detail="Invalid or missing knowledge write token")


class BuildKGRequest(BaseModel):
    workers: int = 4
    batch_size: int = 32
    store_documents: bool = False
    rebuild: bool = False


@router.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    _: None = Depends(_require_knowledge_write_token),
):
    """Upload documents for Knowledge Graph building."""
    uploaded = []
    for file in files:
        if not file.filename:
            continue
        file_path = DATA_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded.append(file.filename)
    return {"message": f"Uploaded {len(uploaded)} files", "files": uploaded}


@router.get("/files")
def list_files(
    _: None = Depends(_require_knowledge_read_token),
):
    """List uploaded files."""
    files = []
    if DATA_DIR.exists():
        files = [f.name for f in DATA_DIR.iterdir() if f.is_file() and f.name != ".gitkeep"]
    return files


@router.post("/build", status_code=202)
async def build_knowledge_graph(
    request: BuildKGRequest,
    background_tasks: BackgroundTasks,
    _: None = Depends(_require_knowledge_write_token),
):
    """Trigger background Knowledge Graph construction."""
    job_id = f"kg_build_{len(KG_JOBS) + 1}"
    KG_JOBS[job_id] = {"status": "pending", "progress": "0%", "details": "Queued"}

    def _run_build():
        try:
            KG_JOBS[job_id]["status"] = "running"
            KG_JOBS[job_id]["details"] = "Loading documents..."

            # Load documents (simple text loader matching CLI logic)
            documents = []
            for path in sorted(DATA_DIR.rglob("*")):
                if path.is_file() and path.suffix.lower() in {".txt", ".md", ".json", ".csv"}:
                    text = path.read_text(encoding="utf-8").strip()
                    if text:
                        documents.append(text)

            if not documents:
                KG_JOBS[job_id]["status"] = "failed"
                KG_JOBS[job_id]["details"] = "No documents found in data/raw"
                return

            KG_JOBS[job_id]["details"] = f"Processing {len(documents)} documents..."

            # Progress callback
            def progress_callback(stats):
                p = int((stats.chunks_processed / (len(documents) * 1.5)) * 100)  # Rough estimate
                p = min(p, 99)
                KG_JOBS[job_id]["progress"] = f"{p}%"
                KG_JOBS[job_id]["details"] = (
                    f"Processed {stats.documents_processed} docs, {stats.entities_added} entities"
                )

            builder = ParallelKGBuilder(
                workers=request.workers,
                batch_size=request.batch_size,
                store_documents=request.store_documents,
                progress_callback=progress_callback,
            )

            result = builder.build(documents)

            # Save default output
            output_path = KG_OUTPUT_DIR / "knowledge_graph.json"

            # Save result logic (simplified from CLI)
            payload = {
                "type": "kg_build_result",
                "stats": result.stats.snapshot(),
                "graph": result.graph.to_dict(),
            }
            import json

            output_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            KG_JOBS[job_id]["status"] = "completed"
            KG_JOBS[job_id]["progress"] = "100%"
            KG_JOBS[job_id]["details"] = f"Completed. Added {result.stats.entities_added} entities."

        except Exception as e:
            KG_JOBS[job_id]["status"] = "failed"
            KG_JOBS[job_id]["details"] = str(e)
            print(f"KG Build failed: {e}")

    background_tasks.add_task(_run_build)
    return {"status": "accepted", "job_id": job_id}


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: str,
    _: None = Depends(_require_knowledge_read_token),
):
    job = KG_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/stats")
def get_graph_stats(
    _: None = Depends(_require_knowledge_read_token),
):
    """Get statistics of the built Knowledge Graph."""
    # Try to load from memory DB or default output JSON
    # For now, we'll try to load the JSON if it exists, or just return empty
    output_path = KG_OUTPUT_DIR / "knowledge_graph.json"
    if not output_path.exists():
        return {"num_entities": 0, "num_relations": 0, "status": "not_built"}

    try:
        # Determine based on file size if we should load full JSON
        # For a real app, this should query a DB.
        # Here we just mock it or read basic stats if we saved them separately.
        # Let's assume we saved a stats.json alongside
        return {
            "status": "available",
            "message": "Graph exists (detailed stats loading to be implemented)",
        }
    except Exception:
        return {"status": "error", "message": "Failed to load stats"}
