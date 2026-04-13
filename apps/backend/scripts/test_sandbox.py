import json
import csv
import sys
import os
import urllib.request
import urllib.error

def test_api():
    base_url = "http://localhost:8000/api/sandbox/v1"
    
    # 1. Look up a mock aadhaar
    dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "mock_aadhaar_dataset.csv")
    if not os.path.exists(dataset_path):
        print(f"ERROR: Dataset not found at {dataset_path}")
        sys.exit(1)
        
    sample_aadhaar = None
    with open(dataset_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_aadhaar = row["aadhaar_number"]
            break
            
    print(f"==== TESTING KYT SANDBOX ====")
    print(f"Targeting: {base_url}")
    print(f"Sample Aadhaar: {sample_aadhaar}")
    
    # 2. Trigger OTP Request
    print("\n[POST] /kyc/otp")
    req_data = json.dumps({"aadhaar_number": sample_aadhaar}).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/kyc/otp", 
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode())
            print(f"Status: {response.status}")
            print(f"Response: {json.dumps(res_body, indent=2)}")
            
            ref_id = res_body.get("reference_id")
    except urllib.error.URLError as e:
        print(f"ERROR: Could not connect to {base_url}. Is the backend running?")
        if hasattr(e, 'read'):
            print(e.read().decode())
        sys.exit(1)

    # 3. Verify OTP Request
    print(f"\n[POST] /kyc/verify with Ref ID {ref_id} & OTP 123456")
    req_data2 = json.dumps({"reference_id": ref_id, "otp": "123456"}).encode("utf-8")
    req2 = urllib.request.Request(
        f"{base_url}/kyc/verify", 
        data=req_data2,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req2) as response:
            res_body = json.loads(response.read().decode())
            print(f"Status: {response.status}")
            profile = res_body.get('profile', {})
            print(f"Profile Acquired -> Name: {profile.get('name')}, DOB: {profile.get('dob')}")
    except urllib.error.URLError as e:
        print(f"ERROR on verify:")
        if hasattr(e, 'read'):
            print(e.read().decode())
        sys.exit(1)
        
    print("\n✅ Verification Successful. All Sandbox APIs are operating perfectly.")

if __name__ == "__main__":
    test_api()
