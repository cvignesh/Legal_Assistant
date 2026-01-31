
import requests
import json
import sys

# Base URL
BASE_URL = "http://localhost:8000/api"

def verify_retrieval_limit():
    print("=" * 60)
    print("Verifying Retrieval Limit Fix")
    print("=" * 60)

    try:
        # Step 1: Create session
        print("\n1. Creating session...")
        session_response = requests.get(f"{BASE_URL}/chat/session")
        if session_response.status_code != 200:
            print(f"✗ Failed to create session: {session_response.text}")
            return False
            
        session_data = session_response.json()
        session_id = session_data['session_id']
        print(f"✓ Session created: {session_id}")

        # Step 2: Send query aimed at broad retrieval
        query = "cases related to cheque dishonour" 
        print(f"\n2. Sending query: '{query}'")
        
        chat_response = requests.post(
            f"{BASE_URL}/chat",
            json={
                'session_id': session_id,
                'message': query
            }
        )

        if chat_response.status_code != 200:
            print(f"✗ Chat request failed: {chat_response.text}")
            return False

        result = chat_response.json()
        citations = result.get('citations', [])
        count = len(citations)
        
        print(f"\n✓ Response received. Citation count: {count}")
        
        # Step 3: Verify count
        # We expect more than 5 if the fix works and there are enough docs
        # The user mentioned "10-12 cases uploaded", so we should get significantly more than 5
        
        if count > 5:
            print(f"\nPASS: Retrieved {count} citations (Limit > 5 verified)")
            return True
        elif count == 5:
            print(f"\nFAIL: Retrieved exactly 5 citations. The hardcoded limit might still be active.")
            return False
        else:
            print(f"\nWARNING: Retrieved {count} citations. This is low, but might be due to data availability, not the limit.")
            # If we get < 5, it's inconclusive unless we know for sure there are more matches. 
            # But the user said they saw exactly 4 before, so seeing > 4 is progress? 
            # Wait, user saw 4 context chunks. If hardcode was 5, maybe only 4 were relevant.
            # But if we assume the hardcode was the bottleneck, 100 top_k should give us more.
            # Let's consider > 5 as definitive PASS for the fix.
            if count == 4:
                 print("Result is 4. This matches the user's previous issue. Fix might not have updated the running process or data is actually limited.")
            return False

    except Exception as e:
        print(f"\n✗ Error during verification: {str(e)}")
        return False

if __name__ == "__main__":
    success = verify_retrieval_limit()
    if not success:
        sys.exit(1)
    sys.exit(0)
