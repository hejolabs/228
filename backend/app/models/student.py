from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(20), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    school: Mapped[str] = mapped_column(String(50), nullable=False)
    grade: Mapped[str] = mapped_column(String(10), nullable=False)  # elementary/middle1/middle2/middle3/high
    parent_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    class_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("class_groups.id"), nullable=False)
    tuition_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL이면 학년 기본값
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    class_group = relationship("ClassGroup")
    cycles = relationship("Cycle", back_populates="student")
