from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.constants import GRADE_CONFIG
from app.database import get_db
from app.models.cycle import Cycle
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentResponse, StudentUpdate

router = APIRouter(prefix="/api/students", tags=["students"])


def _to_response(student: Student) -> dict:
    current_cycle = None
    for c in student.cycles:
        if c.status == "in_progress":
            current_cycle = c
            break

    grade_cfg = GRADE_CONFIG.get(student.grade, {})
    effective_tuition = student.tuition_amount if student.tuition_amount is not None else grade_cfg.get("tuition", 0)

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
        "is_active": student.is_active,
        "created_at": student.created_at,
        "updated_at": student.updated_at,
        "class_group_name": student.class_group.name if student.class_group else None,
        "current_cycle": current_cycle,
        "effective_tuition": effective_tuition,
    }


@router.get("", response_model=list[StudentResponse])
def list_students(class_group_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(Student).filter(Student.is_active)
    if class_group_id:
        query = query.filter(Student.class_group_id == class_group_id)
    students = query.order_by(Student.name).all()
    return [_to_response(s) for s in students]


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id, Student.is_active).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    return _to_response(student)


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
    )
    db.add(student)
    db.flush()  # student.id 확보

    cycle = Cycle(student_id=student.id, cycle_number=1)
    db.add(cycle)
    db.commit()
    db.refresh(student)
    return _to_response(student)


@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id, Student.is_active).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    student.name = data.name
    student.phone = data.phone
    student.school = data.school
    student.grade = data.grade
    student.parent_phone = data.parent_phone
    student.class_group_id = data.class_group_id
    student.tuition_amount = data.tuition_amount
    student.memo = data.memo
    db.commit()
    db.refresh(student)
    return _to_response(student)


@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_id, Student.is_active).first()
    if not student:
        raise HTTPException(status_code=404, detail="학생을 찾을 수 없습니다")
    student.is_active = False
    db.commit()
    return {"message": "삭제되었습니다"}
