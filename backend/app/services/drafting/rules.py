from typing import Dict, Any, List

class DraftingRules:
    """
    Centralized Rule Engine for Petition Drafting.
    Defines what is allowed/disallowed for each document type.
    """
    
    RULES: Dict[str, Dict[str, Any]] = {
        "police_complaint": {
            "include_citations": False,
            "include_procedural_law": False,
            "tone": "informal_factual",
            "affidavit_required": False,
            "required_fields": ["chronology", "accused_details", "core_allegation"],
        },
        "magistrate_156_3": {
            "include_citations": True,
            "include_procedural_law": True,
            "tone": "judicial_formal",
            "affidavit_required": True,
            "required_fields": ["chronology", "legal_sections", "citations"],
        },
        "private_complaint_200": {
            "include_citations": True,
            "include_procedural_law": True,
            "tone": "judicial_formal",
            "affidavit_required": False, # List of witnesses instead
            "required_fields": ["chronology", "legal_sections", "witness_list"],
        },
        "legal_notice": {
            "include_citations": "optional", # Can include if strong
            "include_procedural_law": False,
            "tone": "assertive",
            "affidavit_required": False,
            "required_fields": ["chronology", "demand", "time_limit"],
        }
    }

    @staticmethod
    def get_rules(document_type: str) -> Dict[str, Any]:
        return DraftingRules.RULES.get(document_type, {})

    @staticmethod
    def should_include_citations(document_type: str) -> bool:
        val = DraftingRules.RULES.get(document_type, {}).get("include_citations", False)
        return val is True or val == "optional"
