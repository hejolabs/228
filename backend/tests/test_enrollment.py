"""Phase 5.2/5.3: 수업등록 관리 - 레벨테스트/상태별 일자/사이클 자동시작 테스트."""

import pytest

from app.models.attendance import Attendance


@pytest.fixture()
def class_group(client):
    return client.post("/api/class-groups", json={
        "name": "테스트반",
        "days_of_week": ["mon", "wed"],
        "start_time": "14:30",
        "default_duration_minutes": 90,
    }).json()


STUDENT_BASE = {
    "name": "김학생",
    "phone": "010-1111-2222",
    "school": "서울초",
    "grade": "elementary",
    "parent_phone": "010-3333-4444",
}


class TestLevelTest:
    """레벨테스트 일정/결과 관리."""

    def test_create_with_level_test_info(self, client, class_group):
        """등록 시 레벨테스트 정보 포함 가능."""
        res = client.post("/api/students", json={
            **STUDENT_BASE,
            "class_group_id": class_group["id"],
            "enrollment_status": "level_test",
            "level_test_date": "2026-03-01",
            "level_test_time": "14:00",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["level_test_date"] == "2026-03-01"
        assert data["level_test_time"] == "14:00"
        assert data["level_test_result"] is None

    def test_update_level_test(self, client, class_group):
        """PUT /level-test로 레벨테스트 정보 업데이트."""
        student = client.post("/api/students", json={
            **STUDENT_BASE,
            "class_group_id": class_group["id"],
            "enrollment_status": "level_test",
        }).json()

        res = client.put(f"/api/students/{student['id']}/level-test", json={
            "level_test_date": "2026-03-05",
            "level_test_time": "15:30",
            "level_test_result": "중1 수준, 분수 보충 필요",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["level_test_date"] == "2026-03-05"
        assert data["level_test_time"] == "15:30"
        assert data["level_test_result"] == "중1 수준, 분수 보충 필요"

    def test_update_level_test_not_found(self, client):
        """존재하지 않는 학생 → 404."""
        res = client.put("/api/students/999/level-test", json={
            "level_test_date": "2026-03-05",
        })
        assert res.status_code == 404


class TestStatusDates:
    """상태별 일자 계산."""

    def test_inquiry_date_on_create(self, client, class_group):
        """등록 시 inquiry_date 자동 설정."""
        res = client.post("/api/students", json={
            **STUDENT_BASE,
            "class_group_id": class_group["id"],
        })
        data = res.json()
        assert data["inquiry_date"] is not None
        assert data["level_test_status_date"] is None
        assert data["active_date"] is None
        assert data["stopped_date"] is None

    def test_status_dates_after_transitions(self, client, class_group):
        """상태 전환 시 각 일자가 기록됨."""
        student = client.post("/api/students", json={
            **STUDENT_BASE,
            "class_group_id": class_group["id"],
        }).json()
        sid = student["id"]

        # inquiry → level_test
        res = client.post(f"/api/students/{sid}/status", json={
            "status": "level_test", "memo": "레벨테스트 예약",
        })
        data = res.json()
        assert data["inquiry_date"] is not None
        assert data["level_test_status_date"] is not None
        assert data["active_date"] is None

        # level_test → active
        res = client.post(f"/api/students/{sid}/status", json={
            "status": "active", "memo": "수업 시작",
        })
        data = res.json()
        assert data["active_date"] is not None

        # active → stopped
        res = client.post(f"/api/students/{sid}/status", json={
            "status": "stopped", "memo": "개인 사유",
        })
        data = res.json()
        assert data["stopped_date"] is not None

    def test_all_status_filter(self, client, class_group):
        """enrollment_status=all로 전체 학생 조회."""
        # inquiry 학생
        client.post("/api/students", json={
            **STUDENT_BASE, "name": "문의학생",
            "class_group_id": class_group["id"],
        })
        # active 학생
        student2 = client.post("/api/students", json={
            **STUDENT_BASE, "name": "수업학생",
            "class_group_id": class_group["id"],
            "enrollment_status": "active",
        }).json()
        # stopped 학생
        client.post(f"/api/students/{student2['id']}/status", json={
            "status": "stopped",
        })

        # all 필터
        all_students = client.get("/api/students?enrollment_status=all").json()
        assert len(all_students) == 2

        # 기본 조회 (stopped 제외)
        default = client.get("/api/students").json()
        assert len(default) == 1
        assert default[0]["name"] == "문의학생"


class TestStatusChangeWithCycle:
    """Phase 5.3: 상태 변경 시 사이클 자동 시작."""

    def test_active_with_start_date_creates_cycle(self, client, db, class_group):
        """active 전환 + start_date → 사이클 + 출석 스케줄 자동 생성."""
        student = client.post("/api/students", json={
            **STUDENT_BASE,
            "class_group_id": class_group["id"],
            "enrollment_status": "level_test",
        }).json()

        res = client.post(f"/api/students/{student['id']}/status", json={
            "status": "active",
            "start_date": "2026-03-02",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["enrollment_status"] == "active"
        assert data["current_cycle"] is not None
        assert data["current_cycle"]["total_count"] == 8

        # DB에서 출석 스케줄 확인
        att_count = db.query(Attendance).filter(
            Attendance.student_id == student["id"],
        ).count()
        assert att_count == 8

    def test_active_without_start_date_no_cycle(self, client, class_group):
        """active 전환 + start_date 없음 → 사이클 미생성."""
        student = client.post("/api/students", json={
            **STUDENT_BASE,
            "class_group_id": class_group["id"],
        }).json()

        res = client.post(f"/api/students/{student['id']}/status", json={
            "status": "active",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["current_cycle"] is None

    def test_re_enrollment_with_start_date(self, client, class_group):
        """stopped → active 재등록 + start_date → 새 사이클 생성."""
        student = client.post("/api/students", json={
            **STUDENT_BASE,
            "class_group_id": class_group["id"],
            "enrollment_status": "active",
        }).json()

        # active → stopped
        client.post(f"/api/students/{student['id']}/status", json={
            "status": "stopped",
        })

        # stopped → active (재등록)
        res = client.post(f"/api/students/{student['id']}/status", json={
            "status": "active",
            "start_date": "2026-03-09",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["current_cycle"] is not None
