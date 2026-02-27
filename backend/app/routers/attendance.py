import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.attendance import Attendance
from app.models.class_group import ClassGroup
from app.models.cycle import Cycle
from app.models.student import Student
from app.schemas.attendance import (
    AttendanceCreate,
    AttendanceResponse,
    AttendanceUpdate,
    BulkAttendanceCreate,
    CycleAlertResponse,
)
from app.services.cycle_service import create_new_cycle, process_attendance, recount_cycle

router = APIRouter(prefix="/api", tags=["attendance"])


def _get_active_cycle(db: Session, student_id: int) -> Cycle:
    cycle = (
        db.query(Cycle)
        .filter(Cycle.student_id == student_id, Cycle.status == "in_progress")
        .first()
    )
    if not cycle:
        raise HTTPException(status_code=400, detail="진행 중인 사이클이 없습니다")
    return cycle


def _to_response(att: Attendance, db: Session) -> dict:
    cycle = db.query(Cycle).filter(Cycle.id == att.cycle_id).first()
    if cycle:
        db.refresh(cycle)
    student = db.query(Student).filter(Student.id == att.student_id).first()
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
        "current_count": cycle.current_count if cycle else 0,
        "total_count": cycle.total_count if cycle else 8,
    }


# --- 출석 CRUD ---

@router.post("/attendance", response_model=AttendanceResponse, status_code=201)
def create_attendance(data: AttendanceCreate, db: Session = Depends(get_db)):
    cycle = _get_active_cycle(db, data.student_id)

    att = Attendance(
        student_id=data.student_id,
        cycle_id=cycle.id,
        date=data.date,
        status=data.status,
        counts_toward_cycle=data.counts_toward_cycle,
        excuse_reason=data.excuse_reason,
        memo=data.memo,
    )
    db.add(att)
    db.flush()

    process_attendance(db, att)
    db.commit()
    db.refresh(att)
    return _to_response(att, db)


@router.post("/attendance/bulk", response_model=list[AttendanceResponse])
def bulk_create_attendance(data: BulkAttendanceCreate, db: Session = Depends(get_db)):
    results = []
    for item in data.items:
        cycle = _get_active_cycle(db, item.student_id)

        existing = db.query(Attendance).filter(
            Attendance.student_id == item.student_id,
            Attendance.date == data.date,
        ).first()
        if existing:
            continue

        att = Attendance(
            student_id=item.student_id,
            cycle_id=cycle.id,
            date=data.date,
            status=item.status,
            counts_toward_cycle=item.counts_toward_cycle,
            excuse_reason=item.excuse_reason,
        )
        db.add(att)
        db.flush()
        process_attendance(db, att)
        results.append(att)

    db.commit()
    return [_to_response(a, db) for a in results]


@router.get("/attendance/daily/{date}", response_model=list[AttendanceResponse])
def get_daily_attendance(date: str, class_group_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Attendance).filter(Attendance.date == date)
    if class_group_id:
        student_ids = [
            s.id for s in
            db.query(Student).filter(Student.class_group_id == class_group_id, Student.is_active).all()
        ]
        query = query.filter(Attendance.student_id.in_(student_ids))
    records = query.all()
    return [_to_response(a, db) for a in records]


@router.put("/attendance/{att_id}", response_model=AttendanceResponse)
def update_attendance(att_id: int, data: AttendanceUpdate, db: Session = Depends(get_db)):
    att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="출석 기록을 찾을 수 없습니다")

    att.status = data.status
    att.counts_toward_cycle = data.counts_toward_cycle
    att.excuse_reason = data.excuse_reason
    att.memo = data.memo
    db.flush()

    recount_cycle(db, att.cycle_id)
    db.commit()
    db.refresh(att)
    return _to_response(att, db)


@router.delete("/attendance/{att_id}")
def delete_attendance(att_id: int, db: Session = Depends(get_db)):
    att = db.query(Attendance).filter(Attendance.id == att_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="출석 기록을 찾을 수 없습니다")
    cycle_id = att.cycle_id
    db.delete(att)
    db.flush()
    recount_cycle(db, cycle_id)
    db.commit()
    return {"message": "삭제되었습니다"}


# --- 사이클 알림 ---

@router.get("/cycles/alerts", response_model=list[CycleAlertResponse])
def get_cycle_alerts(db: Session = Depends(get_db)):
    """7회차 이상 도달했거나 완료된 사이클 목록"""
    cycles = (
        db.query(Cycle)
        .filter(Cycle.current_count >= 7)
        .order_by(Cycle.current_count.desc())
        .all()
    )
    results = []
    for c in cycles:
        student = db.query(Student).filter(Student.id == c.student_id).first()
        if not student or not student.is_active:
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


# --- 새 사이클 ---

@router.post("/cycles/{cycle_id}/new-cycle")
def start_new_cycle(cycle_id: int, db: Session = Depends(get_db)):
    old_cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not old_cycle:
        raise HTTPException(status_code=404, detail="사이클을 찾을 수 없습니다")
    if old_cycle.status != "completed":
        raise HTTPException(status_code=400, detail="완료된 사이클만 새 사이클을 시작할 수 있습니다")

    new_cycle = create_new_cycle(db, old_cycle.student_id)
    db.commit()
    return {
        "message": "새 사이클이 시작되었습니다",
        "cycle_id": new_cycle.id,
        "cycle_number": new_cycle.cycle_number,
    }
