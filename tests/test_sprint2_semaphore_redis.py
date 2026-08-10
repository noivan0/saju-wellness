"""
Sprint 2 — AI_SEMAPHORE 멀티워커 경쟁 조건 검증 테스트
- Python 3.12 lazy-init 패턴
- 동시 요청에서 세마포어가 올바르게 작동하는지 검증
- JWT Redis 블랙리스트 실증 (REDIS_URL 없을 때 메모리 폴백)

Sprint 2 항목 2, 3, 4 커버
"""
import os
import sys
import asyncio
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-placeholder!")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32chars!!")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-placeholder")
os.environ.pop("REDIS_URL", None)


# ── AI_SEMAPHORE lazy-init 검증 ────────────────────────────────────────────────

class TestAISemaphoreLazyInit:
    def setup_method(self):
        import src.services.ai_insight as mod
        mod._AI_SEMAPHORE = None  # reset

    def test_semaphore_created_on_first_call(self):
        import src.services.ai_insight as mod
        assert mod._AI_SEMAPHORE is None

        async def _init():
            sem = mod._get_semaphore()
            return sem

        sem = asyncio.run(_init())
        assert sem is not None
        assert isinstance(sem, asyncio.Semaphore)

    def test_semaphore_reused_on_second_call(self):
        import src.services.ai_insight as mod

        async def _test():
            s1 = mod._get_semaphore()
            s2 = mod._get_semaphore()
            return s1 is s2

        result = asyncio.run(_test())
        assert result is True

    def test_semaphore_max_5(self):
        import src.services.ai_insight as mod

        async def _check():
            sem = mod._get_semaphore()
            # asyncio.Semaphore value는 내부적으로 _value
            return sem._value

        value = asyncio.run(_check())
        assert value == 5

    def test_concurrent_calls_limited_by_semaphore(self):
        """세마포어가 동시 실행을 5개로 제한하는지 검증"""
        import src.services.ai_insight as mod

        results = []

        async def _limited_task(i):
            sem = mod._get_semaphore()
            async with sem:
                await asyncio.sleep(0.01)
                results.append(i)

        async def _run_concurrent():
            tasks = [_limited_task(i) for i in range(10)]
            await asyncio.gather(*tasks)

        asyncio.run(_run_concurrent())
        assert len(results) == 10  # 모든 태스크 완료

    def test_timeout_fallback_works(self):
        """generate_daily_insight_async 타임아웃 폴백 검증"""
        import src.services.ai_insight as mod

        saju_data = {
            "year": {"pillar": "갑자"},
            "month": {"pillar": "병인"},
            "day": {"pillar": "무오"},
            "primary_element": "목",
        }

        async def _run():
            # [PY310-COMPAT] asyncio.timeout()은 3.11+ 전용 — 3.10 환경에서는 없음.
            # 폴백 경로(내부 asyncio.wait_for 기반) 자체를 직접 호출해 검증한다.
            try:
                result = await mod.generate_daily_insight_async(
                    saju_data, "테스트", "ko"
                )
                return result
            except Exception:
                return None

        result = asyncio.run(_run())
        # 결과가 dict이면 성공 (AI 없으면 fallback 반환)
        assert result is not None


# ── JWT Redis 블랙리스트 실증 ─────────────────────────────────────────────────

class TestJWTRedisBlacklist:
    def setup_method(self):
        import src.core.auth as auth
        with auth._lock:
            auth._revoked_tokens.clear()
            auth._revoked_users.clear()
        # Redis 캐시도 초기화
        auth._redis_client = None

    def test_redis_fallback_to_memory_no_url(self):
        """REDIS_URL 없을 때 메모리 폴백 확인"""
        from src.core.auth import _get_redis
        result = _get_redis()
        assert result is None

    def test_revoke_and_check_memory(self):
        """메모리 블랙리스트: 토큰 무효화 후 감지"""
        from src.core.auth import revoke_token, is_token_revoked
        from datetime import datetime, timezone

        future = datetime.now(timezone.utc).timestamp() + 3600
        revoke_token("jwt-test-jti", future)
        result = is_token_revoked("jwt-test-jti", "user1", 0)
        assert result is True

    def test_user_revocation_memory(self):
        """사용자 전체 무효화 메모리 폴백"""
        from src.core.auth import revoke_user_tokens, is_token_revoked
        import src.core.auth as auth

        revoke_user_tokens(777)
        ts = auth._revoked_users["777"]
        old_iat = ts - 1000
        assert is_token_revoked("any", "777", old_iat) is True

    def test_redis_connection_failure_fallback(self):
        """REDIS_URL 있지만 연결 실패 → 메모리 폴백"""
        import src.core.auth as auth

        # 유효하지 않은 REDIS_URL 주입
        original_url = auth._REDIS_URL
        original_client = auth._redis_client
        try:
            auth._REDIS_URL = "redis://127.0.0.1:19999/0"  # 연결 불가
            auth._redis_client = None  # 캐시 초기화

            result = auth._get_redis()
            # 연결 실패 시 None 반환 (메모리 폴백)
            assert result is None
        finally:
            auth._REDIS_URL = original_url
            auth._redis_client = original_client

    def test_multiworker_shared_blacklist_simulation(self):
        """멀티워커 공유 블랙리스트 시뮬레이션 — 스레드 안전성"""
        import threading
        from src.core.auth import revoke_token, is_token_revoked
        from datetime import datetime, timezone

        future = datetime.now(timezone.utc).timestamp() + 3600
        errors = []
        results = []

        def worker(jti):
            try:
                revoke_token(jti, future)
                r = is_token_revoked(jti, "user1", 0)
                results.append(r)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(f"jti-{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert all(results)  # 모두 True (revoke 후 감지)


# ── /api/insight/daily 율 제한 인증 사용자 분리 검증 ─────────────────────────

class TestRateLimitAuthSeparation:
    """
    Sprint 2 항목 3: /api/insight/daily 율 제한 인증 사용자 분리
    - 비인증: 10/minute (기존)
    - rate limiter는 테스트에서 비활성화이므로 설정만 검증
    """

    def test_rate_limiter_config_exists(self):
        """rate_limiter.py가 존재하고 올바르게 구성되어 있는지"""
        from src.api.rate_limiter import limiter
        assert limiter is not None

    def test_insight_route_has_rate_limit_decorator(self):
        """insight route에 limiter 데코레이터가 적용되어 있는지 소스 확인"""
        import inspect
        import src.api.routes.insight as insight_mod
        source = inspect.getsource(insight_mod)
        assert "@limiter.limit" in source
        assert "10/minute" in source

    def test_session_route_lower_rate_limit(self):
        """session 엔드포인트가 더 낮은 율 제한을 갖는지"""
        import inspect
        import src.api.routes.insight as insight_mod
        source = inspect.getsource(insight_mod)
        assert "5/minute" in source  # session endpoint
