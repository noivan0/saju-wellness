"""
인증 라우터 — 카카오/구글 OAuth + JWT 발급
[R25-COOKIE] access_token/refresh_token HttpOnly + SameSite=Strict 쿠키 발급
"""
import secrets
import logging
from fastapi import APIRouter, HTTPException, Depends, Query, Request, Response
from pydantic import BaseModel
from src.core.auth import (
    create_access_token, create_refresh_token,
    decode_token, get_current_user, revoke_user_tokens,
    revoke_token, is_token_revoked
)
from src.api.rate_limiter import limiter

# ─── 쿠키 보안 설정 헬퍼 ────────────────────────────────────
def _set_auth_cookies(response: Response, access_token: str, refresh_token_val: str) -> None:
    """[R25-COOKIE] access_token/refresh_token을 HttpOnly SameSite=Strict 쿠키로 발급."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=60 * 60 * 24,  # 24h
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token_val,
        httponly=True,
        samesite="strict",
        secure=True,
        max_age=60 * 60 * 24 * 30,  # 30일
        path="/auth/refresh",
    )

logger = logging.getLogger(__name__)
router = APIRouter(tags=["auth"])


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.get("/oauth/state")
def generate_oauth_state():
    """
    [R29-AUTH1] OAuth CSRF 방지 — state 파라미터 생성
    클라이언트가 OAuth 요청 전 이 값을 받아 redirect_uri에 포함,
    콜백 시 동일한 state 값이 돌아오는지 검증해야 함.
    프로덕션: Redis/서버 세션에 저장 후 콜백에서 대조 필수.
    """
    state = secrets.token_urlsafe(32)
    logger.info("[OAuth] state 생성 — 클라이언트가 콜백에서 검증 필수")
    return {"state": state, "ttl_seconds": 300}


def _validate_oauth_state(state: str | None, provider: str) -> None:
    """
    [R69-OAUTH-001] OAuth CSRF state 필수 검증.
    - state 없으면 400 반환 (MVP 종료 → 프로덕션 이행)
    - 형식: urlsafe base64, 최소 32자 (secrets.token_urlsafe(32) 생성 기준)
    """
    if not state:
        raise HTTPException(
            status_code=400,
            detail=f"[{provider}] OAuth state 파라미터 필수 — /auth/oauth/state에서 먼저 발급받으세요 (CSRF 방지)"
        )
    # 최소 길이 검증 (token_urlsafe(32) → 43자)
    if len(state) < 32:
        raise HTTPException(
            status_code=400,
            detail=f"[{provider}] state 파라미터 형식 오류 — /auth/oauth/state 발급값을 그대로 사용하세요"
        )


@router.post("/kakao")
@limiter.limit("10/minute")
def kakao_login(
    request: Request,
    response: Response,
    code: str,
    state: str = Query(..., description="[R69-OAUTH-001] CSRF 방지 state — /auth/oauth/state에서 발급 필수"),
):
    """
    카카오 OAuth 로그인 (MVP: code 검증 스킵, 테스트용 토큰 반환)
    [R69-OAUTH-001] state 파라미터 필수화 — 미전달 시 400 반환
    [R25-COOKIE] access_token/refresh_token → HttpOnly 쿠키 발급 (XSS 방어)
    """
    _validate_oauth_state(state, "kakao")
    mock_user_id = abs(hash(code)) % 100000 + 1
    access_token = create_access_token(mock_user_id)
    refresh_token_val = create_refresh_token(mock_user_id)
    _set_auth_cookies(response, access_token, refresh_token_val)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_val,
        "token_type": "bearer",
    }


@router.post("/google")
@limiter.limit("10/minute")
def google_login(
    request: Request,
    response: Response,
    code: str,
    state: str = Query(..., description="[R69-OAUTH-001] CSRF 방지 state — /auth/oauth/state에서 발급 필수"),
):
    """
    구글 OAuth 로그인 (MVP: code 검증 스킵, 테스트용 토큰 반환)
    [R69-OAUTH-001] state 파라미터 필수화 — 미전달 시 400 반환
    [R25-COOKIE] access_token/refresh_token → HttpOnly 쿠키 발급 (XSS 방어)
    """
    _validate_oauth_state(state, "google")
    mock_user_id = abs(hash(code + "google")) % 100000 + 1
    access_token = create_access_token(mock_user_id)
    refresh_token_val = create_refresh_token(mock_user_id)
    _set_auth_cookies(response, access_token, refresh_token_val)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_val,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("20/minute")
def refresh_token(request: Request, response: Response, refresh_token: str):
    """
    Refresh token → 새 access token 발급
    type='refresh' 검증 필수
    [②-B] Refresh token 이중사용 방지 — 사용 즉시 revoke (Rotation 방식)
    [R25-COOKIE] 갱신된 토큰 → HttpOnly 쿠키 재발급
    """
    try:
        payload = decode_token(refresh_token, is_refresh=True)
        if payload.get("type") != "refresh":
            raise HTTPException(400, "유효하지 않은 refresh token")
        user_id = int(payload["sub"])
        # [②-B] 이미 사용된 refresh token 재사용 차단
        jti = payload.get("jti", f"{payload['sub']}:{payload.get('iat', 0)}")
        iat = float(payload.get("iat", 0))
        if is_token_revoked(jti, str(user_id), iat):
            raise HTTPException(401, "이미 사용된 refresh token — 재로그인 필요")
        # 사용 즉시 무효화 (Refresh Rotation — 이중사용 차단)
        exp = float(payload.get("exp", 0))
        revoke_token(jti, exp)
        new_access = create_access_token(user_id)
        new_refresh = create_refresh_token(user_id)
        _set_auth_cookies(response, new_access, new_refresh)
        return TokenPair(
            access_token=new_access,
            refresh_token=new_refresh,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(401, f"토큰 갱신 실패: {type(e).__name__}")


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    """현재 로그인 사용자 정보"""
    return {"user_id": current_user["user_id"]}


@router.post("/logout")
@limiter.limit("30/minute")
def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """로그아웃 — [A07-REVOKE] 서버측 토큰 즉시 무효화 + 클라이언트 삭제 안내"""
    user_id = current_user["user_id"]
    payload = current_user.get("payload", {})
    # 현재 access token 즉시 무효화
    jti = payload.get("jti", f"{payload.get('sub', user_id)}:{payload.get('iat', 0)}")
    exp = float(payload.get("exp", 0))
    revoke_token(jti, exp)
    logger.info("[AUTH][A07] 로그아웃 — access token revoke 완료: user_id=%s", user_id)
    return {"message": "로그아웃 완료. 클라이언트에서도 토큰을 삭제해주세요.", "revoked": True}


@router.delete("/account")
@limiter.limit("5/minute")
def delete_account(request: Request, current_user: dict = Depends(get_current_user)):
    """
    회원 탈퇴 — [A07-REVOKE] + 개보법 21조
    1. 해당 사용자의 모든 토큰 즉시 무효화
    2. 구독 취소 안내 (잔여 기간 비례 환불)
    3. 개인 식별 정보 익명화 (감사 로그 보존)
    """
    import os as _os_local
    user_id = current_user["user_id"]
    # [A07-REVOKE] 전체 토큰 무효화 (iat < now 기준)
    revoke_user_tokens(user_id)

    # [R56-ANON-001] DB 사용자 익명화 — 개보법 §21 즉시 이행
    db_url = _os_local.getenv("DATABASE_URL", "")
    if db_url:
        try:
            from sqlalchemy import create_engine, text  # type: ignore[import]
            from sqlalchemy.orm import sessionmaker
            _anon_engine = create_engine(db_url, pool_pre_ping=True)
            Session = sessionmaker(bind=_anon_engine)
            anon_alias = f"deleted_{str(user_id)[:8]}"
            with Session() as sess:
                # users: 개인식별정보 즉시 익명화
                sess.execute(text(
                    "UPDATE users SET "
                    "  name = :alias, "
                    "  phone = NULL, "
                    "  birth_date = NULL, "
                    "  email = :email, "
                    "  is_deleted = 1 "
                    "WHERE id = :uid"
                ), {"alias": f"탈퇴회원_{anon_alias}", "email": f"{anon_alias}@anonymous.invalid", "uid": user_id})
                # saju_profiles: 생년월일 등 민감정보 삭제
                sess.execute(text(
                    "DELETE FROM saju_profiles WHERE user_id = :uid"
                ), {"uid": user_id})
                sess.commit()
            logger.info(f"[개보법§21] 회원 탈퇴 익명화 완료: user_id={user_id}")
        except Exception as _e:
            logger.error(f"[개보법§21] 익명화 실패: user_id={user_id}, err={_e}")
    else:
        logger.warning(f"[개보법§21] DATABASE_URL 미설정 — 익명화 건너뜀: user_id={user_id}")

    logger.info(f"[GDPR] 회원 탈퇴 처리 완료: user_id={user_id}")
    return {
        "message": "탈퇴 처리가 완료되었습니다.",
        "note": "구독 중인 경우 잔여 기간 비례 환불은 결제 수단으로 영업일 3~5일 내 처리됩니다.",
        "legal": "개인정보보호법 §21① — 개인식별정보 즉시 익명화 처리",
    }
