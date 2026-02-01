"""
Ingest Service
Process and ingest files into the knowledge base.
"""
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..parsers.anki_parser import AnkiParser
from ..models.database import AnkiCard as DBAnkiCard, Note
from .vector_service import VectorService
from .graph_service import GraphService


class IngestService:
    """Service for ingesting content into the knowledge base."""
    
    def __init__(
        self,
        vector_service: VectorService,
        graph_service: GraphService
    ):
        self.vector_service = vector_service
        self.graph_service = graph_service
        self.anki_parser = AnkiParser()
    
    async def ingest_anki_file(
        self,
        apkg_path: Path,
        db: AsyncSession
    ) -> Dict[str, int]:
        """
        Process an Anki .apkg file and ingest cards.
        
        Returns:
            Statistics about the ingestion
        """
        # Parse the file
        cards = self.anki_parser.parse(apkg_path)
        
        if not cards:
            return {
                'total': 0,
                'new': 0,
                'updated': 0,
                'mapped': 0,
                'errors': 0
            }
        
        # Ensure graph is loaded for topic mapping
        if not self.graph_service.is_loaded:
            self.graph_service.load_curriculum()
        
        # Prepare topic candidates for matching
        topic_candidates = [
            {
                'id': topic.id,
                'description': f"{topic.label}. {' '.join(topic.learning_objectives[:3])}"
            }
            for topic in self.graph_service.topics.values()
        ]
        
        stats = {
            'total': len(cards),
            'new': 0,
            'updated': 0,
            'mapped': 0,
            'errors': 0
        }
        
        # Process each card
        for card in cards:
            try:
                # Map to topic using embeddings
                card_text = card.to_embedding_text()
                topic_id = self.vector_service.find_best_topic_match(
                    card_text,
                    topic_candidates
                )
                
                if topic_id:
                    stats['mapped'] += 1
                
                # Check if card exists in database
                result = await db.execute(
                    select(DBAnkiCard).where(DBAnkiCard.card_id == card.card_id)
                )
                db_card = result.scalar_one_or_none()
                
                if db_card:
                    # Update existing card
                    db_card.deck_name = card.deck_name
                    db_card.front = card.clean_front
                    db_card.back = card.clean_back
                    db_card.tags = ','.join(card.tags)
                    db_card.topic_id = topic_id
                    db_card.interval = card.interval
                    db_card.ease_factor = card.ease_factor
                    db_card.reviews = card.reviews
                    db_card.lapses = card.lapses
                    if card.last_review:
                        db_card.last_review = datetime.fromtimestamp(card.last_review)
                    db_card.last_synced = datetime.utcnow()
                    stats['updated'] += 1
                else:
                    # Create new card
                    db_card = DBAnkiCard(
                        card_id=card.card_id,
                        note_id=card.note_id,
                        deck_name=card.deck_name,
                        front=card.clean_front,
                        back=card.clean_back,
                        tags=','.join(card.tags),
                        topic_id=topic_id,
                        interval=card.interval,
                        ease_factor=card.ease_factor,
                        reviews=card.reviews,
                        lapses=card.lapses,
                        last_review=datetime.fromtimestamp(card.last_review) if card.last_review else None,
                        last_synced=datetime.utcnow()
                    )
                    db.add(db_card)
                    stats['new'] += 1
                
                # Add to vector store
                doc_id = f"anki_{card.card_id}"
                self.vector_service.add_documents(
                    documents=[card_text],
                    metadatas=[{
                        'source': 'anki',
                        'deck': card.deck_name,
                        'topic_id': topic_id or '',
                        'card_id': card.card_id,
                        'stability': card.stability
                    }],
                    ids=[doc_id]
                )
                
            except Exception as e:
                stats['errors'] += 1
                print(f"Error processing card {card.card_id}: {e}")
        
        await db.commit()
        
        return stats
    
    async def ingest_text_note(
        self,
        title: str,
        content: str,
        topic_id: Optional[str],
        source_path: Optional[Path],
        db: AsyncSession
    ) -> int:
        """
        Ingest a text note into the knowledge base.
        
        Returns:
            Note ID
        """
        # Auto-map to topic if not provided
        if not topic_id and self.graph_service.is_loaded:
            topic_candidates = [
                {
                    'id': topic.id,
                    'description': f"{topic.label}. {' '.join(topic.learning_objectives[:3])}"
                }
                for topic in self.graph_service.topics.values()
            ]
            
            topic_id = self.vector_service.find_best_topic_match(
                f"{title}. {content[:500]}",
                topic_candidates
            )
        
        # Create note in database
        note = Note(
            title=title,
            content=content,
            source_path=str(source_path) if source_path else None,
            topic_id=topic_id,
            is_encrypted=False
        )
        db.add(note)
        await db.flush()
        
        # Add to vector store
        doc_id = f"note_{note.id}"
        self.vector_service.add_documents(
            documents=[f"{title}\n\n{content}"],
            metadatas=[{
                'source': 'note',
                'title': title,
                'topic_id': topic_id or '',
                'note_id': note.id
            }],
            ids=[doc_id]
        )
        
        await db.commit()
        
        return note.id
    
    async def batch_ingest_notes(
        self,
        notes: List[Dict[str, str]],
        db: AsyncSession
    ) -> Dict[str, int]:
        """
        Batch ingest multiple notes.
        
        Args:
            notes: List of dicts with 'title', 'content', 'topic_id' (optional)
        
        Returns:
            Statistics
        """
        stats = {
            'total': len(notes),
            'created': 0,
            'errors': 0
        }
        
        for note_data in notes:
            try:
                await self.ingest_text_note(
                    title=note_data['title'],
                    content=note_data['content'],
                    topic_id=note_data.get('topic_id'),
                    source_path=None,
                    db=db
                )
                stats['created'] += 1
            except Exception as e:
                stats['errors'] += 1
                print(f"Error ingesting note '{note_data.get('title', 'unknown')}': {e}")
        
        return stats
    
    async def delete_anki_deck(
        self,
        deck_name: str,
        db: AsyncSession
    ) -> int:
        """
        Delete all cards from a deck.
        
        Returns:
            Number of cards deleted
        """
        # Get cards from database
        result = await db.execute(
            select(DBAnkiCard).where(DBAnkiCard.deck_name == deck_name)
        )
        cards = result.scalars().all()
        
        # Delete from vector store
        doc_ids = [f"anki_{card.card_id}" for card in cards]
        if doc_ids:
            self.vector_service.delete_documents(doc_ids)
        
        # Delete from database
        count = len(cards)
        for card in cards:
            await db.delete(card)
        
        await db.commit()
        
        return count
    
    async def remap_card_topics(
        self,
        db: AsyncSession
    ) -> Dict[str, int]:
        """
        Re-map all Anki cards to topics using current embeddings.
        
        Returns:
            Statistics
        """
        if not self.graph_service.is_loaded:
            self.graph_service.load_curriculum()
        
        # Get all cards
        result = await db.execute(select(DBAnkiCard))
        cards = result.scalars().all()
        
        # Prepare topic candidates
        topic_candidates = [
            {
                'id': topic.id,
                'description': f"{topic.label}. {' '.join(topic.learning_objectives[:3])}"
            }
            for topic in self.graph_service.topics.values()
        ]
        
        stats = {
            'total': len(cards),
            'remapped': 0,
            'unchanged': 0
        }
        
        for card in cards:
            card_text = f"Question: {card.front}\nAnswer: {card.back}"
            new_topic_id = self.vector_service.find_best_topic_match(
                card_text,
                topic_candidates
            )
            
            if new_topic_id and new_topic_id != card.topic_id:
                card.topic_id = new_topic_id
                stats['remapped'] += 1
                
                # Update vector store metadata
                doc_id = f"anki_{card.card_id}"
                try:
                    self.vector_service.update_documents(
                        documents=[card_text],
                        metadatas=[{
                            'source': 'anki',
                            'deck': card.deck_name,
                            'topic_id': new_topic_id,
                            'card_id': card.card_id,
                            'stability': card.interval * (card.ease_factor / 2.5)
                        }],
                        ids=[doc_id]
                    )
                except:
                    pass  # Document might not exist yet
            else:
                stats['unchanged'] += 1
        
        await db.commit()
        
        return stats
    
    def get_ingest_statistics(self) -> Dict[str, Any]:
        """Get overall ingestion statistics."""
        return {
            'vector_store': self.vector_service.get_collection_info(),
            'topics_loaded': len(self.graph_service.topics) if self.graph_service.is_loaded else 0
        }
