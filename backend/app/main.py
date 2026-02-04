"""
Aetios-Med Backend - FastAPI Application Factory
"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import chat, graph, ingest, quiz, study, system
from app.services.llm_service import LLMService
from app.services.graph_service import GraphService
from app.services.vector_service import VectorService
from app.services.ingest_service import IngestService
from app.services.quiz_service import QuizService
from app.services.retention_service import RetentionService
from app.services.study_plan_service import StudyPlanService
from app.services.encryption_service import EncryptionService
from app.models.database import init_database
from app.agent import create_agent, init_tools


# Global service instances
llm_service: LLMService = None
graph_service: GraphService = None
vector_service: VectorService = None
ingest_service: IngestService = None
quiz_service: QuizService = None
retention_service: RetentionService = None
study_plan_service: StudyPlanService = None
encryption_service: EncryptionService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Initializes services on startup, cleans up on shutdown.
    """
    global llm_service, graph_service, vector_service
    global ingest_service, quiz_service, retention_service, study_plan_service, encryption_service
    
    # Initialize database
    await init_database(settings.database_path)
    
    # Initialize graph service (loads curriculum)
    graph_service = GraphService(
        curriculum_path=settings.curriculum_path
    )
    graph_service.load_curriculum()
    
    # Initialize vector store
    vector_service = VectorService(
        db_path=settings.lancedb_path,
        embedding_model=settings.embedding_model
    )
    vector_service.initialize()
    
    # Initialize LLM (may not be downloaded yet)
    llm_service = LLMService(
        model_path=settings.model_path,
        n_ctx=settings.context_length,
        n_gpu_layers=settings.gpu_layers
    )
    
    # Only load if model exists
    if settings.model_path.exists():
        await llm_service.load_model()
    
    # Initialize retention service
    retention_service = RetentionService()
    
    # Initialize study plan service
    study_plan_service = StudyPlanService(
        graph_service=graph_service,
        retention_service=retention_service
    )
    
    # Initialize quiz service
    quiz_service = QuizService(
        llm_service=llm_service,
        graph_service=graph_service,
        vector_service=vector_service
    )
    
    # Initialize ingest service
    ingest_service = IngestService(
        vector_service=vector_service,
        graph_service=graph_service
    )
    
    # Initialize encryption service
    encryption_service = EncryptionService()
    
    # Initialize agent tools with services
    init_tools({
        'graph_service': graph_service,
        'vector_service': vector_service,
        'retention_service': retention_service,
        'quiz_service': quiz_service,
        'study_plan_service': study_plan_service
    })
    
    # Create agent orchestrator
    agent = create_agent(llm_service=llm_service)
    
    # Make services available to routers
    app.state.llm = llm_service
    app.state.graph = graph_service
    app.state.vector = vector_service
    app.state.ingest = ingest_service
    app.state.quiz = quiz_service
    app.state.retention = retention_service
    app.state.study = study_plan_service
    app.state.encryption = encryption_service
    app.state.agent = agent
    
    yield
    
    # Cleanup
    if llm_service:
        await llm_service.unload()
    if vector_service:
        await vector_service.close()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Aetios-Med API",
        description="Backend for the Medical Study Assistant",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # CORS for Electron renderer
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "app://.", "file://"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routers
    app.include_router(system.router, prefix="/api/system", tags=["System"])
    app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
    app.include_router(graph.router, prefix="/api/graph", tags=["Knowledge Graph"])
    app.include_router(ingest.router, prefix="/api/ingest", tags=["Data Ingestion"])
    app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])
    app.include_router(study.router, prefix="/api/study", tags=["Study Planning"])
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=settings.port,
        reload=False
    )
