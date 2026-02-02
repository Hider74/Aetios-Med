"""
Quiz Router
Quiz generation and submission endpoints.
"""
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy import select, func
from datetime import datetime
from app.models.api_models import QuizRequest, QuizResponse, QuizSubmission, QuizResult
from app.models.database import QuizResult as DBQuizResult, get_session
import uuid
from typing import Dict, Any

router = APIRouter()

# In-memory cache for active quizzes (quiz_id -> quiz data)
# In production, this should use Redis or similar
_active_quizzes: Dict[str, Dict[str, Any]] = {}


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(request: Request, quiz_request: QuizRequest):
    """Generate a quiz for specified topics."""
    quiz_service = request.app.state.quiz if hasattr(request.app.state, 'quiz') else None
    
    if not quiz_service:
        raise HTTPException(status_code=503, detail="Quiz service not available")
    
    # Get database session
    async with get_session() as db:
        # For now, use the first topic_id (service supports single topic)
        topic_id = quiz_request.topic_ids[0] if quiz_request.topic_ids else None
        if not topic_id:
            raise HTTPException(status_code=400, detail="At least one topic_id required")
        
        questions = await quiz_service.generate_quiz(
            topic_id=topic_id,
            num_questions=quiz_request.num_questions,
            difficulty=quiz_request.difficulty,
            db=db
        )
        
        # Generate quiz ID and store quiz data for later validation
        quiz_id = str(uuid.uuid4())
        
        # Store quiz in memory for answer validation
        _active_quizzes[quiz_id] = {
            'topic_id': topic_id,
            'difficulty': quiz_request.difficulty,
            'questions': {q.get('question', ''): q for q in questions}
        }
        
        return QuizResponse(
            quiz_id=quiz_id,
            questions=questions,
            topic_id=topic_id,
            difficulty=quiz_request.difficulty
        )


@router.post("/submit")
async def submit_answer(request: Request, submission: QuizSubmission):
    """Submit a quiz answer and update progress."""
    # Look up quiz data
    quiz_data = _active_quizzes.get(submission.quiz_id)
    if not quiz_data:
        raise HTTPException(status_code=404, detail="Quiz not found or expired")
    
    # Find question by question_id (which should match the question text or a key)
    # The question_id from frontend might be the question text or index
    question_data = None
    for q_text, q_info in quiz_data['questions'].items():
        if submission.question_id == q_text or submission.question_id == q_info.get('question'):
            question_data = q_info
            break
    
    if not question_data:
        # Try finding by index if question_id is numeric
        try:
            idx = int(submission.question_id.replace('q', ''))
            questions_list = list(quiz_data['questions'].values())
            if 0 <= idx < len(questions_list):
                question_data = questions_list[idx]
        except (ValueError, IndexError):
            pass
    
    if not question_data:
        raise HTTPException(status_code=404, detail="Question not found in quiz")
    
    # Check if answer is correct
    correct_answer = question_data.get('correct_answer', '').upper()
    user_answer = submission.answer.upper()
    is_correct = user_answer == correct_answer
    
    # Store result in database
    async with get_session() as db:
        quiz_result = DBQuizResult(
            topic_id=submission.topic_id,
            question=question_data.get('question', ''),
            correct=is_correct,
            difficulty=quiz_data['difficulty'],
            quiz_date=datetime.utcnow()
        )
        db.add(quiz_result)
        await db.commit()
    
    return {
        "correct": is_correct,
        "correct_answer": correct_answer,
        "user_answer": user_answer,
        "explanation": question_data.get('explanation', ''),
        "message": "Answer recorded"
    }


@router.get("/results/{topic_id}", response_model=QuizResult)
async def get_quiz_results(request: Request, topic_id: str):
    """Get quiz results for a topic."""
    async with get_session() as db:
        # Query all quiz results for the topic
        result = await db.execute(
            select(DBQuizResult).where(DBQuizResult.topic_id == topic_id)
        )
        quiz_results = result.scalars().all()
        
        # Calculate statistics
        total = len(quiz_results)
        correct = sum(1 for r in quiz_results if r.correct)
        score = (correct / total * 100) if total > 0 else 0.0
        
        # Group by difficulty
        by_topic = {}
        for difficulty in ['easy', 'medium', 'hard']:
            diff_results = [r for r in quiz_results if r.difficulty == difficulty]
            if diff_results:
                diff_correct = sum(1 for r in diff_results if r.correct)
                by_topic[difficulty] = {
                    'total': len(diff_results),
                    'correct': diff_correct,
                    'score': (diff_correct / len(diff_results) * 100) if diff_results else 0.0
                }
        
        return QuizResult(
            total=total,
            correct=correct,
            score=score,
            by_topic=by_topic
        )


@router.get("/history")
async def get_quiz_history(request: Request, limit: int = 20):
    """Get recent quiz history."""
    async with get_session() as db:
        # Query quiz history ordered by date, with limit
        result = await db.execute(
            select(DBQuizResult)
            .order_by(DBQuizResult.quiz_date.desc())
            .limit(limit)
        )
        quiz_records = result.scalars().all()
        
        # Format quiz records
        quizzes = [
            {
                'quiz_id': record.id,
                'topic_id': record.topic_id,
                'correct': record.correct,
                'quiz_date': record.quiz_date.isoformat(),
                'question': record.question,
                'difficulty': record.difficulty
            }
            for record in quiz_records
        ]
        
        return {"quizzes": quizzes}
