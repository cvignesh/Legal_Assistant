from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class DocumentType(str, Enum):
    POLICE_COMPLAINT = "police_complaint"
    MAGISTRATE_156_3 = "magistrate_156_3"
    PRIVATE_COMPLAINT_200 = "private_complaint_200"
    LEGAL_NOTICE = "legal_notice"

class FactExtractionResult(BaseModel):
    """Output from Fact Engine (LLM)"""
    chronology: List[str] = Field(..., description="Chronological list of events")
    accused_details: Optional[str] = Field(None, description="Name and address of accused")
    complainant_details: Optional[str] = Field(None, description="Name and address of complainant")
    core_allegation: str = Field(..., description="Main grievance e.g. Cheating, Assault")
    monetary_details: Optional[str] = Field(None, description="Amounts involved if any")
    place_of_occurence: Optional[str] = Field(None, description="Where it happened")
    date_of_occurence: Optional[str] = Field(None, description="When it happened")

class LegalIssue(BaseModel):
    """Output from Legal Reasoning Engine (LLM)"""
    act: str = Field(..., description="e.g. IPC, CrPC, NI Act")
    section: str = Field(..., description="e.g. 420, 138")
    reasoning: str = Field(..., description="Why this section applies")
    section_title: str = Field(default="", description="Official title of the section")
    section_full_text: str = Field(default="", description="Complete section text including illustrations, explanations, provisos")
    punishment: str = Field(default="", description="Punishment or penalty details if available")
    is_validated: bool = Field(default=False, description="Whether this section was verified against the internal database")

class ValidatedCitation(BaseModel):
    """Strictly grounded citation from Vector DB"""
    case_title: str
    citation_source: str
    excerpt: str
    relevance_score: float
    relevance_explanation: str = Field(..., description="Why this precedent is relevant to the user's case")
    pdf_url: Optional[str] = None

class DraftingRequest(BaseModel):
    user_story: str
    document_type: DocumentType

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ProceduralAnalysis(BaseModel):
    risk_level: RiskLevel
    issues: List[str] = Field(default=[], description="List of detected procedural issues")
    missing_mandatory_components: List[str] = Field(default=[], description="Mandatory items missing from facts")
    suggestions: List[str] = Field(default=[], description="Actionable advice")
    score: int = Field(default=100, description="0-100 procedural health score")

class DraftingResponse(BaseModel):
    draft_text: str
    facts: FactExtractionResult
    legal_issues: List[LegalIssue]
    citations: List[ValidatedCitation]
    validation_warnings: List[str] = []
    procedural_analysis: Optional[ProceduralAnalysis] = None
    substantive_analysis: List['SubstantiveGap'] = []

class SubstantiveGap(BaseModel):
    section: str = Field(..., description="The legal section being analyzed (e.g. 'BNS 318')")
    missing_ingredient: str = Field(..., description="The specific legal ingredient that is weak or missing")
    question: str = Field(..., description="Clarifying question to ask the user")
    strength_score: int = Field(..., description="0-10 score of how well this ingredient is currently established")
