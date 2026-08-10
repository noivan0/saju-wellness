"""
인증 유틸리티 — 완전판
[CVE-2024-33664] python-jose → PyJWT==2.9.0
[CVE-2024-0232] bcrypt==4.2.0 72바이트 명시 절단
[A07-REVOKE] 탈퇴/로그아웃 시 JWT 블랙리스트 + revoke_user_tokens
[HIGH-3] Redis 기반 블랙리스트 — 멀티워커 공유. REDIS_URL 미설정 시 메모리 폴백.
"""
import os
import logging
import threading
import uuid
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Set
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# ── JWT 블랙리스트 ─────────────────────────────────────────────────────────────
# Redis 기반 (REDIS_URL 있을 때) or 메모리 폴백 (단일 워커 환경)
# Redis key: blacklist:token:{jti}  TTL=토큰 만료까지
#            blacklist:user:{user_id}  TTL=30일
_REDIS_URL = os.getenv("REDIS_URL", "")
_redis_client = None  # lazy init
_redis_lock = threading.Lock()

# 메모리 폴백 (Redis 없을 때)
_revoked_tokens: dict = {}      # jti → expiry_ts
_revoked_users: dict = {}       # user_id → revoked_before_ts
_lock = threading.Lock()

_BLACKLIST_USER_TTL = 30 * 24 * 3600  # 30일 (초)


def _get_redis():
    """Redis 클라이언트 lazy init. REDIS_URL 없거나 연결 실패 시 None 반환."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not _REDIS_URL:
        return None
    with _redis_lock:
        if _redis_client is not None:
            return _redis_client
        try:
            import redis
            client = redis.from_url(_REDIS_URL, decode_responses=True, socket_connect_timeout=2)
            client.ping()
            _redis_client = client
            logger.info("[AUTH] Redis 블랙리스트 연결 성공: %s", _REDIS_URL)
        except Exception as e:
            logger.warning("[AUTH] Redis 연결 실패 — 메모리 폴백 사용: %s", e)
            _redis_client = None
    return _redis_client


def revoke_token(jti: str, expiry: float) -> None:
    """단일 토큰 무효화 (로그아웃). Redis 있으면 Redis, 없으면 메모리."""
    r = _get_redis()
    if r is not None:
        try:
            ttl = max(1, int(expiry - datetime.now(timezone.utc).timestamp()))
            r.setex(f"blacklist:token:{jti}", ttl, "1")
            return
        except Exception as e:
            logger.warning("[AUTH] Redis revoke_token 실패 — 메모리 폴백: %s", e)
    with _lock:
        _revoked_tokens[jti] = expiry


def revoke_user_tokens(user_id: int) -> None:
    """사용자 전체 토큰 무효화 (탈퇴/계정 잠금) — [A07-REVOKE]"""
    now_ts = datetime.now(timezone.utc).timestamp()
    r = _get_redis()
    if r is not None:
        try:
            r.setex(f"blacklist:user:{user_id}", _BLACKLIST_USER_TTL, str(now_ts))
            return
        except Exception as e:
            logger.warning("[AUTH] Redis revoke_user_tokens 실패 — 메모리 폴백: %s", e)
    with _lock:
        _revoked_users[str(user_id)] = now_ts


def is_token_revoked(jti: str, user_id: str, iat: float) -> bool:
    """토큰이 블랙리스트에 있는지 확인. Redis 있으면 Redis, 없으면 메모리."""
    r = _get_redis()
    if r is not None:
        try:
            # 단일 토큰 블랙리스트
            if r.exists(f"blacklist:token:{jti}"):
                return True
            # 사용자 전체 무효화
            val = r.get(f"blacklist:user:{user_id}")
            if val is not None:
                revoked_before = float(val)
                if iat < revoked_before:
                    return True
            return False
        except Exception as e:
            logger.warning("[AUTH] Redis is_token_revoked 실패 — 메모리 폴백: %s", e)
    # 메모리 폴백
    with _lock:
        # 단일 토큰 블랙리스트
        if jti in _revoked_tokens:
            if datetime.now(timezone.utc).timestamp() < _revoked_tokens[jti]:
                return True
            del _revoked_tokens[jti]  # 만료된 항목 정리
        # 사용자 전체 무효화 (iat < revoked_before_ts)
        if user_id in _revoked_users:
            if iat < _revoked_users[user_id]:
                return True
    return False

SECRET_KEY = os.environ["SECRET_KEY"]
REFRESH_SECRET_KEY = os.environ["REFRESH_SECRET_KEY"]  # 기본값 없음 — 미설정 시 서버 시작 실패 (명시적 오류가 silent 취약보다 낫다)
ALGORITHM = "HS256"
ACCESS_EXPIRE_MINUTES = 60 * 24       # 24h
REFRESH_EXPIRE_DAYS = 30              # 30일

class _Bearer401(HTTPBearer):
    """[FIX-401] 기본 HTTPBearer는 Authorization 헤더 누락 시 403을 던진다.
    (starlette 설계상 '인증 스킴 없음' = Forbidden 취급)
    이 서비스의 테스트/클라이언트 계약은 '인증 안 됨' = 401 이므로 오버라이드한다."""

    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except HTTPException as e:
            if e.status_code == 403:
                raise HTTPException(status_code=401, detail="인증이 필요합니다.")
            raise


security = _Bearer401()


def hash_password(password: str) -> str:
    """
    [CVE-2024-0232] 72바이트 명시 절단 후 bcrypt
    """
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """
    [MEDIUM 확인] bcrypt.checkpw() 내부적으로 timing-safe 비교 수행
    — hmac.compare_digest() 별도 추가 불필요
    """
    pwd_bytes = plain.encode("utf-8")[:72]
    return bcrypt.checkpw(pwd_bytes, hashed.encode())


def create_access_token(user_id: int, extra: dict | None = None) -> str:
    """
    [CVE-2024-33664] 알고리즘 명시 + exp/sub 강제
    """
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
        "type": "access",
        **(extra or {}),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Refresh token — 30일, 별도 시크릿"""
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }
    return jwt.encode(payload, REFRESH_SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, is_refresh: bool = False) -> dict:
    """
    알고리즘 명시 → alg:none 차단
    exp + sub 강제 검증
    """
    key = REFRESH_SECRET_KEY if is_refresh else SECRET_KEY
    return jwt.decode(
        token,
        key,
        algorithms=[ALGORITHM],          # 명시적 허용만
        options={"require": ["exp", "sub"]},
    )


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI 의존성 주입 — 모든 보호 라우터에 Depends(get_current_user)
    [A07-REVOKE] 블랙리스트 체크 포함
    """
    try:
        payload = decode_token(creds.credentials)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="refresh token은 API 접근 불가")
        # [A07-REVOKE] 블랙리스트 체크
        jti = payload.get("jti", f"{payload['sub']}:{payload.get('iat', 0)}")
        iat = float(payload.get("iat", 0))
        if is_token_revoked(jti, str(payload["sub"]), iat):
            raise HTTPException(status_code=401, detail="무효화된 토큰 — 재로그인 필요")
        return {"user_id": int(payload["sub"]), "payload": payload}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 만료 — 재로그인 필요",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰",
        )
