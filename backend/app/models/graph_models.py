"""
Graph-specific models for knowledge graph operations.
"""
from pydantic import BaseModel
from typing import List, Dict, Optional


class TopicDetails(BaseModel):
    """Detailed information about a single topic."""
    id: str
    label: str
    type: str = "topic"
    confidence: float = 0.5
    exam_weight: float = 1.0
    learning_objectives: List[str] = []
    prerequisites: List[str] = []
    resources: Optional[Dict[str, str]] = None
    notes_count: int = 0
    anki_cards_count: int = 0
    quiz_attempts: int = 0
    last_studied: Optional[str] = None
    in_scope: bool = True


class GraphStatistics(BaseModel):
    """Overall knowledge graph statistics."""
    total_topics: int
    average_confidence: float
    topics_mastered: int = 0
    topics_in_progress: int = 0
    topics_weak: int = 0
    total_study_time: int = 0
