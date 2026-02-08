from typing import List, Dict, Optional
from app.services.drafting.models import (
    FactExtractionResult, LegalIssue, DocumentType, 
    ProceduralAnalysis, RiskLevel, ValidatedCitation
)
import re

class ProceduralValidator:
    """
    Validates legal drafts against procedural rules and mandatory requirements.
    Addresses gaps like maintainability, mandatory components, and jurisdictional bars.
    """

    @staticmethod
    def validate(
        doc_type: DocumentType,
        facts: FactExtractionResult,
        issues: List[LegalIssue],
        citations: List[ValidatedCitation]
    ) -> ProceduralAnalysis:
        
        analysis = ProceduralAnalysis(
            risk_level=RiskLevel.LOW,
            issues=[],
            missing_mandatory_components=[],
            suggestions=[],
            score=100
        )

        # 1. Statutory Bars (The "Killer" Rules)
        _check_statutory_bars(doc_type, issues, analysis)

        # 2. Mandatory Components Check
        _check_mandatory_components(doc_type, facts, analysis)

        # 3. Citation Integrity Check
        _check_citation_integrity(citations, analysis)

        # 4. Risk Scoring
        _calculate_risk_score(analysis)

        return analysis

def _check_statutory_bars(doc_type: DocumentType, issues: List[LegalIssue], analysis: ProceduralAnalysis):
    """Check for legally barred combinations (e.g., 156(3) for NI Act)"""
    
    # RULE: 156(3) is barred for Section 138 NI Act cases (Priyanka Srivastava guidelines & general practice)
    # Courts insist on Section 200 Private Complaint for NI Act.
    if doc_type == DocumentType.MAGISTRATE_156_3:
        has_ni_act = any("NEGOTIABLE" in i.act.upper() or "138" in i.section for i in issues)
        if has_ni_act:
            analysis.issues.append("Statutory Bar: 156(3) Petition is generally not maintainable for Negotiable Instruments Act (Cheque Bounce) cases.")
            analysis.suggestions.append("Convert this to a Private Complaint under Section 200 CrPC.")
            analysis.risk_level = RiskLevel.CRITICAL

def _check_mandatory_components(doc_type: DocumentType, facts: FactExtractionResult, analysis: ProceduralAnalysis):
    """Check if extraction found mandatory procedural steps"""
    
    # Helper to scan chronology for keywords
    chronology_text = " ".join(facts.chronology).lower()
    
    if doc_type == DocumentType.MAGISTRATE_156_3:
        # RULE: Must have approached Police (154(1)) and SP (154(3))
        if "police" not in chronology_text and "station" not in chronology_text:
            analysis.missing_mandatory_components.append("Date of approaching Local Police (Section 154(1))")
            analysis.issues.append("Premature Filing: No record of approaching local police found.")
        
        if "superintendent" not in chronology_text and "dcp" not in chronology_text and "sp " not in chronology_text and "commissioner" not in chronology_text:
            analysis.missing_mandatory_components.append("Date of representation to SP/DCP (Section 154(3))")
            analysis.issues.append("Priyanka Srivastava Non-Compliance: No representation to Superior Officer detected.")

        # RULE: Affidavit is mandatory
        # (This is usually a document drafting requirement, not a fact check, but we can warn if not explicit)
        analysis.suggestions.append("Ensure a sworn Affidavit (per Priyanka Srivastava v. State of UP) accompanies this petition.")

    elif doc_type == DocumentType.LEGAL_NOTICE:
        # Check for Cheque return logic
        pass 

def _check_citation_integrity(citations: List[ValidatedCitation], analysis: ProceduralAnalysis):
    """Flag weak or unknown citations"""
    for citation in citations:
        if "Unknown Case" in citation.case_title or not citation.case_title:
            analysis.issues.append(f"Weak Citation: A cited case has no title ('{citation.case_title}'). Verify manually.")
            # We don't fail, but we warn.

def _calculate_risk_score(analysis: ProceduralAnalysis):
    """Derive score and final risk level"""
    base_score = 100
    
    if analysis.risk_level == RiskLevel.CRITICAL:
        base_score -= 50
    
    base_score -= (len(analysis.issues) * 10)
    base_score -= (len(analysis.missing_mandatory_components) * 15)
    
    if base_score < 0: base_score = 0
    analysis.score = base_score
    
    # Update RiskLevel if not Critical
    if analysis.risk_level != RiskLevel.CRITICAL:
        if base_score < 50:
            analysis.risk_level = RiskLevel.HIGH
        elif base_score < 80:
            analysis.risk_level = RiskLevel.MEDIUM
        else:
            analysis.risk_level = RiskLevel.LOW
