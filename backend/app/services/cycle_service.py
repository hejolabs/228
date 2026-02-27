from datetime import date

from sqlalchemy.orm import Session

from app.constants import GRADE_CONFIG
from app.models.attendance import Attendance
from app.models.cycle import Cycle
from app.models.payment import Payment
from app.models.student import Student


def process_attendance(db: Session, attendance: Attendance) -> dict:
    """출석 기록 후 사이클 회차를 처리한다.

    Returns:
        dict with keys: cycle_completed (bool), current_count, total_count
    """
    result = {"cycle_completed": False, "current_count": 0, "total_count": 8}

    if not attendance.counts_toward_cycle:
        cycle = db.query(Cycle).filter(Cycle.id == attendance.cycle_id).first()
        if cycle:
            result["current_count"] = cycle.current_count
            result["total_count"] = cycle.total_count
        return result

    cycle = db.query(Cycle).filter(Cycle.id == attendance.cycle_id).first()
    if not cycle:
        return result

    cycle.current_count += 1
    result["current_count"] = cycle.current_count
    result["total_count"] = cycle.total_count

    if cycle.current_count >= cycle.total_count:
        cycle.status = "completed"
        cycle.completed_at = date.today()
        result["cycle_completed"] = True
        _create_payment(db, attendance.student_id, cycle.id)

    db.flush()
    return result


def _create_payment(db: Session, student_id: int, cycle_id: int):
    """사이클 완료 시 미납 Payment를 자동 생성한다."""
    existing = db.query(Payment).filter(
        Payment.student_id == student_id,
        Payment.cycle_id == cycle_id,
    ).first()
    if existing:
        return

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        return

    grade_cfg = GRADE_CONFIG.get(student.grade, {})
    amount = student.tuition_amount if student.tuition_amount is not None else grade_cfg.get("tuition", 0)

    payment = Payment(
        student_id=student_id,
        cycle_id=cycle_id,
        amount=amount,
    )
    db.add(payment)


def recount_cycle(db: Session, cycle_id: int):
    """사이클의 현재 회차를 출석 기록 기준으로 재계산한다."""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        return

    count = db.query(Attendance).filter(
        Attendance.cycle_id == cycle_id,
        Attendance.counts_toward_cycle == True,  # noqa: E712
    ).count()

    cycle.current_count = count

    if count >= cycle.total_count:
        cycle.status = "completed"
        if not cycle.completed_at:
            cycle.completed_at = date.today()
    else:
        cycle.status = "in_progress"
        cycle.completed_at = None

    db.flush()


def create_new_cycle(db: Session, student_id: int) -> Cycle:
    """학생의 새 사이클을 생성한다."""
    last_cycle = (
        db.query(Cycle)
        .filter(Cycle.student_id == student_id)
        .order_by(Cycle.cycle_number.desc())
        .first()
    )
    next_number = (last_cycle.cycle_number + 1) if last_cycle else 1

    cycle = Cycle(student_id=student_id, cycle_number=next_number)
    db.add(cycle)
    db.flush()
    return cycle
