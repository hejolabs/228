from datetime import datetime

from pydantic import BaseModel


class ClassGroupBase(BaseModel):
    name: str
    days_of_week: list[str]  # ["mon", "wed"]
    start_time: str  # "14:30"
    default_duration_minutes: int
    memo: str | None = None


class ClassGroupCreate(ClassGroupBase):
    pass


class ClassGroupUpdate(ClassGroupBase):
    pass


class ClassGroupResponse(ClassGroupBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
