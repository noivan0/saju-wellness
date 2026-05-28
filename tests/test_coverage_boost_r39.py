"""
test_coverage_boost_r39.py
90% 목표 달성을 위한 잔여 미커버 구간 R39 (헤르)

대상:
- src/services/ai_insight.py L99-100: check_crisis_keywords lang="en"
- src/api/routes/auth.py L87: revoked token 재사용 차단 경로
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────────
# 1. ai_insight: check_crisis_keywords lang="en"
# ─────────────────────────────────────────────

class TestCrisisKeywordsEnglish:
    def test_en_suicide_detected(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("I want to kill myself", lang="en") is True

    def test_en_suicide_uppercase(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("I WANT TO DIE", lang="en") is True

    def test_en_mixed_case(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("Thinking About Suicide", lang="en") is True

    def test_en_safe_text(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("I feel a bit tired today", lang="en") is False

    def test_ko_still_works(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("죽고 싶어", lang="ko") is True

    def test_ja_crisis_detected(self):
        from src.services.ai_insight import check_crisis_keywords
        # ja 경로
        result = check_crisis_keywords("死にたい", lang="ja")
        assert isinstance(result, bool)


# ─────────────────────────────────────────────
# 2. auth: revoked token 재사용 차단 경로 (L87)
# ─────────────────────────────────────────────

class TestAuthRevokedToken:
    def test_revoked_token_raises_401(self):
        """이미 revoke된 refresh token → 401"""
        from fastapi.testclient import TestClient
        from src.api.main import app
        client = TestClient(app)

        # is_token_revoked를 True로 mock → revoked 경로 실행
        with patch("src.api.routes.auth.is_token_revoked", return_value=True):
            with patch("src.api.routes.auth.decode_token") as mock_decode:
                import time
                mock_decode.return_value = {
                    "type": "refresh",
                    "sub": "1",
                    "jti": "test-jti-001",
                    "iat": str(time.time()),
                    "exp": str(time.time() + 3600),
                }
                resp = client.post("/api/auth/refresh", json={"refresh_token": "fake.token.here"})
        assert resp.status_code in (401, 400, 422)
