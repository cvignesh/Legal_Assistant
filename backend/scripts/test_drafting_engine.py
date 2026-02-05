
import asyncio
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv("backend/.env")

from app.services.drafting.service import drafting_service
from app.services.drafting.models import DraftingRequest, DocumentType
from app.db.mongo import mongo

logging.basicConfig(level=logging.INFO)

async def test_drafting():
    # Connect to DB
    print("Connecting to MongoDB...")
    mongo.connect()
    
    story = """
    I gave Rs. 10 Lakhs to Mr. Ramesh Gupta on 1st Jan 2024 for a business investment. 
    He promised to return it by 1st March 2024. He gave me a cheque which bounced. 
    Now he is refusing to pay and threatening me. I live in Delhi.
    """
    
    print("\n--- TEST: POLICE COMPLAINT (No Citations) ---")
    req = DraftingRequest(
        user_story=story,
        document_type=DocumentType.POLICE_COMPLAINT
    )
    res = await drafting_service.generate_draft(req)
    print("FACTS:", res.facts)
    print("WARNINGS:", res.validation_warnings)
    print("\nDRAFT PREVIEW:\n", res.draft_text[:500])
    
    print("\n\n--- TEST: MAGISTRATE 156(3) (With Citations) ---")
    req2 = DraftingRequest(
        user_story=story,
        document_type=DocumentType.MAGISTRATE_156_3
    )
    res2 = await drafting_service.generate_draft(req2)
    print("LEGAL ISSUES:", res2.legal_issues)
    print("CITATIONS:", [c.case_title for c in res2.citations])
    print("\nDRAFT PREVIEW:\n", res2.draft_text[:500])

if __name__ == "__main__":
    asyncio.run(test_drafting())
