"""
Graph Router
Knowledge graph and curriculum endpoints.
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Optional
from app.models.api_models import TopicNode, GraphResponse, ConfidenceUpdate, CurriculumSelection
from app.models.graph_models import TopicDetails, GraphStatistics
from app.models.database import get_session
import json

router = APIRouter()


@router.get("/", response_model=GraphResponse)
async def get_graph(request: Request, curriculum: Optional[str] = None):
    """Get the complete knowledge graph with user progress."""
    graph_service = request.app.state.graph
    
    # Check for active semester scope and pass scoped topics to graph service
    semester_service = request.app.state.semester if hasattr(request.app.state, 'semester') else None
    scoped_topic_ids = None
    
    async with get_session() as db:
        # Check for active semester scope if semester service is available
        if semester_service:
            active_scope = await semester_service.get_active_scope(db)
            if active_scope:
                scoped_topic_ids = set(json.loads(active_scope.topic_ids))
        
        # Get graph data with scoped topics in the same session
        graph_data = await graph_service.get_graph_with_progress(
            db,
            scoped_topic_ids=scoped_topic_ids,
            curriculum_key=curriculum
        )
    
    # Convert to response format
    nodes = [
        TopicNode(
            id=node.id,
            label=node.label,
            type=node.type,
            confidence=node.confidence,
            in_scope=node.in_scope
        )
        for node in graph_data.nodes
    ]
    
    edges = [
        {"source": edge.source, "target": edge.target, "type": edge.type}
        for edge in graph_data.edges
    ]
    
    return GraphResponse(
        nodes=nodes,
        edges=edges,
        statistics=graph_data.metadata
    )


@router.get("/topic/{topic_id}", response_model=TopicDetails)
async def get_topic_details(request: Request, topic_id: str, curriculum: Optional[str] = None):
    """Get detailed information about a topic."""
    graph_service = request.app.state.graph
    
    async with get_session() as db:
        details = await graph_service.get_topic_details(topic_id, db, curriculum_key=curriculum)
    
    if not details:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return details


@router.post("/confidence")
async def update_confidence(request: Request, update: ConfidenceUpdate):
    """Update confidence level for a topic."""
    graph_service = request.app.state.graph
    
    success = await graph_service.update_confidence(
        topic_id=update.topic_id,
        confidence=update.confidence,
        notes=update.notes
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return {"status": "updated"}


@router.get("/statistics", response_model=GraphStatistics)
async def get_statistics(request: Request, curriculum: Optional[str] = None):
    """Get knowledge graph statistics."""
    graph_service = request.app.state.graph
    
    async with get_session() as db:
        stats = await graph_service.get_statistics(db, curriculum_key=curriculum)
    return stats


@router.get("/weak-topics")
async def get_weak_topics(
    request: Request,
    threshold: float = 0.3,
    curriculum: Optional[str] = None
):
    """Get topics with low confidence."""
    graph_service = request.app.state.graph
    
    async with get_session() as db:
        weak_topics = await graph_service.get_weak_topics(db, threshold, curriculum_key=curriculum)
    return {"topics": weak_topics}


@router.get("/prerequisites/{topic_id}")
async def get_prerequisites(request: Request, topic_id: str, curriculum: Optional[str] = None):
    """Get prerequisite topics for a given topic."""
    graph_service = request.app.state.graph
    
    prerequisites = await graph_service.get_prerequisites(topic_id, curriculum_key=curriculum)
    return {"prerequisites": prerequisites}


@router.get("/dependents/{topic_id}")
async def get_dependents(request: Request, topic_id: str, curriculum: Optional[str] = None):
    """Get topics that depend on this topic."""
    graph_service = request.app.state.graph
    
    dependents = await graph_service.get_dependents(topic_id, curriculum_key=curriculum)
    return {"dependents": dependents}


@router.get("/curricula")
async def list_curricula(request: Request):
    """List available curricula and the active selection."""
    graph_service = request.app.state.graph
    return {
        "active": graph_service.active_curriculum_key,
        "available": graph_service.get_available_curricula()
    }


@router.post("/active-curriculum")
async def set_active_curriculum(request: Request, selection: CurriculumSelection):
    """Set the active curriculum used for graph-dependent services."""
    graph_service = request.app.state.graph

    try:
        graph_service.set_active_curriculum(selection.curriculum)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Unknown curriculum")

    return {"active": graph_service.active_curriculum_key}


@router.get("/decaying-topics")
async def get_decaying_topics(request: Request, days: int = 7):
    """Get topics that need review based on spaced repetition (not reviewed in X days)."""
    from app.models.database import TopicProgress
    from sqlalchemy import select
    from datetime import datetime, timedelta
    
    try:
        async with get_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            result = await db.execute(
                select(TopicProgress)
                .where(TopicProgress.last_studied < cutoff_date)
                .order_by(TopicProgress.last_studied.asc())
                .limit(20)
            )
            decaying_topics = result.scalars().all()
            
            return {
                "topics": [
                    {
                        "topic_id": t.topic_id,
                        "confidence": t.confidence,
                        "last_studied": t.last_studied.isoformat() if t.last_studied else None,
                        "days_since_review": (datetime.utcnow() - t.last_studied).days if t.last_studied else None,
                        "times_reviewed": t.times_reviewed
                    }
                    for t in decaying_topics
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get decaying topics: {str(e)}")


@router.get("/search-notes")
async def search_notes(request: Request, query: str, limit: int = 5):
    """Search through student notes and annotations."""
    from app.models.database import Note
    from sqlalchemy import select, or_
    
    try:
        async with get_session() as db:
            # Search in title and content
            search_pattern = f"%{query}%"
            result = await db.execute(
                select(Note)
                .where(
                    or_(
                        Note.title.ilike(search_pattern),
                        Note.content.ilike(search_pattern)
                    )
                )
                .limit(limit)
            )
            notes = result.scalars().all()
            
            return {
                "notes": [
                    {
                        "id": note.id,
                        "topic_id": note.topic_id,
                        "title": note.title,
                        "content": note.content[:200] + "..." if len(note.content) > 200 else note.content,
                        "created_at": note.created_at.isoformat() if note.created_at else None
                    }
                    for note in notes
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search notes: {str(e)}")

