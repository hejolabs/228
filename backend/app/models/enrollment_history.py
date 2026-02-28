from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class EnrollmentHistory(Base):
    __tablename__ = "enrollment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 첫 등록 시 NULL
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)

    student = relationship("Student")
