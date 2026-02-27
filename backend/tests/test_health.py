"""Phase 1: 서버 헬스체크 테스트."""


def test_health_check(client):
    """GET /api/health → 200, status ok."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
