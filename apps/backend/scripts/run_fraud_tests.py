import json
import sys
import urllib.request
import urllib.error
import time

# Force UTF-8 on Windows so emoji/unicode chars don't crash the console (cp1252 issue)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000/api/fraud"

class TestContext:
    passed = 0
    failed = 0

def run_test(name, user_id, profile, context, expected_action, expected_flags=None):
    print(f"[{TestContext.passed + TestContext.failed + 1}] {name}")
    req_data = json.dumps({
        "user_id": user_id,
        "profile": profile,
        "context": context
    }).encode("utf-8")
    
    req = urllib.request.Request(
        f"{BASE_URL}/evaluate", 
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode())
            assessment = res_body.get("fraud_assessment", {})
            action = assessment.get("action")
            flags = assessment.get("flags", [])
            
            passed = action == expected_action
            if expected_flags:
                for flag in expected_flags:
                    if flag not in flags:
                        passed = False
            
            sim_score = assessment.get("similarity_score", 0.0)
            if passed:
                print(f"  [PASS] Action: {action}, SIM: {sim_score:.3f}, Flags: {flags}")
                TestContext.passed += 1
            else:
                print(f"  [FAIL] Expected action={expected_action} flags={expected_flags}")
                print(f"         Got action={action} | SIM: {sim_score:.3f} | Flags: {flags}")
                TestContext.failed += 1
                
    except Exception as e:
         print(f"  [ERR]  API Error: {e}")
         TestContext.failed += 1
    print("-" * 40)

async def clear_qdrant():
    """Wipes the kyc_profiles collection in Qdrant for a clean test run."""
    print("[CLEAN] Clearing Qdrant collection: kyc_profiles...")
    import urllib.request
    try:
        req = urllib.request.Request("http://localhost:6333/collections/kyc_profiles", method="DELETE")
        urllib.request.urlopen(req)
        print("  [OK] Collection deleted.")
    except Exception as e:
        print(f"  [INFO] Could not delete collection (might not exist): {e}")

def execute_all_tests():
    # 0. Clean slate
    import asyncio
    try:
        asyncio.run(clear_qdrant())
    except Exception as e:
        print(f"  ⚠️ Warning: Failed to clear Qdrant: {e}")
        
    # A. Core Sybil Attack Detection (Vector Similarity)
    run_test("1. Perfect Clean Entry", "u1", {"name": "Alice Smith", "dob": "01-01-1990", "address": "100 Unique Way"}, {"ip_address": "1.1.1.1"}, "allow")
    print("  [INFO] Waiting 4s for Qdrant background upsert to complete...")
    time.sleep(4) # Allow async qdrant insert to finish before Sybil tests
    
    run_test("2. Exact Duplicate (100% Sybil)", "u2", {"name": "Alice Smith", "dob": "01-01-1990", "address": "100 Unique Way"}, {"ip_address": "1.1.1.2"}, "block", ["SYBIL_IDENTITY_CLONE"])
    
    run_test("3. Typo in First Name", "u3", {"name": "Alisse Smiyh", "dob": "01-01-1990", "address": "100 Unique Way"}, {"ip_address": "1.1.1.3"}, "block", ["SYBIL_IDENTITY_CLONE"])
    
    run_test("4. Typo in Address", "u4", {"name": "Alice Smith", "dob": "01-01-1990", "address": "100 Uniquue Wav"}, {"ip_address": "1.1.1.4"}, "block", ["SYBIL_IDENTITY_CLONE"])
    
    run_test("5. Typo in DOB", "u5", {"name": "Alice Smith", "dob": "02-01-1990", "address": "100 Unique Way"}, {"ip_address": "1.1.1.5"}, "block", ["SYBIL_IDENTITY_CLONE"])

    run_test("6. Same Household (Diff Name)", "u6", {"name": "Bob Smith", "dob": "01-05-1988", "address": "100 Unique Way"}, {"ip_address": "1.1.1.6"}, "allow")
    
    # B. Static Rule Engine
    run_test("7. Future DOB (2026)", "u7", {"name": "Charlie", "dob": "01-01-2026", "address": "12 Normal St"}, {"ip_address": "1.1.1.7"}, "review", ["RULE_INVALID_DOB_RANGE"])
    
    run_test("8. Near Future DOB (2025)", "u8", {"name": "Dave", "dob": "01-01-2025", "address": "12 Normal St"}, {"ip_address": "1.1.1.8"}, "review", ["RULE_INVALID_DOB_RANGE"])
    
    run_test("9. Dummy Address Included", "u9", {"name": "Eve", "dob": "01-01-1990", "address": "123 test street"}, {"ip_address": "1.1.1.9"}, "review", ["RULE_DUMMY_ADDRESS"])
    
    run_test("10. Unknown Address", "u10", {"name": "Frank", "dob": "01-01-1990", "address": "unknown"}, {"ip_address": "1.1.1.10"}, "review", ["RULE_DUMMY_ADDRESS"])
    
    run_test("11. Compound Rule Failure", "u11", {"name": "George", "dob": "01-01-2026", "address": "fake test road"}, {"ip_address": "1.1.1.11"}, "review", ["RULE_INVALID_DOB_RANGE", "RULE_DUMMY_ADDRESS"])

    # C. Context & Edge Inputs
    run_test("12. Empty Profile Dictionary", "u12", {}, {"ip_address": "10.0.0.12"}, "allow")
    
    run_test("13. Missing Context Dict", "u13", {"name": "Hank"}, {}, "allow")
    
    run_test("14. Extreme Name Length", "u14", {"name": "A" * 5000}, {"ip_address": "10.0.0.14"}, "allow")
    
    run_test("15. Unicode / Hindi Characters", "u15", {"name": "राहुल गांधी", "address": "दिल्ली"}, {"ip_address": "10.0.0.15"}, "allow")
    time.sleep(2)
    run_test("16. Unicode Sybil Target", "u16", {"name": "राहुल गांधि", "address": "दिल्लि"}, {"ip_address": "10.0.0.16"}, "block", ["SYBIL_IDENTITY_CLONE"])
    
    run_test("17. Missing Name field entirely", "u17", {"address": "Valid Street 99", "dob": "01-01-1990"}, {"ip_address": "10.0.0.17"}, "allow")
    
    run_test("18. Null Types", "u18", {"name": None, "address": None}, {"ip_address": "10.0.0.18"}, "allow")
    
    run_test("19. Extremely Short Strings", "u19", {"name": "A", "address": "B"}, {"ip_address": "10.0.0.19"}, "allow")

    # D. Real-Time Streaming Velocity Tests
    print("\n--- Initiating Velocity Stream Attacks (IP 9.9.9.9) ---")
    for i in range(7):  # 7 events ensures we exceed the >5 threshold even if one is dropped
        # Use different names to avoid SYBIL_IDENTITY_CLONE
        profile_data = {"name": f"Spammer {i}", "dob": "01-01-1970", "address": f"Spam St {i}"}
        req_data = json.dumps({"user_id": f"v{i}", "profile": profile_data, "context": {"ip_address": "9.9.9.9"}}).encode("utf-8")
        try:
            urllib.request.urlopen(urllib.request.Request(f"{BASE_URL}/evaluate", data=req_data, headers={"Content-Type": "application/json"}, method="POST"))
        except Exception as e:
            print(f"  [WARN] Velocity burst request {i} failed: {e}")
        time.sleep(0.1)  # slight gap to avoid TCP resets
    
    print("Sent 7 fast requests. Waiting 8 seconds for Pathway to aggregate window and flag Redis...")
    time.sleep(8)
    run_test("20. Velocity Blacklist Caught", "u20", {"name": "Another Spammer"}, {"ip_address": "9.9.9.9"}, "block", ["RULE_VELOCITY_ABUSE"])
    
    total = TestContext.passed + TestContext.failed
    print("\n" + "=" * 50)
    print(f"TEST RUN COMPLETE: {TestContext.passed}/{total} Passed | {TestContext.failed}/{total} Failed")
    if TestContext.failed == 0:
        print("  All tests passed!")
    else:
        print(f"  {TestContext.failed} test(s) failed - review output above.")
    
if __name__ == "__main__":
    execute_all_tests()
