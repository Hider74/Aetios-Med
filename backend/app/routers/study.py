"""
Study Router
Study planning and session tracking endpoints.
"""
from fastapi import APIRouter, Request, HTTPException
from app.models.api_models import (
    ExamCreate, ExamResponse, StudyPlanRequest, 
    StudyPlanResponse, StudySessionLog
)
from app.models.database import (
    get_session, Exam, StudySession, TopicProgress, StudyPlan
)
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy import select, desc
import json

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
    try:
        async with get_session() as db:
            today = date.today()
            result = await db.execute(
                select(Exam)
                .where(Exam.date >= today)
                .order_by(Exam.date.asc())
            )
            exams = result.scalars().all()
            
            return [
                ExamResponse(
                    id=exam.id,
                    name=exam.name,
                    date=exam.date.isoformat(),
                    topics=json.loads(exam.topics_json),
                    created_at=exam.created_at.isoformat()
                )
                for exam in exams
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch exams: {str(e)}")


@router.get("/exam/{exam_id}", response_model=ExamResponse)
async def get_exam(request: Request, exam_id: int):
    """Get exam details."""
    try:
        async with get_session() as db:
            result = await db.execute(
                select(Exam).where(Exam.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            
            if not exam:
                raise HTTPException(status_code=404, detail="Exam not found")
            
            return ExamResponse(
                id=exam.id,
                name=exam.name,
                date=exam.date.isoformat(),
                topics=json.loads(exam.topics_json),
                created_at=exam.created_at.isoformat()
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch exam: {str(e)}")


@router.delete("/exam/{exam_id}")
async def delete_exam(request: Request, exam_id: int):
    """Delete an exam."""
    try:
        async with get_session() as db:
            result = await db.execute(
                select(Exam).where(Exam.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            
            if not exam:
                raise HTTPException(status_code=404, detail="Exam not found")
            
            await db.delete(exam)
            await db.commit()
            
            return {"status": "deleted", "exam_id": exam_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete exam: {str(e)}")


@router.patch("/exam/{exam_id}", response_model=ExamResponse)
async def update_exam(request: Request, exam_id: int, exam_update: ExamCreate):
    """Update an existing exam."""
    try:
        async with get_session() as db:
            result = await db.execute(
                select(Exam).where(Exam.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            
            if not exam:
                raise HTTPException(status_code=404, detail="Exam not found")
            
            # Update fields
            exam.name = exam_update.name
            exam.date = exam_update.date
            exam.topics_json = json.dumps(exam_update.topics)
            
            await db.commit()
            await db.refresh(exam)
            
            return ExamResponse(
                id=exam.id,
                name=exam.name,
                date=exam.date.isoformat(),
                topics=json.loads(exam.topics_json),
                created_at=exam.created_at.isoformat()
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update exam: {str(e)}")


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
    try:
        async with get_session() as db:
            result = await db.execute(
                select(StudyPlan).order_by(desc(StudyPlan.created_at))
            )
            plans = result.scalars().all()
            
            # Get exam details for each plan if exam_id is present
            response_plans = []
            for plan in plans:
                plan_data = {
                    "id": plan.id,
                    "start_date": plan.start_date.isoformat(),
                    "end_date": plan.end_date.isoformat(),
                    "hours_per_day": plan.hours_per_day,
                    "topics": json.loads(plan.topics_json),
                    "created_at": plan.created_at.isoformat()
                }
                
                # Get exam name if exam_id exists
                if plan.exam_id:
                    exam_result = await db.execute(
                        select(Exam).where(Exam.id == plan.exam_id)
                    )
                    exam = exam_result.scalar_one_or_none()
                    if exam:
                        plan_data["exam_id"] = exam.id
                        plan_data["exam_name"] = exam.name
                
                response_plans.append(plan_data)
            
            return {"plans": response_plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch study plans: {str(e)}")


@router.post("/session")
async def log_study_session(request: Request, session: StudySessionLog):
    """Log a study session."""
    try:
        async with get_session() as db:
            # Create StudySession record
            study_session = StudySession(
                topic_id=session.topic_id,
                duration_minutes=session.duration_minutes,
                session_date=datetime.utcnow(),
                notes=session.notes
            )
            db.add(study_session)
            
            # Update TopicProgress
            result = await db.execute(
                select(TopicProgress).where(TopicProgress.topic_id == session.topic_id)
            )
            topic_progress = result.scalar_one_or_none()
            
            if topic_progress:
                topic_progress.last_studied = datetime.utcnow()
                topic_progress.times_reviewed += 1
            else:
                # Create new progress record if doesn't exist
                topic_progress = TopicProgress(
                    topic_id=session.topic_id,
                    confidence=0.0,
                    last_studied=datetime.utcnow(),
                    times_reviewed=1
                )
                db.add(topic_progress)
            
            await db.commit()
            
            return {"status": "logged", "session_id": study_session.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log session: {str(e)}")


@router.get("/sessions")
async def get_study_sessions(request: Request, topic_id: Optional[str] = None, limit: int = 20):
    """Get study session history."""
    try:
        async with get_session() as db:
            query = select(StudySession)
            
            if topic_id:
                query = query.where(StudySession.topic_id == topic_id)
            
            query = query.order_by(desc(StudySession.session_date)).limit(limit)
            
            result = await db.execute(query)
            sessions = result.scalars().all()
            
            return {
                "sessions": [
                    {
                        "id": session.id,
                        "topic_id": session.topic_id,
                        "duration_minutes": session.duration_minutes,
                        "session_date": session.session_date.isoformat(),
                        "notes": session.notes,
                        "created_at": session.created_at.isoformat()
                    }
                    for session in sessions
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")


@router.get("/readiness/{exam_id}")
async def get_exam_readiness(request: Request, exam_id: int):
    """Calculate readiness score for an exam."""
    try:
        async with get_session() as db:
            # Get Exam record
            result = await db.execute(
                select(Exam).where(Exam.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            
            if not exam:
                raise HTTPException(status_code=404, detail="Exam not found")
            
            # Parse topics from JSON
            topics = json.loads(exam.topics_json)
            
            if not topics:
                return {
                    "exam_id": exam_id,
                    "exam_name": exam.name,
                    "readiness_score": 0.0,
                    "topics_ready": 0,
                    "topics_weak": 0,
                    "recommended_hours": 0
                }
            
            # Query TopicProgress for each topic
            result = await db.execute(
                select(TopicProgress).where(TopicProgress.topic_id.in_(topics))
            )
            progress_map = {p.topic_id: p for p in result.scalars().all()}
            
            # Calculate statistics
            total_confidence = 0.0
            topics_ready = 0
            topics_weak = 0
            
            for topic_id in topics:
                progress = progress_map.get(topic_id)
                confidence = progress.confidence if progress else 0.0
                
                total_confidence += confidence
                
                if confidence >= 0.7:
                    topics_ready += 1
                if confidence < 0.5:
                    topics_weak += 1
            
            # Calculate average confidence (readiness score)
            avg_confidence = total_confidence / len(topics) if topics else 0.0
            
            # Estimate recommended study hours (2 hours per weak topic)
            recommended_hours = topics_weak * 2
            
            return {
                "exam_id": exam_id,
                "exam_name": exam.name,
                "readiness_score": round(avg_confidence, 2),
                "topics_ready": topics_ready,
                "topics_weak": topics_weak,
                "total_topics": len(topics),
                "recommended_hours": recommended_hours
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate readiness: {str(e)}")
