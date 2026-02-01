"""
Quiz Router
Quiz generation and submission endpoints.
"""
from fastapi import APIRouter, Request, HTTPException
from app.models.api_models import QuizRequest, QuizResponse, QuizSubmission, QuizResult

router = APIRouter()


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: Request, quiz_request: QuizRequest):
    """Generate a quiz for specified topics."""
    quiz_service = request.app.state.quiz if hasattr(request.app.state, 'quiz') else None
    
    if not quiz_service:
        raise HTTPException(status_code=503, detail="Quiz service not available")
    
    quiz = await quiz_service.generate_quiz(
        topic_ids=quiz_request.topic_ids,
        num_questions=quiz_request.num_questions,
        difficulty=quiz_request.difficulty,
        include_weak_areas=quiz_request.include_weak_areas
    )
    
    return quiz


@router.post("/submit")
async def submit_answer(request: Request, submission: QuizSubmission):
    """Submit a quiz answer and update progress."""
    quiz_service = request.app.state.quiz if hasattr(request.app.state, 'quiz') else None
    
    if not quiz_service:
        raise HTTPException(status_code=503, detail="Quiz service not available")
    
    result = await quiz_service.submit_answer(submission)
    
    return result


@router.get("/results/{topic_id}", response_model=QuizResult)
async def get_quiz_results(request: Request, topic_id: str):
    """Get quiz results for a topic."""
    # TODO: Query database for quiz results
    return QuizResult(
        total=0,
        correct=0,
        score=0.0,
        by_topic={}
    )


@router.get("/history")
async def get_quiz_history(request: Request, limit: int = 20):
    """Get recent quiz history."""
    # TODO: Query database for quiz history
    return {"quizzes": []}
