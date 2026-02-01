"""
Ingest Router
Data ingestion endpoints for Anki, PDFs, and notes.
"""
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from app.models.api_models import IngestRequest, IngestResponse
from pathlib import Path

router = APIRouter()


@router.post("/anki", response_model=IngestResponse)
async def ingest_anki(request: Request, file_path: str, auto_map: bool = True):
    """Ingest Anki deck from .apkg file."""
    ingest_service = request.app.state.ingest if hasattr(request.app.state, 'ingest') else None
    
    if not ingest_service:
        raise HTTPException(status_code=503, detail="Ingest service not available")
    
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    result = await ingest_service.ingest_anki(path, auto_map=auto_map)
    
    return IngestResponse(
        success=result["success"],
        items_processed=result["items_processed"],
        items_mapped=result["items_mapped"],
        errors=result.get("errors", []),
        statistics=result.get("statistics", {})
    )


@router.post("/pdf", response_model=IngestResponse)
async def ingest_pdf(request: Request, file: UploadFile = File(...), auto_map: bool = True):
    """Ingest PDF document."""
    # TODO: Implement PDF ingestion
    return IngestResponse(
        success=True,
        items_processed=0,
        items_mapped=0,
        errors=[],
        statistics={}
    )


@router.post("/notes", response_model=IngestResponse)
async def ingest_notes(request: Request, file_path: str, auto_map: bool = True):
    """Ingest markdown or text notes."""
    # TODO: Implement notes ingestion
    return IngestResponse(
        success=True,
        items_processed=0,
        items_mapped=0,
        errors=[],
        statistics={}
    )


@router.get("/status")
async def get_ingest_status(request: Request):
    """Get ingestion statistics."""
    # TODO: Query database for ingest stats
    return {
        "total_cards": 0,
        "total_notes": 0,
        "total_documents": 0,
        "last_sync": None
    }
