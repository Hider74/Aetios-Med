"""
Retention Service
FSRS-inspired spaced repetition and retention prediction.
"""
import math
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import TopicProgress, StudySession, QuizResult, AnkiCard


class RetentionService:
    """Service for predicting retention and scheduling reviews."""
    
    # FSRS-4 default parameters (optimized for general learning)
    DEFAULT_PARAMS = {
        'w': [0.4, 0.6, 2.4, 5.8, 4.93, 0.94, 0.86, 0.01, 1.49, 0.14, 0.94, 2.18, 0.05, 0.34, 1.26, 0.29, 2.61]
    }
    
    def __init__(self):
        self.params = self.DEFAULT_PARAMS['w']
    
    def calculate_retention(
        self,
        stability: float,
        elapsed_days: float,
        factor: float = 0.9
    ) -> float:
        """
        Calculate retention probability using FSRS formula.
        
        Args:
            stability: Memory stability in days
            elapsed_days: Days since last review
            factor: Desired retention (0.9 = 90%)
        
        Returns:
            Retention probability (0-1)
        """
        if stability <= 0:
            return 0.0
        
        # FSRS retention formula: R = (1 + elapsed / (9 * stability)) ^ -1
        retention = math.pow(1 + (elapsed_days / (9 * stability)), -1)
        
        return max(0.0, min(1.0, retention))
    
    def calculate_stability(
        self,
        initial_stability: float,
        reviews: int,
        lapses: int,
        ease_factor: float = 2.5
    ) -> float:
        """
        Calculate memory stability based on review history.
        
        Args:
            initial_stability: Starting stability (typically 1 day)
            reviews: Number of successful reviews
            lapses: Number of times forgotten
            ease_factor: Ease factor (Anki-style)
        
        Returns:
            Current stability in days
        """
        # Simple FSRS-inspired calculation
        if reviews == 0:
            return initial_stability
        
        # Stability increases with reviews
        stability = initial_stability * math.pow(ease_factor, reviews)
        
        # Lapses reduce stability
        if lapses > 0:
            stability = stability / math.pow(1.5, lapses)
        
        return max(1.0, stability)
    
    async def get_decaying_topics(
        self,
        db: AsyncSession,
        threshold: float = 0.8,
        limit: int = 10
    ) -> List[Dict[str, any]]:
        """
        Get topics with decaying retention that need review.
        
        Args:
            db: Database session
            threshold: Retention threshold (topics below this need review)
            limit: Maximum number of topics to return
        
        Returns:
            List of topics with retention predictions
        """
        # Get topics with study history
        result = await db.execute(
            select(TopicProgress)
            .where(TopicProgress.last_studied.isnot(None))
            .order_by(TopicProgress.last_studied.asc())
        )
        progress_list = result.scalars().all()
        
        decaying_topics = []
        
        for progress in progress_list:
            # Calculate days since last studied
            elapsed_days = (datetime.utcnow() - progress.last_studied).total_seconds() / 86400
            
            # Estimate stability from study count and quiz performance
            stability = self._estimate_stability_from_progress(progress)
            
            # Calculate retention
            retention = self.calculate_retention(stability, elapsed_days)
            
            # Calculate optimal review date
            optimal_interval = self._calculate_optimal_interval(stability, threshold)
            next_review = progress.last_studied + timedelta(days=optimal_interval)
            
            if retention < threshold or datetime.utcnow() >= next_review:
                decaying_topics.append({
                    'topic_id': progress.topic_id,
                    'confidence': progress.confidence,
                    'retention': retention,
                    'stability_days': stability,
                    'days_since_study': elapsed_days,
                    'last_studied': progress.last_studied.isoformat(),
                    'next_review': next_review.isoformat(),
                    'urgency': 1.0 - retention  # Higher urgency = lower retention
                })
        
        # Sort by urgency (lowest retention first)
        decaying_topics.sort(key=lambda x: x['urgency'], reverse=True)
        
        return decaying_topics[:limit]
    
    def _estimate_stability_from_progress(self, progress: TopicProgress) -> float:
        """Estimate stability from topic progress."""
        # Base stability from study count
        base_stability = 1.0 * math.pow(1.5, min(progress.study_count, 10))
        
        # Adjust based on confidence
        confidence_multiplier = 0.5 + progress.confidence
        
        # Adjust based on quiz performance
        if progress.quiz_attempts > 0:
            quiz_accuracy = progress.quiz_correct / progress.quiz_attempts
            quiz_multiplier = 0.5 + quiz_accuracy
        else:
            quiz_multiplier = 1.0
        
        stability = base_stability * confidence_multiplier * quiz_multiplier
        
        return max(1.0, stability)
    
    def _calculate_optimal_interval(
        self,
        stability: float,
        desired_retention: float = 0.9
    ) -> float:
        """
        Calculate optimal review interval to maintain desired retention.
        
        Based on FSRS formula: R = (1 + t / (9 * S)) ^ -1
        Solving for t: t = 9 * S * (R^-1 - 1)
        """
        if desired_retention >= 1.0:
            return 0.0
        
        interval = 9 * stability * (math.pow(desired_retention, -1) - 1)
        return max(0.0, interval)
    
    async def predict_review_dates(
        self,
        topic_id: str,
        db: AsyncSession,
        desired_retention: float = 0.9
    ) -> List[Dict[str, any]]:
        """
        Predict future review dates for a topic.
        
        Args:
            topic_id: Topic to predict for
            db: Database session
            desired_retention: Target retention level
        
        Returns:
            List of predicted review dates with retention levels
        """
        # Get topic progress
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id == topic_id)
        )
        progress = result.scalar_one_or_none()
        
        if not progress or not progress.last_studied:
            return []
        
        # Calculate current stability
        stability = self._estimate_stability_from_progress(progress)
        
        # Predict next 5 reviews
        predictions = []
        current_date = progress.last_studied
        current_stability = stability
        
        for i in range(5):
            # Calculate optimal interval
            interval = self._calculate_optimal_interval(current_stability, desired_retention)
            
            # Next review date
            next_date = current_date + timedelta(days=interval)
            
            # Predicted retention at that date
            elapsed = (next_date - current_date).total_seconds() / 86400
            retention = self.calculate_retention(current_stability, elapsed)
            
            predictions.append({
                'review_number': i + 1,
                'date': next_date.isoformat(),
                'interval_days': interval,
                'predicted_retention': retention,
                'stability_days': current_stability
            })
            
            # Update for next iteration (stability increases after successful review)
            current_date = next_date
            current_stability = current_stability * 1.5  # Assume successful review
        
        return predictions
    
    async def get_anki_card_retention(
        self,
        card_id: int,
        db: AsyncSession
    ) -> Optional[Dict[str, any]]:
        """
        Calculate retention for an Anki card.
        
        Returns:
            Retention information or None if card not found
        """
        result = await db.execute(
            select(AnkiCard).where(AnkiCard.card_id == card_id)
        )
        card = result.scalar_one_or_none()
        
        if not card:
            return None
        
        if not card.last_review:
            return {
                'card_id': card_id,
                'retention': 0.0,
                'stability_days': 1.0,
                'days_since_review': None,
                'status': 'never_reviewed'
            }
        
        # Calculate stability
        stability = self.calculate_stability(
            initial_stability=1.0,
            reviews=card.reviews,
            lapses=card.lapses,
            ease_factor=card.ease_factor
        )
        
        # Calculate elapsed time
        elapsed_days = (datetime.utcnow() - card.last_review).total_seconds() / 86400
        
        # Calculate retention
        retention = self.calculate_retention(stability, elapsed_days)
        
        # Determine status
        if retention >= 0.9:
            status = 'strong'
        elif retention >= 0.7:
            status = 'good'
        elif retention >= 0.5:
            status = 'fading'
        else:
            status = 'weak'
        
        return {
            'card_id': card_id,
            'retention': retention,
            'stability_days': stability,
            'days_since_review': elapsed_days,
            'status': status,
            'ease_factor': card.ease_factor,
            'lapses': card.lapses
        }
    
    async def get_weak_anki_cards(
        self,
        db: AsyncSession,
        retention_threshold: float = 0.7,
        limit: int = 20
    ) -> List[Dict[str, any]]:
        """Get Anki cards with low retention that need review."""
        result = await db.execute(
            select(AnkiCard)
            .where(AnkiCard.last_review.isnot(None))
            .order_by(AnkiCard.last_review.asc())
        )
        cards = result.scalars().all()
        
        weak_cards = []
        
        for card in cards:
            retention_info = await self.get_anki_card_retention(card.card_id, db)
            
            if retention_info and retention_info['retention'] < retention_threshold:
                weak_cards.append({
                    'card_id': card.card_id,
                    'deck': card.deck_name,
                    'topic_id': card.topic_id,
                    'front': card.front[:100],
                    'retention': retention_info['retention'],
                    'stability_days': retention_info['stability_days'],
                    'days_since_review': retention_info['days_since_review']
                })
        
        # Sort by lowest retention
        weak_cards.sort(key=lambda x: x['retention'])
        
        return weak_cards[:limit]
    
    def estimate_study_time_needed(
        self,
        num_topics: int,
        avg_confidence: float,
        target_confidence: float = 0.8
    ) -> Dict[str, float]:
        """
        Estimate study time needed to reach target confidence.
        
        Returns:
            Dictionary with time estimates
        """
        # Simple heuristic: each topic needs time inversely proportional to confidence
        confidence_gap = max(0.0, target_confidence - avg_confidence)
        
        # Assume 30 minutes per topic per 0.1 confidence increase
        minutes_per_topic = (confidence_gap / 0.1) * 30
        total_minutes = num_topics * minutes_per_topic
        
        return {
            'total_minutes': total_minutes,
            'total_hours': total_minutes / 60,
            'total_days': total_minutes / (60 * 2),  # 2 hours per day
            'minutes_per_topic': minutes_per_topic
        }
