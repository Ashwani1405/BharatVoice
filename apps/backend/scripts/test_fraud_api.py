import json
import urllib.request
import urllib.error

def test_fraud_api():
    base_url = "http://localhost:8000/api/fraud"
    
    # Fake Profile (would normally come from KYC Sandbox)
    profile = {
        "name": "Jane Gupta",
        "dob": "10-10-1995",
        "address": "456 Tech Park, Bangalore",
        "aadhaar_number": "999988887777"
    }

    print(f"\n[POST] /evaluate fraud API check")
    req_data = json.dumps({
        "user_id": "test-user-123",
        "profile": profile,
        "context": {"ip_address": "8.8.8.8"}
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"{base_url}/evaluate", 
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode())
            print(f"Status: {response.status}")
            print(json.dumps(res_body, indent=2))
    except urllib.error.URLError as e:
        print(f"ERROR: Could not connect to {base_url}. Is the backend running?")
        if hasattr(e, 'read'):
            print(e.read().decode())
        
if __name__ == "__main__":
    test_fraud_api()
