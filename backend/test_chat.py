"""
Simple test for chat endpoint
"""
import requests
import json

# Base URL
BASE_URL = "http://localhost:8000/api"

print("=" * 60)
print("Testing Chat Endpoint")
print("=" * 60)

# Step 1: Create session
print("\n1. Creating session...")
session_response = requests.get(f"{BASE_URL}/chat/session")
session_data = session_response.json()
session_id = session_data['session_id']
print(f"✓ Session created: {session_id}\n")

# Step 2: Send first message
print("2. Sending message: 'What is Section 318 BNS?'")
chat_response = requests.post(
    f"{BASE_URL}/chat",
    json={
        'session_id': session_id,
        'message': 'What is Section 318 BNS?'
    }
)

result = chat_response.json()

if 'detail' in result:
    print(f"✗ Error: {result['detail']}")
else:
    print(f"\n✓ Response received in {result['processing_time_ms']:.0f}ms\n")
    print("Answer:")
    print("-" * 60)
    print(result['answer'][:300] + "..." if len(result['answer']) > 300 else result['answer'])
    print("-" * 60)
    
    print(f"\nCitations ({len(result['citations'])}):")
    for i, citation in enumerate(result['citations'][:5], 1):
        print(f"  {i}. {citation['source']}")
        print(f"     Score: {citation['score']:.3f}")
        print(f"     Text: {citation['text'][:100]}...")
        print()

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)
