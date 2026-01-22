"""
Pydantic models for Judgment Processing
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from enum import Enum


class SectionType(str, Enum):
    """Type of section in judgment"""
    FACT = "Fact"
    SUBMISSION_PETITIONER = "Submission_Petitioner"
    SUBMISSION_RESPONDENT = "Submission_Respondent"
    COURT_OBSERVATION = "Court_Observation"
    STATUTE_CITATION = "Statute_Citation"
    OPERATIVE_ORDER = "Operative_Order"


class PartyRole(str, Enum):
    """Role of party in the case"""
    PETITIONER = "Petitioner"
    RESPONDENT = "Respondent"
    COURT = "Court"
    WITNESS = "Witness"
    PROSECUTION = "Prosecution"
    COUNSEL = "Counsel"  # Added for lawyer/advocate arguments
    NONE = "None"


class Outcome(str, Enum):
    """Judgment outcome"""
    DISMISSED = "Dismissed"
    ALLOWED = "Allowed"
    ACQUITTED = "Acquitted"
    CONVICTED = "Convicted"
    DISPOSED = "Disposed"
    UNKNOWN = "Unknown"


class WinningParty(str, Enum):
    """Winning party in the case"""
    PETITIONER = "Petitioner"
    RESPONDENT = "Respondent"
    STATE = "State"
    NONE = "None"


class JudgmentMetadata(BaseModel):
    """Metadata for a judgment chunk"""
    parent_doc: str = Field(..., description="Source PDF filename")
    case_title: Optional[str] = Field(None, description="Full case title")
    court_name: Optional[str] = Field(None, description="Name of the court")
    city: Optional[str] = Field(None, description="City where court is located")
    year_of_judgment: Optional[int] = Field(None, description="Year judgment was delivered")
    outcome: Outcome = Field(default=Outcome.UNKNOWN)
    winning_party: WinningParty = Field(default=WinningParty.NONE)
    
    # Chunk-specific metadata
    section_type: SectionType = Field(..., description="Type of content")
    party_role: PartyRole = Field(..., description="Associated party role")
    legal_topics: List[str] = Field(default_factory=list, description="Legal topics/concepts")
    original_context: Optional[str] = Field(None, description="Original paragraph context")


class JudgmentChunk(BaseModel):
    """A single atomic unit from a judgment"""
    chunk_id: str = Field(..., description="Unique ID")
    text_for_embedding: str = Field(..., description="Content to embed and index")
    supporting_quote: str = Field(..., description="Exact quote from source validating this chunk")
    metadata: JudgmentMetadata


class JudgmentResult(BaseModel):
    """Result of parsing a judgment PDF"""
    filename: str
    case_title: Optional[str] = None
    court_name: Optional[str] = None
    city: Optional[str] = None
    year_of_judgment: Optional[int] = None
    outcome: Outcome = Outcome.UNKNOWN
    winning_party: WinningParty = WinningParty.NONE
    total_chunks: int
    chunks: List[JudgmentChunk]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
