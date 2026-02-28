"""Phase 5.1: 스케줄 기반 출석 + 사이클 관리 테스트.

1. 사이클 시작 → 8회차 스케줄 자동 생성 (기본: present)
2. 미차감 결석 → 스케줄 1회 연장
3. 사이클 완료 → Payment 자동 생성
4. 수업등록 상태 변경 + 이력
"""


class TestScheduleGeneration:
    """사이클 시작 시 스케줄 자동 생성."""

    def test_start_cycle_creates_8_attendance(self, client, seed_student):
        """사이클 시작 → 8개 출석 레코드 생성."""
        student_id = seed_student["id"]

        # 2026-03-02(월) 시작, 월수반 → 3.2, 3.4, 3.9, 3.11, 3.16, 3.18, 3.23, 3.25
        records = client.get(f"/api/attendance/daily/2026-03-02?class_group_id={seed_student['class_group_id']}").json()
        assert any(r["student_id"] == student_id for r in records)

        # 3.4(수)에도 스케줄 있어야 함
        records_wed = client.get(f"/api/attendance/daily/2026-03-04?class_group_id={seed_student['class_group_id']}").json()
        assert any(r["student_id"] == student_id for r in records_wed)

    def test_schedule_dates_match_class_days(self, client, seed_student):
        """스케줄 날짜가 수업반 요일(월,수)과 일치."""
        student_id = seed_student["id"]

        # 월요일이 아닌 3.3(화)에는 스케줄 없어야 함
        records_tue = client.get(f"/api/attendance/daily/2026-03-03?class_group_id={seed_student['class_group_id']}").json()
        assert not any(r["student_id"] == student_id for r in records_tue)

    def test_all_records_default_present(self, client, seed_student):
        """미리 생성된 출석은 모두 present 상태."""
        records = client.get(f"/api/attendance/daily/2026-03-02?class_group_id={seed_student['class_group_id']}").json()
        student_records = [r for r in records if r["student_id"] == seed_student["id"]]
        assert len(student_records) == 1
        assert student_records[0]["status"] == "present"
        assert student_records[0]["counts_toward_cycle"] is True

    def test_current_cycle_shows_8_of_8(self, client, seed_student):
        """사이클 시작 후 current_count=8, total_count=8."""
        cycle = seed_student["current_cycle"]
        assert cycle is not None
        assert cycle["current_count"] == 8
        assert cycle["total_count"] == 8
        assert cycle["status"] == "in_progress"


class TestExcusedAbsence:
    """미차감 결석 → 스케줄 연장."""

    def test_excused_extends_schedule(self, client, seed_student):
        """미차감 결석 처리 → 스케줄 1회 연장."""
        student_id = seed_student["id"]
        group_id = seed_student["class_group_id"]

        # 3.2(월) 출석 레코드 찾기
        records = client.get(f"/api/attendance/daily/2026-03-02?class_group_id={group_id}").json()
        att = [r for r in records if r["student_id"] == student_id][0]

        # 미차감 결석으로 변경
        res = client.put(f"/api/attendance/{att['id']}", json={
            "status": "absent_excused",
            "counts_toward_cycle": False,
            "excuse_reason": "sick_leave",
        })
        assert res.status_code == 200

        # 기존 마지막 스케줄(3.25 수) 다음 수업일(3.30 월)에 연장 레코드 확인
        extended = client.get(f"/api/attendance/daily/2026-03-30?class_group_id={group_id}").json()
        assert any(r["student_id"] == student_id for r in extended)

    def test_excused_recount_stays_8(self, client, seed_student):
        """미차감 1건 + 연장 1건 → current_count 여전히 8."""
        student_id = seed_student["id"]
        group_id = seed_student["class_group_id"]

        records = client.get(f"/api/attendance/daily/2026-03-02?class_group_id={group_id}").json()
        att = [r for r in records if r["student_id"] == student_id][0]

        client.put(f"/api/attendance/{att['id']}", json={
            "status": "absent_excused",
            "counts_toward_cycle": False,
            "excuse_reason": "sick_leave",
        })

        # 학생 정보 갱신하여 사이클 확인
        student = client.get(f"/api/students/{student_id}").json()
        assert student["current_cycle"]["current_count"] == 8  # 7 + 1(연장) = 8


class TestCycleComplete:
    """사이클 완료 테스트."""

    def test_complete_cycle_creates_payment(self, client, seed_student):
        """사이클 완료 → Payment 자동 생성."""
        cycle_id = seed_student["current_cycle"]["id"]

        res = client.post(f"/api/cycles/{cycle_id}/complete")
        assert res.status_code == 200

        payments = client.get("/api/payments").json()
        assert len(payments) == 1
        assert payments[0]["student_id"] == seed_student["id"]
        assert payments[0]["status"] == "pending"
        assert payments[0]["amount"] == 240000

    def test_cannot_complete_twice(self, client, seed_student):
        """이미 완료된 사이클 재완료 → 400."""
        cycle_id = seed_student["current_cycle"]["id"]

        client.post(f"/api/cycles/{cycle_id}/complete")
        res = client.post(f"/api/cycles/{cycle_id}/complete")
        assert res.status_code == 400


class TestEnrollmentStatus:
    """수업등록 상태 변경 + 이력 테스트."""

    def test_status_change_with_history(self, client, seed_class_group):
        """상태 변경 → 이력 자동 기록."""
        student = client.post("/api/students", json={
            "name": "신규학생",
            "phone": "010-0000-0000",
            "school": "테스트초",
            "grade": "elementary",
            "parent_phone": "010-1111-1111",
            "class_group_id": seed_class_group["id"],
        }).json()

        # inquiry → level_test
        res = client.post(f"/api/students/{student['id']}/status", json={
            "status": "level_test",
            "memo": "레벨테스트 예약",
        })
        assert res.status_code == 200
        assert res.json()["enrollment_status"] == "level_test"

        # 이력 확인
        history = client.get(f"/api/students/{student['id']}/history").json()
        assert len(history) == 2  # 등록 시 1건 + 변경 1건
        assert history[0]["to_status"] == "level_test"  # 최신 먼저
        assert history[0]["memo"] == "레벨테스트 예약"

    def test_invalid_transition_rejected(self, client, seed_class_group):
        """허용되지 않는 전이 → 400."""
        student = client.post("/api/students", json={
            "name": "신규학생",
            "phone": "010-0000-0000",
            "school": "테스트초",
            "grade": "elementary",
            "parent_phone": "010-1111-1111",
            "class_group_id": seed_class_group["id"],
        }).json()

        # inquiry → stopped → level_test (불가)
        client.post(f"/api/students/{student['id']}/status", json={"status": "stopped"})
        res = client.post(f"/api/students/{student['id']}/status", json={"status": "level_test"})
        assert res.status_code == 400

    def test_stopped_to_active_re_enrollment(self, client, seed_class_group):
        """수업종료 → 수업중 (재등록) 가능."""
        student = client.post("/api/students", json={
            "name": "재등록학생",
            "phone": "010-0000-0000",
            "school": "테스트초",
            "grade": "elementary",
            "parent_phone": "010-1111-1111",
            "class_group_id": seed_class_group["id"],
            "enrollment_status": "active",
        }).json()

        client.post(f"/api/students/{student['id']}/status", json={"status": "stopped"})
        res = client.post(f"/api/students/{student['id']}/status", json={"status": "active"})
        assert res.status_code == 200
        assert res.json()["enrollment_status"] == "active"
