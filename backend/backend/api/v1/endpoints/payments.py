from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
import uuid

from backend.schemas.subscription import PaymentRequest, MockPaymentResponse, SubscriptionOut

router = APIRouter()

PLAN_CONFIG = {
    "daily":   {"amount": 50,  "days": 1},
    "weekly":  {"amount": 250, "days": 7},
    "monthly": {"amount": 700, "days": 30},
}

# In-memory store for dev — replace with Supabase table in production
_mock_subscriptions: dict = {}


@router.post("/mock-stk-push", response_model=MockPaymentResponse)
async def mock_stk_push(req: PaymentRequest):
    """
    DEV ONLY — simulates an M-Pesa Pochi la Biashara STK Push.
    Auto-succeeds instantly. In production, replace with real Daraja API call
    and a /payments/callback endpoint for Safaricom's async confirmation.
    """
    if req.plan not in PLAN_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid plan '{req.plan}'. Must be daily, weekly or monthly.")

    plan = PLAN_CONFIG[req.plan]
    transaction_id = f"DEV-{str(uuid.uuid4())[:8].upper()}"
    expires_at = datetime.utcnow() + timedelta(days=plan["days"])

    _mock_subscriptions[req.user_id] = {
        "plan": req.plan,
        "expires_at": expires_at.isoformat(),
        "transaction_id": transaction_id,
        "phone": req.phone,
        "amount": plan["amount"],
    }

    sub_out = SubscriptionOut(
        active=True,
        plan=req.plan,
        expires_at=expires_at.isoformat(),
        transaction_id=transaction_id,
    )

    return MockPaymentResponse(
        transaction_id=transaction_id,
        status="success",
        message=f"[DEV] KES {plan['amount']} payment simulated for {req.phone}",
        subscription=sub_out,
    )


@router.get("/subscription/{user_id}", response_model=SubscriptionOut)
async def get_subscription(user_id: str):
    sub = _mock_subscriptions.get(user_id)
    if not sub:
        return SubscriptionOut(active=False)

    expires = datetime.fromisoformat(sub["expires_at"])
    if datetime.utcnow() > expires:
        return SubscriptionOut(active=False, expired=True)

    return SubscriptionOut(
        active=True,
        plan=sub["plan"],
        expires_at=sub["expires_at"],
        transaction_id=sub["transaction_id"],
    )


@router.delete("/subscription/{user_id}")
async def cancel_subscription(user_id: str):
    """Dev helper — clears a subscription so you can test the paywall again."""
    _mock_subscriptions.pop(user_id, None)
    return {"message": "Subscription cleared"}