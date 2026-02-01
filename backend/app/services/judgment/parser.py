"""
Judgment Parser Service - Migrated from POC with Production Enhancements

This module handles PDF parsing of legal judgments using LLM-based atomization.
Key Features:
- PyMuPDF text extraction
- LLM-based atomic chunking (Groq llama-3.1-8b-instant)
- Anti-hallucination validation with fuzzy matching  (60% threshold)
- Garbage text filtering (corrupted Hindi/encoding issues)
- Global metadata extraction (outcome, court, year)

Processing Flow:
1. Extract text from PDF
2. Clean and sanitize text (remove URLs, fix line breaks)
3. Extract global metadata (first + last 3000 chars)
4. Split into paragraphs
5. Filter garbage and noise
6. Atomize each paragraph via LLM
7. Validate supporting quotes (anti-hallucination)
8. Create structured chunks with metadata
"""
import os
import re
import json
import asyncio
from typing import List, Dict, Any
from pathlib import Path
from difflib import SequenceMatcher
from app.services.parser.utils import extract_text_from_pdf, detect_document_type

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from app.core.config import settings
from app.services.judgment.models import (
    JudgmentChunk,
    JudgmentMetadata,
    JudgmentResult,
    SectionType,
    PartyRole,
    Outcome,
    WinningParty
)


# --- PROMPTS ---
GLOBAL_CONTEXT_PROMPT = """
You are a Legal Data Extractor.
Task: Analyze the text to extract global case details.
Output must be strictly valid JSON with these keys:
- "case_title": (String or null)
- "case_number": (String or null, e.g., "H.C.P.(MD) No.633 of 2019")
- "outcome": (One of: "Dismissed", "Allowed", "Acquitted", "Convicted", "Disposed", "Unknown")
- "winning_party": (One of: "Petitioner", "Respondent", "State", "None")
- "court_name": (Full name of the court, String or null)
- "city": (City where the court is located, String or null)
- "year_of_judgment": (Year when the judgment was delivered, Integer or null)
"""

ATOMIZATION_SYSTEM_PROMPT = """
You are a Strict Legal Data Extractor. 
Task: Break the provided paragraph into "Atomic Units" (standalone statements) based ONLY on the input text.

### CRITICAL GROUNDING RULES ###
1. **NO EXTERNAL KNOWLEDGE**: You are forbidden from using your internal knowledge of Law, Religion, or Case Precedents. 
   - If the text cites "Sura 2", DO NOT infer "Sura 4" or "Polygamy" unless explicitly written in the text.
   - If the text mentions a "Citation", do not guess what the counsel argued previously.
   
2. **VERBATIM PROOF**: For every atomic unit you create, you MUST extract the **Exact Substring** (Quote) from the input text that supports it. 
   - The `supporting_quote` must be an exact copy-paste from the source.
   - If you cannot find the exact words to support a claim, DO NOT create the chunk.

3. **PRONOUN RESOLUTION**: Replace pronouns (He/She/It) with names (e.g., "The Petitioner"), BUT ensure the identity is derived strictly from the immediate context.

4. **TABLES & STATISTICS**: If extracting data from a table, the `supporting_quote` MUST be the exact distinct cell value or contiguous row text found in the raw input. 
   - DO NOT construct sentences like 'The total was X' if the text only says 'Total | X'.
   - Just quote 'X' or 'Total'.

5. **PRESERVE DETAILS**: Your atomic `content` must be comprehensive. Do NOT summarize away specific details like Dates, Amounts, Names, or Conditions.
   - BAD: "The accused was found with contraband."
   - GOOD: "The accused was found with 500g of Heroin on 12th Jan 2023."

6. **GRANULARITY**: Split compound sentences into separate atomic units.
   - Input: "The court dismissed the petition and imposed a fine of Rs 5000."
   - Output Unit 1: "The court dismissed the petition."
   - Output Unit 2: "The court imposed a fine of Rs 5000."

7. **COMPLETE COVERAGE**: Do NOT omit any clause, condition, or side-note. Every meaningful distinct fact in the text must be represented by an atomic unit. If a sentence has 3 distinct facts, generate 3 atomic units.

### CLASSIFICATION RULES ###
- `section_type`: ["Fact", "Submission_Petitioner", "Submission_Respondent", "Court_Observation", "Statute_Citation", "Operative_Order"]
- `party_role`: ["Petitioner", "Respondent", "Court", "Witness", "Prosecution", "Counsel", "Police", "Advocates", "None"]
- `legal_topics`: List of 1-3 specific concepts (e.g., ["Delay in FIR"]).

### OUTPUT FORMAT ###
Return a strictly valid JSON LIST. Example:
[
  {
    "content": "The Petitioner argued that the FIR was delayed.",
    "supporting_quote": "argued that the FIR was lodged with a delay", 
    "section_type": "Submission_Petitioner",
    "party_role": "Petitioner",
    "legal_topics": ["Delay in FIR"]
  }
]
"""


class JudgmentParser:
    def __init__(self):
        """Initialize parser with LLM client based on provider"""
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "openai":
            print(f"   ⚙️ JudgmentParser using OpenAI model: {settings.LLM_MODEL}")
            self.llm = ChatOpenAI(
                api_key=settings.LLM_API_KEY,
                model=settings.LLM_MODEL,
                temperature=settings.GROQ_TEMPERATURE, # Use same low temp
                max_retries=2
            )
        elif provider == "groq":
            print(f"   ⚙️ JudgmentParser using Groq model: {settings.GROQ_MODEL}")
            self.llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL, # Use specialized ingestion model
                temperature=settings.GROQ_TEMPERATURE,
                max_retries=2
            )
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")    
    def extract_text_with_pymupdf(self, file_path: str) -> str:
        """Parses PDF using shared utility with OCR fallback."""
        try:
            pages = extract_text_from_pdf(file_path)
            # Combine text from all pages
            full_text = "\n".join([page_text for _, page_text in pages])
            return full_text
        except Exception as e:
            print(f"Error extracting text: {e}")
            raise

    def clean_text(self, text: str) -> str:
        """Sanitizes text artifacts."""
        # Remove Kanoon URLs/Footers
        text = re.sub(r'Indian Kanoon - http://indiankanoon\.org/doc/\d+/.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'http\S+', '', text)
        
        # Fix "Hard Wraps" (Line breaks in middle of sentences)
        text = re.sub(r'(?<!\n)\n(?=[a-z])', ' ', text)
        
        # Standardize Paragraphs
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    def is_garbage(self, text: str) -> bool:
        """Detects corrupted/mangled text (e.g., Hindi encoding errors, symbols)."""
        text = text.strip()
        
        # Check for high ratio of non-ASCII or corrupted characters
        non_ascii_ratio = sum(1 for c in text if ord(c) > 127) / len(text) if text else 0
        if non_ascii_ratio > 0.5:  # More than 50% non-ASCII (likely corrupted)
            return True
        
        # Check for mangled patterns like ^^l'kiFk, excessive punctuation
        if re.search(r'[\^\{\}\|~`]{3,}', text):  # 3+ special chars in a row
            return True
        
        # Check for gibberish (too many consonants without vowels)
        if re.search(r'[bcdfghjklmnpqrstvwxyz]{8,}', text, re.IGNORECASE):
            return True
        
        return False
    
    def validate_quote_fuzzy(self, quote: str, paragraph: str, threshold: float = None) -> bool:
        """Fuzzy matching to handle PDF OCR errors (e.g., 'servicce' vs 'service')."""
        if threshold is None:
            threshold = settings.FUZZY_MATCH_THRESHOLD
            
        if not quote:
            return False
        
        # Normalize both strings
        clean_quote = " ".join(quote.lower().split())
        clean_para = " ".join(paragraph.lower().split())
        
        # Exact match first (fastest)
        if clean_quote in clean_para:
            return True
        
        # Fuzzy matching for slight variations
        # Check all substrings of similar length in the paragraph
        quote_len = len(clean_quote)
        for i in range(len(clean_para) - quote_len + 1):
            substring = clean_para[i:i + quote_len]
            similarity = SequenceMatcher(None, clean_quote, substring).ratio()
            if similarity >= threshold:
                return True
        
        return False

    def is_noise(self, text: str) -> bool:
        """Smart Filter for page numbers and artifacts."""
        text = text.strip().lower()
        if len(text) < 3: return True
        # Page numbers
        if re.match(r'^(page\s?)?\d+(\sof\s\d+)?$', text): return True
        # Dates alone
        if re.match(r'^\d{1,2}[\/-]\d{1,2}[\/-]\d{2,4}$', text): return True
        return False

    def is_critical_outcome(self, text: str) -> bool:
        keywords = ["dismissed", "allowed", "acquitted", "convicted", "granted", "rejected"]
        return any(k in text.lower() for k in keywords)

    async def get_global_metadata(self, clean_text: str) -> Dict[str, Any]:
        """Reads Head & Tail to extract Verdict using Groq."""
        # First 3k chars + Last 3k chars
        head = clean_text[:3000]
        tail = clean_text[-3000:]
        context = f"--- START OF DOC ---\n{head}\n...\n--- END OF DOC ---\n{tail}"
        
        try:
            # Run LLM call in thread pool (CPU-bound)
            response = await asyncio.to_thread(
                self.llm.invoke,
                [
                    SystemMessage(content=GLOBAL_CONTEXT_PROMPT),
                    HumanMessage(content=context)
                ]
            )
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"⚠️ Global Metadata Failed: {e}")
            return {
                "outcome": "Unknown",
                "winning_party": "Unknown",
                "city": None,
                "case_number": None,
                "year_of_judgment": None
            }

    async def atomize_paragraph(self, paragraph: str, retry_count: int = 0) -> List[Dict]:
        """Calls Groq to atomize text and VALIDATES quotes to stop hallucinations."""
        max_retries = 3
        try:
            response = await asyncio.to_thread(
                self.llm.invoke,
                [
                    SystemMessage(content=ATOMIZATION_SYSTEM_PROMPT),
                    HumanMessage(content=paragraph)
                ]
            )
            
            # Clean up the response more robustly
            content = response.content.strip()
            
            # Remove markdown code blocks (with or without language identifier)
            content = re.sub(r'^```(?:json)?\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            
            # Find the first '[' to strip any introductory text
            json_start = content.find('[')
            if json_start != -1:
                content = content[json_start:]
            
            # Debug: Check if content is empty
            if not content:
                print(f"⚠️ Empty response from LLM for paragraph: {paragraph[:100]}...")
                return []
            
            raw_units = json.loads(content)
            
            # --- VALIDATION LOOP (Anti-Hallucination Logic) ---
            validated_units = []
            
            for unit in raw_units:
                quote = unit.get("supporting_quote", "")
                
                # CHECK: Fuzzy validation to handle PDF OCR errors
                if not self.validate_quote_fuzzy(quote, paragraph):
                    print(f"⚠️ Hallucination Blocked: '{unit.get('content', '')}'")
                    print(f"   Reason: Quote '{quote[:80]}...' not found in source text.")
                    continue  # SKIP this chunk (It is fake/hallucinated)
                
                # If valid, we keep it
                validated_units.append(unit)
            
            return validated_units
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON Parse Error: {e}")
            print(f"   Raw LLM Response: {response.content[:200]}...")
            return []
        except Exception as e:
            # Enhanced retry logic for rate limits with exponential backoff
            if "429" in str(e) and retry_count < max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff: 1s, 2s, 4s
                print(f"⏳ Groq Rate Limit (attempt {retry_count + 1}/{max_retries}). Sleeping {wait_time}s...")
                await asyncio.sleep(wait_time)
                return await self.atomize_paragraph(paragraph, retry_count + 1)
            print(f"⚠️ Atomization Failed: {e}")
            return []

    async def process_pdf(self, file_path: str) -> JudgmentResult:
        """Main entry point: Process PDF to structured judgment chunks."""
        print(f"\n🚀 Processing Judgment: {file_path}")
        
        filename = Path(file_path).name
        errors = []
        warnings = []
        
        # 1. PARSE (PyMuPDF)
        try:
            raw_text = self.extract_text_with_pymupdf(file_path)
        except Exception as e:
            error_msg = f"Failed to parse PDF: {e}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)
            return JudgmentResult(
                filename=filename,
                total_chunks=0,
                chunks=[],
                errors=errors
            )

        # 1b. EXTRACT DOC URL (Regex)
        # Look for pattern: http://indiankanoon.org/doc/123456/
        doc_url_match = re.search(r'http://indiankanoon\.org/doc/\d+/?', raw_text, re.IGNORECASE)
        doc_url = doc_url_match.group(0) if doc_url_match else None
        if doc_url:
            print(f"   🔗 Found Document URL: {doc_url}")

        # 2. CLEAN
        clean_doc = self.clean_text(raw_text)
        
        # Check Document Type
        doc_type = detect_document_type(clean_doc[:10000])
        if doc_type == "ACT":
            error_msg = "Error: This document appears to be an Act/Statute. Please upload it via the Act Ingestion Service."
            print(f"❌ {error_msg}")
            errors.append(error_msg)
            return JudgmentResult(
                filename=filename,
                total_chunks=0,
                chunks=[],
                errors=errors
            )
        
        # 3. GLOBAL CONTEXT
        print("   🔍 Extracting Global Metadata...")
        global_meta = await self.get_global_metadata(clean_doc)
        print(f"      Case: {global_meta.get('case_title')}")
        print(f"      Case No: {global_meta.get('case_number')}")
        print(f"      Court: {global_meta.get('court_name')} ({global_meta.get('city')})")
        print(f"      Year: {global_meta.get('year_of_judgment')}")
        print(f"      Verdict: {global_meta.get('outcome')} | Winner: {global_meta.get('winning_party')}")
        
        paragraphs = clean_doc.split('\n\n')
        final_chunks = []
        
        print(f"   ⚡ Atomizing {len(paragraphs)} paragraphs...")
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            
            # Progress indicator every 10 paragraphs
            if i % 10 == 0 and i > 0:
                print(f"   📝 Progress: {i}/{len(paragraphs)} paragraphs processed, {len(final_chunks)} chunks so far")
            
            # GARBAGE FILTER: Skip corrupted text before calling LLM
            if self.is_garbage(para):
                warning_msg = f"Skipped garbage text at paragraph {i}"
                warnings.append(warning_msg)
                print(f"   🗑️ {warning_msg}: {para[:50]}...")
                continue
            
            # Smart Filter
            if len(para) < 50:
                if self.is_noise(para):
                    continue
                if not self.is_critical_outcome(para):
                    continue
            
            # 4. ATOMIZATION (Groq)
            atomic_units = await self.atomize_paragraph(para)
            
            for j, unit in enumerate(atomic_units):
                # Construct the Chunk
                chunk_id = f"{Path(filename).stem}_{i}_{j}"
                
                # Construct rich context string for embedding
                # This ensures the embedding vector captures the "Who, Where, When" context
                case_title = global_meta.get("case_title") or "Unknown"
                case_number = global_meta.get("case_number") or ""
                year = str(global_meta.get("year_of_judgment") or "Unknown")
                court = global_meta.get("court_name") or "Unknown"
                outcome = global_meta.get("outcome", "Unknown")
                
                section = unit.get("section_type", "Fact")
                role = unit.get("party_role", "None")
                topics = ", ".join(unit.get("legal_topics", [])) if unit.get("legal_topics") else "None"
                content = unit.get("content", "")
                
                rich_embedding_text = (
                    f"Case: {case_title} | No: {case_number} | Year: {year} | Court: {court} | Outcome: {outcome}\n"
                    f"Section: {section} | Role: {role} | Topics: {topics}\n"
                    f"Content:\n{content}\n"
                    f"Quote:\n{unit.get('supporting_quote', '')}"
                )

                try:
                    chunk = JudgmentChunk(
                        chunk_id=chunk_id,
                        text_for_embedding=rich_embedding_text,
                        supporting_quote=unit.get("supporting_quote", ""),
                        metadata=JudgmentMetadata(
                            # Global Layers
                            parent_doc=filename,
                            case_title=global_meta.get("case_title"),
                            case_number=global_meta.get("case_number"),
                            court_name=global_meta.get("court_name"),
                            city=global_meta.get("city"),
                            year_of_judgment=global_meta.get("year_of_judgment"),
                            outcome=global_meta.get("outcome", "Unknown"),
                            winning_party=global_meta.get("winning_party", "None"),
                            doc_url=doc_url,  # Inject extracted URL
                            # Local Layers
                            section_type=unit.get("section_type", "Fact"),
                            party_role=unit.get("party_role", "None"),
                            legal_topics=unit.get("legal_topics", []),
                            original_context=para[:400]  # For reference
                        )
                    )
                    
                    # Only add if we have valid content
                    if content:
                        final_chunks.append(chunk)
                        
                except Exception as e:
                    error_msg = f"Failed to create chunk {chunk_id}: {e}"
                    warnings.append(error_msg)
                    print(f"   ⚠️ {error_msg}")
        
        print(f"   ✅ Extracted {len(final_chunks)} atomic units")
        
        # Normalize Outcome
        raw_outcome = global_meta.get("outcome", "Unknown")
        if raw_outcome == "Partially Allowed":
            raw_outcome = "Partly Allowed"

        return JudgmentResult(
            filename=filename,
            case_title=global_meta.get("case_title"),
            court_name=global_meta.get("court_name"),
            city=global_meta.get("city"),
            year_of_judgment=global_meta.get("year_of_judgment"),
            outcome=Outcome(raw_outcome),
            winning_party=WinningParty(global_meta.get("winning_party", "None")),
            total_chunks=len(final_chunks),
            chunks=final_chunks,
            errors=errors,
            warnings=warnings
        )
