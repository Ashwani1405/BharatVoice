# Razorpay & Ledger Integration: Developer Context

This document provides the technical context for the BharatVoice Payment & Ledger system (Sprint 5 implementation). Use this as a reference for integrating payments into new modules or debugging the existing flow.

---

## 🏗️ Architecture Overview

The system uses a **Synchronous Gateway + Asynchronous Webhook** pattern to ensure data integrity and avoid losing transaction records.

1.  **Client Initiation**: Frontend requests an `order_id` from the Backend.
2.  **Razorpay Checkout**: Frontend uses the `order_id` to open the Razorpay popup.
3.  **Webhook Notification**: Razorpay sends a POST request to our `/webhook` endpoint once the payment is "captured".
4.  **Ledger Update**: The Backend verifies the webhook signature and atomically credits the user's balance in the Postgres Ledger.

---

## 🔑 Required Configuration (.env)

Ensure these variables are set in your environment:

```env
RAZORPAY_KEY_ID=rzp_test_...         # Your Razorpay Dashboard API Key
RAZORPAY_KEY_SECRET=...              # Your Razorpay Dashboard API Secret
RAZORPAY_WEBHOOK_SECRET=...          # Set this in Razorpay Dashboard > Webhooks
```

---

## 🛠️ Main Components

### 1. `razorpay_client.py`
**Path**: `apps/backend/app/services/payments/razorpay_client.py`
- Handles raw SDK calls.
- **Note**: Uses `asyncio.to_thread` because the `razorpay` Python library is synchronous and would otherwise block the FastAPI event loop.

### 2. `ledger.py`
**Path**: `apps/backend/app/services/payments/ledger.py`
- Handles the DB side of transactions.
- All credits/debits must go through `record_transaction` to ensure consistent logging.

### 3. `routes.py`
**Path**: `apps/backend/app/api/payments/routes.py`
- Exposes two critical endpoints:
    - `POST /create-order`: Returns a fresh `order_id`.
    - `POST /webhook`: The entry point for Razorpay notifications. **Internal Security**: Validates signatures before processing.

---

## 🔄 The Webhook Payload Flow

When a payment is captured, Razorpay sends a JSON payload. We extract:
- `user_id`: Retrieved from `payload.notes.user_id` (which we passed during order creation).
- `amount`: The total paid (in paise).
- `id`: The Razorpay Payment ID (for reconciliation).

```python
# Example of how we record the transaction in the webhook
await record_transaction(
    user_id=user_id,
    amount=amount,
    type="credit",
    description="Razorpay deposit",
    razorpay_payment_id=payment_id
)
```

---

## 🛑 Troubleshooting 500 Errors

If `POST /create-order` returns a 500 error:
1.  **Invalid Keys**: Check if `RAZORPAY_KEY_ID` and `SECRET` are correct.
2.  **Razorpay Service Down**: Check the [Razorpay Status Page](https://status.razorpay.com/).
3.  **Logs**: Check the backend logs for `Failed to create Razorpay order: ...`.
4.  **Currency/Amount**: Ensure the amount is an integer and at least 100 (1 INR).

---

## 🧪 Quick Test Command

To verify the API is alive (requires a valid JWT):
```bash
python -c "import urllib.request as r; req=r.Request('http://localhost:8000/api/payments/create-order?amount=1000', method='POST', headers={'Authorization': 'Bearer YOUR_JWT'}); print(r.urlopen(req).read().decode())"
```
