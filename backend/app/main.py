from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.constants import GRADE_CONFIG
from app.database import Base, SessionLocal, engine
from app.routers import class_groups, students
from app.seed import seed_class_groups

# 모델 import (create_all에서 테이블 생성을 위해 필요)
import app.models.student  # noqa: F401
import app.models.cycle  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_class_groups(db)
    finally:
        db.close()
    yield


app = FastAPI(title="수학공부방 관리 시스템", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(class_groups.router)
app.include_router(students.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/grades")
def get_grades():
    return GRADE_CONFIG
