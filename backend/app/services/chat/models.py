"""
Pydantic models for chat service
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessage(BaseModel):
    """A single chat message"""
    role: str = Field(..., description="user or assistant")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Citation(BaseModel):
    """Citation source for an answer"""
    chunk_id: str
    score: float
    text: str = Field(..., description="Excerpt from the source")
    source: str = Field(..., description="Source document name")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Request to send a chat message"""
    session_id: str = Field(..., description="Session ID for conversation continuity")
    message: str = Field(..., description="User's message")


class GroupedSource(BaseModel):
    """Grouped source combining multiple chunks from same document"""
    id: str
    title: str
    doc_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunks: List[Citation]


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    session_id: str
    answer: str
    citations: List[Citation]  # Kept for backward compatibility
    sources: List[GroupedSource] = Field(default_factory=list)
    processing_time_ms: float
