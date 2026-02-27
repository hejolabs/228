import json

from sqlalchemy.orm import Session

from app.models.class_group import ClassGroup


SEED_CLASS_GROUPS = [
    {"name": "월수반A", "days_of_week": ["mon", "wed"], "start_time": "14:30", "default_duration_minutes": 90, "memo": "사실상 초등 전용"},
    {"name": "월수반B", "days_of_week": ["mon", "wed"], "start_time": "16:30", "default_duration_minutes": 120, "memo": "초등/중등 혼용"},
    {"name": "화목반A", "days_of_week": ["tue", "thu"], "start_time": "14:30", "default_duration_minutes": 90, "memo": "사실상 초등 전용"},
    {"name": "화목반B", "days_of_week": ["tue", "thu"], "start_time": "16:30", "default_duration_minutes": 120, "memo": "중등"},
    {"name": "화목반C", "days_of_week": ["tue", "thu"], "start_time": "20:00", "default_duration_minutes": 120, "memo": "중등 전용"},
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
    db.commit()
