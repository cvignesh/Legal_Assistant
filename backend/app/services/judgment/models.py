"""
Pydantic models for Judgment Processing
"""
from enum import Enum
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class SectionType(str, Enum):
    """Type of section in judgment"""
    FACT = "Fact"
    SUBMISSION_PETITIONER = "Submission_Petitioner"
    SUBMISSION_RESPONDENT = "Submission_Respondent"
    COURT_OBSERVATION = "Court_Observation"
    STATUTE_CITATION = "Statute_Citation"
    OPERATIVE_ORDER = "Operative_Order"
    OTHER = "Other"  # Catch-all for unknown sections


class PartyRole(str, Enum):
    """Role of party in the case"""
    PETITIONER = "Petitioner"
    RESPONDENT = "Respondent"
    COURT = "Court"
    WITNESS = "Witness"
    PROSECUTION = "Prosecution"
    COUNSEL = "Counsel"  # Lawyer/advocate arguments
    POLICE = "Police"  # Police/investigation submissions
    ADVOCATES = "Advocates"  # Multiple advocates (collective)
    ACCUSED = "Accused"  # Criminal defendant
    OTHER = "Other"  # Catch-all for unknown roles
    NONE = "None"


class Outcome(str, Enum):
    """Judgment outcome"""
    DISMISSED = "Dismissed"
    ALLOWED = "Allowed"
    ACQUITTED = "Acquitted"
    CONVICTED = "Convicted"
    DISPOSED = "Disposed"
    PARTLY_ALLOWED = "Partly Allowed"
    UNKNOWN = "Unknown"


class WinningParty(str, Enum):
    """Winning party in the case"""
    PETITIONER = "Petitioner"
    RESPONDENT = "Respondent"
    STATE = "State"
    UNKNOWN = "Unknown"
    NONE = "None"


class JudgmentMetadata(BaseModel):
    """Metadata for a judgment chunk"""
    parent_doc: str = Field(..., description="Source PDF filename")
    case_title: Optional[str] = Field(None, description="Full case title")
    court_name: Optional[str] = Field(None, description="Name of the court")
    case_number: Optional[str] = Field(None, description="Case number (e.g. HCP No 123/2019)")
    city: Optional[str] = Field(None, description="City where court is located")
    year_of_judgment: Optional[int] = Field(None, description="Year judgment was delivered")
    doc_url: Optional[str] = Field(None, description="URL to original document (e.g. Indian Kanoon)")
    outcome: str = Field(default="Unknown", description="Judgment outcome")
    winning_party: str = Field(default="None", description="Winning party")
    
    # Chunk-specific metadata
    section_type: str = Field(..., description="Type of content")
    party_role: str = Field(..., description="Associated party role")
    legal_topics: List[str] = Field(default_factory=list, description="Legal topics/concepts")
    original_context: Optional[str] = Field(None, description="Original paragraph context")


class JudgmentChunk(BaseModel):
    """A single atomic unit from a judgment"""
    chunk_id: str = Field(..., description="Unique ID")
    text_for_embedding: str = Field(..., description="Composite content (Metadata + Text) to embed and index")
    supporting_quote: str = Field(..., description="Exact quote from source validating this chunk")
    metadata: JudgmentMetadata


class JudgmentResult(BaseModel):
    """Result of parsing a judgment PDF"""
    filename: str
    case_title: Optional[str] = None
    court_name: Optional[str] = None
    city: Optional[str] = None
    year_of_judgment: Optional[int] = None
    outcome: str = "Unknown"
    winning_party: str = "None"
    total_chunks: int
    chunks: List[JudgmentChunk]
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
