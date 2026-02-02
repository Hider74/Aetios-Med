"""
Chat Router
Chat and conversation endpoints with the LLM agent.
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from app.models.api_models import ChatRequest, ChatResponse, ChatMessage
from app.models.database import get_session, ChatMessage as DBChatMessage
from sqlalchemy import select, delete
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
    
    # Store user message in database
    async with get_session() as db:
        if chat_request.messages:
            user_message = chat_request.messages[-1]
            if user_message.role == "user":
                db_user_message = DBChatMessage(
                    role=user_message.role,
                    content=user_message.content,
                    session_id="default"
                )
                db.add(db_user_message)
                await db.commit()
    
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
    
    # Store assistant response in database
    async with get_session() as db:
        db_assistant_message = DBChatMessage(
            role="assistant",
            content=response_text,
            session_id="default"
        )
        db.add(db_assistant_message)
        await db.commit()
    
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
async def get_chat_history(request: Request, limit: int = 50, session_id: str = "default"):
    """Get recent chat history."""
    try:
        async with get_session() as db:
            result = await db.execute(
                select(DBChatMessage)
                .where(DBChatMessage.session_id == session_id)
                .order_by(DBChatMessage.timestamp.asc())
                .limit(limit)
            )
            messages = result.scalars().all()
            
            return {
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat()
                    }
                    for msg in messages
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch chat history: {str(e)}")


@router.delete("/history")
async def clear_chat_history(request: Request, session_id: str = "default"):
    """Clear chat history."""
    try:
        async with get_session() as db:
            await db.execute(
                delete(DBChatMessage).where(DBChatMessage.session_id == session_id)
            )
            await db.commit()
            
            return {"status": "cleared", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")
