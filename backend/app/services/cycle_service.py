import json
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.constants import GRADE_CONFIG
from app.models.attendance import Attendance
from app.models.class_group import ClassGroup
from app.models.cycle import Cycle
from app.models.payment import Payment
from app.models.student import Student

# Python weekday() → 요일 문자열 매핑
WEEKDAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}


def generate_schedule(
    db: Session, student_id: int, cycle_id: int, start_date: date, days_of_week: list[str], count: int = 8
) -> list[Attendance]:
    """수업반 요일 기준으로 출석 스케줄을 미리 생성한다 (기본: present)."""
    schedule_dates: list[date] = []
    current = start_date
    for _ in range(365):
        day_name = WEEKDAY_MAP[current.weekday()]
        if day_name in days_of_week:
            schedule_dates.append(current)
            if len(schedule_dates) >= count:
                break
        current += timedelta(days=1)

    records = []
    for d in schedule_dates:
        att = Attendance(
            student_id=student_id,
            cycle_id=cycle_id,
            date=d,
            status="present",
            counts_toward_cycle=True,
        )
        db.add(att)
        records.append(att)

    db.flush()
    return records


def start_cycle(db: Session, student_id: int, start_date: date) -> Cycle:
    """사이클 생성 + 8회차 스케줄 자동 생성.

    납부 확인 후 호출된다. 수업반의 days_of_week 기준으로 스케줄을 미리 만든다.
    current_count = 8 (모두 출석으로 미리 생성), status = "in_progress".
    사이클 완료는 수동으로 처리 (마지막 수업일 이후 complete_cycle 호출).
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise ValueError("학생을 찾을 수 없습니다")

    group = db.query(ClassGroup).filter(ClassGroup.id == student.class_group_id).first()
    if not group:
        raise ValueError("수업반을 찾을 수 없습니다")

    days = json.loads(group.days_of_week) if isinstance(group.days_of_week, str) else group.days_of_week

    # 사이클 번호 결정
    last_cycle = (
        db.query(Cycle)
        .filter(Cycle.student_id == student_id)
        .order_by(Cycle.cycle_number.desc())
        .first()
    )
    next_number = (last_cycle.cycle_number + 1) if last_cycle else 1

    cycle = Cycle(
        student_id=student_id,
        cycle_number=next_number,
        current_count=8,
        total_count=8,
        started_at=start_date,
    )
    db.add(cycle)
    db.flush()

    generate_schedule(db, student_id, cycle.id, start_date, days, count=8)

    return cycle


def extend_schedule(db: Session, cycle_id: int):
    """미차감 결석 시 스케줄 1회 연장. 마지막 스케줄 다음 수업 요일에 추가."""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        return

    student = db.query(Student).filter(Student.id == cycle.student_id).first()
    if not student:
        return

    group = db.query(ClassGroup).filter(ClassGroup.id == student.class_group_id).first()
    if not group:
        return

    days = json.loads(group.days_of_week) if isinstance(group.days_of_week, str) else group.days_of_week

    # 이 사이클의 마지막 스케줄 날짜
    last_att = (
        db.query(Attendance)
        .filter(Attendance.cycle_id == cycle_id)
        .order_by(Attendance.date.desc())
        .first()
    )
    if not last_att:
        return

    # 마지막 날짜 다음 날부터 다음 수업 요일 찾기
    next_dates = _find_next_class_dates(last_att.date, days, count=1)
    if not next_dates:
        return

    att = Attendance(
        student_id=cycle.student_id,
        cycle_id=cycle_id,
        date=next_dates[0],
        status="present",
        counts_toward_cycle=True,
    )
    db.add(att)
    db.flush()


def _find_next_class_dates(after_date: date, days_of_week: list[str], count: int = 1) -> list[date]:
    """지정 날짜 이후의 다음 수업 요일 날짜들을 찾는다."""
    result: list[date] = []
    current = after_date + timedelta(days=1)
    for _ in range(365):
        day_name = WEEKDAY_MAP[current.weekday()]
        if day_name in days_of_week:
            result.append(current)
            if len(result) >= count:
                break
        current += timedelta(days=1)
    return result


def recount_cycle(db: Session, cycle_id: int):
    """사이클의 현재 회차를 출석 기록 기준으로 재계산한다.

    스케줄 기반 시스템에서는 상태를 자동 변경하지 않는다.
    완료 처리는 complete_cycle()로 수동 수행.
    """
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        return

    count = db.query(Attendance).filter(
        Attendance.cycle_id == cycle_id,
        Attendance.counts_toward_cycle == True,  # noqa: E712
    ).count()

    cycle.current_count = count
    db.flush()


def complete_cycle(db: Session, cycle_id: int):
    """사이클을 수동으로 완료 처리하고 다음 사이클 수업료 Payment를 생성한다."""
    cycle = db.query(Cycle).filter(Cycle.id == cycle_id).first()
    if not cycle:
        raise ValueError("사이클을 찾을 수 없습니다")

    if cycle.current_count < cycle.total_count:
        raise ValueError("아직 회차가 완료되지 않았습니다")

    cycle.status = "completed"
    cycle.completed_at = date.today()
    _create_next_payment(db, cycle.student_id, cycle.id)
    db.flush()


def _create_next_payment(db: Session, student_id: int, cycle_id: int):
    """사이클 완료 시 다음 사이클 수업료 Payment를 자동 생성한다."""
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
