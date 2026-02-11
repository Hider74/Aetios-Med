"""
Quiz Service
Generate quizzes and track performance using LLM.
"""
import json
import random
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
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
        question_type: str = "sba",  # NEW: "sba" or "saq"
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions — SBA (multiple choice) or SAQ (short answer).
        
        Args:
            topic_id: Topic to quiz on
            num_questions: Number of questions to generate
            difficulty: 'easy', 'medium', or 'hard'
            question_type: 'sba' for Single Best Answer or 'saq' for Short Answer Questions
            db: Database session for context
        
        Returns:
            List of quiz questions with answers
        """
        if question_type == "saq":
            return await self._generate_saq(topic_id, num_questions, difficulty, db)
        else:
            # Existing SBA generation logic (unchanged)
            return await self._generate_sba(topic_id, num_questions, difficulty, db)
    
    async def _generate_sba(
        self,
        topic_id: str,
        num_questions: int = 5,
        difficulty: str = "medium",
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate SBA (Single Best Answer) multiple-choice questions for a topic using LLM.
        
        Args:
            topic_id: Topic to quiz on
            num_questions: Number of questions to generate
            difficulty: 'easy', 'medium', or 'hard'
            db: Database session for context
        
        Returns:
            List of SBA quiz questions with answers
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
                q['question_type'] = 'sba'
                q['timestamp'] = datetime.utcnow().isoformat()
            
            return questions
            
        except json.JSONDecodeError as e:
            # Fallback: return empty or generate simple questions
            print(f"JSON parsing failed: {e}. Response preview: {response[:200]}")
            return self._generate_fallback_questions(topic, num_questions, difficulty)
    
    def _generate_fallback_questions(
        self,
        topic,
        num_questions: int,
        difficulty: str
    ) -> List[Dict[str, Any]]:
        """
        Handle failed quiz generation gracefully.
        Returns empty list and logs the error for troubleshooting.
        The frontend should handle empty quiz responses appropriately.
        """
        print(f"Quiz generation failed for topic {topic.id}. LLM may not be loaded or available.")
        print(f"Check that the model is loaded and functioning correctly.")
        return []
    
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
    
    async def _generate_saq(
        self,
        topic_id: str,
        num_questions: int,
        difficulty: str,
        db: Optional[AsyncSession] = None
    ) -> List[Dict[str, Any]]:
        """Generate SAQ questions using the LLM."""
        if not self.graph_service.is_loaded:
            self.graph_service.load_curriculum()
        
        if topic_id not in self.graph_service.topics:
            raise ValueError(f"Topic {topic_id} not found")
        
        topic = self.graph_service.topics[topic_id]
        
        # Get related content from vector store (same as SBA)
        related_docs = self.vector_service.get_documents_by_topic(topic_id, n_results=5)
        
        # Build context (same pattern as SBA)
        context_parts = [f"Topic: {topic.label}"]
        if topic.learning_objectives:
            context_parts.append("Learning Objectives:\n" + "\n".join(
                f"- {obj}" for obj in topic.learning_objectives[:5]
            ))
        if related_docs:
            context_parts.append("\nRelated Content:")
            for doc in related_docs[:3]:
                doc_text = doc.get('document', '')
                if doc_text:
                    context_parts.append(f"- {doc_text[:300]}")
        
        context = "\n\n".join(context_parts)
        
        # Load SAQ prompt template
        prompt_template_path = Path(__file__).parent.parent / "data" / "prompts" / "saq_generation.txt"
        if prompt_template_path.exists():
            with open(prompt_template_path, 'r') as f:
                prompt_template = f.read()
            prompt = prompt_template.format(
                topic_name=topic.label,
                num_questions=num_questions,
                difficulty=difficulty,
                confidence=0.5  # Default; could be fetched from DB
            )
            prompt += f"\n\nAdditional Context:\n{context}"
        else:
            # Fallback inline prompt
            prompt = f"""Generate {num_questions} Short Answer Questions (SAQs) about {topic.label}.
Difficulty: {difficulty}

{context}

Each question must include:
- The question text with marks shown e.g. "(5 marks)"
- A "marks" field (integer)
- A "key_points" array (one string per mark)
- A "model_answer" string
- An "explanation" string

Return ONLY a JSON array."""
        
        # Generate via LLM
        try:
            response = await self.llm_service.complete(
                messages=[
                    {"role": "system", "content": "You are a UK medical education expert creating SAQ exam questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
        except Exception as e:
            print(f"SAQ generation failed: {e}")
            return []
        
        # Parse JSON response
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                questions = json.loads(response[json_start:json_end])
            else:
                raise ValueError("No JSON array found")
            
            # Add metadata
            for q in questions:
                q['topic_id'] = topic_id
                q['difficulty'] = difficulty
                q['question_type'] = 'saq'
                q['timestamp'] = datetime.utcnow().isoformat()
            
            return questions
        except (json.JSONDecodeError, ValueError) as e:
            print(f"SAQ JSON parsing failed: {e}. Response: {response[:200]}")
            return []
    
    async def evaluate_saq_answer(
        self,
        question: str,
        model_answer: str,
        key_points: List[str],
        student_answer: str,
        topic_id: str,
        difficulty: str,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Evaluate a student's SAQ answer using LLM-based marking.
        
        Returns structured marking result with points-based scoring.
        """
        total_marks = len(key_points)
        
        # Format key points for the prompt
        key_points_formatted = "\n".join(
            f"{i+1}. {kp}" for i, kp in enumerate(key_points)
        )
        
        # Load marking prompt template
        prompt_template_path = Path(__file__).parent.parent / "data" / "prompts" / "saq_marking.txt"
        if prompt_template_path.exists():
            with open(prompt_template_path, 'r') as f:
                prompt_template = f.read()
            marking_prompt = prompt_template.format(
                question=question,
                total_marks=total_marks,
                key_points_formatted=key_points_formatted,
                model_answer=model_answer,
                student_answer=student_answer
            )
        else:
            # Fallback inline prompt
            marking_prompt = f"""Mark this SAQ answer.

Question: {question}
Total Marks: {total_marks}
Key Points (1 mark each):
{key_points_formatted}

Model Answer: {model_answer}

Student's Answer: {student_answer}

Return a JSON object with: score, max_score, percentage, key_points_assessment (array of {{key_point, awarded, student_evidence}}), feedback, areas_to_review."""
        
        # Get LLM marking
        try:
            response = await self.llm_service.complete(
                messages=[
                    {"role": "system", "content": "You are a strict but fair medical examiner. Mark SAQ answers objectively against the key points provided."},
                    {"role": "user", "content": marking_prompt}
                ],
                temperature=0.3,  # Low temperature for consistent marking
                max_tokens=2000
            )
        except Exception as e:
            print(f"SAQ marking failed: {e}")
            # Return a safe fallback
            return {
                'score': 0,
                'max_score': total_marks,
                'percentage': 0.0,
                'key_points_assessment': [
                    {'key_point': kp, 'awarded': False, 'student_evidence': 'Marking failed'}
                    for kp in key_points
                ],
                'feedback': 'Automated marking failed. Please review your answer against the model answer.',
                'areas_to_review': [],
                'model_answer': model_answer,
                'error': str(e)
            }
        
        # Parse marking result
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(response[json_start:json_end])
            else:
                raise ValueError("No JSON object found in marking response")
            
            # Ensure required fields
            score = result.get('score', 0)
            max_score = result.get('max_score', total_marks)
            
            # Validate score bounds
            score = max(0, min(score, max_score))
            
            result['score'] = score
            result['max_score'] = max_score
            result['percentage'] = round((score / max_score) * 100, 1) if max_score > 0 else 0.0
            result['model_answer'] = model_answer
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"SAQ marking JSON parsing failed: {e}")
            result = {
                'score': 0,
                'max_score': total_marks,
                'percentage': 0.0,
                'key_points_assessment': [],
                'feedback': f'Could not parse marking result. Model answer: {model_answer}',
                'areas_to_review': [],
                'model_answer': model_answer
            }
        
        # Update confidence based on SAQ score (proportional to SBA)
        # Map SAQ percentage to confidence adjustment
        score_ratio = result['score'] / result['max_score'] if result['max_score'] > 0 else 0
        
        # Save result to database
        quiz_result = QuizResult(
            topic_id=topic_id,
            question=question,
            correct_answer=model_answer[:500],  # Truncate for DB storage
            user_answer=student_answer[:500],
            is_correct=(score_ratio >= 0.5),  # "Correct" if ≥50% marks
            difficulty=difficulty,
            timestamp=datetime.utcnow()
        )
        db.add(quiz_result)
        
        # Update topic confidence proportionally
        await self._update_confidence_from_saq(topic_id, score_ratio, difficulty, db)
        
        await db.commit()
        
        return result
    
    async def _update_confidence_from_saq(
        self,
        topic_id: str,
        score_ratio: float,  # 0.0 to 1.0
        difficulty: str,
        db: AsyncSession
    ) -> float:
        """Update topic confidence based on SAQ score ratio."""
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
        
        # Difficulty weights (same as SBA)
        difficulty_weights = {
            'easy': 0.05,
            'medium': 0.1,
            'hard': 0.15
        }
        weight = difficulty_weights.get(difficulty, 0.1)
        
        # SAQ scoring is proportional: full marks = full positive adjustment
        # Zero marks = full negative adjustment
        # Partial marks = proportional
        if score_ratio >= 0.5:
            # Positive adjustment scaled by how well they did above 50%
            positive_factor = (score_ratio - 0.5) * 2  # Maps 0.5-1.0 to 0.0-1.0
            adjustment = weight * (1 - progress.confidence) * positive_factor
            progress.confidence = min(1.0, progress.confidence + adjustment)
        else:
            # Negative adjustment scaled by how poorly they did below 50%
            negative_factor = (0.5 - score_ratio) * 2  # Maps 0.0-0.5 to 1.0-0.0
            adjustment = weight * progress.confidence * negative_factor
            progress.confidence = max(0.0, progress.confidence - adjustment)
        
        # Update quiz stats
        progress.quiz_attempts += 1
        if score_ratio >= 0.5:
            progress.quiz_correct += 1
        
        progress.updated_at = datetime.utcnow()
        
        return progress.confidence
