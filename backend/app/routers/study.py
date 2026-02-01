"""
Study Router
Study planning and session tracking endpoints.
"""
from fastapi import APIRouter, Request, HTTPException
from app.models.api_models import (
    ExamCreate, ExamResponse, StudyPlanRequest, 
    StudyPlanResponse, StudySessionLog
)
from typing import List

router = APIRouter()


@router.post("/exam", response_model=ExamResponse)
async def create_exam(request: Request, exam: ExamCreate):
    """Create a new exam entry."""
    study_service = request.app.state.study if hasattr(request.app.state, 'study') else None
    
    if not study_service:
        raise HTTPException(status_code=503, detail="Study service not available")
    
    result = await study_service.create_exam(exam)
    return result


@router.get("/exams", response_model=List[ExamResponse])
async def get_exams(request: Request):
    """Get all upcoming exams."""
    # TODO: Query database for exams
    return []


@router.get("/exam/{exam_id}", response_model=ExamResponse)
async def get_exam(request: Request, exam_id: int):
    """Get exam details."""
    # TODO: Query database for specific exam
    raise HTTPException(status_code=404, detail="Exam not found")


@router.delete("/exam/{exam_id}")
async def delete_exam(request: Request, exam_id: int):
    """Delete an exam."""
    # TODO: Delete from database
    return {"status": "deleted"}


@router.post("/plan", response_model=StudyPlanResponse)
async def generate_study_plan(request: Request, plan_request: StudyPlanRequest):
    """Generate a personalized study plan."""
    study_service = request.app.state.study if hasattr(request.app.state, 'study') else None
    
    if not study_service:
        raise HTTPException(status_code=503, detail="Study service not available")
    
    plan = await study_service.generate_plan(plan_request)
    return plan


@router.get("/plans")
async def get_study_plans(request: Request):
    """Get all study plans."""
    # TODO: Query database for plans
    return {"plans": []}


@router.post("/session")
async def log_study_session(request: Request, session: StudySessionLog):
    """Log a study session."""
    # TODO: Save to database
    return {"status": "logged"}


@router.get("/sessions")
async def get_study_sessions(request: Request, topic_id: str = None, limit: int = 20):
    """Get study session history."""
    # TODO: Query database for sessions
    return {"sessions": []}


@router.get("/readiness/{exam_id}")
async def get_exam_readiness(request: Request, exam_id: int):
    """Calculate readiness score for an exam."""
    # TODO: Calculate based on topic confidences
    return {
        "exam_id": exam_id,
        "readiness_score": 0.0,
        "topics_ready": 0,
        "topics_weak": 0,
        "recommended_hours": 0
    }
