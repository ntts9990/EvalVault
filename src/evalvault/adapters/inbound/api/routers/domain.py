"""API Router for Domain Memory."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from evalvault.adapters.outbound.domain_memory import build_domain_memory_adapter
from evalvault.config.settings import get_settings
from evalvault.ports.outbound.domain_memory_port import DomainMemoryPort

router = APIRouter()
_settings = get_settings()
DEFAULT_MEMORY_DB_PATH = (
    _settings.evalvault_memory_db_path if _settings.db_backend == "sqlite" else None
)


def get_memory_adapter(db_path: str | None = DEFAULT_MEMORY_DB_PATH) -> DomainMemoryPort:
    """Get memory adapter instance."""
    from pathlib import Path

    return build_domain_memory_adapter(db_path=Path(db_path) if db_path else None)


# --- Pydantic Models ---
class FactResponse(BaseModel):
    fact_id: str
    subject: str
    predicate: str
    object: str
    language: str | None
    domain: str | None
    verification_score: float
    verification_count: int
    created_at: str

    model_config = {"from_attributes": True}


class BehaviorResponse(BaseModel):
    behavior_id: str
    description: str
    trigger_pattern: str | None
    success_rate: float
    use_count: int
    last_used: str

    model_config = {"from_attributes": True}


# --- Endpoints ---


@router.get("/facts", response_model=list[FactResponse])
def list_facts(
    domain: str | None = None,
    language: str | None = None,
    subject: str | None = None,
    limit: int = 100,
    db_path: str = DEFAULT_MEMORY_DB_PATH,
):
    """List factual facts."""
    adapter = get_memory_adapter(db_path)
    facts = adapter.list_facts(domain=domain, language=language, subject=subject, limit=limit)
    return [
        FactResponse(
            fact_id=f.fact_id,
            subject=f.subject,
            predicate=f.predicate,
            object=f.object,
            language=f.language,
            domain=f.domain,
            verification_score=f.verification_score,
            verification_count=f.verification_count,
            created_at=f.created_at.isoformat(),
        )
        for f in facts
    ]


@router.get("/facts/{fact_id}", response_model=FactResponse)
def get_fact(fact_id: str, db_path: str = DEFAULT_MEMORY_DB_PATH):
    """Get a specific fact."""
    adapter = get_memory_adapter(db_path)
    try:
        f = adapter.get_fact(fact_id)
        return FactResponse(
            fact_id=f.fact_id,
            subject=f.subject,
            predicate=f.predicate,
            object=f.object,
            language=f.language,
            domain=f.domain,
            verification_score=f.verification_score,
            verification_count=f.verification_count,
            created_at=f.created_at.isoformat(),
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Fact not found")


@router.delete("/facts/{fact_id}")
def delete_fact(fact_id: str, db_path: str = DEFAULT_MEMORY_DB_PATH):
    """Delete a fact."""
    adapter = get_memory_adapter(db_path)
    if adapter.delete_fact(fact_id):
        return {"status": "deleted", "fact_id": fact_id}
    raise HTTPException(status_code=404, detail="Fact not found")


@router.get("/behaviors", response_model=list[BehaviorResponse])
def list_behaviors(
    domain: str | None = None, limit: int = 100, db_path: str = DEFAULT_MEMORY_DB_PATH
):
    """List behaviors."""
    adapter = get_memory_adapter(db_path)
    behaviors = adapter.list_behaviors(domain=domain, limit=limit)
    return [
        BehaviorResponse(
            behavior_id=b.behavior_id,
            description=b.description,
            trigger_pattern=b.trigger_pattern,
            success_rate=b.success_rate,
            use_count=b.use_count,
            last_used=b.last_used.isoformat(),
        )
        for b in behaviors
    ]
