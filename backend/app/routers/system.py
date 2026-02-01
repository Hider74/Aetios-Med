"""
System Router
Health checks and system status endpoints.
"""
from fastapi import APIRouter, Request
from datetime import datetime
from app.models.api_models import HealthResponse, ModelStatus

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Health check endpoint."""
    llm_service = request.app.state.llm
    graph_service = request.app.state.graph
    vector_service = request.app.state.vector
    
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        services={
            "llm": llm_service.is_loaded if llm_service else False,
            "graph": graph_service.is_loaded if graph_service else False,
            "vector": vector_service.is_initialized if vector_service else False,
        }
    )


@router.get("/model-status", response_model=ModelStatus)
async def model_status(request: Request):
    """Get LLM model status."""
    llm_service = request.app.state.llm
    
    if not llm_service:
        return ModelStatus(
            is_loaded=False,
            context_length=0,
            gpu_layers=0
        )
    
    return ModelStatus(
        is_loaded=llm_service.is_loaded,
        model_path=str(llm_service.model_path) if llm_service.model_path else None,
        context_length=llm_service.n_ctx,
        gpu_layers=llm_service.n_gpu_layers
    )


@router.post("/load-model")
async def load_model(request: Request):
    """Load the LLM model."""
    llm_service = request.app.state.llm
    
    if llm_service.is_loaded:
        return {"status": "already_loaded"}
    
    await llm_service.load_model()
    return {"status": "loaded"}


@router.post("/unload-model")
async def unload_model(request: Request):
    """Unload the LLM model to free memory."""
    llm_service = request.app.state.llm
    
    await llm_service.unload()
    return {"status": "unloaded"}
