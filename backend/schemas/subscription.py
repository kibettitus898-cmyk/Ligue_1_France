from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PaymentRequest(BaseModel):
    phone: str           # 2547XXXXXXXX format
    plan: str            # "daily" | "weekly" | "monthly"
    user_id: str

class SubscriptionOut(BaseModel):
    active: bool
    plan: Optional[str] = None
    expires_at: Optional[str] = None
    transaction_id: Optional[str] = None
    expired: Optional[bool] = None

class MockPaymentResponse(BaseModel):
    transaction_id: str
    status: str
    message: str
    subscription: SubscriptionOut