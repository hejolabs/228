from datetime import date as date_type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.constants import GRADE_CONFIG
from app.database import get_db
from app.models.cycle import Cycle
from app.models.enrollment_history import EnrollmentHistory
from app.models.student import Student
from app.services.cycle_service import start_cycle
from app.schemas.student import (
    EnrollmentHistoryResponse,
    LevelTestUpdate,
    StatusChangeRequest,
    StudentCreate,
    StudentResponse,
    StudentUpdate,
)

router = APIRouter(prefix="/api/students", tags=["students"])

# 허용되는 상태 전이
ALLOWED_TRANSITIONS = {
    "inquiry": {"level_test", "active", "stopped"},
    "level_test": {"active", "stopped"},
    "active": {"stopped"},
    "stopped": {"active"},
}


def _get_status_dates(db: Session, student_id: int) -> dict:
    """EnrollmentHistory에서 각 상태별 최초 전환 일자를 조회."""
    histories = (
        db.query(EnrollmentHistory)
        .filter(EnrollmentHistory.student_id == student_id)
        .order_by(EnrollmentHistory.changed_at.asc())
        .all()
    )
    status_date_map = {
        "inquiry": "inquiry_date",
        "level_test": "level_test_status_date",
        "active": "active_date",
        "stopped": "stopped_date",
    }
    dates: dict = {v: None for v in status_date_map.values()}
    for h in histories:
        key = status_date_map.get(h.to_status)
        if key and dates[key] is None:
            dates[key] = h.changed_at
    return dates


def _to_response(student: Student, db: Session) -> dict:
    current_cycle = None
    for c in student.cycles:
        if c.status == "in_progress":
            current_cycle = c
            break

    grade_cfg = GRADE_CONFIG.get(student.grade, {})
    effective_tuition = student.tuition_amount if student.tuition_amount is not None else grade_cfg.get("tuition", 0)

    status_dates = _get_status_dates(db, student.id)

    return {
        "id": student.id,
        "name": student.name,
        "phone": student.phone,
        "school": student.school,
        "grade": student.grade,
        "parent_phone": student.parent_phone,
        "class_group_id": student.class_group_id,
        "tuition_amount": student.tuition_amount,
        "memo": student.memo,
        "enrollment_status": student.enrollment_status,
        "level_test_date": student.level_test_date,
        "level_test_time": student.level_test_time,
        "level_test_result": student.level_test_result,
        "created_at": student.created_at,
        "updated_at": student.updated_at,
        "class_group_name": student.class_group.name if student.class_group else None,
        "current_cycle": current_cycle,
        "effective_tuition": effective_tuition,
        **status_dates,
    }


@router.get("", response_model=list[StudentResponse])
def list_students(
    class_group_id: int | None = None,
    enrollment_status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Student)
    if enrollment_status == "all":
        pass  # 전체 조회
    elif enrollment_status:
        query = query.filter(Student.enrollment_status == enrollment_status)
    else:
        # 기본: stopped 제외 (문의/레벨테스트/수업중 모두 표시)
        query = query.filter(Student.enrollment_status != "stopped")
    if class_group_id:
        query = query.filter(Student.class_group_id == class_group_id)
    students = query.order_by(Student.name).all()
    return [_to_response(s, db) for s in students]


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    return _to_response(student, db)


@router.post("", response_model=StudentResponse, status_code=201)
def create_student(data: StudentCreate, db: Session = Depends(get_db)):
    student = Student(
        name=data.name,
        phone=data.phone,
        school=data.school,
        grade=data.grade,
        parent_phone=data.parent_phone,
        class_group_id=data.class_group_id,
        tuition_amount=data.tuition_amount,
        memo=data.memo,
        enrollment_status=data.enrollment_status,
        level_test_date=data.level_test_date,
        level_test_time=data.level_test_time,
        level_test_result=data.level_test_result,
    )
    db.add(student)
    db.flush()

    # 첫 이력 기록
    history = EnrollmentHistory(
        student_id=student.id,
        from_status=None,
        to_status=data.enrollment_status,
    )
    db.add(history)
    db.commit()
    db.refresh(student)
    return _to_response(student, db)


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student or student.enrollment_status == "stopped":
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    student.name = data.name
    student.phone = data.phone
    student.school = data.school
    student.grade = data.grade
    student.parent_phone = data.parent_phone
    student.class_group_id = data.class_group_id
    student.tuition_amount = data.tuition_amount
    student.memo = data.memo
    student.level_test_date = data.level_test_date
    student.level_test_time = data.level_test_time
    student.level_test_result = data.level_test_result
    db.commit()
    db.refresh(student)
    return _to_response(student, db)


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student or student.enrollment_status == "stopped":
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    old_status = student.enrollment_status
    student.enrollment_status = "stopped"
    history = EnrollmentHistory(
        student_id=student.id,
        from_status=old_status,
        to_status="stopped",
    )
    db.add(history)
    db.commit()
    return {"message": "삭제되었습니다"}


@router.post("/{student_id}/status", response_model=StudentResponse)
def change_status(student_id: int, data: StatusChangeRequest, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")

    current = student.enrollment_status
    target = data.status
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"'{current}' → '{target}' 전이는 허용되지 않습니다",
        )

    old_status = student.enrollment_status
    student.enrollment_status = target

    history = EnrollmentHistory(
        student_id=student.id,
        from_status=old_status,
        to_status=target,
        memo=data.memo,
    )
    db.add(history)

    # active 전환 시 start_date가 있으면 사이클 자동 시작
    if target == "active" and data.start_date:
        existing = db.query(Cycle).filter(
            Cycle.student_id == student_id,
            Cycle.status == "in_progress",
        ).first()
        if not existing:
            sd = date_type.fromisoformat(data.start_date)
            start_cycle(db, student_id, sd)

    db.commit()
    db.refresh(student)
    return _to_response(student, db)


@router.put("/{student_id}/level-test", response_model=StudentResponse)
def update_level_test(student_id: int, data: LevelTestUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    student.level_test_date = data.level_test_date
    student.level_test_time = data.level_test_time
    student.level_test_result = data.level_test_result
    db.commit()
    db.refresh(student)
    return _to_response(student, db)


@router.get("/{student_id}/history", response_model=list[EnrollmentHistoryResponse])
def get_history(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    histories = (
        db.query(EnrollmentHistory)
        .filter(EnrollmentHistory.student_id == student_id)
        .order_by(EnrollmentHistory.changed_at.desc())
        .all()
    )
    return histories
