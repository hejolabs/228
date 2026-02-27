from datetime import date, datetime

from pydantic import BaseModel


class StudentBase(BaseModel):
    name: str
    phone: str
    school: str
    grade: str  # elementary/middle1/middle2/middle3/high
    parent_phone: str
    class_group_id: int
    tuition_amount: int | None = None
    memo: str | None = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class CycleResponse(BaseModel):
    id: int
    cycle_number: int
    current_count: int
    total_count: int
    status: str
    started_at: date
    completed_at: date | None

    model_config = {"from_attributes": True}


class StudentResponse(StudentBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    class_group_name: str | None = None
    current_cycle: CycleResponse | None = None
    effective_tuition: int = 0

    model_config = {"from_attributes": True}
