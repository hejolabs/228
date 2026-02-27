"""Phase 5: 수업료 관리 + 메시지 생성 테스트.

1. 8회 완료 → Payment 자동 생성 (pending)
2. 메시지 생성 → message_sent = True
3. 입금 확인 → status = paid
4. 미납 목록 필터
"""


def attend(client, student_id: int, date: str):
    return client.post("/api/attendance", json={
        "student_id": student_id, "date": date, "status": "present",
    })


class TestPaymentAutoCreate:
    """사이클 완료 시 Payment 자동 생성."""

    def test_payment_created_on_cycle_complete(self, client, seed_student):
        """8회 출석 → pending Payment 자동 생성."""
        student_id = seed_student["id"]

        for i in range(1, 9):
            attend(client, student_id, f"2026-03-{i:02d}")

        payments = client.get("/api/payments?status=pending").json()
        assert len(payments) == 1
        assert payments[0]["student_id"] == student_id
        assert payments[0]["status"] == "pending"
        assert payments[0]["amount"] == 240000  # 초등 기본

    def test_no_payment_before_complete(self, client, seed_student):
        """7회 출석 → Payment 미생성."""
        student_id = seed_student["id"]

        for i in range(1, 8):
            attend(client, student_id, f"2026-03-{i:02d}")

        payments = client.get("/api/payments").json()
        assert len(payments) == 0


class TestMessage:
    """메시지 생성 테스트."""

    def test_generate_message(self, client, seed_student):
        """메시지 생성 → 학생 이름, 금액 포함."""
        student_id = seed_student["id"]

        for i in range(1, 9):
            attend(client, student_id, f"2026-03-{i:02d}")

        payments = client.get("/api/payments").json()
        payment_id = payments[0]["id"]

        res = client.post(f"/api/payments/{payment_id}/message")
        assert res.status_code == 200
        data = res.json()
        assert "김테스트" in data["message"]
        assert "240,000" in data["message"]

        # message_sent 플래그 확인
        payment = client.get(f"/api/payments/{payment_id}").json()
        assert payment["message_sent"] is True


class TestPaymentConfirm:
    """입금 확인 테스트."""

    def test_confirm_payment(self, client, seed_student):
        """입금 확인 → status paid."""
        student_id = seed_student["id"]

        for i in range(1, 9):
            attend(client, student_id, f"2026-03-{i:02d}")

        payments = client.get("/api/payments").json()
        payment_id = payments[0]["id"]

        res = client.post(f"/api/payments/{payment_id}/confirm", json={
            "payment_method": "transfer",
        })
        assert res.status_code == 200
        assert res.json()["status"] == "paid"
        assert res.json()["payment_method"] == "transfer"

    def test_cannot_confirm_twice(self, client, seed_student):
        """이미 납부 완료된 건 재확인 → 400."""
        student_id = seed_student["id"]

        for i in range(1, 9):
            attend(client, student_id, f"2026-03-{i:02d}")

        payments = client.get("/api/payments").json()
        payment_id = payments[0]["id"]

        client.post(f"/api/payments/{payment_id}/confirm", json={"payment_method": "transfer"})
        res = client.post(f"/api/payments/{payment_id}/confirm", json={"payment_method": "cash"})
        assert res.status_code == 400
