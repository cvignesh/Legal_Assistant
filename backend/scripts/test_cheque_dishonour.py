"""
Test Petition Drafting Engine with Real Cheque Dishonour Scenario
This test uses a scenario matching the judgment: Dara Singh vs Deepa (Section 138 NI Act)
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

import asyncio
from app.services.drafting.service import DraftingService
from app.services.drafting.models import DraftingRequest

async def test_cheque_dishonour_case():
    """Test with a cheque dishonour scenario matching real judgment in DB"""
    
    # User story matching the judgment pattern
    user_story = """
    I am Rajesh Kumar. On 15th March 2024, my neighbor Mr. Suresh Sharma approached me 
    requesting financial help of Rs. 2,00,000 for his business. Being neighbors and friends, 
    I agreed to help him. On 20th March 2024, I gave him Rs. 2,00,000 in cash as a loan.
    
    Mr. Sharma issued me a cheque bearing number 123456 dated 20th June 2024 for Rs. 2,00,000 
    drawn on State Bank of India, Rohini Branch, Delhi, as repayment of the loan amount.
    
    When I presented the cheque on 25th June 2024, it was dishonored by the bank with the 
    remark "Insufficient Funds". I immediately sent a legal demand notice to Mr. Sharma on 
    30th June 2024 through registered post, demanding payment of the cheque amount within 
    15 days as required under law.
    
    Despite receiving the notice, Mr. Sharma has failed to make any payment. He is now 
    avoiding me and refusing to return my money. I have the original cheque, bank dishonor 
    memo, demand notice, and postal receipt as evidence.
    
    I want to file a criminal complaint for cheque dishonour and recover my money.
    """
    
    request = DraftingRequest(
        user_story=user_story,
        document_type="police_complaint"  # Correct enum value
    )
    
    print("=" * 80)
    print("TESTING PETITION DRAFTING ENGINE - CHEQUE DISHONOUR CASE")
    print("=" * 80)
    print(f"\nUSER STORY:\n{user_story}\n")
    print("=" * 80)
    
    service = DraftingService()
    result = await service.generate_draft(request)
    
    print("\n" + "=" * 80)
    print("EXTRACTED FACTS:")
    print("=" * 80)
    for fact in result.extracted_facts.key_facts:
        print(f"  • {fact}")
    
    print("\n" + "=" * 80)
    print("IDENTIFIED LEGAL ISSUES:")
    print("=" * 80)
    for issue in result.legal_issues:
        status = "✓ VERIFIED" if issue.verified else "✗ NOT VERIFIED"
        print(f"  [{status}] {issue.act} Section {issue.section}")
        print(f"      Issue: {issue.legal_issue}")
        print(f"      Reasoning: {issue.reasoning}\n")
    
    print("=" * 80)
    print("VALIDATION WARNINGS:")
    print("=" * 80)
    if result.validation_warnings:
        for warning in result.validation_warnings:
            print(f"  ⚠ {warning}")
    else:
        print("  None")
    
    print("\n" + "=" * 80)
    print("GROUNDED CITATIONS:")
    print("=" * 80)
    if result.citations:
        for i, citation in enumerate(result.citations, 1):
            print(f"\n  {i}. {citation.case_title}")
            print(f"     Source: {citation.citation_source}")
            print(f"     Relevance Score: {citation.relevance_score:.2f}")
            print(f"     Excerpt: {citation.excerpt[:150]}...")
    else:
        print("  No citations found")
    
    print("\n" + "=" * 80)
    print("DRAFT PREVIEW (First 500 chars):")
    print("=" * 80)
    print(result.draft_text[:500] + "...")
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY:")
    print("=" * 80)
    print(f"  Facts Extracted: {len(result.extracted_facts.key_facts)}")
    print(f"  Legal Issues Identified: {len(result.legal_issues)}")
    print(f"  Issues Verified: {sum(1 for i in result.legal_issues if i.verified)}")
    print(f"  Citations Found: {len(result.citations)}")
    print(f"  Validation Warnings: {len(result.validation_warnings)}")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_cheque_dishonour_case())
