from datetime import date, datetime

from pydantic import BaseModel


class AttendanceCreate(BaseModel):
    student_id: int
    date: date
    status: str  # present/late/early_leave/absent/absent_excused
    counts_toward_cycle: bool = True
    excuse_reason: str | None = None
    memo: str | None = None


class AttendanceUpdate(BaseModel):
    status: str
    counts_toward_cycle: bool = True
    excuse_reason: str | None = None
    memo: str | None = None


class BulkAttendanceItem(BaseModel):
    student_id: int
    status: str
    counts_toward_cycle: bool = True
    excuse_reason: str | None = None


class BulkAttendanceCreate(BaseModel):
    date: date
    items: list[BulkAttendanceItem]


class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    cycle_id: int
    date: date
    status: str
    counts_toward_cycle: bool
    excuse_reason: str | None
    memo: str | None
    created_at: datetime
    student_name: str | None = None
    class_group_name: str | None = None
    start_time: str | None = None
    current_count: int = 0
    total_count: int = 8

    model_config = {"from_attributes": True}


class CycleAlertResponse(BaseModel):
    student_id: int
    student_name: str
    class_group_name: str
    cycle_id: int
    cycle_number: int
    current_count: int
    total_count: int
    status: str
