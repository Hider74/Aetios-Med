"""
Study Plan Service
Generate personalized study plans based on weak areas and exam dates.
"""
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from icalendar import Calendar, Event, vText

from ..models.database import TopicProgress, Exam, StudyPlan
from .graph_service import GraphService
from .retention_service import RetentionService


class StudyPlanService:
    """Service for generating and managing study plans."""
    
    def __init__(
        self,
        graph_service: GraphService,
        retention_service: RetentionService
    ):
        self.graph_service = graph_service
        self.retention_service = retention_service
    
    async def generate_study_plan(
        self,
        exam_id: Optional[int],
        start_date: datetime,
        end_date: datetime,
        hours_per_day: float,
        db: AsyncSession,
        focus_weak_areas: bool = True
    ) -> int:
        """
        Generate a personalized study plan.
        
        Args:
            exam_id: Optional exam to prepare for
            start_date: Plan start date
            end_date: Plan end date
            hours_per_day: Available study hours per day
            db: Database session
            focus_weak_areas: Prioritize weak topics
        
        Returns:
            Study plan ID
        """
        if not self.graph_service.is_loaded:
            self.graph_service.load_curriculum()
        
        # Get exam topics if specified
        exam_topics = set()
        exam_name = "General Study Plan"
        
        if exam_id:
            result = await db.execute(
                select(Exam).where(Exam.id == exam_id)
            )
            exam = result.scalar_one_or_none()
            if exam:
                exam_name = exam.name
                exam_topics = set(json.loads(exam.topics))
        
        # Get all topic progress
        result = await db.execute(select(TopicProgress))
        progress_map = {p.topic_id: p for p in result.scalars().all()}
        
        # Get decaying topics (need review)
        decaying = await self.retention_service.get_decaying_topics(db, threshold=0.8, limit=50)
        decaying_ids = {t['topic_id'] for t in decaying}
        
        # Score and prioritize topics
        topic_priorities = []
        
        for topic in self.graph_service.topics.values():
            progress = progress_map.get(topic.id)
            
            # Calculate priority score
            score = 0.0
            
            # Confidence-based scoring
            if progress:
                confidence = progress.confidence
                if focus_weak_areas:
                    # Prioritize low confidence topics
                    score += (1.0 - confidence) * 100
                else:
                    # Balanced approach
                    score += (1.0 - confidence) * 50
            else:
                # Never studied
                score += 80
            
            # Exam relevance
            if exam_topics and topic.id in exam_topics:
                score += 50 * topic.exam_weight
            else:
                score += 10 * topic.exam_weight
            
            # Decaying retention
            if topic.id in decaying_ids:
                score += 40
            
            # Prerequisites (learn foundation first)
            if not topic.prerequisites:
                score += 20
            elif all(
                (prog := progress_map.get(prereq)) and prog.confidence > 0.7
                for prereq in topic.prerequisites
            ):
                score += 10
            
            topic_priorities.append({
                'topic_id': topic.id,
                'topic_label': topic.label,
                'topic_type': topic.type,
                'priority_score': score,
                'current_confidence': progress.confidence if progress else 0.0,
                'exam_weight': topic.exam_weight
            })
        
        # Sort by priority
        topic_priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Generate daily schedule
        total_days = (end_date - start_date).days + 1
        minutes_per_day = int(hours_per_day * 60)
        
        daily_schedule = []
        topic_index = 0
        
        for day_num in range(total_days):
            day_date = start_date + timedelta(days=day_num)
            
            # Skip weekends if exam is far away
            if exam_id and day_date.weekday() in [5, 6]:  # Saturday, Sunday
                days_until_exam = (end_date - day_date).days
                if days_until_exam > 14:
                    continue
            
            day_topics = []
            remaining_minutes = minutes_per_day
            
            while remaining_minutes > 0 and topic_index < len(topic_priorities):
                topic_info = topic_priorities[topic_index]
                
                # Allocate time based on priority and confidence
                base_time = 30
                if topic_info['current_confidence'] < 0.3:
                    time_needed = 60  # Low confidence needs more time
                elif topic_info['current_confidence'] < 0.7:
                    time_needed = 45
                else:
                    time_needed = 30  # Quick review
                
                time_allocated = min(time_needed, remaining_minutes)
                
                day_topics.append({
                    'topic_id': topic_info['topic_id'],
                    'topic_label': topic_info['topic_label'],
                    'duration_minutes': time_allocated,
                    'activity': self._suggest_activity(topic_info['current_confidence'])
                })
                
                remaining_minutes -= time_allocated
                
                # Move to next topic if this one is fully scheduled
                if time_allocated >= time_needed:
                    topic_index += 1
            
            if day_topics:
                daily_schedule.append({
                    'date': day_date.isoformat(),
                    'day_of_week': day_date.strftime('%A'),
                    'topics': day_topics,
                    'total_minutes': minutes_per_day - remaining_minutes
                })
        
        # Create plan in database
        plan_data = {
            'daily_schedule': daily_schedule,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'hours_per_day': hours_per_day,
                'total_topics': topic_index,
                'focus_weak_areas': focus_weak_areas
            }
        }
        
        study_plan = StudyPlan(
            name=exam_name,
            start_date=start_date,
            end_date=end_date,
            plan_data=json.dumps(plan_data),
            exam_id=exam_id,
            is_active=True
        )
        
        db.add(study_plan)
        await db.commit()
        await db.refresh(study_plan)
        
        return study_plan.id
    
    def _suggest_activity(self, confidence: float) -> str:
        """Suggest study activity based on confidence level."""
        if confidence < 0.3:
            return "Learn basics + flashcards + quiz"
        elif confidence < 0.7:
            return "Review + practice questions"
        else:
            return "Quick review + advanced quiz"
    
    async def get_study_plan(
        self,
        plan_id: int,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get a study plan by ID."""
        result = await db.execute(
            select(StudyPlan).where(StudyPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None
        
        plan_data = json.loads(plan.plan_data)
        
        return {
            'id': plan.id,
            'name': plan.name,
            'start_date': plan.start_date.isoformat(),
            'end_date': plan.end_date.isoformat(),
            'is_active': plan.is_active,
            'created_at': plan.created_at.isoformat(),
            'daily_schedule': plan_data.get('daily_schedule', []),
            'metadata': plan_data.get('metadata', {})
        }
    
    async def export_to_ics(
        self,
        plan_id: int,
        db: AsyncSession
    ) -> Optional[str]:
        """
        Export study plan to ICS calendar format.
        
        Returns:
            ICS file content as string
        """
        plan_dict = await self.get_study_plan(plan_id, db)
        
        if not plan_dict:
            return None
        
        # Create calendar
        cal = Calendar()
        cal.add('prodid', '-//Aetios-Med Study Planner//mxm.dk//')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'PUBLISH')
        cal.add('x-wr-calname', vText(f"Aetios: {plan_dict['name']}"))
        cal.add('x-wr-timezone', 'UTC')
        
        # Add events for each day
        for day in plan_dict['daily_schedule']:
            day_date = datetime.fromisoformat(day['date'])
            
            # Create one event per topic
            start_time = day_date.replace(hour=9, minute=0)  # Default start at 9 AM
            
            for topic_info in day['topics']:
                event = Event()
                
                # Set event properties
                event.add('summary', f"Study: {topic_info['topic_label']}")
                event.add('dtstart', start_time)
                
                duration = timedelta(minutes=topic_info['duration_minutes'])
                event.add('dtend', start_time + duration)
                
                event.add('description', 
                    f"Activity: {topic_info['activity']}\n"
                    f"Duration: {topic_info['duration_minutes']} minutes\n"
                    f"Topic ID: {topic_info['topic_id']}"
                )
                
                event.add('location', 'Study Session')
                event.add('status', 'CONFIRMED')
                
                # Add alarm (15 minutes before)
                from icalendar import Alarm
                alarm = Alarm()
                alarm.add('action', 'DISPLAY')
                alarm.add('trigger', timedelta(minutes=-15))
                alarm.add('description', f"Study session starting: {topic_info['topic_label']}")
                event.add_component(alarm)
                
                cal.add_component(event)
                
                # Move start time forward
                start_time += duration
        
        return cal.to_ical().decode('utf-8')
    
    async def get_today_plan(
        self,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get today's study plan items from active plan."""
        # Get active plan
        result = await db.execute(
            select(StudyPlan)
            .where(StudyPlan.is_active == True)
            .order_by(StudyPlan.created_at.desc())
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return None
        
        plan_data = json.loads(plan.plan_data)
        today_str = datetime.utcnow().date().isoformat()
        
        # Find today's schedule
        today_schedule = None
        for day in plan_data.get('daily_schedule', []):
            if day['date'].startswith(today_str):
                today_schedule = day
                break
        
        if not today_schedule:
            return None
        
        return {
            'plan_id': plan.id,
            'plan_name': plan.name,
            'date': today_schedule['date'],
            'day_of_week': today_schedule['day_of_week'],
            'topics': today_schedule['topics'],
            'total_minutes': today_schedule['total_minutes']
        }
    
    async def mark_topic_completed(
        self,
        plan_id: int,
        date: str,
        topic_id: str,
        db: AsyncSession
    ) -> bool:
        """Mark a topic as completed in the study plan."""
        result = await db.execute(
            select(StudyPlan).where(StudyPlan.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            return False
        
        plan_data = json.loads(plan.plan_data)
        
        # Find the day and topic
        for day in plan_data.get('daily_schedule', []):
            if day['date'] == date:
                for topic in day['topics']:
                    if topic['topic_id'] == topic_id:
                        topic['completed'] = True
                        topic['completed_at'] = datetime.utcnow().isoformat()
        
        # Update plan
        plan.plan_data = json.dumps(plan_data)
        await db.commit()
        
        return True
    
    async def get_plan_progress(
        self,
        plan_id: int,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """Get progress statistics for a study plan."""
        plan_dict = await self.get_study_plan(plan_id, db)
        
        if not plan_dict:
            return None
        
        total_topics = 0
        completed_topics = 0
        total_minutes = 0
        completed_minutes = 0
        
        for day in plan_dict['daily_schedule']:
            for topic in day['topics']:
                total_topics += 1
                total_minutes += topic['duration_minutes']
                
                if topic.get('completed', False):
                    completed_topics += 1
                    completed_minutes += topic['duration_minutes']
        
        return {
            'plan_id': plan_id,
            'total_topics': total_topics,
            'completed_topics': completed_topics,
            'completion_percentage': (completed_topics / total_topics * 100) if total_topics > 0 else 0,
            'total_minutes': total_minutes,
            'completed_minutes': completed_minutes,
            'remaining_minutes': total_minutes - completed_minutes
        }
