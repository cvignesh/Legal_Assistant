import requests
import json
import sys

BASE_URL = "http://localhost:8000/api"

def test_viability():
    print("🚀 Testing Viability Predictor Endpoint...")
    
    payload = {
        "facts": "My cheque bounced because the signature didn't match, preventing me from paying the vendor. I received a notice but replied after 45 days.",
        "user_role": "Petitioner",  # Expecting "High" or "Medium" depending on luck, but "Petitioner" (Complainant) usually implies we want the Accused to be convicted.
        # Wait, if I am the one whose cheque bounced, I am the ACCUSED (Respondent).
        # If I am the vendor, I am the PETITIONER (Complainant).
        # Let's say I am the detailed person (Accused) - "My cheque bounced".
        # So User Role = Respondent.
        "user_role": "Respondent",
        "court_filter": "All Courts"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/viability", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Success! Response:")
            print(json.dumps(data, indent=2))
            
            # Assertions
            assert "viability_score" in data
            assert "viability_label" in data
            assert len(data.get("top_precedents", [])) >= 0
            assert "strategic_advice" in data
            print("\n✅ All assertions passed.")
        else:
            print(f"\n❌ Failed with Status {response.status_code}")
            print(response.text)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_viability()
