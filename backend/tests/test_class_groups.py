"""Phase 2: 수업반 관리 CRUD 테스트."""

import pytest


CLASS_GROUP_DATA = {
    "name": "월수반A",
    "days_of_week": ["mon", "wed"],
    "start_time": "14:30",
    "default_duration_minutes": 90,
    "memo": "초등 전용",
}


class TestClassGroupCreate:
    """수업반 생성 테스트."""

    def test_create_class_group(self, client):
        """POST → 201, 생성된 데이터 확인."""
        res = client.post("/api/class-groups", json=CLASS_GROUP_DATA)

        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "월수반A"
        assert data["days_of_week"] == ["mon", "wed"]
        assert data["start_time"] == "14:30"
        assert data["default_duration_minutes"] == 90
        assert data["is_active"] is True

    def test_create_duplicate_name_fails(self, client):
        """같은 이름으로 두 번 생성 → 409 Conflict."""
        client.post("/api/class-groups", json=CLASS_GROUP_DATA)
        res = client.post("/api/class-groups", json=CLASS_GROUP_DATA)

        assert res.status_code == 409


class TestClassGroupRead:
    """수업반 조회 테스트."""

    def test_list_class_groups(self, client):
        """생성 후 목록에 포함 확인."""
        client.post("/api/class-groups", json=CLASS_GROUP_DATA)
        client.post("/api/class-groups", json={
            **CLASS_GROUP_DATA, "name": "화목반A",
            "days_of_week": ["tue", "thu"],
        })

        res = client.get("/api/class-groups")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2

    def test_get_class_group_by_id(self, client):
        """상세 조회 → 정확한 데이터 반환."""
        created = client.post("/api/class-groups", json=CLASS_GROUP_DATA).json()

        res = client.get(f"/api/class-groups/{created['id']}")
        assert res.status_code == 200
        assert res.json()["name"] == "월수반A"

    def test_get_nonexistent_class_group_404(self, client):
        """존재하지 않는 ID → 404."""
        res = client.get("/api/class-groups/9999")
        assert res.status_code == 404


class TestClassGroupUpdate:
    """수업반 수정 테스트."""

    def test_update_class_group(self, client):
        """PUT → 변경된 값 반영."""
        created = client.post("/api/class-groups", json=CLASS_GROUP_DATA).json()

        updated_data = {**CLASS_GROUP_DATA, "name": "월수반B", "default_duration_minutes": 120}
        res = client.put(f"/api/class-groups/{created['id']}", json=updated_data)

        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "월수반B"
        assert data["default_duration_minutes"] == 120


class TestClassGroupDelete:
    """수업반 삭제 (soft delete) 테스트."""

    def test_soft_delete_class_group(self, client):
        """삭제 후 목록에서 안 보임."""
        created = client.post("/api/class-groups", json=CLASS_GROUP_DATA).json()

        res = client.delete(f"/api/class-groups/{created['id']}")
        assert res.status_code == 200

        # 목록에서 사라짐
        groups = client.get("/api/class-groups").json()
        assert len(groups) == 0

        # 상세 조회도 404
        res = client.get(f"/api/class-groups/{created['id']}")
        assert res.status_code == 404
