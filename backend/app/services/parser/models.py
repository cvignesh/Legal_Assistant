"""
Pydantic models for Legal Document Chunking
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class ParsingMode(str, Enum):
    """Parsing mode for different types of legal documents"""
    NARRATIVE = "NARRATIVE"   # Illustrations/Explanations attached to sections
    STRICT = "STRICT"         # Provisos attached to sections
    SCHEDULE = "SCHEDULE"     # Row-by-row table parsing


class ChunkType(str, Enum):
    """Type of chunk extracted from document"""
    SECTION = "Section"
    DEFINITION = "Definition"
    SCHEDULE_ENTRY = "Schedule_Entry"
    CHAPTER_HEADER = "Chapter_Header"


class ChunkMetadata(BaseModel):
    """Metadata for a legal chunk"""
    act_name: str = Field(..., description="Full name of the Act")
    act_short: str = Field(..., description="Short name/abbreviation (e.g., BNS, BNSS)")
    chapter: Optional[str] = Field(None, description="Parent chapter name")
    section_id: str = Field(..., description="Section number (e.g., 103, 3A)")
    section_title: Optional[str] = Field(None, description="Section title if available")
    chunk_type: ChunkType = Field(default=ChunkType.SECTION)
    has_illustration: bool = Field(default=False)
    has_explanation: bool = Field(default=False)
    has_proviso: bool = Field(default=False)
    page_start: Optional[int] = Field(None, description="Starting page number (1-indexed)")
    page_end: Optional[int] = Field(None, description="Ending page number (1-indexed)")


class LegalChunk(BaseModel):
    """A single chunk from a legal document"""
    chunk_id: str = Field(..., description="Unique ID (e.g., BNS_Sec_103)")
    text_for_embedding: str = Field(..., description="Enriched text with context for embedding")
    raw_content: str = Field(..., description="Original section text as extracted")
    metadata: ChunkMetadata


class DocumentResult(BaseModel):
    """Result of parsing a single document"""
    filename: str
    act_name: str
    act_short: str
    parsing_mode: ParsingMode
    total_pages: int
    total_chunks: int
    chunks: List[LegalChunk]
    errors: List[str] = Field(default_factory=list)
