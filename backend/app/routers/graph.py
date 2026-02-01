"""
Graph Router
Knowledge graph and curriculum endpoints.
"""
from fastapi import APIRouter, Request, HTTPException
from app.models.api_models import TopicNode, GraphResponse, ConfidenceUpdate
from app.models.graph_models import TopicDetails, GraphStatistics

router = APIRouter()


@router.get("/", response_model=GraphResponse)
async def get_graph(request: Request):
    """Get the complete knowledge graph with user progress."""
    graph_service = request.app.state.graph
    
    graph_data = await graph_service.get_graph_with_progress()
    
    return GraphResponse(
        nodes=graph_data["nodes"],
        edges=graph_data["edges"],
        statistics=graph_data["statistics"]
    )


@router.get("/topic/{topic_id}", response_model=TopicDetails)
async def get_topic_details(request: Request, topic_id: str):
    """Get detailed information about a topic."""
    graph_service = request.app.state.graph
    
    details = await graph_service.get_topic_details(topic_id)
    
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
async def get_statistics(request: Request):
    """Get knowledge graph statistics."""
    graph_service = request.app.state.graph
    
    stats = await graph_service.get_statistics()
    return stats


@router.get("/weak-topics")
async def get_weak_topics(request: Request, threshold: float = 0.3):
    """Get topics with low confidence."""
    graph_service = request.app.state.graph
    
    weak_topics = await graph_service.get_weak_topics(threshold)
    return {"topics": weak_topics}


@router.get("/prerequisites/{topic_id}")
async def get_prerequisites(request: Request, topic_id: str):
    """Get prerequisite topics for a given topic."""
    graph_service = request.app.state.graph
    
    prerequisites = await graph_service.get_prerequisites(topic_id)
    return {"prerequisites": prerequisites}


@router.get("/dependents/{topic_id}")
async def get_dependents(request: Request, topic_id: str):
    """Get topics that depend on this topic."""
    graph_service = request.app.state.graph
    
    dependents = await graph_service.get_dependents(topic_id)
    return {"dependents": dependents}
