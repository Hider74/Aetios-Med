"""
Quiz Service
Generate quizzes and track performance using LLM.
"""
import json
import random
from typing import List, Dict, Optional, Any
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import QuizResult, TopicProgress
from .graph_service import GraphService
from .vector_service import VectorService
from .llm_service import LLMService


class QuizService:
    """Service for generating and managing quizzes."""
    
    def __init__(
        self,
        llm_service: LLMService,
        graph_service: GraphService,
        vector_service: VectorService
    ):
        self.llm_service = llm_service
        self.graph_service = graph_service
        self.vector_service = vector_service
    
    async def generate_quiz(
        self,
        topic_id: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions for a topic using LLM.
        
        Args:
            topic_id: Topic to quiz on
            num_questions: Number of questions to generate
            difficulty: 'easy', 'medium', or 'hard'
            db: Database session for context
        
        Returns:
            List of quiz questions with answers
        """
        if not self.graph_service.is_loaded:
            self.graph_service.load_curriculum()
        
        if topic_id not in self.graph_service.topics:
            raise ValueError(f"Topic {topic_id} not found")
        
        topic = self.graph_service.topics[topic_id]
        
        # Get related content from vector store
        related_docs = self.vector_service.get_documents_by_topic(topic_id, n_results=5)
        
        # Build context
        context_parts = []
        context_parts.append(f"Topic: {topic.label}")
        
        if topic.learning_objectives:
            context_parts.append(f"Learning Objectives:\n" + "\n".join(
                f"- {obj}" for obj in topic.learning_objectives[:5]
            ))
        
        if related_docs:
            context_parts.append("\nRelated Content:")
            for doc in related_docs[:3]:
                doc_text = doc.get('document', '')
                if doc_text:
                    context_parts.append(f"- {doc_text[:300]}")
        
        context = "\n\n".join(context_parts)
        
        # Create prompt for LLM
        prompt = f"""You are a medical education expert creating quiz questions.

Generate {num_questions} multiple-choice questions (A, B, C, D) about the following topic.
Difficulty level: {difficulty}

{context}

Requirements:
- Questions should test understanding, not just recall
- Provide 4 options (A, B, C, D) for each question
- Include the correct answer
- Make distractors plausible but clearly incorrect
- Format as JSON array

Return ONLY a JSON array with this structure:
[
  {{
    "question": "Question text here?",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct_answer": "B",
    "explanation": "Why this is correct"
  }}
]"""
        
        # Generate questions
        try:
            response = await self.llm_service.complete(
                messages=[
                    {"role": "system", "content": "You are a medical education expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048
            )
        except Exception as e:
            print(f"LLM generation failed: {e}")
            return self._generate_fallback_questions(topic, num_questions, difficulty)
        
        # Parse response
        try:
            # Extract JSON from response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                questions = json.loads(json_str)
            else:
                raise ValueError("No JSON array found in response")
            
            # Add metadata
            for q in questions:
                q['topic_id'] = topic_id
                q['difficulty'] = difficulty
                q['timestamp'] = datetime.utcnow().isoformat()
            
            return questions
            
        except json.JSONDecodeError as e:
            # Fallback: return empty or generate simple questions
            return self._generate_fallback_questions(topic, num_questions, difficulty)
    
    def _generate_fallback_questions(
        self,
        topic,
        num_questions: int,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """Generate simple fallback questions when LLM fails."""
        questions = []
        
        for i in range(num_questions):
            if i < len(topic.learning_objectives):
                obj = topic.learning_objectives[i]
                questions.append({
                    'question': f"Which of the following best describes: {obj}?",
                    'options': {
                        'A': 'Option A',
                        'B': 'Option B',
                        'C': 'Option C',
                        'D': 'Option D'
                    },
                    'correct_answer': 'A',
                    'explanation': 'This is a placeholder question.',
                    'topic_id': topic.id,
                    'difficulty': difficulty,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        return questions
    
    async def submit_quiz_answer(
        self,
        topic_id: str,
        question: str,
        correct_answer: str,
        user_answer: str,
        difficulty: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Submit a quiz answer and update user progress.
        
        Returns:
            Result with correctness and updated confidence
        """
        is_correct = user_answer.upper() == correct_answer.upper()
        
        # Save result
        quiz_result = QuizResult(
            topic_id=topic_id,
            question=question,
            correct_answer=correct_answer.upper(),
            user_answer=user_answer.upper(),
            is_correct=is_correct,
            difficulty=difficulty,
            timestamp=datetime.utcnow()
        )
        db.add(quiz_result)
        
        # Update topic confidence
        new_confidence = await self._update_confidence_from_quiz(
            topic_id,
            is_correct,
            difficulty,
            db
        )
        
        await db.commit()
        
        return {
            'is_correct': is_correct,
            'correct_answer': correct_answer.upper(),
            'user_answer': user_answer.upper(),
            'new_confidence': new_confidence
        }
    
    async def _update_confidence_from_quiz(
        self,
        topic_id: str,
        is_correct: bool,
        difficulty: str,
        db: AsyncSession
    ) -> float:
        """Update topic confidence based on quiz performance."""
        # Get current progress
        result = await db.execute(
            select(TopicProgress).where(TopicProgress.topic_id == topic_id)
        )
        progress = result.scalar_one_or_none()
        
        if not progress:
            progress = TopicProgress(
                topic_id=topic_id,
                confidence=0.5
            )
            db.add(progress)
        
        # Calculate confidence adjustment
        difficulty_weights = {
            'easy': 0.05,
            'medium': 0.1,
            'hard': 0.15
        }
        
        weight = difficulty_weights.get(difficulty, 0.1)
        
        if is_correct:
            # Increase confidence (with diminishing returns)
            adjustment = weight * (1 - progress.confidence)
            progress.confidence = min(1.0, progress.confidence + adjustment)
        else:
            # Decrease confidence
            adjustment = weight * progress.confidence
            progress.confidence = max(0.0, progress.confidence - adjustment)
        
        # Update quiz statistics
        progress.quiz_attempts += 1
        if is_correct:
            progress.quiz_correct += 1
        
        progress.updated_at = datetime.utcnow()
        
        return progress.confidence
    
    async def get_quiz_statistics(
        self,
        topic_id: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Get quiz statistics for a topic."""
        result = await db.execute(
            select(QuizResult).where(QuizResult.topic_id == topic_id)
        )
        results = result.scalars().all()
        
        if not results:
            return {
                'total_questions': 0,
                'correct': 0,
                'accuracy': 0.0,
                'by_difficulty': {}
            }
        
        total = len(results)
        correct = sum(1 for r in results if r.is_correct)
        
        by_difficulty = {}
        for difficulty in ['easy', 'medium', 'hard']:
            diff_results = [r for r in results if r.difficulty == difficulty]
            if diff_results:
                diff_correct = sum(1 for r in diff_results if r.is_correct)
                by_difficulty[difficulty] = {
                    'total': len(diff_results),
                    'correct': diff_correct,
                    'accuracy': diff_correct / len(diff_results)
                }
        
        return {
            'total_questions': total,
            'correct': correct,
            'accuracy': correct / total,
            'by_difficulty': by_difficulty
        }
    
    async def get_recommended_quiz_topics(
        self,
        db: AsyncSession,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get topics that would benefit from quiz practice."""
        if not self.graph_service.is_loaded:
            self.graph_service.load_curriculum()
        
        # Get all progress
        result = await db.execute(select(TopicProgress))
        progress_map = {p.topic_id: p for p in result.scalars().all()}
        
        # Score topics
        recommendations = []
        for topic in self.graph_service.topics.values():
            progress = progress_map.get(topic.id)
            
            # Calculate recommendation score
            score = 0.0
            
            if progress:
                # Topics with medium confidence benefit most from quizzing
                if 0.3 <= progress.confidence <= 0.7:
                    score += 1.0 - abs(progress.confidence - 0.5)
                
                # Recently studied topics
                if progress.last_studied:
                    days_ago = (datetime.utcnow() - progress.last_studied).days
                    if days_ago <= 7:
                        score += 0.5
                
                # Low quiz attempt count
                if progress.quiz_attempts < 10:
                    score += 0.3
            else:
                # Never studied topics
                score += 0.2
            
            # Exam weight
            score += topic.exam_weight * 0.1
            
            recommendations.append({
                'topic_id': topic.id,
                'topic_label': topic.label,
                'score': score,
                'confidence': progress.confidence if progress else 0.0
            })
        
        # Sort and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
