"""Phase 3: 학생 관리 CRUD 테스트."""

import pytest


@pytest.fixture()
def class_group(client):
    """테스트용 수업반."""
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


class TestStudentCreate:
    """학생 등록 테스트."""

    def test_create_student_with_auto_cycle(self, client, class_group):
        """등록 시 첫 사이클(1번째, 0/8) 자동 생성."""
        res = client.post("/api/students", json={
            **STUDENT_BASE, "class_group_id": class_group["id"],
        })

        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "김학생"
        assert data["current_cycle"] is not None
        assert data["current_cycle"]["cycle_number"] == 1
        assert data["current_cycle"]["current_count"] == 0
        assert data["current_cycle"]["total_count"] == 8
        assert data["current_cycle"]["status"] == "in_progress"

    def test_elementary_default_tuition(self, client, class_group):
        """초등 학년 → effective_tuition 240,000원."""
        res = client.post("/api/students", json={
            **STUDENT_BASE, "grade": "elementary",
            "class_group_id": class_group["id"],
        })

        assert res.json()["effective_tuition"] == 240000

    def test_middle1_default_tuition(self, client, class_group):
        """중1 학년 → effective_tuition 320,000원."""
        res = client.post("/api/students", json={
            **STUDENT_BASE, "grade": "middle1",
            "class_group_id": class_group["id"],
        })

        assert res.json()["effective_tuition"] == 320000

    def test_high_default_tuition(self, client, class_group):
        """고등 학년 → effective_tuition 400,000원."""
        res = client.post("/api/students", json={
            **STUDENT_BASE, "grade": "high",
            "class_group_id": class_group["id"],
        })

        assert res.json()["effective_tuition"] == 400000

    def test_custom_tuition_overrides_default(self, client, class_group):
        """개별 수업료 설정 시 학년 기본값 대신 적용."""
        res = client.post("/api/students", json={
            **STUDENT_BASE, "class_group_id": class_group["id"],
            "tuition_amount": 200000,
        })

        data = res.json()
        assert data["tuition_amount"] == 200000
        assert data["effective_tuition"] == 200000  # 기본 240,000 대신 200,000


class TestStudentRead:
    """학생 조회 테스트."""

    def test_filter_by_class_group(self, client, class_group):
        """수업반별 필터 조회."""
        other_group = client.post("/api/class-groups", json={
            "name": "다른반",
            "days_of_week": ["tue", "thu"],
            "start_time": "16:30",
            "default_duration_minutes": 120,
        }).json()

        client.post("/api/students", json={
            **STUDENT_BASE, "name": "학생A",
            "class_group_id": class_group["id"],
        })
        client.post("/api/students", json={
            **STUDENT_BASE, "name": "학생B",
            "class_group_id": other_group["id"],
        })

        # 전체 조회 → 2명
        all_students = client.get("/api/students").json()
        assert len(all_students) == 2

        # 필터 조회 → 1명
        filtered = client.get(f"/api/students?class_group_id={class_group['id']}").json()
        assert len(filtered) == 1
        assert filtered[0]["name"] == "학생A"


class TestStudentUpdate:
    """학생 수정 테스트."""

    def test_update_student(self, client, class_group):
        """PUT → 변경된 값 반영."""
        created = client.post("/api/students", json={
            **STUDENT_BASE, "class_group_id": class_group["id"],
        }).json()

        res = client.put(f"/api/students/{created['id']}", json={
            **STUDENT_BASE, "name": "박학생", "school": "부산중",
            "class_group_id": class_group["id"],
        })

        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "박학생"
        assert data["school"] == "부산중"


class TestStudentDelete:
    """학생 삭제 (soft delete) 테스트."""

    def test_soft_delete_student(self, client, class_group):
        """삭제 후 목록에서 안 보임."""
        created = client.post("/api/students", json={
            **STUDENT_BASE, "class_group_id": class_group["id"],
        }).json()

        res = client.delete(f"/api/students/{created['id']}")
        assert res.status_code == 200

        students = client.get("/api/students").json()
        assert len(students) == 0


class TestGradesAPI:
    """학년 상수 API 테스트."""

    def test_get_grades(self, client):
        """5개 학년 데이터 반환 확인."""
        res = client.get("/api/grades")

        assert res.status_code == 200
        data = res.json()
        assert len(data) == 5
        assert "elementary" in data
        assert "middle1" in data
        assert "middle2" in data
        assert "middle3" in data
        assert "high" in data
        assert data["elementary"]["tuition"] == 240000
