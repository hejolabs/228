import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.class_group import ClassGroup
from app.schemas.class_group import ClassGroupCreate, ClassGroupResponse, ClassGroupUpdate

router = APIRouter(prefix="/api/class-groups", tags=["class-groups"])


@router.get("", response_model=list[ClassGroupResponse])
def list_class_groups(db: Session = Depends(get_db)):
    groups = db.query(ClassGroup).filter(ClassGroup.is_active).order_by(ClassGroup.start_time).all()
    for g in groups:
        g.days_of_week = json.loads(g.days_of_week)
    return groups


@router.get("/{group_id}", response_model=ClassGroupResponse)
def get_class_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(ClassGroup).filter(ClassGroup.id == group_id, ClassGroup.is_active).first()
    if not group:
        raise HTTPException(status_code=404, detail="수업반을 찾을 수 없습니다")
    group.days_of_week = json.loads(group.days_of_week)
    return group


@router.post("", response_model=ClassGroupResponse, status_code=201)
def create_class_group(data: ClassGroupCreate, db: Session = Depends(get_db)):
    group = ClassGroup(
        name=data.name,
        days_of_week=json.dumps(data.days_of_week),
        start_time=data.start_time,
        default_duration_minutes=data.default_duration_minutes,
        memo=data.memo,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    group.days_of_week = json.loads(group.days_of_week)
    return group


@router.put("/{group_id}", response_model=ClassGroupResponse)
def update_class_group(group_id: int, data: ClassGroupUpdate, db: Session = Depends(get_db)):
    group = db.query(ClassGroup).filter(ClassGroup.id == group_id, ClassGroup.is_active).first()
    if not group:
        raise HTTPException(status_code=404, detail="수업반을 찾을 수 없습니다")
    group.name = data.name
    group.days_of_week = json.dumps(data.days_of_week)
    group.start_time = data.start_time
    group.default_duration_minutes = data.default_duration_minutes
    group.memo = data.memo
    db.commit()
    db.refresh(group)
    group.days_of_week = json.loads(group.days_of_week)
    return group


@router.delete("/{group_id}")
def delete_class_group(group_id: int, db: Session = Depends(get_db)):
    group = db.query(ClassGroup).filter(ClassGroup.id == group_id, ClassGroup.is_active).first()
    if not group:
        raise HTTPException(status_code=404, detail="수업반을 찾을 수 없습니다")
    group.is_active = False
    db.commit()
    return {"message": "삭제되었습니다"}
