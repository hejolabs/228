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
    enrollment_status: str = "inquiry"


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
    enrollment_status: str
    created_at: datetime
    updated_at: datetime
    class_group_name: str | None = None
    current_cycle: CycleResponse | None = None
    effective_tuition: int = 0

    model_config = {"from_attributes": True}


class StatusChangeRequest(BaseModel):
    status: str
    memo: str | None = None


class EnrollmentHistoryResponse(BaseModel):
    id: int
    from_status: str | None
    to_status: str
    changed_at: datetime
    memo: str | None

    model_config = {"from_attributes": True}
