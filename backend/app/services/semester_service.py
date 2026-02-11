"""
Semester Service
Manages semester curriculum scopes for focused study planning.
"""
import json
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
import numpy as np

from ..models.database import SemesterScope
from ..parsers.pdf_parser import PDFParser
from .graph_service import GraphService
from .vector_service import VectorService


class SemesterService:
    """Service for managing semester curriculum scopes."""
    
    def __init__(self, graph_service: GraphService, vector_service: VectorService):
        self.graph_service = graph_service
        self.vector_service = vector_service
        self.pdf_parser = PDFParser()
    
    async def extract_topics_from_pdf(self, pdf_path: Path, filename: str) -> List[Dict]:
        """
        Extract text from a curriculum PDF and match against knowledge graph topics.
        
        Returns a list of matched topics with confidence scores:
        [
            {"topic_id": "cardiology", "topic_label": "Cardiology", "match_score": 0.85},
            ...
        ]
        """
        # 1. Parse PDF using existing PDFParser
        chunks = self.pdf_parser.parse(pdf_path)
        if not chunks:
            return []
        
        # 2. Combine all text for matching
        full_text = "\n".join(c.text for c in chunks)
        
        # 3. Ensure graph is loaded
        if not self.graph_service.is_loaded:
            self.graph_service.load_curriculum()
        
        # 4. For each topic in the graph, check if the PDF content is semantically related
        # Use vector similarity to match PDF text against topic descriptions
        topic_candidates = [
            {
                'id': topic.id,
                'label': topic.label,
                'description': f"{topic.label}. {' '.join(topic.learning_objectives[:5])}"
            }
            for topic in self.graph_service.topics.values()
        ]
        
        matched_topics = []
        
        # Compute similarity using embeddings
        # Get embeddings for PDF text (use first 2000 chars for efficiency)
        pdf_text_sample = full_text[:2000]
        pdf_embedding = self.vector_service.embedder.encode(
            [pdf_text_sample],
            show_progress_bar=False,
            convert_to_numpy=True
        )[0]
        
        # Get embeddings for each topic description
        topic_descriptions = [c['description'] for c in topic_candidates]
        topic_embeddings = self.vector_service.embedder.encode(
            topic_descriptions,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Compute cosine similarity
        for i, candidate in enumerate(topic_candidates):
            # Cosine similarity
            score = float(np.dot(pdf_embedding, topic_embeddings[i]) / 
                         (np.linalg.norm(pdf_embedding) * np.linalg.norm(topic_embeddings[i])))
            
            # Also check if topic label appears in the text (simple keyword matching boost)
            if candidate['label'].lower() in full_text.lower():
                score = min(1.0, score * 1.2)  # 20% boost if exact match found
            
            if score > 0.3:  # Threshold for relevance
                matched_topics.append({
                    'topic_id': candidate['id'],
                    'topic_label': candidate['label'],
                    'match_score': round(score, 3)
                })
        
        # Sort by match score descending
        matched_topics.sort(key=lambda x: x['match_score'], reverse=True)
        
        return matched_topics
    
    async def create_scope(
        self, 
        name: str, 
        topic_ids: List[str],
        db: AsyncSession,
        year: int = None,
        semester_number: int = None,
        exam_date: datetime = None,
        source_filename: str = None
    ) -> int:
        """Create a new semester scope."""
        scope = SemesterScope(
            name=name,
            year=year,
            semester_number=semester_number,
            exam_date=exam_date,
            topic_ids=json.dumps(topic_ids),
            source_filename=source_filename,
            is_active=False
        )
        db.add(scope)
        await db.commit()
        await db.refresh(scope)
        return scope.id
    
    async def activate_scope(self, scope_id: int, db: AsyncSession):
        """Activate a scope (deactivates all others)."""
        # Deactivate all
        await db.execute(
            update(SemesterScope).values(is_active=False)
        )
        # Activate this one
        result = await db.execute(
            select(SemesterScope).where(SemesterScope.id == scope_id)
        )
        scope = result.scalar_one_or_none()
        if scope:
            scope.is_active = True
            await db.commit()
    
    async def deactivate_all_scopes(self, db: AsyncSession):
        """Deactivate all scopes (show full curriculum)."""
        await db.execute(
            update(SemesterScope).values(is_active=False)
        )
        await db.commit()
    
    async def get_active_scope(self, db: AsyncSession) -> Optional[SemesterScope]:
        """Get the currently active scope, if any."""
        result = await db.execute(
            select(SemesterScope).where(SemesterScope.is_active == True)
        )
        return result.scalar_one_or_none()
    
    async def get_all_scopes(self, db: AsyncSession) -> List[SemesterScope]:
        """Get all semester scopes."""
        result = await db.execute(
            select(SemesterScope).order_by(SemesterScope.created_at.desc())
        )
        return list(result.scalars().all())
    
    async def get_scope_by_id(self, scope_id: int, db: AsyncSession) -> Optional[SemesterScope]:
        """Get a semester scope by ID."""
        result = await db.execute(
            select(SemesterScope).where(SemesterScope.id == scope_id)
        )
        return result.scalar_one_or_none()
    
    async def update_scope_topics(self, scope_id: int, topic_ids: List[str], db: AsyncSession):
        """Update the topic list for a scope (for user corrections after auto-matching)."""
        result = await db.execute(
            select(SemesterScope).where(SemesterScope.id == scope_id)
        )
        scope = result.scalar_one_or_none()
        if scope:
            scope.topic_ids = json.dumps(topic_ids)
            scope.updated_at = datetime.now(timezone.utc)
            await db.commit()
    
    async def delete_scope(self, scope_id: int, db: AsyncSession):
        """Delete a semester scope."""
        await db.execute(
            delete(SemesterScope).where(SemesterScope.id == scope_id)
        )
        await db.commit()
