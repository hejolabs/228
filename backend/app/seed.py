import json

from sqlalchemy.orm import Session

from app.models.class_group import ClassGroup
from app.models.enrollment_history import EnrollmentHistory
from app.models.student import Student


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
    {"name": "윤소희", "phone": "010-7890-1234", "school": "강남중", "grade": "middle1", "parent_phone": "010-3210-9876", "class_group": "월수반B", "enrollment_status": "level_test"},
]


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

    group_map = {g.name: g.id for g in db.query(ClassGroup).all()}
    for data in SEED_STUDENTS:
        student = Student(
            name=data["name"],
            phone=data["phone"],
            school=data["school"],
            grade=data["grade"],
            parent_phone=data["parent_phone"],
            class_group_id=group_map[data["class_group"]],
            enrollment_status=data["enrollment_status"],
        )
        db.add(student)
        db.flush()
        history = EnrollmentHistory(
            student_id=student.id,
            from_status=None,
            to_status=data["enrollment_status"],
        )
        db.add(history)

    db.commit()
