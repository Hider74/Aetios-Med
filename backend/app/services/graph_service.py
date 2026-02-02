"""
Graph Service
NetworkX-based knowledge graph for curriculum management.
"""
import json
import networkx as nx
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import TopicProgress, StudySession, QuizResult, Note, AnkiCard
from ..models.graph_models import (
    CurriculumTopic, GraphEdge, KnowledgeGraph, 
    GraphStatistics, TopicDetails
)


class GraphService:
    """Service for managing curriculum knowledge graph."""
    
    def __init__(self, curriculum_path: Path):
        self.curriculum_path = curriculum_path
        self.graph: nx.DiGraph = nx.DiGraph()
        self.topics: Dict[str, CurriculumTopic] = {}
        self.is_loaded = False
    
    def load_curriculum(self) -> None:
        """Load curriculum from JSON file."""
        if self.is_loaded:
            return
        
        if not self.curriculum_path.exists():
            raise FileNotFoundError(f"Curriculum not found at {self.curriculum_path}")
        
        with open(self.curriculum_path, 'r') as f:
            data = json.load(f)
        
        # Parse topics
        for topic_data in data.get('topics', []):
            topic = CurriculumTopic(**topic_data)
            self.topics[topic.id] = topic
            self.graph.add_node(
                topic.id,
                label=topic.label,
                type=topic.type,
                exam_weight=topic.exam_weight
            )
        
        # Create edges
        for topic in self.topics.values():
            # Parent relationship
            if topic.parent:
                self.graph.add_edge(topic.parent, topic.id, type='parent')
            
            # Prerequisites
            for prereq_id in topic.prerequisites:
                self.graph.add_edge(prereq_id, topic.id, type='prerequisite')
        
        self.is_loaded = True
    
    async def get_graph_with_progress(
        self, 
        db: AsyncSession
    ) -> KnowledgeGraph:
        """Get complete graph with user progress merged."""
        if not self.is_loaded:
            self.load_curriculum()
        
        # Query all progress
        result = await db.execute(select(TopicProgress))
        progress_map = {p.topic_id: p for p in result.scalars().all()}
        
        # Merge progress into topics
        nodes = []
        for topic in self.topics.values():
            topic_copy = topic.model_copy()
            
            if topic.id in progress_map:
                progress = progress_map[topic.id]
                topic_copy.confidence = progress.confidence
                topic_copy.last_studied = progress.last_studied
                topic_copy.study_count = progress.study_count
            
            nodes.append(topic_copy)
        
        # Build edges
        edges = [
            GraphEdge(source=u, target=v, type=data.get('type', 'related'))
            for u, v, data in self.graph.edges(data=True)
        ]
        
        return KnowledgeGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                'total_topics': len(nodes),
                'total_edges': len(edges),
                'loaded_at': datetime.utcnow().isoformat()
            }
        )
    
    async def get_statistics(self, db: AsyncSession) -> GraphStatistics:
        """Calculate graph statistics."""
        if not self.is_loaded:
            self.load_curriculum()
        
        result = await db.execute(select(TopicProgress))
        progress_list = result.scalars().all()
        progress_map = {p.topic_id: p for p in progress_list}
        
        total_topics = len(self.topics)
        topics_by_type = {}
        confidences = []
        topics_studied = 0
        topics_mastered = 0
        topics_weak = 0
        
        topic_confidence_pairs = []
        
        for topic in self.topics.values():
            # Count by type
            topics_by_type[topic.type] = topics_by_type.get(topic.type, 0) + 1
            
            confidence = 0.0
            if topic.id in progress_map:
                progress = progress_map[topic.id]
                confidence = progress.confidence
                if progress.study_count > 0:
                    topics_studied += 1
            
            confidences.append(confidence)
            topic_confidence_pairs.append({
                'topic_id': topic.id,
                'label': topic.label,
                'confidence': confidence
            })
            
            if confidence > 0.8:
                topics_mastered += 1
            elif confidence < 0.3:
                topics_weak += 1
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Sort for most/least confident
        topic_confidence_pairs.sort(key=lambda x: x['confidence'])
        
        return GraphStatistics(
            total_topics=total_topics,
            topics_by_type=topics_by_type,
            avg_confidence=avg_confidence,
            topics_studied=topics_studied,
            topics_mastered=topics_mastered,
            topics_weak=topics_weak,
            most_confident=topic_confidence_pairs[-5:],
            least_confident=topic_confidence_pairs[:5]
        )
    
    async def get_topic_details(
        self, 
        topic_id: str, 
        db: AsyncSession
    ) -> TopicDetails:
        """Get detailed information about a topic."""
        if not self.is_loaded:
            self.load_curriculum()
        
        if topic_id not in self.topics:
            raise ValueError(f"Topic {topic_id} not found")
        
        topic = self.topics[topic_id].model_copy()
        
        # Get progress
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id == topic_id)
        )
        progress = result.scalar_one_or_none()
        if progress:
            topic.confidence = progress.confidence
            topic.last_studied = progress.last_studied
            topic.study_count = progress.study_count
        
        # Get prerequisites
        prereq_topics = [
            self.topics[prereq_id] for prereq_id in topic.prerequisites
            if prereq_id in self.topics
        ]
        
        # Get dependents (topics that require this)
        dependents = self.get_dependents(topic_id)
        
        # Get study history
        result = await db.execute(
            select(StudySession)
            .where(StudySession.topic_id == topic_id)
            .order_by(StudySession.timestamp.desc())
            .limit(10)
        )
        study_history = [
            {
                'timestamp': s.timestamp.isoformat(),
                'duration_minutes': s.duration_minutes,
                'session_type': s.session_type,
                'confidence_after': s.confidence_after
            }
            for s in result.scalars().all()
        ]
        
        # Get quiz stats
        result = await db.execute(
            select(QuizResult).where(QuizResult.topic_id == topic_id)
        )
        quiz_results = result.scalars().all()
        quiz_stats = {
            'total': len(quiz_results),
            'correct': sum(1 for r in quiz_results if r.is_correct),
            'accuracy': sum(1 for r in quiz_results if r.is_correct) / len(quiz_results) if quiz_results else 0.0
        }
        
        # Query related notes count
        result = await db.execute(
            select(Note).where(Note.topic_id == topic_id)
        )
        related_notes_count = len(result.scalars().all())
        
        # Query related Anki cards count
        result = await db.execute(
            select(AnkiCard).where(AnkiCard.topic_id == topic_id)
        )
        related_cards_count = len(result.scalars().all())
        
        return TopicDetails(
            topic=topic,
            prerequisites=prereq_topics,
            dependents=dependents,
            related_notes=related_notes_count,
            related_cards=related_cards_count,
            study_history=study_history,
            quiz_stats=quiz_stats
        )
    
    def get_prerequisites(self, topic_id: str) -> List[CurriculumTopic]:
        """Get all prerequisite topics (direct and transitive)."""
        if topic_id not in self.topics:
            return []
        
        prereq_ids = set()
        to_visit = [topic_id]
        
        while to_visit:
            current = to_visit.pop()
            for pred in self.graph.predecessors(current):
                edge_type = self.graph.edges[pred, current].get('type')
                if edge_type == 'prerequisite' and pred not in prereq_ids:
                    prereq_ids.add(pred)
                    to_visit.append(pred)
        
        return [self.topics[tid] for tid in prereq_ids if tid in self.topics]
    
    def get_dependents(self, topic_id: str) -> List[CurriculumTopic]:
        """Get all topics that depend on this one."""
        if topic_id not in self.graph:
            return []
        
        dependent_ids = set()
        for succ in self.graph.successors(topic_id):
            edge_type = self.graph.edges[topic_id, succ].get('type')
            if edge_type == 'prerequisite':
                dependent_ids.add(succ)
        
        return [self.topics[tid] for tid in dependent_ids if tid in self.topics]
    
    async def update_topic_confidence(
        self,
        topic_id: str,
        new_confidence: float,
        db: AsyncSession
    ) -> None:
        """Update confidence for a topic."""
        if topic_id not in self.topics:
            raise ValueError(f"Topic {topic_id} not found")
        
        # Clamp confidence
        new_confidence = max(0.0, min(1.0, new_confidence))
        
        # Get or create progress
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id == topic_id)
        )
        progress = result.scalar_one_or_none()
        
        if progress:
            progress.confidence = new_confidence
            progress.updated_at = datetime.utcnow()
        else:
            progress = TopicProgress(
                topic_id=topic_id,
                confidence=new_confidence
            )
            db.add(progress)
        
        await db.commit()
    
    def get_learning_path(
        self, 
        start_topic: str, 
        end_topic: str
    ) -> Optional[List[str]]:
        """Find shortest learning path between two topics."""
        if start_topic not in self.graph or end_topic not in self.graph:
            return None
        
        try:
            path = nx.shortest_path(self.graph, start_topic, end_topic)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_topics_by_type(self, topic_type: str) -> List[CurriculumTopic]:
        """Get all topics of a specific type."""
        return [t for t in self.topics.values() if t.type == topic_type]
    
    def get_next_topics(
        self, 
        current_mastered: List[str]
    ) -> List[CurriculumTopic]:
        """Get topics that are ready to learn based on mastered prerequisites."""
        mastered_set = set(current_mastered)
        next_topics = []
        
        for topic in self.topics.values():
            if topic.id in mastered_set:
                continue
            
            # Check if all prerequisites are mastered
            prereqs = set(topic.prerequisites)
            if prereqs.issubset(mastered_set):
                next_topics.append(topic)
        
        return next_topics
