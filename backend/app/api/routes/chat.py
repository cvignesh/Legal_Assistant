"""
Chat API Routes
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.services.chat.models import ChatRequest, ChatResponse
from app.services.chat.chat_service import chat_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a chat message and get a response with citations
    
    Uses LangChain ConversationalRetrievalChain with:
    - Hybrid search retrieval
    - Conversation memory (in-memory)
    - Citation extraction
    """
    try:
        response = await chat_service.chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.get("/chat/session")
async def create_session():
    """
    Create a new chat session
    
    Returns a unique session ID to use for subsequent messages
    """
    session_id = chat_service.create_session_id()
    return {"session_id": session_id}


@router.delete("/chat/session/{session_id}")
async def clear_session(session_id: str):
    """
    Clear conversation memory for a session
    
    Resets the conversation history
    """
    chat_service.clear_session(session_id)
    return {"message": "Session cleared", "session_id": session_id}
