from datetime import datetime

from pydantic import BaseModel


class PaymentResponse(BaseModel):
    id: int
    student_id: int
    cycle_id: int
    amount: int
    payment_method: str | None
    status: str
    message_sent: bool
    message_sent_at: datetime | None
    paid_at: datetime | None
    memo: str | None
    created_at: datetime
    student_name: str | None = None
    class_group_name: str | None = None
    cycle_number: int = 0

    model_config = {"from_attributes": True}


class PaymentConfirm(BaseModel):
    payment_method: str = "transfer"
    memo: str | None = None


class MessageResponse(BaseModel):
    payment_id: int
    message: str
