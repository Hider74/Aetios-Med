"""
Agent tools for Aetios medical tutor.
Defines all 18 agent tools in OpenAI function-calling format.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, date
import json
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import (
    TopicProgress, AnkiCard, Note, StudySession, 
    QuizResult, Exam, StudyPlan
)

# Global services dictionary
_services: Dict[str, Any] = {}

# Learning algorithm constants
CONFIDENCE_INCREASE_CORRECT = 0.05  # Confidence boost for correct quiz answers
CONFIDENCE_DECREASE_INCORRECT = 0.1  # Confidence penalty for incorrect quiz answers
FSRS_RETENTION_THRESHOLD = 0.8  # 80% retention threshold for spaced repetition
ANKI_INTERVAL_NORMALIZATION_DAYS = 30  # Normalize intervals to 30-day scale for retention estimation


def init_tools(services_dict: Dict[str, Any]) -> None:
    """
    Initialize agent tools with service instances.
    
    Args:
        services_dict: Dictionary containing service instances:
            - graph_service: GraphService instance
            - vector_service: VectorService instance
            - retention_service: RetentionService instance
            - quiz_service: QuizService instance
            - study_plan_service: StudyPlanService instance
    """
    global _services
    _services = services_dict


async def get_weak_topics(threshold: float = 0.3, db: AsyncSession = None) -> List[Dict]:
    """
    Get topics where student confidence is below threshold.
    
    Args:
        threshold: Confidence threshold (0-1), default 0.3
        db: Database session
        
    Returns:
        List of weak topics with details
    """
    if db is None:
        return []
    
    try:
        result = await db.execute(
            select(TopicProgress)
            .where(TopicProgress.confidence < threshold)
            .order_by(TopicProgress.confidence.asc())
        )
        weak_topics = result.scalars().all()
        
        return [
            {
                'topic_id': t.topic_id,
                'confidence': t.confidence,
                'last_studied': t.last_studied.isoformat() if t.last_studied else None,
                'times_reviewed': t.times_reviewed,
                'notes': t.notes
            }
            for t in weak_topics
        ]
    except Exception as e:
        print(f"Error getting weak topics: {e}")
        return []


async def get_decaying_topics(days: int = 7, db: AsyncSession = None) -> List[Dict]:
    """
    Get topics not reviewed in specified days (spaced repetition).
    
    Args:
        days: Number of days since last review, default 7
        db: Database session
        
    Returns:
        List of topics needing review
    """
    if db is None or 'retention_service' not in _services:
        return []
    
    try:
        retention_service = _services['retention_service']
        # Use FSRS-based retention calculation
        # Threshold of 0.8 means topics with <80% predicted retention need review
        decaying_topics = await retention_service.get_decaying_topics(
            db=db, 
            threshold=FSRS_RETENTION_THRESHOLD, 
            limit=20
        )
        return decaying_topics
    except Exception as e:
        print(f"Error getting decaying topics: {e}")
        return []


async def get_prerequisites(topic_id: str, db: AsyncSession = None) -> List[Dict]:
    """
    Get prerequisite topics for a given topic.
    
    Args:
        topic_id: Topic identifier
        db: Database session
        
    Returns:
        List of prerequisite topics
    """
    if 'graph_service' not in _services:
        return []
    
    try:
        graph_service = _services['graph_service']
        if not graph_service.is_loaded:
            graph_service.load_curriculum()
        
        prereqs = graph_service.get_prerequisites(topic_id)
        
        return [
            {
                'topic_id': p.id,
                'label': p.label,
                'type': p.type,
                'exam_weight': p.exam_weight
            }
            for p in prereqs
        ]
    except Exception as e:
        print(f"Error getting prerequisites: {e}")
        return []


async def get_dependent_topics(topic_id: str, db: AsyncSession = None) -> List[Dict]:
    """
    Get topics that depend on this topic.
    
    Args:
        topic_id: Topic identifier
        db: Database session
        
    Returns:
        List of dependent topics
    """
    if 'graph_service' not in _services:
        return []
    
    try:
        graph_service = _services['graph_service']
        if not graph_service.is_loaded:
            graph_service.load_curriculum()
        
        dependents = graph_service.get_dependents(topic_id)
        
        return [
            {
                'topic_id': d.id,
                'label': d.label,
                'type': d.type,
                'exam_weight': d.exam_weight
            }
            for d in dependents
        ]
    except Exception as e:
        print(f"Error getting dependent topics: {e}")
        return []


async def get_topic_details(topic_id: str, db: AsyncSession = None) -> Dict:
    """
    Get detailed information about a topic.
    
    Args:
        topic_id: Topic identifier
        db: Database session
        
    Returns:
        Topic details including confidence, last studied, resources
    """
    if db is None or 'graph_service' not in _services:
        return {}
    
    try:
        graph_service = _services['graph_service']
        if not graph_service.is_loaded:
            graph_service.load_curriculum()
        
        if topic_id not in graph_service.topics:
            return {'error': f'Topic {topic_id} not found'}
        
        topic = graph_service.topics[topic_id]
        
        # Get progress from DB
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id == topic_id)
        )
        progress = result.scalar_one_or_none()
        
        # Count Anki cards
        card_count = await db.execute(
            select(func.count(AnkiCard.id)).where(AnkiCard.topic_id == topic_id)
        )
        total_cards = card_count.scalar() or 0
        
        # Count notes
        note_count = await db.execute(
            select(func.count(Note.id)).where(Note.topic_id == topic_id)
        )
        total_notes = note_count.scalar() or 0
        
        return {
            'topic_id': topic.id,
            'label': topic.label,
            'type': topic.type,
            'exam_weight': topic.exam_weight,
            'confidence': progress.confidence if progress else 0.0,
            'last_studied': progress.last_studied.isoformat() if progress and progress.last_studied else None,
            'times_reviewed': progress.times_reviewed if progress else 0,
            'learning_objectives': topic.learning_objectives if hasattr(topic, 'learning_objectives') else [],
            'resources': topic.resources if hasattr(topic, 'resources') else {},
            'total_cards': total_cards,
            'total_notes': total_notes
        }
    except Exception as e:
        print(f"Error getting topic details: {e}")
        return {'error': str(e)}


async def search_notes(query: str, limit: int = 5, db: AsyncSession = None) -> List[Dict]:
    """
    Search through student's notes and annotations.
    
    Args:
        query: Search query string
        limit: Maximum number of results, default 5
        db: Database session
        
    Returns:
        List of matching notes
    """
    if 'vector_service' not in _services:
        return []
    
    try:
        vector_service = _services['vector_service']
        
        # Use vector similarity search
        results = vector_service.query_similar(query, n_results=limit)
        
        matched_notes = []
        if results.get('ids'):
            for i in range(len(results['ids'])):
                matched_notes.append({
                    'id': results['ids'][i],
                    'content': results['documents'][i] if i < len(results['documents']) else '',
                    'metadata': results['metadatas'][i] if i < len(results['metadatas']) else {},
                    'score': 1.0 - results['distances'][i] if i < len(results['distances']) else 0.0
                })
        
        return matched_notes
    except Exception as e:
        print(f"Error searching notes: {e}")
        return []


async def get_anki_stats(topic_id: Optional[str] = None, db: AsyncSession = None) -> Dict:
    """
    Get Anki flashcard statistics.
    
    Args:
        topic_id: Optional topic filter
        db: Database session
        
    Returns:
        Statistics including cards due, accuracy, retention
    """
    if db is None:
        return {}
    
    try:
        query = select(AnkiCard)
        if topic_id:
            query = query.where(AnkiCard.topic_id == topic_id)
        
        result = await db.execute(query)
        cards = result.scalars().all()
        
        if not cards:
            return {
                'total_cards': 0,
                'cards_due': 0,
                'accuracy': 0.0
            }
        
        now = datetime.utcnow()
        due_cards = [c for c in cards if c.due_date and c.due_date <= now]
        
        # Estimate retention/mastery from intervals
        # Longer intervals indicate better retention (content has "stuck" longer)
        avg_interval = sum(c.interval for c in cards) / len(cards) if cards else 0
        # Normalize to 30-day scale: intervals >= 30 days suggest strong retention
        retention_estimate = min(1.0, avg_interval / ANKI_INTERVAL_NORMALIZATION_DAYS)
        
        return {
            'total_cards': len(cards),
            'cards_due': len(due_cards),
            'retention_estimate': retention_estimate,
            'avg_interval_days': avg_interval,
            'avg_ease_factor': sum(c.ease_factor for c in cards) / len(cards) if cards else 2.5
        }
    except Exception as e:
        print(f"Error getting Anki stats: {e}")
        return {'error': str(e)}


async def generate_quiz(
    topic_id: str, 
    num_questions: int = 5, 
    difficulty: str = "medium",
    db: AsyncSession = None
) -> Dict:
    """
    Generate a quiz for a topic.
    
    Args:
        topic_id: Topic identifier
        num_questions: Number of questions to generate, default 5
        difficulty: Difficulty level (easy/medium/hard), default "medium"
        db: Database session
        
    Returns:
        Quiz with questions and metadata
    """
    if 'quiz_service' not in _services or db is None:
        return {
            "quiz_id": f"quiz_{datetime.utcnow().timestamp()}",
            "topic_id": topic_id,
            "questions": [],
            "difficulty": difficulty,
            "error": "Quiz service not available"
        }
    
    try:
        quiz_service = _services['quiz_service']
        questions = await quiz_service.generate_quiz(
            topic_id=topic_id,
            num_questions=num_questions,
            difficulty=difficulty,
            db=db
        )
        
        return {
            "quiz_id": f"quiz_{datetime.utcnow().timestamp()}",
            "topic_id": topic_id,
            "questions": questions,
            "difficulty": difficulty
        }
    except Exception as e:
        print(f"Error generating quiz: {e}")
        return {
            "quiz_id": f"quiz_{datetime.utcnow().timestamp()}",
            "topic_id": topic_id,
            "questions": [],
            "difficulty": difficulty,
            "error": str(e)
        }


async def log_quiz_result(topic_id: str, correct: bool, question: str, db: AsyncSession = None) -> Dict:
    """
    Log the result of a quiz question.
    
    Args:
        topic_id: Topic identifier
        correct: Whether answer was correct
        question: The question text
        db: Database session
        
    Returns:
        Updated statistics
    """
    if db is None:
        return {"logged": False, "error": "No database session"}
    
    try:
        # Save quiz result
        quiz_result = QuizResult(
            topic_id=topic_id,
            question=question,
            correct=correct,
            difficulty="medium",
            quiz_date=datetime.utcnow()
        )
        db.add(quiz_result)
        
        # Update topic progress confidence
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id == topic_id)
        )
        progress = result.scalar_one_or_none()
        
        if progress:
            # Adjust confidence based on result
            if correct:
                progress.confidence = min(1.0, progress.confidence + CONFIDENCE_INCREASE_CORRECT)
            else:
                progress.confidence = max(0.0, progress.confidence - CONFIDENCE_DECREASE_INCORRECT)
            progress.updated_at = datetime.utcnow()
        else:
            # Create new progress entry
            progress = TopicProgress(
                topic_id=topic_id,
                confidence=0.5 if correct else 0.3,
                times_reviewed=0
            )
            db.add(progress)
        
        await db.commit()
        
        return {
            "logged": True, 
            "topic_id": topic_id,
            "new_confidence": progress.confidence
        }
    except Exception as e:
        await db.rollback()
        print(f"Error logging quiz result: {e}")
        return {"logged": False, "error": str(e)}


async def log_study_session(
    topic_id: str, 
    duration_minutes: int, 
    notes: Optional[str] = None,
    db: AsyncSession = None
) -> Dict:
    """
    Log a study session.
    
    Args:
        topic_id: Topic identifier
        duration_minutes: Session duration in minutes
        notes: Optional session notes
        db: Database session
        
    Returns:
        Session confirmation with updated stats
    """
    if db is None:
        return {"logged": False, "error": "No database session"}
    
    try:
        # Create study session record
        session = StudySession(
            topic_id=topic_id,
            duration_minutes=duration_minutes,
            session_date=datetime.utcnow(),
            notes=notes
        )
        db.add(session)
        
        # Update topic progress
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id == topic_id)
        )
        progress = result.scalar_one_or_none()
        
        if progress:
            progress.last_studied = datetime.utcnow()
            progress.times_reviewed += 1
            progress.updated_at = datetime.utcnow()
        else:
            progress = TopicProgress(
                topic_id=topic_id,
                confidence=0.3,
                last_studied=datetime.utcnow(),
                times_reviewed=1
            )
            db.add(progress)
        
        await db.commit()
        
        return {
            "session_id": f"session_{session.id}",
            "topic_id": topic_id,
            "duration_minutes": duration_minutes,
            "times_reviewed": progress.times_reviewed
        }
    except Exception as e:
        await db.rollback()
        print(f"Error logging study session: {e}")
        return {"logged": False, "error": str(e)}


async def get_study_history(
    topic_id: Optional[str] = None, 
    days: int = 30,
    db: AsyncSession = None
) -> List[Dict]:
    """
    Get study session history.
    
    Args:
        topic_id: Optional topic filter
        days: Number of days to look back, default 30
        db: Database session
        
    Returns:
        List of study sessions
    """
    if db is None:
        return []
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = select(StudySession).where(
            StudySession.session_date >= cutoff_date
        ).order_by(StudySession.session_date.desc())
        
        if topic_id:
            query = query.where(StudySession.topic_id == topic_id)
        
        result = await db.execute(query)
        sessions = result.scalars().all()
        
        return [
            {
                'session_id': s.id,
                'topic_id': s.topic_id,
                'duration_minutes': s.duration_minutes,
                'session_date': s.session_date.isoformat(),
                'notes': s.notes
            }
            for s in sessions
        ]
    except Exception as e:
        print(f"Error getting study history: {e}")
        return []


async def generate_study_plan(
    exam_id: Optional[int] = None, 
    weeks: int = 4,
    db: AsyncSession = None
) -> Dict:
    """
    Generate a personalized study plan.
    
    Args:
        exam_id: Optional exam to prepare for
        weeks: Planning horizon in weeks, default 4
        db: Database session
        
    Returns:
        Study plan with daily/weekly breakdown
    """
    if db is None or 'study_plan_service' not in _services:
        return {
            "plan_id": f"plan_{datetime.utcnow().timestamp()}",
            "weeks": weeks,
            "exam_id": exam_id,
            "schedule": [],
            "error": "Study plan service not available"
        }
    
    try:
        study_plan_service = _services['study_plan_service']
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(weeks=weeks)
        
        plan_id = await study_plan_service.generate_study_plan(
            exam_id=exam_id,
            start_date=start_date,
            end_date=end_date,
            hours_per_day=2.0,
            db=db,
            focus_weak_areas=True
        )
        
        # Retrieve the plan
        result = await db.execute(
            select(StudyPlan).where(StudyPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if plan:
            plan_data = json.loads(plan.plan_json)
            return {
                "plan_id": plan_id,
                "weeks": weeks,
                "exam_id": exam_id,
                "schedule": plan_data
            }
        else:
            return {
                "plan_id": plan_id,
                "weeks": weeks,
                "exam_id": exam_id,
                "schedule": []
            }
    except Exception as e:
        print(f"Error generating study plan: {e}")
        return {
            "plan_id": f"plan_{datetime.utcnow().timestamp()}",
            "weeks": weeks,
            "exam_id": exam_id,
            "schedule": [],
            "error": str(e)
        }


async def get_exam_readiness(exam_id: int, db: AsyncSession = None) -> Dict:
    """
    Assess readiness for an upcoming exam.
    
    Args:
        exam_id: Exam identifier
        db: Database session
        
    Returns:
        Readiness assessment with weak areas
    """
    if db is None:
        return {
            "exam_id": exam_id,
            "readiness_score": 0.0,
            "weak_areas": [],
            "strong_areas": []
        }
    
    try:
        # Get exam
        result = await db.execute(
            select(Exam).where(Exam.id == exam_id)
        )
        exam = result.scalar_one_or_none()
        
        if not exam:
            return {"error": f"Exam {exam_id} not found"}
        
        exam_topics = json.loads(exam.topics_json)
        
        # Get progress for exam topics
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id.in_(exam_topics))
        )
        progress_list = result.scalars().all()
        progress_map = {p.topic_id: p for p in progress_list}
        
        # Calculate readiness
        confidences = []
        weak_areas = []
        strong_areas = []
        
        for topic_id in exam_topics:
            if topic_id in progress_map:
                confidence = progress_map[topic_id].confidence
                confidences.append(confidence)
                
                if confidence < 0.5:
                    weak_areas.append({
                        'topic_id': topic_id,
                        'confidence': confidence
                    })
                elif confidence >= 0.8:
                    strong_areas.append({
                        'topic_id': topic_id,
                        'confidence': confidence
                    })
            else:
                confidences.append(0.0)
                weak_areas.append({
                    'topic_id': topic_id,
                    'confidence': 0.0
                })
        
        readiness_score = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Get retention scores if available
        retention_info = []
        if 'retention_service' in _services:
            retention_service = _services['retention_service']
            # Get topics with retention below threshold that need review
            decaying = await retention_service.get_decaying_topics(db, threshold=FSRS_RETENTION_THRESHOLD, limit=50)
            retention_info = [d for d in decaying if d['topic_id'] in exam_topics]
        
        return {
            "exam_id": exam_id,
            "exam_name": exam.name,
            "exam_date": exam.date.isoformat(),
            "readiness_score": readiness_score,
            "weak_areas": weak_areas,
            "strong_areas": strong_areas,
            "topics_needing_review": retention_info
        }
    except Exception as e:
        print(f"Error getting exam readiness: {e}")
        return {
            "exam_id": exam_id,
            "readiness_score": 0.0,
            "weak_areas": [],
            "strong_areas": [],
            "error": str(e)
        }


async def get_curriculum_overview(db: AsyncSession = None) -> Dict:
    """
    Get overview of the medical curriculum structure.
    
    Args:
        db: Database session
        
    Returns:
        Curriculum structure with topics and progress
    """
    if db is None or 'graph_service' not in _services:
        return {
            "total_topics": 0,
            "completed_topics": 0,
            "in_progress": 0,
            "weak_topics": 0,
            "categories": []
        }
    
    try:
        graph_service = _services['graph_service']
        if not graph_service.is_loaded:
            graph_service.load_curriculum()
        
        total_topics = len(graph_service.topics)
        
        # Get all progress
        result = await db.execute(select(TopicProgress))
        progress_list = result.scalars().all()
        progress_map = {p.topic_id: p for p in progress_list}
        
        # Count by confidence levels
        completed_topics = 0  # >= 0.8
        in_progress = 0  # 0.3 - 0.8
        weak_topics = 0  # < 0.3
        
        for topic_id in graph_service.topics.keys():
            if topic_id in progress_map:
                confidence = progress_map[topic_id].confidence
                if confidence >= 0.8:
                    completed_topics += 1
                elif confidence >= 0.3:
                    in_progress += 1
                else:
                    weak_topics += 1
            else:
                weak_topics += 1  # Never studied = weak
        
        # Group by type/category
        categories = {}
        for topic in graph_service.topics.values():
            topic_type = topic.type
            if topic_type not in categories:
                categories[topic_type] = {
                    'total': 0,
                    'completed': 0,
                    'in_progress': 0,
                    'weak': 0
                }
            
            categories[topic_type]['total'] += 1
            
            if topic.id in progress_map:
                confidence = progress_map[topic.id].confidence
                if confidence >= 0.8:
                    categories[topic_type]['completed'] += 1
                elif confidence >= 0.3:
                    categories[topic_type]['in_progress'] += 1
                else:
                    categories[topic_type]['weak'] += 1
            else:
                categories[topic_type]['weak'] += 1
        
        return {
            "total_topics": total_topics,
            "completed_topics": completed_topics,
            "in_progress": in_progress,
            "weak_topics": weak_topics,
            "categories": [
                {"type": k, **v} for k, v in categories.items()
            ]
        }
    except Exception as e:
        print(f"Error getting curriculum overview: {e}")
        return {
            "total_topics": 0,
            "completed_topics": 0,
            "in_progress": 0,
            "weak_topics": 0,
            "categories": [],
            "error": str(e)
        }


async def update_confidence(
    topic_id: str, 
    confidence: float, 
    notes: Optional[str] = None,
    db: AsyncSession = None
) -> Dict:
    """
    Update confidence level for a topic.
    
    Args:
        topic_id: Topic identifier
        confidence: Confidence level (0-1)
        notes: Optional notes about confidence change
        db: Database session
        
    Returns:
        Updated topic details
    """
    if db is None:
        return {"error": "No database session"}
    
    try:
        # Clamp confidence to [0, 1]
        confidence = max(0.0, min(1.0, confidence))
        
        # Get or create progress
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id == topic_id)
        )
        progress = result.scalar_one_or_none()
        
        if progress:
            progress.confidence = confidence
            if notes:
                progress.notes = notes
            progress.updated_at = datetime.utcnow()
        else:
            progress = TopicProgress(
                topic_id=topic_id,
                confidence=confidence,
                notes=notes,
                times_reviewed=0
            )
            db.add(progress)
        
        await db.commit()
        
        return {
            "topic_id": topic_id,
            "confidence": confidence,
            "updated_at": progress.updated_at.isoformat()
        }
    except Exception as e:
        await db.rollback()
        print(f"Error updating confidence: {e}")
        return {"error": str(e)}


async def add_exam(name: str, date: str, topics: List[str], db: AsyncSession = None) -> Dict:
    """
    Add a new exam to track.
    
    Args:
        name: Exam name
        date: Exam date (ISO format YYYY-MM-DD)
        topics: List of topic IDs covered
        db: Database session
        
    Returns:
        Created exam details
    """
    if db is None:
        return {"error": "No database session"}
    
    try:
        # Parse date
        exam_date = datetime.fromisoformat(date).date()
        
        # Create exam
        exam = Exam(
            name=name,
            date=exam_date,
            topics_json=json.dumps(topics)
        )
        db.add(exam)
        await db.commit()
        
        return {
            "exam_id": exam.id,
            "name": name,
            "date": date,
            "topics": topics
        }
    except Exception as e:
        await db.rollback()
        print(f"Error adding exam: {e}")
        return {"error": str(e)}


async def get_upcoming_exams(db: AsyncSession = None) -> List[Dict]:
    """
    Get list of upcoming exams.
    
    Args:
        db: Database session
        
    Returns:
        List of upcoming exams with dates
    """
    if db is None:
        return []
    
    try:
        today = date.today()
        
        result = await db.execute(
            select(Exam)
            .where(Exam.date >= today)
            .order_by(Exam.date.asc())
        )
        exams = result.scalars().all()
        
        return [
            {
                'exam_id': e.id,
                'name': e.name,
                'date': e.date.isoformat(),
                'topics': json.loads(e.topics_json),
                'days_until': (e.date - today).days
            }
            for e in exams
        ]
    except Exception as e:
        print(f"Error getting upcoming exams: {e}")
        return []


async def open_resource(url: str, db: AsyncSession = None) -> Dict:
    """
    Open a learning resource (launches in browser/app).
    
    Args:
        url: Resource URL
        
    Returns:
        Confirmation of resource opening
    """
    return {
        "opened": True,
        "url": url
    }


# OpenAI function definitions
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_weak_topics",
            "description": "Get topics where student confidence is below threshold. Use this to identify areas needing more study.",
            "parameters": {
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "number",
                        "description": "Confidence threshold (0-1), topics below this are returned",
                        "default": 0.3
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_decaying_topics",
            "description": "Get topics not reviewed in specified days according to spaced repetition. Use to find what needs review.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days since last review",
                        "default": 7
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_prerequisites",
            "description": "Get prerequisite topics that should be mastered before studying the given topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Topic identifier"
                    }
                },
                "required": ["topic_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_dependent_topics",
            "description": "Get topics that depend on mastering the given topic. Shows what can be unlocked next.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Topic identifier"
                    }
                },
                "required": ["topic_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_topic_details",
            "description": "Get detailed information about a specific topic including confidence, last studied date, resources, and notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Topic identifier"
                    }
                },
                "required": ["topic_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_notes",
            "description": "Search through student's notes and annotations to find relevant past learning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_anki_stats",
            "description": "Get Anki flashcard statistics including cards due, accuracy, and retention rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Optional topic filter to get stats for specific topic"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": "Generate a quiz for a specific topic to test understanding. Returns questions with multiple choice options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Topic identifier to generate quiz for"
                    },
                    "num_questions": {
                        "type": "integer",
                        "description": "Number of questions to generate",
                        "default": 5
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "medium", "hard"],
                        "description": "Difficulty level of questions",
                        "default": "medium"
                    }
                },
                "required": ["topic_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_quiz_result",
            "description": "Log the result of a quiz question to track learning progress and update confidence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Topic identifier"
                    },
                    "correct": {
                        "type": "boolean",
                        "description": "Whether the answer was correct"
                    },
                    "question": {
                        "type": "string",
                        "description": "The question text that was answered"
                    }
                },
                "required": ["topic_id", "correct", "question"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_study_session",
            "description": "Log a study session to track time spent and update topic progress.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Topic identifier"
                    },
                    "duration_minutes": {
                        "type": "integer",
                        "description": "Duration of study session in minutes"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the study session"
                    }
                },
                "required": ["topic_id", "duration_minutes"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_study_history",
            "description": "Get history of past study sessions to review learning patterns and time allocation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Optional topic filter to get history for specific topic"
                    },
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back",
                        "default": 30
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_study_plan",
            "description": "Generate a personalized study plan based on weak areas, upcoming exams, and spaced repetition needs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {
                        "type": "integer",
                        "description": "Optional exam ID to prepare for"
                    },
                    "weeks": {
                        "type": "integer",
                        "description": "Planning horizon in weeks",
                        "default": 4
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exam_readiness",
            "description": "Assess readiness for an upcoming exam by analyzing confidence in covered topics and identifying weak areas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "exam_id": {
                        "type": "integer",
                        "description": "Exam identifier"
                    }
                },
                "required": ["exam_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_curriculum_overview",
            "description": "Get overview of the entire medical curriculum structure with progress across all topics and categories.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_confidence",
            "description": "Update confidence level for a topic based on self-assessment or quiz performance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic_id": {
                        "type": "string",
                        "description": "Topic identifier"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level (0-1 scale)"
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about confidence change"
                    }
                },
                "required": ["topic_id", "confidence"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_exam",
            "description": "Add a new exam to track and prepare for. This helps generate relevant study plans.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Exam name"
                    },
                    "date": {
                        "type": "string",
                        "description": "Exam date in ISO format (YYYY-MM-DD)"
                    },
                    "topics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of topic IDs covered in the exam"
                    }
                },
                "required": ["name", "date", "topics"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_exams",
            "description": "Get list of upcoming exams with dates and covered topics to prioritize study efforts.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_resource",
            "description": "Open a learning resource (textbook, video, guideline) in browser or appropriate application.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Resource URL to open"
                    }
                },
                "required": ["url"]
            }
        }
    }
]


# Map function names to implementations
TOOL_FUNCTIONS = {
    "get_weak_topics": get_weak_topics,
    "get_decaying_topics": get_decaying_topics,
    "get_prerequisites": get_prerequisites,
    "get_dependent_topics": get_dependent_topics,
    "get_topic_details": get_topic_details,
    "search_notes": search_notes,
    "get_anki_stats": get_anki_stats,
    "generate_quiz": generate_quiz,
    "log_quiz_result": log_quiz_result,
    "log_study_session": log_study_session,
    "get_study_history": get_study_history,
    "generate_study_plan": generate_study_plan,
    "get_exam_readiness": get_exam_readiness,
    "get_curriculum_overview": get_curriculum_overview,
    "update_confidence": update_confidence,
    "add_exam": add_exam,
    "get_upcoming_exams": get_upcoming_exams,
    "open_resource": open_resource
}


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Execute a tool by name with given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments to pass to the tool
        
    Returns:
        Tool execution result
        
    Raises:
        ValueError: If tool name is not recognized
    """
    if tool_name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    func = TOOL_FUNCTIONS[tool_name]
    # All tools are now async
    return await func(**arguments)
