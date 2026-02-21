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
    
    def __init__(
        self,
        curriculum_paths: Dict[str, Path],
        active_curriculum_key: Optional[str] = None
    ):
        self.curriculum_paths = curriculum_paths
        self.active_curriculum_key = active_curriculum_key or self._default_curriculum_key()
        self.graphs: Dict[str, nx.DiGraph] = {}
        self.topics_by_curriculum: Dict[str, Dict[str, CurriculumTopic]] = {}
        self.loaded_curricula = set()

        # Active curriculum references
        self.graph: nx.DiGraph = nx.DiGraph()
        self.topics: Dict[str, CurriculumTopic] = {}
        self.is_loaded = False

    def _default_curriculum_key(self) -> str:
        """Choose a default curriculum key based on available files."""
        uploaded_path = self.curriculum_paths.get("uploaded")
        if uploaded_path and uploaded_path.exists():
            return "uploaded"

        ukmla_path = self.curriculum_paths.get("ukmla")
        if ukmla_path and ukmla_path.exists():
            return "ukmla"

        # Fallback to the first configured curriculum key
        return next(iter(self.curriculum_paths.keys()))

    def _resolve_curriculum_key(self, curriculum_key: Optional[str]) -> str:
        """Resolve a curriculum key, validating it against known paths."""
        if curriculum_key:
            if curriculum_key not in self.curriculum_paths:
                raise ValueError(f"Unknown curriculum: {curriculum_key}")
            return curriculum_key

        if self.active_curriculum_key:
            return self.active_curriculum_key

        return self._default_curriculum_key()

    def get_available_curricula(self) -> List[str]:
        """Return curriculum keys that have an existing file on disk."""
        available = []
        for key, path in self.curriculum_paths.items():
            if path.exists():
                available.append(key)
        return available

    def set_active_curriculum(self, curriculum_key: str) -> None:
        """Set the active curriculum, loading it if needed."""
        if curriculum_key not in self.curriculum_paths:
            raise ValueError(f"Unknown curriculum: {curriculum_key}")

        path = self.curriculum_paths[curriculum_key]
        if not path.exists():
            raise FileNotFoundError(f"Curriculum not found at {path}")

        self.active_curriculum_key = curriculum_key
        self.load_curriculum(curriculum_key)

        self.graph = self.graphs[curriculum_key]
        self.topics = self.topics_by_curriculum[curriculum_key]
        self.is_loaded = True

    def _get_graph_and_topics(
        self,
        curriculum_key: Optional[str]
    ) -> Tuple[str, nx.DiGraph, Dict[str, CurriculumTopic]]:
        """Get the graph and topics for a curriculum, loading if needed."""
        key = self._resolve_curriculum_key(curriculum_key)
        if key not in self.loaded_curricula:
            self.load_curriculum(key)

        return key, self.graphs[key], self.topics_by_curriculum[key]
    
    def load_curriculum(self, curriculum_key: Optional[str] = None) -> None:
        """Load curriculum from JSON file."""
        key = self._resolve_curriculum_key(curriculum_key)
        if key in self.loaded_curricula:
            if key == self.active_curriculum_key:
                self.graph = self.graphs[key]
                self.topics = self.topics_by_curriculum[key]
                self.is_loaded = True
            return

        curriculum_path = self.curriculum_paths.get(key)
        if not curriculum_path:
            raise ValueError(f"Unknown curriculum: {key}")

        if not curriculum_path.exists():
            raise FileNotFoundError(f"Curriculum not found at {curriculum_path}")

        with open(curriculum_path, 'r') as f:
            data = json.load(f)

        # Support both top-level and nested curriculum formats
        if isinstance(data, dict) and "curriculum" in data:
            data = data["curriculum"]

        graph = nx.DiGraph()
        topics: Dict[str, CurriculumTopic] = {}

        # Graph-optimized format (nodes + edges)
        if isinstance(data, dict) and "nodes" in data and "edges" in data:
            for node in data.get("nodes", []):
                node_id = node.get("id")
                node_label = node.get("name") or node.get("label") or node_id
                node_type = node.get("label") or node.get("type") or "topic"
                if not node_id:
                    continue

                topic = CurriculumTopic(
                    id=node_id,
                    label=node_label,
                    type=node_type
                )
                topics[topic.id] = topic
                graph.add_node(
                    topic.id,
                    label=topic.label,
                    type=topic.type,
                    exam_weight=topic.exam_weight
                )

            for edge in data.get("edges", []):
                source = edge.get("source")
                target = edge.get("target")
                edge_type = edge.get("type", "related")
                if source and target:
                    graph.add_edge(source, target, type=edge_type)
        else:
            # Standard curriculum format (topics with parent/prerequisites)
            for topic_data in data.get('topics', []):
                topic = CurriculumTopic(**topic_data)
                topics[topic.id] = topic
                graph.add_node(
                    topic.id,
                    label=topic.label,
                    type=topic.type,
                    exam_weight=topic.exam_weight
                )

            # Create edges
            for topic in topics.values():
                # Parent relationship
                if topic.parent:
                    graph.add_edge(topic.parent, topic.id, type='parent')

                # Prerequisites
                for prereq_id in topic.prerequisites:
                    graph.add_edge(prereq_id, topic.id, type='prerequisite')

        self.graphs[key] = graph
        self.topics_by_curriculum[key] = topics
        self.loaded_curricula.add(key)

        if key == self.active_curriculum_key:
            self.graph = graph
            self.topics = topics
            self.is_loaded = True
    
    async def get_graph_with_progress(
        self,
        db: AsyncSession,
        scoped_topic_ids: Optional[set] = None,
        curriculum_key: Optional[str] = None
    ) -> KnowledgeGraph:
        """Get complete graph with user progress merged."""
        _, graph, topics = self._get_graph_and_topics(curriculum_key)
        
        # Query all progress
        result = await db.execute(select(TopicProgress))
        progress_map = {p.topic_id: p for p in result.scalars().all()}
        
        # Merge progress into topics
        nodes = []
        for topic in topics.values():
            topic_copy = topic.model_copy()
            
            if topic.id in progress_map:
                progress = progress_map[topic.id]
                topic_copy.confidence = progress.confidence
                topic_copy.last_studied = progress.last_studied
                topic_copy.study_count = progress.study_count
            
            # Set in_scope flag based on semester scope
            if scoped_topic_ids is not None:
                topic_copy.in_scope = topic.id in scoped_topic_ids
            else:
                topic_copy.in_scope = True  # All topics in scope if no filter
            
            nodes.append(topic_copy)
        
        # Build edges
        edges = [
            GraphEdge(source=u, target=v, type=data.get('type', 'related'))
            for u, v, data in graph.edges(data=True)
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
    
    async def get_statistics(
        self,
        db: AsyncSession,
        curriculum_key: Optional[str] = None
    ) -> GraphStatistics:
        """Calculate graph statistics."""
        _, _, topics = self._get_graph_and_topics(curriculum_key)
        
        result = await db.execute(select(TopicProgress))
        progress_list = result.scalars().all()
        progress_map = {p.topic_id: p for p in progress_list}
        
        total_topics = len(topics)
        topics_by_type = {}
        confidences = []
        topics_studied = 0
        topics_mastered = 0
        topics_weak = 0
        
        topic_confidence_pairs = []
        
        for topic in topics.values():
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
            average_confidence=avg_confidence,  # Fixed: was avg_confidence, model expects average_confidence
            topics_studied=topics_studied,
            topics_mastered=topics_mastered,
            topics_weak=topics_weak,
            most_confident=topic_confidence_pairs[-5:],
            least_confident=topic_confidence_pairs[:5]
        )
    
    async def get_weak_topics(
        self,
        db: AsyncSession,
        threshold: float = 0.3,
        curriculum_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get topics with confidence below threshold."""
        _, _, topics = self._get_graph_and_topics(curriculum_key)
        
        result = await db.execute(select(TopicProgress))
        progress_map = {p.topic_id: p for p in result.scalars().all()}
        
        weak_topics = []
        for topic in topics.values():
            confidence = 0.0
            if topic.id in progress_map:
                confidence = progress_map[topic.id].confidence
            
            if confidence < threshold:
                weak_topics.append({
                    'topic_id': topic.id,
                    'label': topic.label,
                    'confidence': confidence,
                    'type': topic.type
                })
        
        # Sort by confidence (weakest first)
        weak_topics.sort(key=lambda x: x['confidence'])
        return weak_topics
    
    async def get_topic_details(
        self,
        topic_id: str,
        db: AsyncSession,
        curriculum_key: Optional[str] = None
    ) -> TopicDetails:
        """Get detailed information about a topic."""
        _, graph, topics = self._get_graph_and_topics(curriculum_key)

        if topic_id not in topics:
            raise ValueError(f"Topic {topic_id} not found")

        topic = topics[topic_id].model_copy()
        
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
            topics[prereq_id] for prereq_id in topic.prerequisites
            if prereq_id in topics
        ]
        
        # Get dependents (topics that require this)
        dependents = self.get_dependents(topic_id, curriculum_key=curriculum_key)
        
        # Get study history
        result = await db.execute(
            select(StudySession)
            .where(StudySession.topic_id == topic_id)
            .order_by(StudySession.session_date.desc())
            .limit(10)
        )
        study_history = [
            {
                'timestamp': s.session_date.isoformat(),
                'duration': s.duration,
                'quality': s.quality
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
    
    def get_prerequisites(
        self,
        topic_id: str,
        curriculum_key: Optional[str] = None
    ) -> List[CurriculumTopic]:
        """Get all prerequisite topics (direct and transitive)."""
        _, graph, topics = self._get_graph_and_topics(curriculum_key)

        if topic_id not in topics:
            return []
        
        prereq_ids = set()
        to_visit = [topic_id]
        
        while to_visit:
            current = to_visit.pop()
            for pred in graph.predecessors(current):
                edge_type = graph.edges[pred, current].get('type')
                if edge_type == 'prerequisite' and pred not in prereq_ids:
                    prereq_ids.add(pred)
                    to_visit.append(pred)

        return [topics[tid] for tid in prereq_ids if tid in topics]
    
    def get_dependents(
        self,
        topic_id: str,
        curriculum_key: Optional[str] = None
    ) -> List[CurriculumTopic]:
        """Get all topics that depend on this one."""
        _, graph, topics = self._get_graph_and_topics(curriculum_key)

        if topic_id not in graph:
            return []

        dependent_ids = set()
        for succ in graph.successors(topic_id):
            edge_type = graph.edges[topic_id, succ].get('type')
            if edge_type == 'prerequisite':
                dependent_ids.add(succ)

        return [topics[tid] for tid in dependent_ids if tid in topics]
    
    async def update_topic_confidence(
        self,
        topic_id: str,
        new_confidence: float,
        db: AsyncSession,
        curriculum_key: Optional[str] = None
    ) -> None:
        """Update confidence for a topic."""
        _, _, topics = self._get_graph_and_topics(curriculum_key)

        if topic_id not in topics:
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
        end_topic: str,
        curriculum_key: Optional[str] = None
    ) -> Optional[List[str]]:
        """Find shortest learning path between two topics."""
        _, graph, _ = self._get_graph_and_topics(curriculum_key)

        if start_topic not in graph or end_topic not in graph:
            return None
        
        try:
            path = nx.shortest_path(graph, start_topic, end_topic)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def get_topics_by_type(
        self,
        topic_type: str,
        curriculum_key: Optional[str] = None
    ) -> List[CurriculumTopic]:
        """Get all topics of a specific type."""
        _, _, topics = self._get_graph_and_topics(curriculum_key)
        return [t for t in topics.values() if t.type == topic_type]
    
    def get_next_topics(
        self, 
        current_mastered: List[str],
        curriculum_key: Optional[str] = None
    ) -> List[CurriculumTopic]:
        """Get topics that are ready to learn based on mastered prerequisites."""
        _, _, topics = self._get_graph_and_topics(curriculum_key)

        mastered_set = set(current_mastered)
        next_topics = []

        for topic in topics.values():
            if topic.id in mastered_set:
                continue
            
            # Check if all prerequisites are mastered
            prereqs = set(topic.prerequisites)
            if prereqs.issubset(mastered_set):
                next_topics.append(topic)
        
        return next_topics
