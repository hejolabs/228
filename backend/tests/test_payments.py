"""Phase 5.1: 수업료 관리 테스트 (선불 시스템).

1. 사이클 완료 → Payment 자동 생성 (pending)
2. 메시지 생성 → message_sent = True
3. 입금 확인 → status = paid
4. 납부 후 다음 사이클 시작
"""


class TestPaymentAutoCreate:
    """사이클 완료 시 Payment 자동 생성."""

    def test_payment_created_on_cycle_complete(self, client, seed_student):
        """사이클 완료 → pending Payment 자동 생성."""
        cycle_id = seed_student["current_cycle"]["id"]

        client.post(f"/api/cycles/{cycle_id}/complete")

        payments = client.get("/api/payments?status=pending").json()
        assert len(payments) == 1
        assert payments[0]["student_id"] == seed_student["id"]
        assert payments[0]["status"] == "pending"
        assert payments[0]["amount"] == 240000  # 초등 기본

    def test_no_payment_before_complete(self, client, seed_student):
        """사이클 미완료 → Payment 없음."""
        payments = client.get("/api/payments").json()
        assert len(payments) == 0


class TestMessage:
    """메시지 생성 테스트."""

    def test_generate_message(self, client, seed_student):
        """메시지 생성 → 학생 이름, 금액 포함."""
        cycle_id = seed_student["current_cycle"]["id"]
        client.post(f"/api/cycles/{cycle_id}/complete")

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
        cycle_id = seed_student["current_cycle"]["id"]
        client.post(f"/api/cycles/{cycle_id}/complete")

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
        cycle_id = seed_student["current_cycle"]["id"]
        client.post(f"/api/cycles/{cycle_id}/complete")

        payments = client.get("/api/payments").json()
        payment_id = payments[0]["id"]

        client.post(f"/api/payments/{payment_id}/confirm", json={"payment_method": "transfer"})
        res = client.post(f"/api/payments/{payment_id}/confirm", json={"payment_method": "cash"})
        assert res.status_code == 400


class TestNextCycleStart:
    """납부 확인 후 다음 사이클 시작."""

    def test_start_next_cycle_after_payment(self, client, seed_student):
        """완료 + 납부 확인 → 다음 사이클 시작 가능."""
        cycle_id = seed_student["current_cycle"]["id"]

        # 사이클 완료
        client.post(f"/api/cycles/{cycle_id}/complete")

        # 납부 확인
        payments = client.get("/api/payments").json()
        client.post(f"/api/payments/{payments[0]['id']}/confirm", json={"payment_method": "transfer"})

        # 다음 사이클 시작 (3.30 월요일부터)
        res = client.post(f"/api/cycles/{cycle_id}/start-next", json={
            "start_date": "2026-03-30",
        })
        assert res.status_code == 200
        assert res.json()["cycle_number"] == 2

    def test_cannot_start_without_payment(self, client, seed_student):
        """미납 상태에서 다음 사이클 시작 → 400."""
        cycle_id = seed_student["current_cycle"]["id"]
        client.post(f"/api/cycles/{cycle_id}/complete")

        res = client.post(f"/api/cycles/{cycle_id}/start-next", json={
            "start_date": "2026-03-30",
        })
        assert res.status_code == 400
