"""
Chat Router
Chat and conversation endpoints with the LLM agent.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.models.api_models import ChatRequest, ChatResponse, ChatMessage
from typing import AsyncIterable
import json

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(request: Request, chat_request: ChatRequest):
    """Send a message to the AI tutor."""
    llm_service = request.app.state.llm
    graph_service = request.app.state.graph
    vector_service = request.app.state.vector
    
    if not llm_service.is_loaded:
        raise HTTPException(status_code=503, detail="LLM model not loaded")
    
    # TODO: Implement agent orchestration with tool calling
    # For now, basic completion
    response_text = await llm_service.complete(
        messages=chat_request.messages,
        temperature=chat_request.temperature,
        max_tokens=chat_request.max_tokens
    )
    
    response_message = ChatMessage(
        role="assistant",
        content=response_text
    )
    
    return ChatResponse(
        message=response_message,
        finish_reason="stop"
    )


@router.post("/stream")
async def stream_message(request: Request, chat_request: ChatRequest):
    """Stream a chat response."""
    llm_service = request.app.state.llm
    
    if not llm_service.is_loaded:
        raise HTTPException(status_code=503, detail="LLM model not loaded")
    
    async def event_generator() -> AsyncIterable[str]:
        """Generate SSE events."""
        async for chunk in llm_service.stream_complete(
            messages=chat_request.messages,
            temperature=chat_request.temperature,
            max_tokens=chat_request.max_tokens
        ):
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/history")
async def get_chat_history(request: Request, limit: int = 50):
    """Get recent chat history."""
    # TODO: Query database for chat history
    return {"messages": []}


@router.delete("/history")
async def clear_chat_history(request: Request):
    """Clear chat history."""
    # TODO: Clear from database
    return {"status": "cleared"}
