"""
test_auth_core_r39.py
src/core/auth.py 미커버 구간 R39

L42: is_token_revoked() — 만료된 토큰 del 정리 경로
L45-46: is_token_revoked() — revoke_user() 이후 iat < revoked_before_ts 경로
"""
import sys, os, time, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestIsTokenRevoked:
    def test_expired_jti_removed_and_returns_false(self):
        """블랙리스트에 만료된 jti → del 처리 후 False 반환 (L42)"""
        from src.core.auth import revoke_token, is_token_revoked
        import time
        # 이미 만료된 것처럼 exp를 과거로 설정
        jti = "expired-jti-test-001"
        past_exp = time.time() - 1  # 이미 만료
        revoke_token(jti, past_exp)
        # 만료된 토큰 → del 후 False
        result = is_token_revoked(jti, "1", time.time() - 100)
        assert result is False  # 만료됐으므로 정리 후 False

    def test_user_revoke_blocks_old_token(self):
        """revoke_user_tokens() 이후 발급된 이전 토큰 → True (L45-46)"""
        from src.core.auth import revoke_user_tokens, is_token_revoked
        import time
        user_id = 99999
        old_iat = time.time() - 3600  # 1시간 전 발급
        revoke_user_tokens(user_id)  # 지금 시점으로 revoke
        # iat < revoked_before_ts → True
        result = is_token_revoked("some-jti-002", str(user_id), old_iat)
        assert result is True

    def test_user_revoke_allows_new_token(self):
        """revoke_user_tokens() 이전 iat → False (새 토큰은 허용)"""
        from src.core.auth import revoke_user_tokens, is_token_revoked
        import time
        user_id = 88888
        revoke_user_tokens(user_id)
        new_iat = time.time() + 1  # revoke 이후 발급
        result = is_token_revoked("some-jti-003", str(user_id), new_iat)
        assert result is False

    def test_valid_jti_not_expired(self):
        """블랙리스트에 있고 아직 만료 안 된 jti → True"""
        from src.core.auth import revoke_token, is_token_revoked
        import time
        jti = "valid-jti-test-004"
        future_exp = time.time() + 3600  # 1시간 후 만료
        revoke_token(jti, future_exp)
        result = is_token_revoked(jti, "2", time.time())
        assert result is True
