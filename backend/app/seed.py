import json
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.class_group import ClassGroup
from app.models.enrollment_history import EnrollmentHistory
from app.models.student import Student
from app.services.cycle_service import start_cycle

# Python weekday() → 요일 문자열 매핑
WEEKDAY_MAP = {0: "mon", 1: "tue", 2: "wed", 3: "thu", 4: "fri", 5: "sat", 6: "sun"}

SEED_CLASS_GROUPS = [
    {"name": "월수반A", "days_of_week": ["mon", "wed"], "start_time": "14:30", "default_duration_minutes": 90, "memo": "사실상 초등 전용"},
    {"name": "월수반B", "days_of_week": ["mon", "wed"], "start_time": "16:30", "default_duration_minutes": 120, "memo": "초등/중등 혼용"},
    {"name": "화목반A", "days_of_week": ["tue", "thu"], "start_time": "14:30", "default_duration_minutes": 90, "memo": "사실상 초등 전용"},
    {"name": "화목반B", "days_of_week": ["tue", "thu"], "start_time": "16:30", "default_duration_minutes": 120, "memo": "중등"},
    {"name": "화목반C", "days_of_week": ["tue", "thu"], "start_time": "20:00", "default_duration_minutes": 120, "memo": "중등 전용"},
]

SEED_STUDENTS = [
    {"name": "김서연", "phone": "010-1234-5678", "school": "서울초", "grade": "elementary", "parent_phone": "010-9876-5432", "class_group": "월수반A", "enrollment_status": "active"},
    {"name": "이준호", "phone": "010-2345-6789", "school": "서울초", "grade": "elementary", "parent_phone": "010-8765-4321", "class_group": "월수반A", "enrollment_status": "active"},
    {"name": "박지민", "phone": "010-3456-7890", "school": "강남중", "grade": "middle1", "parent_phone": "010-7654-3210", "class_group": "월수반B", "enrollment_status": "active"},
    {"name": "최유진", "phone": "010-4567-8901", "school": "강남중", "grade": "middle2", "parent_phone": "010-6543-2109", "class_group": "화목반B", "enrollment_status": "active"},
    {"name": "정하은", "phone": "010-5678-9012", "school": "서초고", "grade": "high", "parent_phone": "010-5432-1098", "class_group": "화목반C", "enrollment_status": "active"},
    {"name": "강민수", "phone": "010-6789-0123", "school": "서울초", "grade": "elementary", "parent_phone": "010-4321-0987", "class_group": "화목반A", "enrollment_status": "inquiry"},
    {"name": "윤소희", "phone": "010-7890-1234", "school": "강남중", "grade": "middle1", "parent_phone": "010-3210-9876", "class_group": "월수반B", "enrollment_status": "level_test", "level_test_date": "2026-03-05", "level_test_time": "15:00"},
]


def _find_cycle_start_date(days_of_week: list[str]) -> date:
    """오늘 기준으로 가장 최근 과거/오늘의 수업 요일을 찾아 시작일로 반환."""
    today = date.today()
    # 오늘부터 7일 전까지 역순 탐색
    for i in range(7):
        d = today - timedelta(days=i)
        if WEEKDAY_MAP[d.weekday()] in days_of_week:
            return d
    # fallback: 오늘
    return today


def seed_class_groups(db: Session):
    if db.query(ClassGroup).count() > 0:
        return
    for data in SEED_CLASS_GROUPS:
        group = ClassGroup(
            name=data["name"],
            days_of_week=json.dumps(data["days_of_week"]),
            start_time=data["start_time"],
            default_duration_minutes=data["default_duration_minutes"],
            memo=data["memo"],
        )
        db.add(group)
    db.flush()

    # 학생 시드 데이터
    if db.query(Student).count() > 0:
        db.commit()
        return

    group_map = {g.name: g for g in db.query(ClassGroup).all()}
    for data in SEED_STUDENTS:
        group = group_map[data["class_group"]]
        student = Student(
            name=data["name"],
            phone=data["phone"],
            school=data["school"],
            grade=data["grade"],
            parent_phone=data["parent_phone"],
            class_group_id=group.id,
            enrollment_status=data["enrollment_status"],
            level_test_date=data.get("level_test_date"),
            level_test_time=data.get("level_test_time"),
        )
        db.add(student)
        db.flush()

        # 이력 기록
        history = EnrollmentHistory(
            student_id=student.id,
            from_status=None,
            to_status=data["enrollment_status"],
        )
        db.add(history)

        # active 학생 → 사이클 + 8회차 출석 스케줄 생성
        if data["enrollment_status"] == "active":
            days = json.loads(group.days_of_week) if isinstance(group.days_of_week, str) else group.days_of_week
            cycle_start = _find_cycle_start_date(days)
            start_cycle(db, student.id, cycle_start)

    db.commit()
