"""
Ingest Router
Data ingestion endpoints for Anki, PDFs, and notes.
"""
from fastapi import APIRouter, Request, HTTPException, UploadFile, File
from app.models.api_models import IngestRequest, IngestResponse
from app.models.database import get_session, AnkiCard, Note
from pathlib import Path
from sqlalchemy import select, func
import tempfile
import os

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
    
    try:
        async with get_session() as db:
            stats = await ingest_service.ingest_anki_file(path, db)
            
            return IngestResponse(
                success=True,
                items_processed=stats.get('total', 0),
                items_mapped=stats.get('mapped', 0),
                errors=[],
                statistics={
                    'new': stats.get('new', 0),
                    'updated': stats.get('updated', 0),
                    'errors': stats.get('errors', 0)
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest Anki file: {str(e)}")


@router.post("/pdf", response_model=IngestResponse)
async def ingest_pdf(request: Request, file: UploadFile = File(...), auto_map: bool = True):
    """Ingest PDF document."""
    ingest_service = request.app.state.ingest if hasattr(request.app.state, 'ingest') else None
    
    if not ingest_service:
        raise HTTPException(status_code=503, detail="Ingest service not available")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Save uploaded file temporarily
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        
        async with get_session() as db:
            stats = await ingest_service.ingest_pdf_file(temp_path, file.filename, db)
            
            return IngestResponse(
                success=True,
                items_processed=stats.get('chunks', 0),
                items_mapped=stats.get('notes_created', 0),
                errors=stats.get('errors', []),
                statistics={
                    'pages': stats.get('pages', 0),
                    'chunks': stats.get('chunks', 0),
                    'notes_created': stats.get('notes_created', 0),
                    'topics_mapped': stats.get('topics_mapped', 0)
                }
            )
    except ImportError:
        raise HTTPException(status_code=503, detail="PDF processing libraries not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest PDF: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/notes", response_model=IngestResponse)
async def ingest_notes(request: Request, file_path: str, auto_map: bool = True):
    """Ingest markdown or text notes."""
    ingest_service = request.app.state.ingest if hasattr(request.app.state, 'ingest') else None
    
    if not ingest_service:
        raise HTTPException(status_code=503, detail="Ingest service not available")
    
    path = Path(file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Check file extension
    if path.suffix not in ['.txt', '.md']:
        raise HTTPException(status_code=400, detail="File must be .txt or .md")
    
    try:
        # Read file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        async with get_session() as db:
            stats = await ingest_service.ingest_note_file(path, content, db)
            
            return IngestResponse(
                success=True,
                items_processed=stats.get('sections', 0),
                items_mapped=stats.get('notes_created', 0),
                errors=stats.get('errors', []),
                statistics={
                    'sections': stats.get('sections', 0),
                    'notes_created': stats.get('notes_created', 0),
                    'topics_mapped': stats.get('topics_mapped', 0)
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest notes: {str(e)}")


@router.get("/status")
async def get_ingest_status(request: Request):
    """Get ingestion statistics."""
    try:
        async with get_session() as db:
            # Count AnkiCards
            result = await db.execute(select(func.count(AnkiCard.id)))
            total_cards = result.scalar() or 0
            
            # Count Notes
            result = await db.execute(select(func.count(Note.id)))
            total_notes = result.scalar() or 0
            
            # Count unique documents (distinct deck names for Anki + distinct file paths for Notes)
            result = await db.execute(select(func.count(func.distinct(AnkiCard.deck_name))))
            anki_decks = result.scalar() or 0
            
            result = await db.execute(select(func.count(func.distinct(Note.file_path))).where(Note.file_path.isnot(None)))
            note_files = result.scalar() or 0
            
            total_documents = anki_decks + note_files
            
            # Get last sync timestamp (most recent from both tables)
            result = await db.execute(
                select(func.max(AnkiCard.updated_at))
            )
            last_anki_sync = result.scalar()
            
            result = await db.execute(
                select(func.max(Note.updated_at))
            )
            last_note_sync = result.scalar()
            
            # Determine the most recent timestamp
            last_sync = None
            if last_anki_sync and last_note_sync:
                last_sync = max(last_anki_sync, last_note_sync).isoformat() if max(last_anki_sync, last_note_sync) else None
            elif last_anki_sync:
                last_sync = last_anki_sync.isoformat()
            elif last_note_sync:
                last_sync = last_note_sync.isoformat()
            
            return {
                "total_cards": total_cards,
                "total_notes": total_notes,
                "total_documents": total_documents,
                "last_sync": last_sync
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
