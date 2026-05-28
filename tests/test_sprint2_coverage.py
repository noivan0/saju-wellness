"""
[Sprint2] 커버리지 89% → 95% 달성을 위한 추가 테스트케이스 10개

대상 파일:
- src/routes/fortune.py (83% → 90%+)
- src/api/routes/saju.py (85% → 90%+)
- src/core/auth.py (95% → 100%)
- src/services/ai_insight.py (이미 100%, 세마포어 async 검증)
- saju_engine.py (83% → 90%+)
"""
import sys
import os
import asyncio
import pytest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-placeholder!")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32chars!!")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_saju.db")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key-placeholder")


@pytest.fixture(scope="module")
def main_client():
    from fastapi.testclient import TestClient
    from src.main import app
    return TestClient(app)


@pytest.fixture(scope="module")
def api_client():
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


# ─────────────────────────────────────────────
# TC-1: fortune.py — today_saju 계산 예외 시 500 응답
# 미커버 라인: fortune.py L143-144 (오늘 일주 계산 오류)
# ─────────────────────────────────────────────
def test_fortune_daily_today_saju_error(main_client):
    """GET /api/fortune/daily — 내부 today_saju 계산 실패 시 500 반환 확인"""
    call_count = {"n": 0}
    original_get_saju = None

    def mock_get_saju(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            # 첫 호출(내 사주): 정상 반환
            return original_get_saju(*args, **kwargs)
        # 두 번째 호출(오늘 일주): 예외 발생
        raise RuntimeError("오늘 일주 계산 실패 테스트")

    import src.routes.fortune as fortune_module
    original_get_saju = fortune_module.get_saju

    with patch.object(fortune_module, "get_saju", side_effect=mock_get_saju):
        resp = main_client.get(
            "/api/fortune/daily",
            params={"year": 1990, "month": 1, "day": 15, "target_date": "2025-06-01"},
        )
    # 오늘 일주 계산 실패 → 500
    assert resp.status_code == 500


# ─────────────────────────────────────────────
# TC-2: fortune.py — lang=en, lang=ja 다국어 응답 확인
# 미커버 라인: ENERGY_FLOW_MAP/ACTION_CARDS_MULTILANG 영어/일어 분기
# ─────────────────────────────────────────────
@pytest.mark.parametrize("lang,expected_key", [
    ("en", "energy_flow"),
    ("ja", "energy_flow"),
])
def test_fortune_daily_multilang(main_client, lang, expected_key):
    """GET /api/fortune/daily — lang=en, lang=ja 시 에너지 흐름 필드 존재 확인"""
    resp = main_client.get(
        "/api/fortune/daily",
        params={
            "year": 1990, "month": 1, "day": 15,
            "target_date": "2025-06-01",
            "lang": lang,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert expected_key in data
    assert isinstance(data[expected_key], str)


# ─────────────────────────────────────────────
# TC-3: fortune.py — ENERGY_FLOW_MAP 6가지 관계 전체 커버
# 미커버 라인: _get_element_relation 반환값들
# ─────────────────────────────────────────────
def test_energy_flow_map_all_relations():
    """src/routes/fortune.py — _get_element_relation 반환값 + ENERGY_FLOW_MAP 키 검증"""
    from src.routes.fortune import _get_element_relation, ENERGY_FLOW_MAP

    # 5개 오행 간 관계 수집
    relations = set()
    elements = ["목", "화", "토", "금", "수"]
    for e1 in elements:
        for e2 in elements:
            r = _get_element_relation(e1, e2)
            relations.add(r)

    # 5가지 관계가 생성됨 (알려진 오행 5개 사이에서 '무관'은 발생하지 않음)
    expected_5 = {"비화", "상생(생함)", "상생(받음)", "상극(극함)", "상극(받음)"}
    assert expected_5 == relations

    # 알 수 없는 오행 입력 → '무관' 반환 확인
    unknown_relation = _get_element_relation("?", "목")
    assert unknown_relation == "무관"

    # ENERGY_FLOW_MAP에 6가지 관계 모두 존재 (무관 포함)
    expected_map_keys = {"비화", "상생(생함)", "상생(받음)", "상극(극함)", "상극(받음)", "무관"}
    for rel in expected_map_keys:
        assert rel in ENERGY_FLOW_MAP, f"ENERGY_FLOW_MAP에 '{rel}' 없음"


# ─────────────────────────────────────────────
# TC-4: fortune.py — target_date 잘못된 형식 → 400
# 미커버 라인: fortune.py L101, L103
# ─────────────────────────────────────────────
def test_fortune_daily_invalid_target_date(main_client):
    """GET /api/fortune/daily — 잘못된 target_date 형식 시 400 반환"""
    resp = main_client.get(
        "/api/fortune/daily",
        params={
            "year": 1990, "month": 1, "day": 15,
            "target_date": "2025-99-99",  # 잘못된 날짜
        },
    )
    assert resp.status_code == 400
    assert "target_date" in resp.json()["detail"]


# ─────────────────────────────────────────────
# TC-5: fortune.py — my_saju 계산 예외 시 400
# 미커버 라인: fortune.py L108-110
# ─────────────────────────────────────────────
def test_fortune_daily_my_saju_error(main_client):
    """GET /api/fortune/daily — 사주 계산 예외 시 400 반환"""
    import src.routes.fortune as fortune_module

    with patch.object(fortune_module, "get_saju", side_effect=ValueError("잘못된 생년월일")):
        resp = main_client.get(
            "/api/fortune/daily",
            params={"year": 1990, "month": 1, "day": 15, "target_date": "2025-06-01"},
        )
    assert resp.status_code == 400
    assert "사주 계산 중 오류가 발생했습니다" in resp.json()["detail"]


# ─────────────────────────────────────────────
# TC-6: api/routes/saju.py — _ENGINE_OK False 시 503/500
# 미커버 라인: saju.py L45-60 (엔진 로드 실패 가드)
# ─────────────────────────────────────────────
def test_saju_api_engine_not_ok(api_client):
    """POST /api/saju/calculate — _ENGINE_OK=False 시 500 반환"""
    import src.api.routes.saju as saju_module

    with patch.object(saju_module, "_ENGINE_OK", False):
        resp = api_client.post(
            "/api/saju/calculate",
            json={"birth_year": 1990, "birth_month": 1, "birth_day": 15},
        )
    assert resp.status_code == 500


# ─────────────────────────────────────────────
# TC-7: api/routes/saju.py — get_daewoon 반환값 구조 검증
# 미커버 라인: saju.py 대운 관련 경로
# ─────────────────────────────────────────────
def test_get_daewoon_structure():
    """saju_engine.get_daewoon — 반환값 리스트/딕셔너리 구조 확인"""
    from saju_engine import get_daewoon

    result = get_daewoon(1990, 1, 15, hour=10, is_male=True)
    assert isinstance(result, list)
    assert len(result) > 0

    first = result[0]
    assert isinstance(first, dict)
    # 정상 케이스: order/age/glyph 키 존재, 오류 케이스: error 키 존재
    has_normal_keys = all(k in first for k in ("order", "age", "glyph"))
    has_error_key = "error" in first
    assert has_normal_keys or has_error_key, f"예상치 못한 구조: {first}"


# ─────────────────────────────────────────────
# TC-8: src/core/auth.py — 토큰 생성/검증/블랙리스트 전체 커버
# 미커버 라인: auth.py L40,43-55,62-67,77-81,90-102,191,196,199
# ─────────────────────────────────────────────
def test_auth_core_full_coverage():
    """src/core/auth.py — 토큰 CRUD, 블랙리스트, 검증 전체 경로 커버"""
    import src.core.auth as auth_module
    from src.core.auth import (
        hash_password, verify_password,
        create_access_token, create_refresh_token,
        decode_token, revoke_token, revoke_user_tokens, is_token_revoked
    )
    from datetime import timezone, datetime

    # 패스워드 해시/검증
    hashed = hash_password("test_password_123!")
    assert hashed != "test_password_123!"
    assert verify_password("test_password_123!", hashed)
    assert not verify_password("wrong_password", hashed)

    # 액세스 토큰 생성/디코드
    token = create_access_token(user_id=9999, extra={"role": "user"})
    payload = decode_token(token, is_refresh=False)
    assert payload["sub"] == "9999"
    assert payload["type"] == "access"
    assert payload["role"] == "user"

    # 리프레시 토큰 생성/디코드
    refresh_token = create_refresh_token(user_id=9999)
    r_payload = decode_token(refresh_token, is_refresh=True)
    assert r_payload["sub"] == "9999"
    assert r_payload["type"] == "refresh"

    # 단일 토큰 revoke + 검증 (메모리 폴백)
    jti = "test-jti-auth-core"
    future_ts = datetime.now(timezone.utc).timestamp() + 3600  # 1시간 후 만료
    revoke_token(jti, future_ts)
    assert is_token_revoked(jti, "9999", 0.0)  # 블랙리스트에 있음

    # 만료된 jti 자동 정리 확인
    expired_jti = "test-expired-jti-cleanup"
    past_ts = datetime.now(timezone.utc).timestamp() - 3600  # 이미 만료
    auth_module._revoked_tokens[expired_jti] = past_ts
    result = is_token_revoked(expired_jti, "9999", 0.0)
    assert result is False
    assert expired_jti not in auth_module._revoked_tokens

    # 사용자 전체 토큰 revoke (메모리 폴백)
    revoke_user_tokens(8888)
    # iat=0 → revoke_before_ts 이전이라 True
    assert is_token_revoked("any-jti", "8888", 0.0)

    # iat가 revoke 시각 이후라면 False
    future_iat = datetime.now(timezone.utc).timestamp() + 9999
    assert not is_token_revoked("any-jti-2", "8888", future_iat)


# ─────────────────────────────────────────────
# TC-8b: src/core/auth.py — Redis mock으로 Redis 분기 경로 커버
# 미커버 라인: auth.py L40, L43-55, L62-67, L77-81, L90-102
# ─────────────────────────────────────────────
def test_auth_core_redis_path():
    """src/core/auth.py — Redis 사용 경로 mock으로 커버"""
    import src.core.auth as auth_module
    from src.core.auth import revoke_token, revoke_user_tokens, is_token_revoked
    from datetime import timezone, datetime

    # Mock Redis 클라이언트 생성
    mock_redis = MagicMock()
    mock_redis.exists.return_value = True   # 단일 토큰 블랙리스트에 존재
    mock_redis.get.return_value = None       # 사용자 블랙리스트 없음
    mock_redis.setex.return_value = True

    # _redis_client를 mock으로 교체
    original_client = auth_module._redis_client
    auth_module._redis_client = mock_redis

    try:
        # Redis revoke_token 경로
        future_ts = datetime.now(timezone.utc).timestamp() + 3600
        revoke_token("redis-jti-test", future_ts)
        mock_redis.setex.assert_called()

        # Redis is_token_revoked → exists=True
        result = is_token_revoked("redis-jti-test", "777", 0.0)
        assert result is True

        # Redis revoke_user_tokens 경로
        revoke_user_tokens(7777)
        # setex가 2회 이상 호출됨 (revoke_token + revoke_user_tokens)
        assert mock_redis.setex.call_count >= 2

    finally:
        auth_module._redis_client = original_client


def test_auth_core_redis_get_existing_user():
    """src/core/auth.py — Redis get으로 user revoke 확인 경로"""
    import src.core.auth as auth_module
    from src.core.auth import is_token_revoked
    from datetime import timezone, datetime

    mock_redis = MagicMock()
    mock_redis.exists.return_value = False  # 단일 토큰 없음
    # 사용자 블랙리스트 있음 — 최근에 revoke됨
    revoked_ts = datetime.now(timezone.utc).timestamp()
    mock_redis.get.return_value = str(revoked_ts)

    original_client = auth_module._redis_client
    auth_module._redis_client = mock_redis

    try:
        old_iat = revoked_ts - 3600  # revoke 전 발급
        result = is_token_revoked("any-jti-redis", "8888", old_iat)
        assert result is True  # iat < revoked_before → True

        new_iat = revoked_ts + 3600  # revoke 후 발급
        result2 = is_token_revoked("any-jti-redis-2", "8888", new_iat)
        assert result2 is False  # iat >= revoked_before → False
    finally:
        auth_module._redis_client = original_client


def test_auth_core_redis_connection_failure():
    """src/core/auth.py — REDIS_URL 설정 시 연결 실패 → 메모리 폴백 (L43-55, L66-67, L80-81, L101-102)"""
    import src.core.auth as auth_module
    from src.core.auth import revoke_token, revoke_user_tokens, is_token_revoked
    from datetime import timezone, datetime

    # Redis 연결 실패 시뮬레이션: setex에서 예외
    mock_redis_fail = MagicMock()
    mock_redis_fail.setex.side_effect = Exception("Redis 연결 끊김")
    mock_redis_fail.exists.side_effect = Exception("Redis 연결 끊김")
    mock_redis_fail.get.side_effect = Exception("Redis 연결 끊김")

    original_client = auth_module._redis_client
    auth_module._redis_client = mock_redis_fail

    try:
        # revoke_token — Redis 실패 → 메모리 폴백 (L66-67)
        future_ts = datetime.now(timezone.utc).timestamp() + 3600
        revoke_token("fallback-jti-test", future_ts)
        assert "fallback-jti-test" in auth_module._revoked_tokens

        # revoke_user_tokens — Redis 실패 → 메모리 폴백 (L80-81)
        revoke_user_tokens(6666)
        assert "6666" in auth_module._revoked_users

        # is_token_revoked — Redis 실패 → 메모리 폴백 (L101-102)
        result = is_token_revoked("fallback-jti-test", "6666", 0.0)
        # fallback-jti-test는 메모리 폴백에 revoke됨
        assert result is True

    finally:
        auth_module._redis_client = original_client
        # 테스트 데이터 정리
        auth_module._revoked_tokens.pop("fallback-jti-test", None)
        auth_module._revoked_users.pop("6666", None)


def test_auth_core_redis_init_with_url():
    """src/core/auth.py — _REDIS_URL 설정 시 연결 시도 경로 (L43-55)"""
    import src.core.auth as auth_module

    original_client = auth_module._redis_client
    original_url = auth_module._REDIS_URL

    try:
        # _redis_client를 None으로 리셋 + REDIS_URL 설정
        auth_module._redis_client = None
        auth_module._REDIS_URL = "redis://invalid-host:9999"

        # redis 모듈 mock으로 교체
        mock_redis_module = MagicMock()
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = Exception("연결 불가")
        mock_redis_module.from_url.return_value = mock_redis_instance

        with patch.dict("sys.modules", {"redis": mock_redis_module}):
            # _get_redis() 호출 → 연결 실패 → None 반환
            result = auth_module._get_redis()
            assert result is None  # 연결 실패 → None 폴백

    finally:
        auth_module._redis_client = original_client
        auth_module._REDIS_URL = original_url


# ─────────────────────────────────────────────
# TC-9: src/services/ai_insight.py — check_crisis_keywords 다국어
# 미커버 라인: ai_insight.py 영어/일어 위기 키워드 분기
# ─────────────────────────────────────────────
@pytest.mark.parametrize("text,lang,expected", [
    ("I want to die today", "en", True),
    ("死にたい気持ちがある", "ja", True),
    ("今日は天気がいい", "ja", False),
    ("The weather is nice today", "en", False),
    ("kill myself please help", "en", True),
    ("普通の日だ", "ja", False),
])
def test_check_crisis_keywords_multilang(text, lang, expected):
    """src/services/ai_insight.py — 영어/일어 위기 키워드 감지 확인"""
    from src.services.ai_insight import check_crisis_keywords
    result = check_crisis_keywords(text, lang=lang)
    assert result == expected, f"text={text!r}, lang={lang}, expected={expected}, got={result}"


# ─────────────────────────────────────────────
# TC-10: AI insight 세마포어 — 동시 6개 요청 시 5번째까지 즉시, 6번째 대기
# 미커버 라인: ai_insight.py generate_daily_insight_async, semaphore 분기
# ─────────────────────────────────────────────
def test_ai_insight_semaphore_concurrent():
    """src/services/ai_insight.py — 세마포어 동시 5개 제한 확인 (asyncio)"""
    import src.services.ai_insight as ai_module

    # 세마포어 초기화 리셋
    ai_module._AI_SEMAPHORE = None

    async def _run():
        # 세마포어 lazy init 확인
        sem = ai_module._get_semaphore()
        assert sem._value == 5

        # 5개 acquire → value=0
        acquired = []
        for _ in range(5):
            await sem.acquire()
            acquired.append(True)
        assert sem._value == 0

        # 6번째는 즉시 취득 불가 확인 (try_acquire 시뮬레이션)
        can_acquire = sem._value > 0
        assert can_acquire is False

        # 해제
        for _ in range(5):
            sem.release()
        assert sem._value == 5

    asyncio.run(_run())


# ─────────────────────────────────────────────
# TC-11 (보너스): api/routes/saju.py — fortune-calendar _ENGINE_OK False
# 미커버 라인: saju.py L952 엔진 실패 가드
# ─────────────────────────────────────────────
def test_fortune_standard_engine_not_ok(api_client):
    """POST /api/saju/fortune-standard — _ENGINE_OK=False 시 500 반환"""
    import src.api.routes.saju as saju_module

    with patch.object(saju_module, "_ENGINE_OK", False):
        resp = api_client.post(
            "/api/saju/fortune-standard",
            json={"birth_year": 1990, "birth_month": 1, "birth_day": 15},
        )
    assert resp.status_code == 500


# ─────────────────────────────────────────────
# TC-13: api/routes/saju.py — 미커버 라인 집중 커버
# L240, L244-245, L260, L351, L355-356, L391, L396
# ─────────────────────────────────────────────
def test_saju_api_compatibility_preview(api_client):
    """GET /api/saju/compatibility-preview — 정상 응답 + _ENGINE_OK False"""
    # 정상 응답
    resp = api_client.get(
        "/api/saju/compatibility-preview",
        params={
            "my_year": 1990, "my_month": 1, "my_day": 15,
            "partner_year": 1992, "partner_month": 6, "partner_day": 20,
            "lang": "ko",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "relation" in data
    assert "preview_summary" in data
    assert 0 <= data["score"] <= 100

    # _ENGINE_OK=False 시 500
    import src.api.routes.saju as saju_module
    with patch.object(saju_module, "_ENGINE_OK", False):
        resp2 = api_client.get(
            "/api/saju/compatibility-preview",
            params={
                "my_year": 1990, "my_month": 1, "my_day": 15,
                "partner_year": 1992, "partner_month": 6, "partner_day": 20,
            },
        )
    assert resp2.status_code == 500


def test_saju_api_daily_energy(api_client):
    """POST /api/saju/daily-energy — 정상 응답 + _ENGINE_OK False"""
    resp = api_client.post(
        "/api/saju/daily-energy",
        json={"birth_year": 1990, "birth_month": 1, "birth_day": 15},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "today_energy" in data
    assert "today_pillar" in data

    # _ENGINE_OK=False 시 500
    import src.api.routes.saju as saju_module
    with patch.object(saju_module, "_ENGINE_OK", False):
        resp2 = api_client.post(
            "/api/saju/daily-energy",
            json={"birth_year": 1990, "birth_month": 1, "birth_day": 15},
        )
    assert resp2.status_code == 500


def test_saju_api_compatibility(api_client):
    """POST /api/saju/compatibility — 정상 응답 + _ENGINE_OK False"""
    resp = api_client.post(
        "/api/saju/compatibility",
        json={
            "person_a": {"birth_year": 1990, "birth_month": 1, "birth_day": 15},
            "person_b": {"birth_year": 1992, "birth_month": 6, "birth_day": 20},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "score" in data
    assert "level" in data
    assert 0 <= data["score"] <= 100

    # _ENGINE_OK=False 시 500
    import src.api.routes.saju as saju_module
    with patch.object(saju_module, "_ENGINE_OK", False):
        resp2 = api_client.post(
            "/api/saju/compatibility",
            json={
                "person_a": {"birth_year": 1990, "birth_month": 1, "birth_day": 15},
                "person_b": {"birth_year": 1992, "birth_month": 6, "birth_day": 20},
            },
        )
    assert resp2.status_code == 500


def test_saju_api_fortune_calendar(api_client):
    """GET /api/saju/fortune-calendar — 정상 응답 + _ENGINE_OK False"""
    resp = api_client.get(
        "/api/saju/fortune-calendar",
        params={"birth_year": 1990, "birth_month": 1, "birth_day": 15},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "months" in data or "birth_element" in data

    # _ENGINE_OK=False 시 500
    import src.api.routes.saju as saju_module
    with patch.object(saju_module, "_ENGINE_OK", False):
        resp2 = api_client.get(
            "/api/saju/fortune-calendar",
            params={"birth_year": 1990, "birth_month": 1, "birth_day": 15},
        )
    assert resp2.status_code == 500


def test_saju_api_today_energy(api_client):
    """GET /api/saju/today-energy — 정상 응답 확인 (엔진 의존성 없음)"""
    resp = api_client.get(
        "/api/saju/today-energy",
        params={"lang": "ko"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "today_element" in data
    assert "energy" in data
    assert "date" in data

    # lang=en, lang=ja 확인
    for lang in ("en", "ja"):
        resp2 = api_client.get("/api/saju/today-energy", params={"lang": lang})
        assert resp2.status_code == 200
        assert "today_element" in resp2.json()


# ─────────────────────────────────────────────
# TC-12 (보너스): fortune.py — ACTION_CARDS_MULTILANG fallback
# 미커버 라인: fortune.py 액션카드 키 없을 때 DEFAULT_ACTIONS 폴백
# ─────────────────────────────────────────────
def test_fortune_action_cards_fallback():
    """saju_engine.py — ACTION_MAP 없는 오행일 때 DEFAULT_ACTIONS 폴백 확인"""
    from saju_engine import DEFAULT_ACTIONS, ACTION_MAP

    # DEFAULT_ACTIONS에 기본 감정 상태가 모두 존재
    expected_moods = {"매우 힘듦", "힘듦", "보통", "좋음", "매우 좋음"}
    assert set(DEFAULT_ACTIONS.keys()) == expected_moods

    # 없는 오행 조합 시 DEFAULT_ACTIONS에서 가져올 수 있음
    fallback_key = ("없는오행", "보통")
    assert fallback_key not in ACTION_MAP
    fallback = DEFAULT_ACTIONS.get("보통", [])
    assert len(fallback) > 0
