"""auth.py 단위 테스트"""
import pytest, os
os.environ["SECRET_KEY"] = "test_secret_key_32chars_minimum_"
os.environ["REFRESH_SECRET_KEY"] = "test_refresh_secret_32chars_min_"

from src.core.auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "mypassword123"
        hashed = hash_password(pw)
        assert verify_password(pw, hashed)

    def test_wrong_password_rejected(self):
        hashed = hash_password("correct")
        assert not verify_password("wrong", hashed)

    def test_72byte_truncation(self):
        """CVE-2024-0232: 72바이트 초과 입력 — 절단 후 동일 해시"""
        long_pw = "a" * 100
        hashed = hash_password(long_pw)
        # 72바이트로 절단되므로 처음 72자는 동일하게 검증
        assert verify_password("a" * 72, hashed)


class TestJWTTokens:
    def test_access_token_create_decode(self):
        token = create_access_token(42)
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_refresh_token_separate_secret(self):
        token = create_refresh_token(42)
        payload = decode_token(token, is_refresh=True)
        assert payload["type"] == "refresh"

    def test_refresh_cannot_decode_as_access(self):
        """refresh token을 access로 decode하면 실패"""
        import jwt
        token = create_refresh_token(42)
        with pytest.raises((jwt.InvalidSignatureError, jwt.DecodeError)):
            decode_token(token, is_refresh=False)

    def test_alg_none_rejected(self):
        """alg:none 공격 차단 확인"""
        import jwt
        malicious = jwt.encode({"sub": "1", "type": "access"}, "", algorithm="none")
        with pytest.raises(Exception):
            decode_token(malicious)

    def test_exp_required(self):
        """exp 클레임 없는 토큰 거부"""
        import jwt
        no_exp = jwt.encode({"sub": "1"}, os.environ["SECRET_KEY"], algorithm="HS256")
        with pytest.raises(jwt.MissingRequiredClaimError):
            decode_token(no_exp)
