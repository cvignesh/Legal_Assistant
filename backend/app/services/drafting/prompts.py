FACT_EXTRACTION_PROMPT = """
You are an expert Legal Clerk. 
Task: Extract structured facts from the user's story for a legal petition.

User Story:
{user_story}

Instructions:
1. Extract a chronological list of events.
2. Identify the Complainant and Accused (if mentioned).
3. Extract specific details: Dates (as a single string), Amounts, Places.
4. Identify the core allegation (e.g., Cheating, Breach of Trust).

Output JSON format matching 'FactExtractionResult':
{{
    "chronology": ["Event 1", "Event 2"],
    "accused_details": "Name/Address or Unknown",
    "complainant_details": "Name/Address or User",
    "core_allegation": "Cheating u/s 420",
    "monetary_details": "Rs. 10 Lakhs",
    "place_of_occurence": "Delhi",
    "date_of_occurence": "1st Jan 2024 to 1st March 2024"
}}
"""

LEGAL_MAPPING_PROMPT = """
You are a legal expert. Given the extracted facts, identify applicable Indian laws.

**IMPORTANT**: Use the NEW criminal code:
- Use "BNS" (Bharatiya Nyaya Sanhita, 2023) instead of IPC
- BNS Section 318 = Old IPC Section 420 (Cheating)
- BNS Section 351 = Old IPC Section 506 (Criminal Intimidation)
- For civil matters, use the Negotiable Instruments Act, 1881 (Section 138 for cheque bounce)

Facts:
{facts_json}

Instructions:
1. Map facts to relevant BNS sections (NOT IPC).
2. For each section, provide reasoning.
3. Output ONLY a JSON array.

Output JSON format:
[
    {{
        "act": "BNS",
        "section": "318",
        "reasoning": "Cheating and dishonestly inducing delivery of property..."
    }},
    {{
        "act": "Negotiable Instruments Act, 1881",
        "section": "138",
        "reasoning": "Dishonour of cheque for insufficiency of funds..."
    }}
]
"""

SUBSTANTIVE_ANALYSIS_PROMPT = """
You are a Senior Criminal Laywer reviewing a junior's draft.
Your goal is to ensure the "Ingredients of the Offence" are fully met.

Case Context:
User Story: {user_story}
Identified Sections: {sections}

Standard Ingredients Required:
1. CHEATING (Sec 420 IPC / 318 BNS):
   - Deception at Inception (Fraudulent intention must exist at the very beginning).
   - Inducement (Victim must have done something they wouldn't have done otherwise).
   - Loss/Damage.
   *Crucial Check*: Distinguish from "Civil Breach of Contract". Mere failure to return money is NOT cheating. Must prove he never intended to return it.

2. CRIMINAL BREACH OF TRUST (Sec 406 IPC / 316 BNS):
   - Entrustment (Property given with a specific direction/contract).
   - Misappropriation (Used for own purpose vs the directed purpose).

3. CRIMINAL INTIMIDATION (Sec 506 IPC / 351 BNS):
   - Threat to person/reputation.
   - Intent to cause alarm.

Analyze the user story against these ingredients for the identified sections.
If an ingredient is WEAK or MISSING, generate a CLARIFYING QUESTION to help the user strengthen the petition.

Output JSON:
[
    {{
        "section": "BNS 318 (Cheating)",
        "missing_ingredient": "Deception at Inception",
        "question": "Did the accused provide any false documents, fake promises, or misrepresentation BEFORE you gave the money? (To prove it wasn't just a loan that went bad).",
        "strength_score": 4
    }}
]

If the case is strong (strength_score > 8), return an empty list or only minor suggestions.
"""
