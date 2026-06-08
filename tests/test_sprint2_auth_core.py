"""
Sprint 2 — src/core/auth.py 커버리지 향상 테스트
목표: 49.6% → 75%+

테스트 항목:
- _get_redis: REDIS_URL 없을 때 None / lazy init
- revoke_token: 메모리 폴백 (Redis 없음)
- revoke_user_tokens: 메모리 폴백
- is_token_revoked: 메모리 폴백 — 단일/전체
- hash_password / verify_password
- create_access_token / create_refresh_token / decode_token
- get_current_user: 정상 / 만료 / 유효하지않음 / 블랙리스트
"""
import os
import sys
import pytest
import time
from datetime import datetime, timedelta, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-placeholder!")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32chars!!")
os.environ.pop("REDIS_URL", None)  # Redis 없는 상태로 강제


# core.auth 임포트는 환경변수 설정 이후
import src.core.auth as auth_mod
from src.core.auth import (
    _get_redis,
    revoke_token,
    revoke_user_tokens,
    is_token_revoked,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


# ── _get_redis ────────────────────────────────────────────────────────────────

class TestGetRedis:
    def test_returns_none_without_redis_url(self):
        # REDIS_URL 미설정 → None
        result = _get_redis()
        assert result is None

    def test_returns_same_none_on_second_call(self):
        r1 = _get_redis()
        r2 = _get_redis()
        assert r1 is None
        assert r2 is None


# ── revoke_token (메모리 폴백) ─────────────────────────────────────────────────

class TestRevokeToken:
    def setup_method(self):
        # 매 테스트마다 메모리 블랙리스트 초기화
        with auth_mod._lock:
            auth_mod._revoked_tokens.clear()
            auth_mod._revoked_users.clear()

    def test_revoke_adds_to_memory(self):
        future = datetime.now(timezone.utc).timestamp() + 3600
        revoke_token("test-jti-001", future)
        assert "test-jti-001" in auth_mod._revoked_tokens

    def test_revoked_token_is_detected(self):
        future = datetime.now(timezone.utc).timestamp() + 3600
        revoke_token("test-jti-002", future)
        # iat를 과거로 설정
        past_iat = datetime.now(timezone.utc).timestamp() - 100
        assert is_token_revoked("test-jti-002", "user1", past_iat) is True

    def test_expired_token_not_detected(self):
        # 이미 만료된 토큰을 추가
        past_expiry = datetime.now(timezone.utc).timestamp() - 1
        revoke_token("test-jti-expired", past_expiry)
        # 만료된 항목은 정리되므로 False 반환
        result = is_token_revoked("test-jti-expired", "user1", 0)
        assert result is False

    def test_nonexistent_jti_not_revoked(self):
        result = is_token_revoked("nonexistent-jti-xyz", "user999", 0)
        assert result is False


# ── revoke_user_tokens ────────────────────────────────────────────────────────

class TestRevokeUserTokens:
    def setup_method(self):
        with auth_mod._lock:
            auth_mod._revoked_tokens.clear()
            auth_mod._revoked_users.clear()

    def test_revoke_user_adds_to_memory(self):
        revoke_user_tokens(42)
        assert "42" in auth_mod._revoked_users

    def test_old_token_from_revoked_user_is_blocked(self):
        revoke_user_tokens(99)
        revoked_ts = auth_mod._revoked_users["99"]
        # iat < revoked_ts → blocked
        old_iat = revoked_ts - 100
        result = is_token_revoked("any-jti", "99", old_iat)
        assert result is True

    def test_new_token_from_revoked_user_passes(self):
        revoke_user_tokens(88)
        revoked_ts = auth_mod._revoked_users["88"]
        # iat > revoked_ts → not blocked
        new_iat = revoked_ts + 100
        result = is_token_revoked("any-jti", "88", new_iat)
        assert result is False


# ── hash_password / verify_password ──────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_returns_string(self):
        h = hash_password("testpassword123!")
        assert isinstance(h, str)

    def test_verify_correct_password(self):
        h = hash_password("correcthorse!")
        assert verify_password("correcthorse!", h) is True

    def test_verify_wrong_password(self):
        h = hash_password("correcthorse!")
        assert verify_password("wrongpass!", h) is False

    def test_hash_is_unique(self):
        h1 = hash_password("samepass")
        h2 = hash_password("samepass")
        # bcrypt salt → 항상 다름
        assert h1 != h2

    def test_long_password_truncated_to_72(self):
        # 72바이트 절단 → 동일한 앞부분이면 동일 검증 통과
        long = "a" * 80
        h = hash_password(long)
        assert verify_password("a" * 80, h) is True

    def test_empty_password(self):
        h = hash_password("")
        assert verify_password("", h) is True
        assert verify_password("x", h) is False


# ── create_access_token / create_refresh_token / decode_token ─────────────────

class TestTokenCreation:
    def test_create_access_token_returns_string(self):
        token = create_access_token(1)
        assert isinstance(token, str)
        assert len(token) > 10

    def test_decode_access_token(self):
        token = create_access_token(42)
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_access_token_has_exp_sub(self):
        token = create_access_token(5)
        payload = decode_token(token)
        assert "exp" in payload
        assert "sub" in payload

    def test_create_refresh_token(self):
        token = create_refresh_token(10)
        payload = decode_token(token, is_refresh=True)
        assert payload["sub"] == "10"
        assert payload["type"] == "refresh"

    def test_access_token_wrong_secret_fails(self):
        import jwt
        token = create_access_token(1)
        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(token, "wrong-secret", algorithms=["HS256"], options={"require": ["exp", "sub"]})

    def test_create_with_extra_payload(self):
        token = create_access_token(7, extra={"role": "admin"})
        payload = decode_token(token)
        assert payload.get("role") == "admin"


# ── get_current_user ──────────────────────────────────────────────────────────

class TestGetCurrentUser:
    def test_valid_token_returns_user_id(self):
        from unittest.mock import MagicMock
        from src.core.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials

        token = create_access_token(123)
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        user = get_current_user(creds)
        assert user["user_id"] == 123

    def test_refresh_token_raises_401(self):
        from src.core.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException

        token = create_refresh_token(1)
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401

    def test_invalid_token_raises_401(self):
        from src.core.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token.xyz")
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401

    def test_expired_token_raises_401(self):
        import jwt as _jwt
        from src.core.auth import get_current_user, SECRET_KEY, ALGORITHM
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException

        payload = {
            "sub": "1",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
            "type": "access",
        }
        expired_token = _jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token)
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401

    def test_blacklisted_token_raises_401(self):
        from src.core.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException

        with auth_mod._lock:
            auth_mod._revoked_tokens.clear()

        # 토큰 생성
        token = create_access_token(555)
        payload = decode_token(token)
        jti = payload.get("jti", f"{payload['sub']}:{payload.get('iat', 0)}")
        exp = float(payload["exp"])
        revoke_token(jti, exp)

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc:
            get_current_user(creds)
        assert exc.value.status_code == 401
