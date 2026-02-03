import requests
import json

BASE_URL = "http://localhost:8000"

def run_test(name, method, endpoint, payload=None, expected_status=200):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {name}...")
    print(f"  URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=payload)
        
        print(f"  Status Code: {response.status_code}")
        if response.status_code == expected_status:
            print("  ✅ PASS")
        else:
            print(f"  ❌ FAIL (Expected {expected_status})")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"  ❌ FAIL (Exception: {e})")
    print("-" * 30)

if __name__ == "__main__":
    # Test Root
    run_test("Root Endpoint", "GET", "/")

    # Test PII (Mocked)
    run_test("PII Check", "POST", "/validate", {
        "text": "Contact John Doe at test@example.com in New York.",
        "validators": [{"name": "detect_pii", "mode": "redact"}]
    })

    run_test("Grounded (Fail - Hallucination)", "POST", "/validate", {
        "text": "The moon is made of green cheese.",
        "context": [{"text": "The moon is a natural satellite of Earth."}],
        "validators": [{"name": "grounded_in_context", "parameters": {"threshold": 0.5}}]
    }, expected_status=200) # Should be 200 but body has failure

    # Test Grounded (Fail - Contradiction)
    run_test("Grounded (Fail - Contradiction)", "POST", "/validate", {
        "text": "The sky is blue.",
        "context": [{"id": "c1", "text": "The sky is blue."}],
        "validators": [{"name": "grounded_in_context", "parameters": {"threshold": 0.5}}]
    })
    
    # Test Flexible Citations (Sources: ...)
    run_test("Citations Check (Flexible Format)", "POST", "/validate", {
        "text": "The study shows specific results Sources: http://example.com.",
        "validators": [{"name": "citations_present"}]
    }, expected_status=200)

    # Test Grounded (Fail) - Hallucination
    run_test("Grounded (Fail)", "POST", "/validate", {
        "text": "The sky is green.",
        "context": [{"id": "c1", "text": "The sky is blue."}],
        "validators": [{"name": "grounded_in_context", "parameters": {"threshold": 0.9}}]
    })
