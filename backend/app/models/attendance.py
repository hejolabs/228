from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    cycle_id: Mapped[int] = mapped_column(Integer, ForeignKey("cycles.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # present/late/early_leave/absent/absent_excused
    counts_toward_cycle: Mapped[bool] = mapped_column(Boolean, default=True)
    excuse_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)  # school_event/sick_leave/class_cancelled
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    student = relationship("Student")
    cycle = relationship("Cycle")
