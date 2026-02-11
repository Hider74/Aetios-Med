"""
Semester Router
Semester curriculum scope management endpoints.
"""
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from typing import Optional
from datetime import datetime
from pathlib import Path
import tempfile
import os
import json

from app.models.api_models import (
    SemesterScopeCreate, SemesterScopeResponse, 
    SemesterTopicMatch, SemesterUploadResponse
)
from app.models.database import get_session

router = APIRouter()


@router.post("/upload", response_model=SemesterUploadResponse)
async def upload_semester_pdf(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    year: Optional[int] = Form(None),
    semester_number: Optional[int] = Form(None),
    exam_date: Optional[str] = Form(None)
):
    """
    Upload a curriculum PDF, extract text, return matched topics for user review.
    Does NOT create a scope yet - just shows matches.
    """
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
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
        
        # Extract topics from PDF
        matched_topics = await semester_service.extract_topics_from_pdf(temp_path, file.filename)
        
        return SemesterUploadResponse(
            matched_topics=[
                SemesterTopicMatch(**topic) for topic in matched_topics
            ],
            scope_id=None,
            source_filename=file.filename
        )
    
    except ImportError:
        raise HTTPException(status_code=503, detail="PDF processing libraries not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/create", response_model=dict)
async def create_semester_scope(request: Request, scope: SemesterScopeCreate):
    """Create a scope from confirmed topic list."""
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
    try:
        # Parse exam_date if provided
        exam_date_obj = None
        if scope.exam_date:
            exam_date_obj = datetime.fromisoformat(scope.exam_date.replace('Z', '+00:00'))
        
        async with get_session() as db:
            scope_id = await semester_service.create_scope(
                name=scope.name,
                topic_ids=scope.topic_ids,
                year=scope.year,
                semester_number=scope.semester_number,
                exam_date=exam_date_obj,
                source_filename=scope.source_filename,
                db=db
            )
            
            return {"scope_id": scope_id, "success": True}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scope: {str(e)}")


@router.post("/upload-and-create", response_model=dict)
async def upload_and_create_scope(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    year: Optional[int] = Form(None),
    semester_number: Optional[int] = Form(None),
    exam_date: Optional[str] = Form(None)
):
    """
    Combined: upload PDF + auto-create scope with all matched topics.
    For users who trust the auto-matching.
    """
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
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
        
        # Extract topics from PDF
        matched_topics = await semester_service.extract_topics_from_pdf(temp_path, file.filename)
        
        # Create scope with all matched topics
        topic_ids = [t['topic_id'] for t in matched_topics]
        
        # Parse exam_date if provided
        exam_date_obj = None
        if exam_date:
            exam_date_obj = datetime.fromisoformat(exam_date.replace('Z', '+00:00'))
        
        async with get_session() as db:
            scope_id = await semester_service.create_scope(
                name=name,
                topic_ids=topic_ids,
                year=year,
                semester_number=semester_number,
                exam_date=exam_date_obj,
                source_filename=file.filename,
                db=db
            )
        
        return {
            "scope_id": scope_id,
            "success": True,
            "matched_topics_count": len(matched_topics)
        }
    
    except ImportError:
        raise HTTPException(status_code=503, detail="PDF processing libraries not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create scope: {str(e)}")
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.get("/scopes")
async def get_semester_scopes(request: Request):
    """List all semester scopes."""
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
    try:
        async with get_session() as db:
            scopes = await semester_service.get_all_scopes(db)
            
            return {
                "scopes": [
                    {
                        "id": scope.id,
                        "name": scope.name,
                        "year": scope.year,
                        "semester_number": scope.semester_number,
                        "exam_date": scope.exam_date.isoformat() if scope.exam_date else None,
                        "topic_ids": json.loads(scope.topic_ids),
                        "source_filename": scope.source_filename,
                        "is_active": scope.is_active,
                        "created_at": scope.created_at.isoformat(),
                        "updated_at": scope.updated_at.isoformat()
                    }
                    for scope in scopes
                ]
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch scopes: {str(e)}")


@router.get("/active")
async def get_active_semester_scope(request: Request):
    """Get the currently active scope (or null)."""
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
    try:
        async with get_session() as db:
            scope = await semester_service.get_active_scope(db)
            
            if not scope:
                return {"scope": None}
            
            return {
                "scope": {
                    "id": scope.id,
                    "name": scope.name,
                    "year": scope.year,
                    "semester_number": scope.semester_number,
                    "exam_date": scope.exam_date.isoformat() if scope.exam_date else None,
                    "topic_ids": json.loads(scope.topic_ids),
                    "source_filename": scope.source_filename,
                    "is_active": scope.is_active,
                    "created_at": scope.created_at.isoformat(),
                    "updated_at": scope.updated_at.isoformat()
                }
            }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active scope: {str(e)}")


@router.put("/{scope_id}/activate")
async def activate_semester_scope(request: Request, scope_id: int):
    """Activate a specific semester scope."""
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
    try:
        async with get_session() as db:
            # Check if scope exists
            scope = await semester_service.get_scope_by_id(scope_id, db)
            if not scope:
                raise HTTPException(status_code=404, detail="Scope not found")
            
            await semester_service.activate_scope(scope_id, db)
            
            return {"success": True, "message": f"Activated scope: {scope.name}"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to activate scope: {str(e)}")


@router.put("/deactivate")
async def deactivate_semester_scope(request: Request):
    """Deactivate all scopes (show full curriculum)."""
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
    try:
        async with get_session() as db:
            await semester_service.deactivate_all_scopes(db)
            
            return {"success": True, "message": "All scopes deactivated"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deactivate scopes: {str(e)}")


@router.put("/{scope_id}/topics")
async def update_scope_topics(request: Request, scope_id: int, topic_ids: dict):
    """Update the topics in a scope (for user corrections)."""
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
    try:
        async with get_session() as db:
            # Check if scope exists
            scope = await semester_service.get_scope_by_id(scope_id, db)
            if not scope:
                raise HTTPException(status_code=404, detail="Scope not found")
            
            await semester_service.update_scope_topics(
                scope_id, 
                topic_ids.get('topic_ids', []),
                db
            )
            
            return {"success": True, "message": "Scope topics updated"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update scope topics: {str(e)}")


@router.delete("/{scope_id}")
async def delete_semester_scope(request: Request, scope_id: int):
    """Delete a semester scope."""
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    
    if not semester_service:
        raise HTTPException(status_code=503, detail="Semester service not available")
    
    try:
        async with get_session() as db:
            # Check if scope exists
            scope = await semester_service.get_scope_by_id(scope_id, db)
            if not scope:
                raise HTTPException(status_code=404, detail="Scope not found")
            
            await semester_service.delete_scope(scope_id, db)
            
            return {"success": True, "message": "Scope deleted"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete scope: {str(e)}")
