"""
사주담 — auth API 테스트 (nova-qa 감사 R30)

대상: src/api/routes/auth.py (57% → 목표 90%+)
헤르2 체크포인트:
- JWT 만료/리프레시 로테이션
- OAuth CSRF state 검증
- 소셜 로그인 (카카오/구글)
- /me, /logout, /account 엔드포인트
"""
import os
import pytest

# conftest보다 먼저 환경변수 설정
os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-placeholder!")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32chars!!")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_saju.db")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key-placeholder")

from fastapi.testclient import TestClient
from src.api.main import app
from src.core.auth import create_access_token, create_refresh_token


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture
def access_token():
    return create_access_token(999)


@pytest.fixture
def refresh_token_str():
    return create_refresh_token(888)


class TestOAuthState:
    def test_generate_state(self, client):
        """OAuth CSRF 방지 state 생성"""
        r = client.get("/api/auth/oauth/state")
        assert r.status_code == 200
        data = r.json()
        assert "state" in data
        assert len(data["state"]) > 20
        assert data["ttl_seconds"] == 300

    def test_state_unique_each_call(self, client):
        """state는 매 호출마다 다른 값"""
        s1 = client.get("/api/auth/oauth/state").json()["state"]
        s2 = client.get("/api/auth/oauth/state").json()["state"]
        assert s1 != s2


class TestKakaoLogin:
    def test_kakao_login_with_code(self, client):
        """카카오 코드로 토큰 발급"""
        r = client.post("/api/auth/kakao?code=test_code_123&state=test_state_value_csrf_protection_32chars_min")
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_kakao_login_with_state(self, client):
        """state 파라미터 포함 (CSRF 방지)"""
        r = client.post("/api/auth/kakao?code=abc&state=test_state_value_csrf_protection_32chars_min")
        assert r.status_code == 200

    def test_kakao_missing_code(self, client):
        """code 없으면 422"""
        r = client.post("/api/auth/kakao")
        assert r.status_code == 422


class TestGoogleLogin:
    def test_google_login_with_code(self, client):
        """구글 코드로 토큰 발급"""
        r = client.post("/api/auth/google?code=google_test_code&state=test_state_value_csrf_protection_32chars_min")
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_google_missing_code(self, client):
        """code 없으면 422"""
        r = client.post("/api/auth/google")
        assert r.status_code == 422


class TestRefreshToken:
    def test_refresh_valid(self, client, refresh_token_str):
        """유효한 refresh token → 새 access token 발급"""
        r = client.post(f"/api/auth/refresh?refresh_token={refresh_token_str}")
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_rotation_reuse_blocked(self, client):
        """리프레시 토큰 로테이션: 재사용 차단 (독립 토큰 사용)"""
        fresh_token = create_refresh_token(7777)
        # 첫 번째 사용
        r1 = client.post(f"/api/auth/refresh?refresh_token={fresh_token}")
        assert r1.status_code == 200
        # 동일 토큰 재사용 → 401
        r2 = client.post(f"/api/auth/refresh?refresh_token={fresh_token}")
        assert r2.status_code == 401

    def test_refresh_invalid_token(self, client):
        """잘못된 refresh token → 401"""
        r = client.post("/api/auth/refresh?refresh_token=totally.invalid.token")
        assert r.status_code == 401

    def test_access_token_as_refresh_rejected(self, client, access_token):
        """access token을 refresh로 사용 → 400/401"""
        r = client.post(f"/api/auth/refresh?refresh_token={access_token}")
        assert r.status_code in (400, 401)


class TestMeEndpoint:
    def test_get_me_authenticated(self, client, access_token):
        """인증된 사용자 정보 조회"""
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200
        data = r.json()
        assert "user_id" in data

    def test_get_me_no_auth(self, client):
        """인증 없이 /me → 401"""
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_get_me_invalid_token(self, client):
        """잘못된 토큰 → 401"""
        r = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert r.status_code == 401


class TestLogout:
    def test_logout(self, client, access_token):
        """로그아웃 — 클라이언트 토큰 삭제 안내"""
        r = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200
        assert "message" in r.json()

    def test_logout_no_auth(self, client):
        """인증 없이 logout → 401"""
        r = client.post("/api/auth/logout")
        assert r.status_code == 401


class TestDeleteAccount:
    def test_delete_account(self, client, access_token):
        """회원 탈퇴 — 개보법 21조"""
        r = client.delete("/api/auth/account", headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200
        data = r.json()
        assert "message" in data

    def test_delete_account_no_auth(self, client):
        """인증 없이 탈퇴 → 401"""
        r = client.delete("/api/auth/account")
        assert r.status_code == 401
