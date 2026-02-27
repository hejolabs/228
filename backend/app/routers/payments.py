from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.constants import GRADE_CONFIG
from app.database import get_db
from app.models.class_group import ClassGroup
from app.models.cycle import Cycle
from app.models.payment import Payment
from app.models.student import Student
from app.schemas.payment import MessageResponse, PaymentConfirm, PaymentResponse

router = APIRouter(prefix="/api/payments", tags=["payments"])


def _to_response(p: Payment, db: Session) -> dict:
    student = db.query(Student).filter(Student.id == p.student_id).first()
    cycle = db.query(Cycle).filter(Cycle.id == p.cycle_id).first()
    group = None
    if student:
        group = db.query(ClassGroup).filter(ClassGroup.id == student.class_group_id).first()
    return {
        "id": p.id,
        "student_id": p.student_id,
        "cycle_id": p.cycle_id,
        "amount": p.amount,
        "payment_method": p.payment_method,
        "status": p.status,
        "message_sent": p.message_sent,
        "message_sent_at": p.message_sent_at,
        "paid_at": p.paid_at,
        "memo": p.memo,
        "created_at": p.created_at,
        "student_name": student.name if student else None,
        "class_group_name": group.name if group else None,
        "cycle_number": cycle.cycle_number if cycle else 0,
    }


@router.get("", response_model=list[PaymentResponse])
def list_payments(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Payment)
    if status:
        query = query.filter(Payment.status == status)
    payments = query.order_by(Payment.created_at.desc()).all()
    return [_to_response(p, db) for p in payments]


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="수업료 정보를 찾을 수 없습니다")
    return _to_response(payment, db)


@router.post("/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(payment_id: int, data: PaymentConfirm, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="수업료 정보를 찾을 수 없습니다")
    if payment.status == "paid":
        raise HTTPException(status_code=400, detail="이미 납부 완료된 건입니다")

    payment.status = "paid"
    payment.payment_method = data.payment_method
    payment.paid_at = datetime.now()
    payment.memo = data.memo
    db.commit()
    db.refresh(payment)
    return _to_response(payment, db)


@router.post("/{payment_id}/message", response_model=MessageResponse)
def generate_message(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="수업료 정보를 찾을 수 없습니다")

    student = db.query(Student).filter(Student.id == payment.student_id).first()
    cycle = db.query(Cycle).filter(Cycle.id == payment.cycle_id).first()
    grade_cfg = GRADE_CONFIG.get(student.grade, {}) if student else {}

    student_name = student.name if student else "학생"
    grade_label = grade_cfg.get("label", "")
    cycle_number = cycle.cycle_number if cycle else 0
    amount_str = f"{payment.amount:,}"

    message = (
        f"안녕하세요, 수학공부방입니다.\n"
        f"\n"
        f"{student_name} 학생({grade_label})의\n"
        f"{cycle_number}회차 수업(8회)이 완료되었습니다.\n"
        f"\n"
        f"수업료: {amount_str}원\n"
        f"\n"
        f"입금 확인 후 다음 회차 수업이 시작됩니다.\n"
        f"감사합니다."
    )

    payment.message_sent = True
    payment.message_sent_at = datetime.now()
    db.commit()

    return {"payment_id": payment.id, "message": message}
