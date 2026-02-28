import json
from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.attendance import Attendance
from app.models.class_group import ClassGroup
from app.models.cycle import Cycle
from app.models.payment import Payment
from app.models.student import Student
from app.schemas.attendance import (
    AttendanceResponse,
    AttendanceUpdate,
    CycleAlertResponse,
)
from app.services.cycle_service import (
    complete_cycle,
    extend_schedule,
    recount_cycle,
    start_cycle,
)

router = APIRouter(prefix="/api", tags=["attendance"])


def _to_response(att: Attendance, db: Session) -> dict:
    cycle = db.query(Cycle).filter(Cycle.id == att.cycle_id).first()
    if cycle:
        db.refresh(cycle)
    student = db.query(Student).filter(Student.id == att.student_id).first()
    class_group = student.class_group if student else None
    return {
        "id": att.id,
        "student_id": att.student_id,
        "cycle_id": att.cycle_id,
        "date": att.date,
        "status": att.status,
        "counts_toward_cycle": att.counts_toward_cycle,
        "excuse_reason": att.excuse_reason,
        "memo": att.memo,
        "created_at": att.created_at,
        "student_name": student.name if student else None,
        "class_group_name": class_group.name if class_group else None,
        "start_time": class_group.start_time if class_group else None,
        "current_count": cycle.current_count if cycle else 0,
        "total_count": cycle.total_count if cycle else 8,
    }


# --- 출석 조회/수정 (스케줄 기반) ---

@router.get("/attendance/daily/{date}", response_model=list[AttendanceResponse])
def get_daily_attendance(date: str, class_group_id: int | None = None, db: Session = Depends(get_db)):
    """해당 날짜에 스케줄이 있는 출석 기록 조회."""
    query = db.query(Attendance).filter(Attendance.date == date)
    if class_group_id:
        student_ids = [
            s.id for s in
            db.query(Student).filter(
                Student.class_group_id == class_group_id,
                Student.enrollment_status == "active",
            ).all()
        ]
        query = query.filter(Attendance.student_id.in_(student_ids))
    records = query.all()
    return [_to_response(a, db) for a in records]


@router.put("/attendance/{att_id}", response_model=AttendanceResponse)
def update_attendance(att_id: int, data: AttendanceUpdate, db: Session = Depends(get_db)):
    """출석 상태 변경. 미차감 결석 시 스케줄 1회 연장."""
    att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="출석 기록을 찾을 수 없습니다")

    was_counting = att.counts_toward_cycle
    att.status = data.status
    att.counts_toward_cycle = data.counts_toward_cycle
    att.excuse_reason = data.excuse_reason
    att.memo = data.memo
    db.flush()

    # 미차감으로 변경된 경우 → 스케줄 1회 연장
    if was_counting and not data.counts_toward_cycle:
        extend_schedule(db, att.cycle_id)

    recount_cycle(db, att.cycle_id)
    db.commit()
    db.refresh(att)
    return _to_response(att, db)


# --- 사이클 알림 ---

@router.get("/cycles/alerts", response_model=list[CycleAlertResponse])
def get_cycle_alerts(db: Session = Depends(get_db)):
    """완료된 사이클 목록 (다음 사이클 시작 대기)"""
    cycles = (
        db.query(Cycle)
        .filter(Cycle.status == "completed")
        .order_by(Cycle.completed_at.desc())
        .all()
    )
    results = []
    for c in cycles:
        student = db.query(Student).filter(Student.id == c.student_id).first()
        if not student or student.enrollment_status != "active":
            continue
        group = db.query(ClassGroup).filter(ClassGroup.id == student.class_group_id).first()
        results.append({
            "student_id": student.id,
            "student_name": student.name,
            "class_group_name": group.name if group else "",
            "cycle_id": c.id,
            "cycle_number": c.cycle_number,
            "current_count": c.current_count,
            "total_count": c.total_count,
            "status": c.status,
        })
    return results


# --- 사이클 완료 (수동) ---

@router.post("/cycles/{cycle_id}/complete")
def complete_cycle_endpoint(cycle_id: int, db: Session = Depends(get_db)):
    """사이클 수동 완료. 마지막 수업일 이후 클릭. 다음 사이클 Payment 자동 생성."""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise HTTPException(status_code=404, detail="사이클을 찾을 수 없습니다")
    if cycle.status == "completed":
        raise HTTPException(status_code=400, detail="이미 완료된 사이클입니다")

    try:
        complete_cycle(db, cycle_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    return {"message": "사이클이 완료되었습니다", "cycle_id": cycle_id}


# --- 사이클 시작 (납부 확인 후) ---

class StartCycleRequest(BaseModel):
    start_date: str  # "2026-02-02"


@router.post("/cycles/{cycle_id}/start-next")
def start_next_cycle(cycle_id: int, data: StartCycleRequest, db: Session = Depends(get_db)):
    """기존 학생: 이전 사이클 완료 + 납부 확인 후 다음 사이클 시작."""
    old_cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not old_cycle:
        raise HTTPException(status_code=404, detail="사이클을 찾을 수 없습니다")
    if old_cycle.status != "completed":
        raise HTTPException(status_code=400, detail="완료된 사이클만 다음 사이클을 시작할 수 있습니다")

    # 납부 확인 체크
    payment = db.query(Payment).filter(
        Payment.cycle_id == cycle_id,
        Payment.student_id == old_cycle.student_id,
    ).first()
    if not payment or payment.status != "paid":
        raise HTTPException(status_code=400, detail="수업료 납부를 먼저 확인해주세요")

    sd = date_type.fromisoformat(data.start_date)
    new_cycle = start_cycle(db, old_cycle.student_id, sd)

    db.commit()
    return {
        "message": "새 사이클이 시작되었습니다",
        "cycle_id": new_cycle.id,
        "cycle_number": new_cycle.cycle_number,
    }


@router.post("/students/{student_id}/start-cycle")
def start_first_cycle(student_id: int, data: StartCycleRequest, db: Session = Depends(get_db)):
    """신규 학생: 첫 사이클 시작 (납부 확인 후)."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    if student.enrollment_status != "active":
        raise HTTPException(status_code=400, detail="수업중 상태인 학생만 사이클을 시작할 수 있습니다")

    # 이미 진행 중인 사이클이 있는지 확인
    existing = db.query(Cycle).filter(
        Cycle.student_id == student_id,
        Cycle.status == "in_progress",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="이미 진행 중인 사이클이 있습니다")

    sd = date_type.fromisoformat(data.start_date)
    new_cycle = start_cycle(db, student_id, sd)

    db.commit()
    return {
        "message": "첫 사이클이 시작되었습니다",
        "cycle_id": new_cycle.id,
        "cycle_number": new_cycle.cycle_number,
    }
