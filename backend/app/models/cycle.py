from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Cycle(Base):
    __tablename__ = "cycles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(Integer, ForeignKey("students.id"), nullable=False)
    cycle_number: Mapped[int] = mapped_column(Integer, nullable=False)  # N번째 사이클
    current_count: Mapped[int] = mapped_column(Integer, default=0)  # 현재 회차 (0~8)
    total_count: Mapped[int] = mapped_column(Integer, default=8)
    status: Mapped[str] = mapped_column(String(20), default="in_progress")  # in_progress / completed
    started_at: Mapped[date] = mapped_column(Date, default=date.today)
    completed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    student = relationship("Student", back_populates="cycles")
