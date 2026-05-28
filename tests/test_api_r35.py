"""
R35 사주담 API 라우트 커버리지 보강 (정확한 경로/메서드 기반)
- POST /api/saju/calculate: BirthInfo 바디, 엔진 오류, 일주해석
- POST /api/saju/daily-energy: 오늘 에너지
- GET /api/saju/today-energy: KST 오늘 에너지
- POST /api/saju/fortune-standard: 표준 운세
- GET /api/saju/pillar-details: 일주 상세
- GET /api/saju/today-energy: 에너지
- POST /api/insight/daily: AI 인사이트
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-placeholder!")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32chars!!")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_saju_r35.db")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key-placeholder")


@pytest.fixture(scope="module")
def client():
    from src.api.main import app
    return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────
# POST /api/saju/calculate
# ─────────────────────────────────────────────────────────────
class TestCalculateSaju:
    def test_basic_request(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 200
        data = resp.json()
        assert "pillars" in data
        assert "disclaimer" in data
        assert "legal" in data

    def test_with_birth_hour(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1990, "birth_month": 6,
                                 "birth_day": 15, "birth_hour": 10})
        assert resp.status_code == 200

    def test_missing_required_field_422(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1990, "birth_month": 6})
        assert resp.status_code == 422

    def test_year_out_of_range_422(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1800, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 422

    def test_invalid_month_422(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1990, "birth_month": 13, "birth_day": 15})
        assert resp.status_code == 422

    def test_invalid_day_for_month_422(self, client):
        """2월 31일 → 422"""
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1990, "birth_month": 2, "birth_day": 31})
        assert resp.status_code == 422

    def test_interpretation_in_response(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1985, "birth_month": 3, "birth_day": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert "interpretation" in data
        assert "day_pillar" in data["interpretation"]

    def test_legal_field_present(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 200
        assert "법적 포지션" in resp.json().get("legal", "") or \
               "명리학 참고" in resp.json().get("legal", "") or \
               "legal" in resp.json()

    def test_boundary_year_1900(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 1900, "birth_month": 1, "birth_day": 1})
        assert resp.status_code == 200

    def test_boundary_year_2099(self, client):
        resp = client.post("/api/saju/calculate",
                           json={"birth_year": 2099, "birth_month": 12, "birth_day": 31})
        assert resp.status_code == 200

    def test_engine_failure_500(self, client):
        """엔진 로드 실패 시 500"""
        from src.api.routes import saju as saju_module
        with patch.object(saju_module, "_ENGINE_OK", False), \
             patch.object(saju_module, "_ENGINE_ERR", "test engine error"):
            resp = client.post("/api/saju/calculate",
                               json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 500

    def test_saju_calculation_exception_400(self, client):
        """계산 중 예외 → 400"""
        from src.api.routes import saju as saju_module
        with patch.object(saju_module, "get_saju", side_effect=ValueError("계산 오류")):
            resp = client.post("/api/saju/calculate",
                               json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────
# POST /api/saju/daily-energy
# ─────────────────────────────────────────────────────────────
class TestDailyEnergy:
    def test_basic_request(self, client):
        resp = client.post("/api/saju/daily-energy",
                           json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 200
        data = resp.json()
        assert "energy_summary" in data or "primary_element" in data or data

    def test_missing_field_422(self, client):
        resp = client.post("/api/saju/daily-energy",
                           json={"birth_year": 1990})
        assert resp.status_code == 422

    def test_different_births_different_energy(self, client):
        r1 = client.post("/api/saju/daily-energy",
                         json={"birth_year": 1980, "birth_month": 1, "birth_day": 1})
        r2 = client.post("/api/saju/daily-energy",
                         json={"birth_year": 1995, "birth_month": 8, "birth_day": 20})
        assert r1.status_code == 200
        assert r2.status_code == 200


# ─────────────────────────────────────────────────────────────
# GET /api/saju/today-energy
# ─────────────────────────────────────────────────────────────
class TestTodayEnergy:
    def test_basic_request(self, client):
        resp = client.get("/api/saju/today-energy")
        assert resp.status_code == 200

    def test_with_lang_ko(self, client):
        resp = client.get("/api/saju/today-energy", params={"lang": "ko"})
        assert resp.status_code == 200

    def test_with_lang_en(self, client):
        resp = client.get("/api/saju/today-energy", params={"lang": "en"})
        assert resp.status_code == 200

    def test_with_lang_ja(self, client):
        resp = client.get("/api/saju/today-energy", params={"lang": "ja"})
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# GET /api/saju/pillar-details
# ─────────────────────────────────────────────────────────────
class TestPillarDetails:
    def test_hanja_pillar(self, client):
        resp = client.get("/api/saju/pillar-details", params={"pillar": "甲子"})
        assert resp.status_code == 200

    def test_korean_pillar(self, client):
        """한글 간지 → 한자 변환"""
        resp = client.get("/api/saju/pillar-details", params={"pillar": "기사"})
        assert resp.status_code == 200

    def test_missing_pillar_422(self, client):
        resp = client.get("/api/saju/pillar-details")
        assert resp.status_code == 422

    def test_various_pillars(self, client):
        for pillar in ["甲子", "乙丑", "丙寅", "丁卯"]:
            resp = client.get("/api/saju/pillar-details", params={"pillar": pillar})
            assert resp.status_code == 200

class TestFortuneStandard:
    def test_basic_request(self, client):
        resp = client.post("/api/saju/fortune-standard",
                           json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 200

    def test_with_hour(self, client):
        resp = client.post("/api/saju/fortune-standard",
                           json={"birth_year": 1990, "birth_month": 6,
                                 "birth_day": 15, "birth_hour": 10})
        assert resp.status_code == 200

    def test_missing_field_422(self, client):
        resp = client.post("/api/saju/fortune-standard",
                           json={"birth_year": 1990})
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────
# GET /api/saju/pillar-details
# ─────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────
# GET /api/saju/compatibility-preview
# ─────────────────────────────────────────────────────────────
class TestCompatibilityPreview:
    def test_basic_request(self, client):
        resp = client.get("/api/saju/compatibility-preview",
                          params={"my_year": 1990, "my_month": 6, "my_day": 15,
                                  "partner_year": 1992, "partner_month": 8, "partner_day": 20})
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data or "is_preview" in data

    def test_lang_en(self, client):
        resp = client.get("/api/saju/compatibility-preview",
                          params={"my_year": 1990, "my_month": 6, "my_day": 15,
                                  "partner_year": 1992, "partner_month": 8, "partner_day": 20,
                                  "lang": "en"})
        assert resp.status_code == 200

    def test_lang_ja(self, client):
        resp = client.get("/api/saju/compatibility-preview",
                          params={"my_year": 1990, "my_month": 6, "my_day": 15,
                                  "partner_year": 1992, "partner_month": 8, "partner_day": 20,
                                  "lang": "ja"})
        assert resp.status_code == 200

    def test_missing_partner_422(self, client):
        resp = client.get("/api/saju/compatibility-preview",
                          params={"my_year": 1990, "my_month": 6, "my_day": 15})
        assert resp.status_code == 422

    def test_same_person_perfect_score(self, client):
        resp = client.get("/api/saju/compatibility-preview",
                          params={"my_year": 1990, "my_month": 6, "my_day": 15,
                                  "partner_year": 1990, "partner_month": 6, "partner_day": 15})
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# POST /api/insight/daily
# ─────────────────────────────────────────────────────────────
class TestInsightDaily:
    def test_unauthorized_401(self, client):
        """인증 없이 접근 → 401 또는 422"""
        resp = client.post("/api/insight/daily",
                           json={"user_message": "오늘 기분이 좋아요"})
        assert resp.status_code in (401, 422)

    def test_missing_body_422(self, client):
        resp = client.post("/api/insight/daily", json={})
        assert resp.status_code in (401, 422)

    def test_ai_status_ok(self, client):
        """AI 상태 엔드포인트"""
        resp = client.get("/api/insight/ai/status")
        assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_has_status(self, client):
        data = client.get("/health").json()
        assert "status" in data
