"""8회차 사이클 핵심 로직 테스트.

테스트 시나리오:
1. 출석 1회 → current_count 1/8
2. 출석 8회 → status completed
3. 미차감 출석 → current_count 안 오름
4. 완료 후 새 사이클 시작
5. 출석 수정 시 회차 재계산
6. 출석 삭제 시 회차 재계산
"""


def attend(client, student_id: int, date: str, status: str = "present", counts: bool = True, excuse: str | None = None):
    """출석 기록 헬퍼 함수."""
    return client.post("/api/attendance", json={
        "student_id": student_id,
        "date": date,
        "status": status,
        "counts_toward_cycle": counts,
        "excuse_reason": excuse,
    })


class TestAttendanceCycleCount:
    """출석 → 회차 차감 테스트."""

    def test_first_attendance_increments_to_1(self, client, seed_student):
        """출석 1회 → current_count가 0에서 1로 증가."""
        res = attend(client, seed_student["id"], "2026-03-02")

        assert res.status_code == 201
        data = res.json()
        assert data["current_count"] == 1
        assert data["total_count"] == 8

    def test_eight_attendances_complete_cycle(self, client, seed_student):
        """출석 8회 → 사이클 status가 completed로 변경."""
        student_id = seed_student["id"]

        # 8번 출석
        for i in range(1, 9):
            res = attend(client, student_id, f"2026-03-{i:02d}")

        last = res.json()
        assert last["current_count"] == 8

        # 알림 API에서 completed 확인
        alerts = client.get("/api/cycles/alerts").json()
        assert len(alerts) == 1
        assert alerts[0]["status"] == "completed"
        assert alerts[0]["current_count"] == 8

    def test_seven_attendances_show_alert(self, client, seed_student):
        """출석 7회 → 알림 목록에 표시 (임박 상태)."""
        student_id = seed_student["id"]

        for i in range(1, 8):
            attend(client, student_id, f"2026-03-{i:02d}")

        alerts = client.get("/api/cycles/alerts").json()
        assert len(alerts) == 1
        assert alerts[0]["current_count"] == 7
        assert alerts[0]["status"] == "in_progress"


class TestExcusedAbsence:
    """미차감 출석 테스트."""

    def test_excused_absence_does_not_count(self, client, seed_student):
        """미차감 결석 → current_count 증가 안 함."""
        student_id = seed_student["id"]

        # 일반 출석 1회
        attend(client, student_id, "2026-03-01")

        # 미차감 결석
        res = attend(client, student_id, "2026-03-02",
                     status="absent_excused", counts=False, excuse="sick_leave")
        data = res.json()
        assert data["current_count"] == 1  # 여전히 1

    def test_mixed_attendance_correct_count(self, client, seed_student):
        """일반 출석 3회 + 미차감 2회 → current_count 3."""
        student_id = seed_student["id"]

        attend(client, student_id, "2026-03-01")  # 1
        attend(client, student_id, "2026-03-02", status="absent_excused", counts=False, excuse="school_event")
        attend(client, student_id, "2026-03-03")  # 2
        attend(client, student_id, "2026-03-04", status="absent_excused", counts=False, excuse="sick_leave")
        res = attend(client, student_id, "2026-03-05")  # 3

        assert res.json()["current_count"] == 3


class TestNewCycle:
    """사이클 완료 후 새 사이클 시작 테스트."""

    def test_new_cycle_after_completion(self, client, seed_student):
        """8회 완료 → 새 사이클 시작 → cycle_number 2, current_count 0."""
        student_id = seed_student["id"]
        cycle_id = seed_student["current_cycle"]["id"]

        # 8회 출석으로 완료
        for i in range(1, 9):
            attend(client, student_id, f"2026-03-{i:02d}")

        # 새 사이클 시작
        res = client.post(f"/api/cycles/{cycle_id}/new-cycle")
        assert res.status_code == 200
        data = res.json()
        assert data["cycle_number"] == 2

        # 학생 조회 → 새 사이클 반영 확인
        student = client.get(f"/api/students/{student_id}").json()
        assert student["current_cycle"]["cycle_number"] == 2
        assert student["current_cycle"]["current_count"] == 0

    def test_cannot_start_new_cycle_if_not_completed(self, client, seed_student):
        """미완료 사이클에서 새 사이클 시작 시도 → 400 에러."""
        cycle_id = seed_student["current_cycle"]["id"]

        res = client.post(f"/api/cycles/{cycle_id}/new-cycle")
        assert res.status_code == 400


class TestAttendanceModification:
    """출석 수정/삭제 시 회차 재계산 테스트."""

    def test_update_to_excused_recounts(self, client, seed_student):
        """출석을 미차감으로 수정 → current_count 감소."""
        student_id = seed_student["id"]

        # 3회 출석
        r1 = attend(client, student_id, "2026-03-01")
        attend(client, student_id, "2026-03-02")
        attend(client, student_id, "2026-03-03")

        att_id = r1.json()["id"]

        # 첫 번째를 미차감으로 수정
        res = client.put(f"/api/attendance/{att_id}", json={
            "status": "absent_excused",
            "counts_toward_cycle": False,
            "excuse_reason": "sick_leave",
        })
        assert res.json()["current_count"] == 2  # 3 → 2

    def test_delete_attendance_recounts(self, client, seed_student):
        """출석 삭제 → current_count 감소."""
        student_id = seed_student["id"]

        r1 = attend(client, student_id, "2026-03-01")
        attend(client, student_id, "2026-03-02")

        att_id = r1.json()["id"]

        # 삭제
        client.delete(f"/api/attendance/{att_id}")

        # 학생 조회로 확인
        student = client.get(f"/api/students/{student_id}").json()
        assert student["current_cycle"]["current_count"] == 1  # 2 → 1
