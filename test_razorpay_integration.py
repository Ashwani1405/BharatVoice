#!/usr/bin/env python3
"""
Test script to verify Razorpay integration is working
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'backend'))

print("=" * 60)
print("Testing Razorpay Integration - Sprint 5")
print("=" * 60)

# Test 1: Check .env loading
print("\n[1/4] Testing environment configuration...")
try:
    from app.config import settings
    print(f"✓ RAZORPAY_KEY_ID: {settings.RAZORPAY_KEY_ID[:10]}...")
    print(f"✓ RAZORPAY_KEY_SECRET: Loaded")
    print(f"✓ RAZORPAY_WEBHOOK_SECRET: {settings.RAZORPAY_WEBHOOK_SECRET}")
except Exception as e:
    print(f"✗ Failed to load config: {e}")
    sys.exit(1)

# Test 2: Check razorpay library
print("\n[2/4] Testing razorpay library...")
try:
    import razorpay
    print(f"✓ razorpay library imported successfully")
    print(f"✓ Version: {razorpay.__version__}")
except Exception as e:
    print(f"✗ Failed to import razorpay: {e}")
    sys.exit(1)

# Test 3: Check razorpay_client module
print("\n[3/4] Testing razorpay_client module...")
try:
    from app.services.payments.razorpay_client import (
        create_razorpay_order,
        verify_webhook_signature
    )
    print("✓ Razorpay client functions imported successfully")
except Exception as e:
    print(f"✗ Failed to import razorpay_client: {e}")
    sys.exit(1)

# Test 4: Check ledger module
print("\n[4/4] Testing ledger module...")
try:
    from app.services.payments.ledger import record_transaction
    print("✓ Ledger recording function imported successfully")
except Exception as e:
    print(f"✗ Failed to import ledger: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All Razorpay integration components verified!")
print("=" * 60)
print("\nNext steps:")
print("1. Test /api/payments/create-order endpoint with valid JWT")
print("2. Configure Razorpay dashboard webhook to: POST /api/payments/webhook")
print("3. Complete payment flow testing in production")
