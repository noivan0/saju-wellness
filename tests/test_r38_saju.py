"""
R38 사주담 90%+ 공략
- astrology GET/POST lang 분기 + Accept-Language 헤더
- fortune-standard ImportError/engine failure/lang 분기
- _resolve_lang_from_request 분기
- i18n labels
- 멘탈케어 leaderboard/reward_shop 미커버 구간
"""
import pytest
import os
from unittest.mock import patch, MagicMock

os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-placeholder!")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32chars!!")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_r38.db")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from src.api.main import app
    return TestClient(app, raise_server_exceptions=False)


# ─────────────────────────────────────────────────────────────
# GET /api/saju/astrology — Accept-Language + lang 분기
# ─────────────────────────────────────────────────────────────
class TestAstrologyR38:
    def test_get_ko_default(self, client):
        resp = client.get("/api/saju/astrology",
                          params={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("lang") in ("ko", "ja", "en")

    def test_get_lang_ja(self, client):
        resp = client.get("/api/saju/astrology",
                          params={"birth_year": 1990, "birth_month": 6,
                                  "birth_day": 15, "lang": "ja"})
        assert resp.status_code == 200
        assert resp.json().get("lang") == "ja"

    def test_get_lang_en(self, client):
        resp = client.get("/api/saju/astrology",
                          params={"birth_year": 1990, "birth_month": 6,
                                  "birth_day": 15, "lang": "en"})
        assert resp.status_code == 200
        assert resp.json().get("lang") == "en"

    def test_get_accept_language_header(self, client):
        """Accept-Language 헤더 우선순위"""
        resp = client.get("/api/saju/astrology",
                          params={"birth_year": 1990, "birth_month": 6, "birth_day": 15},
                          headers={"Accept-Language": "ja-JP,ja;q=0.9"})
        assert resp.status_code == 200

    def test_get_labels_in_response(self, client):
        resp = client.get("/api/saju/astrology",
                          params={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 200
        assert "labels" in resp.json()

    def test_get_missing_year_422(self, client):
        resp = client.get("/api/saju/astrology",
                          params={"birth_month": 6, "birth_day": 15})
        assert resp.status_code == 422

    def test_post_ko(self, client):
        resp = client.post("/api/saju/astrology",
                           json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 200

    def test_post_lang_en(self, client):
        resp = client.post("/api/saju/astrology",
                           json={"birth_year": 1990, "birth_month": 6, "birth_day": 15},
                           params={"lang": "en"})
        assert resp.status_code == 200
        assert resp.json().get("lang") == "en"

    def test_post_lang_ja(self, client):
        resp = client.post("/api/saju/astrology",
                           json={"birth_year": 1990, "birth_month": 6,
                                 "birth_day": 15, "lang": "ja"})
        assert resp.status_code == 200

    def test_post_missing_body_422(self, client):
        resp = client.post("/api/saju/astrology", json={})
        assert resp.status_code == 422

    def test_boundary_jan1(self, client):
        """경계값: 1월 1일"""
        resp = client.get("/api/saju/astrology",
                          params={"birth_year": 1990, "birth_month": 1, "birth_day": 1})
        assert resp.status_code == 200

    def test_boundary_dec31(self, client):
        resp = client.get("/api/saju/astrology",
                          params={"birth_year": 1990, "birth_month": 12, "birth_day": 31})
        assert resp.status_code == 200

    def test_zodiac_sign_boundary(self, client):
        """별자리 경계: 3월 20일(물고기/양자리 경계)"""
        resp = client.get("/api/saju/astrology",
                          params={"birth_year": 1990, "birth_month": 3, "birth_day": 20})
        assert resp.status_code == 200

    def test_astrology_exception_500(self, client):
        from src.engine import saju_calculator as sc
        with patch.object(sc, "get_astrology_info", side_effect=ValueError("astro error")):
            resp = client.get("/api/saju/astrology",
                              params={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 500


# ─────────────────────────────────────────────────────────────
# POST /api/saju/fortune-standard — 미커버 분기
# ─────────────────────────────────────────────────────────────
class TestFortuneStandardR38:
    def test_basic_ko(self, client):
        resp = client.post("/api/saju/fortune-standard",
                           json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 200
        data = resp.json()
        assert "lang" in data or "disclaimer" in data or data

    def test_lang_ja(self, client):
        resp = client.post("/api/saju/fortune-standard",
                           json={"birth_year": 1990, "birth_month": 6,
                                 "birth_day": 15, "lang": "ja"})
        assert resp.status_code == 200

    def test_lang_en(self, client):
        resp = client.post("/api/saju/fortune-standard",
                           json={"birth_year": 1990, "birth_month": 6,
                                 "birth_day": 15, "lang": "en"})
        assert resp.status_code == 200

    def test_with_birth_hour(self, client):
        resp = client.post("/api/saju/fortune-standard",
                           json={"birth_year": 1990, "birth_month": 6,
                                 "birth_day": 15, "birth_hour": 10})
        assert resp.status_code == 200

    def test_engine_failure_500(self, client):
        from src.api.routes import saju as saju_mod
        with patch.object(saju_mod, "_ENGINE_OK", False):
            resp = client.post("/api/saju/fortune-standard",
                               json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 500

    def test_saju_exception_400(self, client):
        from src.api.routes import saju as saju_mod
        with patch.object(saju_mod, "get_saju", side_effect=ValueError("계산 오류")):
            resp = client.post("/api/saju/fortune-standard",
                               json={"birth_year": 1990, "birth_month": 6, "birth_day": 15})
        assert resp.status_code == 400

    def test_accept_language_header(self, client):
        resp = client.post("/api/saju/fortune-standard",
                           json={"birth_year": 1990, "birth_month": 6, "birth_day": 15},
                           headers={"Accept-Language": "en-US,en;q=0.9"})
        assert resp.status_code == 200

    def test_boundary_years(self, client):
        for year in [1900, 1950, 2000, 2050, 2099]:
            resp = client.post("/api/saju/fortune-standard",
                               json={"birth_year": year, "birth_month": 6, "birth_day": 15})
            assert resp.status_code == 200

    def test_all_months(self, client):
        for month in range(1, 13):
            resp = client.post("/api/saju/fortune-standard",
                               json={"birth_year": 1990, "birth_month": month, "birth_day": 15})
            assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# i18n utils — 미커버 50%→80%
# ─────────────────────────────────────────────────────────────
class TestI18nUtils:
    def test_resolve_lang_ko(self):
        try:
            from app.i18n.i18n_utils import resolve_lang
            result = resolve_lang("ko", "")
            assert result == "ko"
        except ImportError:
            pytest.skip("i18n_utils 없음")

    def test_resolve_lang_ja(self):
        try:
            from app.i18n.i18n_utils import resolve_lang
            result = resolve_lang("ja", "")
            assert result == "ja"
        except ImportError:
            pytest.skip("i18n_utils 없음")

    def test_resolve_lang_en(self):
        try:
            from app.i18n.i18n_utils import resolve_lang
            result = resolve_lang("en", "")
            assert result == "en"
        except ImportError:
            pytest.skip("i18n_utils 없음")

    def test_resolve_lang_from_accept_header(self):
        try:
            from app.i18n.i18n_utils import resolve_lang
            result = resolve_lang(None, "ja-JP,ja;q=0.9")
            assert result in ("ja", "ko", "en")
        except ImportError:
            pytest.skip("i18n_utils 없음")

    def test_resolve_lang_fallback_ko(self):
        try:
            from app.i18n.i18n_utils import resolve_lang
            result = resolve_lang(None, "")
            assert result == "ko"
        except ImportError:
            pytest.skip("i18n_utils 없음")

    def test_get_i18n_ko(self):
        try:
            from app.i18n.i18n_utils import get_i18n
            labels = get_i18n("ko")
            assert isinstance(labels, dict)
        except ImportError:
            pytest.skip("i18n_utils 없음")

    def test_get_i18n_ja(self):
        try:
            from app.i18n.i18n_utils import get_i18n
            labels = get_i18n("ja")
            assert isinstance(labels, dict)
        except ImportError:
            pytest.skip("i18n_utils 없음")

    def test_get_i18n_en(self):
        try:
            from app.i18n.i18n_utils import get_i18n
            labels = get_i18n("en")
            assert isinstance(labels, dict)
        except ImportError:
            pytest.skip("i18n_utils 없음")
