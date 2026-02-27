"""테스트 공통 설정.

- StaticPool로 메모리 DB 단일 연결 공유 (스레드 간 테이블 공유)
- 각 테스트마다 DB를 새로 만들어서 테스트 간 간섭 없음
- client fixture로 API 호출 가능
"""
import os

os.environ["TESTING"] = "1"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# StaticPool: 모든 스레드가 같은 메모리 DB 연결을 공유
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    """각 테스트마다 깨끗한 DB를 제공."""
    Base.metadata.create_all(bind=engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db):
    """FastAPI TestClient - 실제 서버 없이 API 호출 가능."""
    def _override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def seed_class_group(client):
    """테스트용 수업반 1개 생성."""
    res = client.post("/api/class-groups", json={
        "name": "테스트반",
        "days_of_week": ["mon", "wed"],
        "start_time": "14:30",
        "default_duration_minutes": 90,
    })
    return res.json()


@pytest.fixture()
def seed_student(client, seed_class_group):
    """테스트용 학생 1명 생성 (사이클 자동 생성됨)."""
    res = client.post("/api/students", json={
        "name": "김테스트",
        "phone": "010-1111-2222",
        "school": "서울초",
        "grade": "elementary",
        "parent_phone": "010-3333-4444",
        "class_group_id": seed_class_group["id"],
    })
    return res.json()
