"""
API request/response models using Pydantic.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# ============================================================================
# System Health Models
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    services: Dict[str, bool]


class ModelStatus(BaseModel):
    """LLM model status information."""
    is_loaded: bool
    model_path: Optional[str] = None
    context_length: int
    gpu_layers: int


# ============================================================================
# Chat Models
# ============================================================================

class ChatMessage(BaseModel):
    """Single chat message."""
    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    """Chat request with message history."""
    messages: List[ChatMessage]
    session_id: Optional[str] = "default"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None


class ChatResponse(BaseModel):
    """Chat response from the AI tutor."""
    message: ChatMessage
    finish_reason: str


# ============================================================================
# Knowledge Graph Models
# ============================================================================

class TopicNode(BaseModel):
    """Knowledge graph topic node."""
    id: str
    label: str
    type: str = "topic"
    confidence: float = 0.5
    exam_weight: float = 1.0
    learning_objectives: List[str] = []
    prerequisites: List[str] = []
    in_scope: bool = True


class GraphResponse(BaseModel):
    """Knowledge graph response."""
    nodes: List[TopicNode]
    edges: List[Dict[str, Any]]
    statistics: Optional[Dict[str, Any]] = None


class ConfidenceUpdate(BaseModel):
    """Update confidence for a topic."""
    topic_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    notes: Optional[str] = None


class CurriculumSelection(BaseModel):
    """Select an active curriculum scope."""
    curriculum: str


# ============================================================================
# Quiz Models
# ============================================================================

class QuizRequest(BaseModel):
    """Request to generate a quiz."""
    topic_ids: List[str]
    num_questions: int = 5
    difficulty: str = "medium"
    question_type: str = "sba"  # "sba" or "saq"


class QuizResponse(BaseModel):
    """Response containing generated quiz questions."""
    quiz_id: str
    questions: List[Dict[str, Any]]
    topic_id: str
    difficulty: str


class QuizSubmission(BaseModel):
    """Submit an answer to a quiz question."""
    quiz_id: str
    question_id: str
    topic_id: str
    answer: str


class SAQSubmission(BaseModel):
    """Submit an SAQ (Short Answer Question) answer for marking."""
    quiz_id: str
    question_id: str
    topic_id: str
    answer: str  # Free-text answer from student


class QuizResult(BaseModel):
    """Quiz results and statistics."""
    total: int
    correct: int
    score: float
    by_topic: Dict[str, Any] = {}


# ============================================================================
# Ingest Models
# ============================================================================

class IngestRequest(BaseModel):
    """Request to ingest data into the vector store."""
    file_path: str
    file_type: str  # "pdf", "anki", "notes"
    topic_id: Optional[str] = None


class IngestResponse(BaseModel):
    """Response from data ingestion."""
    success: bool
    message: str
    items_processed: int = 0
    items_mapped: int = 0
    errors: List[str] = []
    statistics: Dict[str, Any] = {}


# ============================================================================
# Study Planning Models
# ============================================================================

class ExamCreate(BaseModel):
    """Create a new exam."""
    name: str
    date: str  # ISO date string
    topics: List[str]


class ExamResponse(BaseModel):
    """Exam information response."""
    id: int
    name: str
    date: str
    topics: List[str]
    created_at: str


class StudyPlanRequest(BaseModel):
    """Request to generate a study plan."""
    exam_id: int
    hours_per_day: float = 2.0
    focus_weak_topics: bool = True


class StudyPlanResponse(BaseModel):
    """Generated study plan response."""
    exam_id: int
    plan: Dict[str, Any]  # Daily study schedule
    created_at: str


class StudySessionLog(BaseModel):
    """Log a completed study session."""
    topic_id: str
    duration: int  # seconds
    quality: int = Field(ge=1, le=5)  # 1-5 rating
    notes: Optional[str] = None


# ============================================================================
# Semester Scope Models
# ============================================================================

class SemesterScopeCreate(BaseModel):
    """Create a new semester scope."""
    name: str
    topic_ids: List[str]
    year: Optional[int] = None
    semester_number: Optional[int] = None
    exam_date: Optional[str] = None
    source_filename: Optional[str] = None


class SemesterTopicMatch(BaseModel):
    """Matched topic from curriculum PDF."""
    topic_id: str
    topic_name: str
    confidence: float
    matched_text: str


class SemesterUploadResponse(BaseModel):
    """Response from semester PDF upload."""
    matched_topics: List[SemesterTopicMatch]
    scope_id: Optional[int] = None
    source_filename: str


class SemesterScopeResponse(BaseModel):
    """Semester scope information."""
    id: int
    name: str
    topic_ids: List[str]
    year: Optional[int] = None
    semester_number: Optional[int] = None
    exam_date: Optional[str] = None
    source_filename: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str
