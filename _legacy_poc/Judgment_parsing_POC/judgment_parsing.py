import os
import re
import json
import time
import fitz  # PyMuPDF
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()

# Hardcoded GROQ API Key
os.environ["GROQ_API_KEY"] = "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"

# --- CONFIGURATION ---
# We use Groq (Llama 3.3) for the "Brain" because it's fast & efficient for JSON tasks.
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    max_retries=2
)

# --- PROMPTS ---
GLOBAL_CONTEXT_PROMPT = """
You are a Legal Data Extractor.
Task: Analyze the text to extract global case details.
Output must be strictly valid JSON with these keys:
- "case_title": (String or null)
- "outcome": (One of: "Dismissed", "Allowed", "Acquitted", "Convicted", "Disposed", "Unknown")
- "winning_party": (One of: "Petitioner", "Respondent", "State", "None")
- "court_name": (String or null)
"""

ATOMIZATION_SYSTEM_PROMPT = """
You are an expert Legal Analyst.
Task: Break the provided paragraph into "Atomic Units" (standalone statements).

RULES:
1. **Split**: Break complex compound sentences into separate facts/arguments.
2. **Resolve Pronouns**: REPLACE "He", "She", "It", "They" with actual names (e.g., "The Petitioner", "Witness PW-2").
3. **Classify**:
   - `section_type`: ["Fact", "Submission_Petitioner", "Submission_Respondent", "Court_Observation", "Statute_Citation", "Operative_Order"]
   - `party_role`: ["Petitioner", "Respondent", "Court", "Witness", "Prosecution", "None"]
   - `legal_topics`: List of specific concepts (e.g., ["Delay in FIR", "Alibi"]).

OUTPUT FORMAT:
Return a strictly valid JSON LIST of objects. Example:
[
  {
    "content": "The Petitioner argued that there was a 5-day delay in FIR.",
    "section_type": "Submission_Petitioner",
    "party_role": "Petitioner",
    "legal_topics": ["Delay in FIR"]
  }
]
"""

class LegalPipeline:
    
    def extract_text_with_pymupdf(self, file_path: str) -> str:
        """Parses PDF using PyMuPDF (fitz) for speed and accuracy."""
        doc = fitz.open(file_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text() + "\n"
        return full_text

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

    def get_global_metadata(self, clean_text: str) -> Dict[str, Any]:
        """Reads Head & Tail to extract Verdict using Groq."""
        # First 3k chars + Last 3k chars
        head = clean_text[:3000]
        tail = clean_text[-3000:]
        context = f"--- START OF DOC ---\n{head}\n...\n--- END OF DOC ---\n{tail}"
        
        try:
            response = llm.invoke([
                SystemMessage(content=GLOBAL_CONTEXT_PROMPT),
                HumanMessage(content=context)
            ])
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"⚠️ Global Metadata Failed: {e}")
            return {"outcome": "Unknown", "winning_party": "Unknown"}

    def atomize_paragraph(self, paragraph: str, retry_count: int = 0) -> List[Dict]:
        """Calls Groq (Llama 3.3) to atomize text."""
        max_retries = 3
        try:
            response = llm.invoke([
                SystemMessage(content=ATOMIZATION_SYSTEM_PROMPT),
                HumanMessage(content=paragraph)
            ])
            
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
            
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON Parse Error: {e}")
            print(f"   Raw LLM Response: {response.content[:200]}...")
            return []
        except Exception as e:
            # Enhanced retry logic for rate limits with exponential backoff
            if "429" in str(e) and retry_count < max_retries:
                wait_time = 2 ** retry_count  # Exponential backoff: 1s, 2s, 4s
                print(f"⏳ Groq Rate Limit (attempt {retry_count + 1}/{max_retries}). Sleeping {wait_time}s...")
                time.sleep(wait_time)
                return self.atomize_paragraph(paragraph, retry_count + 1)
            print(f"⚠️ Atomization Failed: {e}")
            return []

    def process_pdf_to_json(self, file_path: str, output_json_path: str):
        print(f"\n🚀 Processing File: {file_path}")
        
        # 1. PARSE (PyMuPDF)
        try:
            raw_text = self.extract_text_with_pymupdf(file_path)
        except Exception as e:
            print(f"❌ Failed to parse PDF: {e}")
            return

        # 2. CLEAN
        clean_doc = self.clean_text(raw_text)
        
        # 3. GLOBAL CONTEXT
        print("   🔍 Extracting Global Metadata...")
        global_meta = self.get_global_metadata(clean_doc)
        print(f"      Verdict: {global_meta.get('outcome')} | Winner: {global_meta.get('winning_party')}")
        
        paragraphs = clean_doc.split('\n\n')
        final_chunks = []
        
        print(f"   ⚡ Atomizing {len(paragraphs)} paragraphs (this may take a moment)...")
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para: continue
            
            # Smart Filter
            if len(para) < 50:
                if self.is_noise(para): continue
                if not self.is_critical_outcome(para): continue
            
            # 4. ATOMIZATION (Groq)
            atomic_units = self.atomize_paragraph(para)
            
            for j, unit in enumerate(atomic_units):
                # Construct the Payload
                chunk_payload = {
                    "id": f"{os.path.basename(file_path)}_{i}_{j}",
                    "text_content": unit.get("content", ""),
                    "metadata": {
                        # Global Layers
                        "parent_doc": os.path.basename(file_path),
                        "outcome": global_meta.get("outcome"),
                        "winning_party": global_meta.get("winning_party"),
                        "case_title": global_meta.get("case_title"),
                        # Local Layers
                        "section_type": unit.get("section_type", "Unknown"),
                        "party_role": unit.get("party_role", "Unknown"),
                        "legal_topics": unit.get("legal_topics", []),
                        "original_context": para[:400] # For reference
                    }
                }
                
                # Only add if we have valid content
                if chunk_payload["text_content"]:
                    final_chunks.append(chunk_payload)
            
            # Optional: Sleep to avoid hammering free tier limits
            # time.sleep(0.2)

        # 5. SAVE TO JSON (Instead of Embedding)
        print(f"   💾 Saving {len(final_chunks)} atomic units to {output_json_path}...")
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(final_chunks, f, indent=2)
        
        print("✅ Done! You can now inspect the JSON file.")

        # --- EMBEDDING SECTION (COMMENTED OUT) ---
        # print("   embedding chunks...")
        # vectors = embedder.embed_documents([c["text_content"] for c in final_chunks])
        # collection.upsert(
        #     ids=[c["id"] for c in final_chunks],
        #     embeddings=vectors,
        #     documents=[c["text_content"] for c in final_chunks],
        #     metadatas=[c["metadata"] for c in final_chunks]
        # )

if __name__ == "__main__":
    # Point this to your actual PDF file
    pdf_path = "Smt_Noor_Jahan_Begum_Anjali_Mishra_vs_State_Of_U_P_4_Others_on_16_December_2014.PDF"
    output_path = "processed_judgment.json"
    
    pipeline = LegalPipeline()
    pipeline.process_pdf_to_json(pdf_path, output_path)