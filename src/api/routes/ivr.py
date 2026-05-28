"""
사주담 IVR (Interactive Voice Response) — Twilio 음성 전화 연동
================================================================
법적 포지션: 문화·오락 서비스 (심리상담/의료 아님)
자살예방상담전화: 1393 (24시간)

플로우:
  1. Twilio가 전화 수신 → POST /api/ivr/incoming 호출
  2. TwiML로 환영 메시지 + 생년월일(8자리 YYYYMMDD) 입력 안내
  3. POST /api/ivr/gather → 입력값 파싱 → 오늘의 사주 운세 계산
  4. 운세 TTS로 읽어주기 → 다시 듣기(1) / 종료(9) DTMF 메뉴
  5. 위기 키워드 발화 감지 → 1393 안내

보안:
  - X-Twilio-Signature 검증 (HMAC-SHA1)
  - TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN lazy-init guard
  - 발신번호 E.164 형식 저장 (로그 최소화)
  - 입력값 숫자 전용 sanitize
"""
from __future__ import annotations

import os
import hashlib
import hmac
import base64
import urllib.parse
import datetime
from zoneinfo import ZoneInfo
_KST = ZoneInfo("Asia/Seoul")
import logging
from typing import Optional

from fastapi import APIRouter, Request, Response, HTTPException, Form
from fastapi.responses import PlainTextResponse

logger = logging.getLogger("saju.ivr")

router = APIRouter(prefix="/api/ivr", tags=["IVR"])

# ── Twilio 설정 (lazy-init guard) ────────────────────────────────────────────
TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER: Optional[str] = os.getenv("TWILIO_FROM_NUMBER", "")

# Twilio 서명 검증 활성화 여부 (기본값: true — 미설정 시 서명 검증 활성화)
if not os.getenv("VERIFY_TWILIO_SIGNATURE"):
    logging.getLogger("saju.ivr").warning(
        "VERIFY_TWILIO_SIGNATURE 미설정 — 기본값 true 적용 (운영 .env에 명시 권고)"
    )
VERIFY_TWILIO_SIGNATURE: bool = os.getenv("VERIFY_TWILIO_SIGNATURE", "true").lower() == "true"

# ── CallSid 중복 방지 (in-memory, R45 MEDIUM 해소) ───────────────────────────
# Redis SETNX 방식이 이상적이나 Redis 미연결 환경 대비 in-memory TTL set 사용
# 프로덕션 Redis 환경 전환 시: redis.setnx(f"ivr:callsid:{sid}", 1, ex=300)
import threading
import time as _time

_callsid_lock = threading.Lock()
_callsid_seen: dict[str, float] = {}  # CallSid → 첫 수신 timestamp
_CALLSID_TTL = 300  # 5분 TTL (Twilio 통화 최대 지속 시간 내)


def _is_duplicate_callsid(callsid: str) -> bool:
    """CallSid 중복 수신 방지 — True 반환 시 중복 요청."""
    if not callsid:
        return False
    now = _time.monotonic()
    with _callsid_lock:
        # TTL 만료 항목 제거 (주기적 GC)
        expired = [k for k, t in _callsid_seen.items() if now - t > _CALLSID_TTL]
        for k in expired:
            del _callsid_seen[k]
        if callsid in _callsid_seen:
            return True  # 중복
        _callsid_seen[callsid] = now
        return False


# ── 내부 상수 ─────────────────────────────────────────────────────────────────
DISCLAIMER_KO = (
    "안녕하세요, 사주담입니다. "
    "본 서비스는 명리학 기반 문화 오락 서비스로, "
    "심리상담이나 의료 진단을 대체하지 않습니다."
)

WELCOME_PROMPT = (
    "오늘의 운세를 알아보려면 "
    "생년월일 여덟 자리를 입력해주세요. "
    "예시: 1990년 3월 15일이면 "
    "1, 9, 9, 0, 0, 3, 1, 5 를 누르세요. "
    "입력 후 우물정 키를 눌러주세요."
)

CRISIS_RESPONSE = (
    "힘드신 상황이군요. "
    "자살예방상담전화 1393으로 전화해 주세요. "
    "24시간 무료로 전문 상담사와 연결됩니다. "
    "지금 바로 전화하시면 도움 받으실 수 있습니다."
)

INVALID_INPUT = (
    "죄송합니다, 입력값을 인식하지 못했습니다. "
    "다시 시도해 주세요."
)

MENU_PROMPT = (
    "다시 들으시려면 1번을, "
    "처음으로 돌아가시려면 2번을, "
    "종료하시려면 9번을 눌러주세요."
)

GOODBYE = "사주담을 이용해 주셔서 감사합니다. 오늘도 좋은 하루 되세요."

# 오행별 운세 TTS 스크립트 (짧게)
FORTUNE_BY_ELEMENT = {
    "목": "오늘은 목 기운이 강합니다. 새로운 시작과 성장의 기운이 흐르는 날입니다. 창의적인 활동과 도전을 시도해보세요.",
    "화": "오늘은 화 기운이 활발합니다. 열정과 에너지가 넘치는 날입니다. 적극적으로 행동하면 좋은 결과를 얻을 수 있습니다.",
    "토": "오늘은 토 기운이 안정적입니다. 차분하고 신중하게 움직이는 것이 유리한 날입니다. 관계와 신뢰를 쌓기 좋습니다.",
    "금": "오늘은 금 기운이 날카롭습니다. 판단력과 결단력이 필요한 일을 처리하기 좋은 날입니다. 정확성을 발휘해보세요.",
    "수": "오늘은 수 기운이 유연합니다. 지혜와 통찰이 빛나는 날입니다. 깊이 생각하고 물처럼 유연하게 대처하세요.",
}


def _is_twilio_configured() -> bool:
    """Twilio 자격증명 설정 여부 확인. [R16-IVR-001] 모듈 전역 참조 동적화"""
    import sys as _sys
    _m = _sys.modules[__name__]
    return bool(getattr(_m, "TWILIO_ACCOUNT_SID", None) and getattr(_m, "TWILIO_AUTH_TOKEN", None))


def _verify_twilio_signature(request_url: str, post_params: dict, signature: str) -> bool:
    """
    Twilio X-Twilio-Signature HMAC-SHA1 검증.
    https://www.twilio.com/docs/usage/webhooks/webhooks-security
    [R16-IVR-001] 모듈 전역 변수 직접 참조 — 테스트 monkeypatch 반영 보장
    """
    import sys
    _module = sys.modules[__name__]
    _token = getattr(_module, "TWILIO_AUTH_TOKEN", None)
    _verify = getattr(_module, "VERIFY_TWILIO_SIGNATURE", False)

    if not _token:
        return False

    # 파라미터를 알파벳 순 정렬 후 URL에 붙여서 서명 검증
    sorted_params = "".join(
        f"{k}{v}" for k, v in sorted(post_params.items())
    )
    s = request_url + sorted_params
    computed = base64.b64encode(
        hmac.new(
            _token.encode("utf-8"),
            s.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("utf-8")
    return hmac.compare_digest(computed, signature)


def _sanitize_digits(raw: str) -> str:
    """DTMF 입력값에서 숫자만 추출."""
    return "".join(c for c in (raw or "") if c.isdigit())


def _parse_birthday(digits: str) -> Optional[datetime.date]:
    """
    8자리 YYYYMMDD → datetime.date.
    유효하지 않은 날짜면 None 반환.
    """
    if len(digits) != 8:
        return None
    try:
        return datetime.date(
            int(digits[:4]),
            int(digits[4:6]),
            int(digits[6:8]),
        )
    except ValueError:
        return None


def _get_today_element() -> str:
    """오늘 날짜의 천간 오행 계산 (간이 버전)."""
    today = datetime.date.today()
    # 천간 순서: 갑을병정무기경신임계 → 목목화화토토금금수수
    heavenly_stem_idx = today.toordinal() % 10
    stem_to_element = ["목", "목", "화", "화", "토", "토", "금", "금", "수", "수"]
    return stem_to_element[heavenly_stem_idx]


def _get_birth_element(birthday: datetime.date) -> str:
    """생일 천간 오행 계산 (간이 버전)."""
    heavenly_stem_idx = birthday.toordinal() % 10
    stem_to_element = ["목", "목", "화", "화", "토", "토", "금", "금", "수", "수"]
    return stem_to_element[heavenly_stem_idx]


def _get_element_relation(birth_elem: str, today_elem: str) -> str:
    """오행 상생상극 관계 판단."""
    sheng = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}
    ke = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}

    if birth_elem == today_elem:
        return "비화"
    elif sheng.get(birth_elem) == today_elem:
        return "상생(생함)"
    elif sheng.get(today_elem) == birth_elem:
        return "상생(받음)"
    elif ke.get(birth_elem) == today_elem:
        return "상극(극함)"
    elif ke.get(today_elem) == birth_elem:
        return "상극(받음)"
    else:
        return "무관"


def _build_fortune_script(birthday: datetime.date) -> str:
    """
    생년월일 기반 오늘의 운세 TTS 스크립트 생성.
    """
    today = datetime.date.today()
    birth_elem = _get_birth_element(birthday)
    today_elem = _get_today_element()
    relation = _get_element_relation(birth_elem, today_elem)

    today_fortune = FORTUNE_BY_ELEMENT.get(today_elem, "오늘도 좋은 하루 보내세요.")

    relation_msg = {
        "비화": "나의 기운과 오늘 기운이 같은 흐름이에요. 자신감 있게 움직이기 좋은 날입니다.",
        "상생(생함)": "나의 기운이 오늘 에너지를 키워주는 흐름입니다. 베풀고 도와주는 역할이 빛나는 날이에요.",
        "상생(받음)": "오늘 일진이 나를 응원하는 흐름입니다. 에너지를 받아 하고 싶은 일을 추진하기 좋습니다.",
        "상극(극함)": "나의 기운과 오늘 흐름이 부딪히는 날이에요. 신중하게 한 발씩 나아가는 게 유리합니다.",
        "상극(받음)": "오늘 일진의 기운이 내 에너지에 자극을 줍니다. 자극을 성장의 계기로 삼아보세요.",
        "무관": "오늘 일진과 나의 기운이 독립적으로 작용하는 날이에요. 내 페이스대로 움직이면 됩니다.",
    }.get(relation, "오늘도 평온한 하루입니다.")

    return (
        f"{today.year}년 {today.month}월 {today.day}일 오늘의 운세입니다. "
        f"{today_fortune} "
        f"{relation_msg} "
        f"본 내용은 명리학적 관점의 참고 정보이며 전문적 심리상담을 대체하지 않습니다."
    )


def _twiml_response(twiml_body: str) -> PlainTextResponse:
    """TwiML XML 응답 반환."""
    return PlainTextResponse(
        content=twiml_body,
        media_type="application/xml; charset=utf-8",
    )


def _twiml_say(text: str, language: str = "ko-KR", voice: str = "Polly.Seoyeon") -> str:
    """<Say> TwiML 태그 생성 (AWS Polly 한국어 음성)."""
    escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<Say language="{language}" voice="{voice}">{escaped}</Say>'


def _twiml_gather(
    action: str,
    num_digits: Optional[int] = None,
    finish_on_key: str = "#",
    timeout: int = 10,
    inner: str = "",
) -> str:
    """<Gather> TwiML 태그 생성."""
    attrs = f'action="{action}" method="POST" timeout="{timeout}" finishOnKey="{finish_on_key}"'
    if num_digits:
        attrs += f' numDigits="{num_digits}"'
    return f"<Gather {attrs}>{inner}</Gather>"


def _twiml_redirect(url: str, method: str = "POST") -> str:
    """<Redirect> TwiML 태그 생성."""
    return f'<Redirect method="{method}">{url}</Redirect>'


def _build_twiml(*elements: str) -> str:
    """완전한 TwiML 문서 생성."""
    body = "\n    ".join(elements)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {body}
</Response>"""


# ── 미들웨어: Twilio 서명 검증 ────────────────────────────────────────────────
async def _check_twilio_configured():
    """Twilio 미설정 시 503 반환."""
    if not _is_twilio_configured():
        raise HTTPException(
            status_code=503,
            detail={
                "status": "twilio_not_configured",
                "message": "전화 기능이 준비 중입니다. TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN을 설정해주세요.",
            },
        )


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post("/incoming", summary="Twilio 수신 전화 webhook")
async def ivr_incoming(request: Request):
    """
    Twilio가 전화 수신 시 호출하는 webhook.
    환영 메시지 + 생년월일 DTMF 입력 안내 TwiML 반환.
    """
    if not _is_twilio_configured():
        return _twiml_response(_build_twiml(
            _twiml_say(
                "안녕하세요, 사주담입니다. 현재 서비스 준비 중입니다. 잠시 후 다시 전화해주세요.",
            ),
            "<Hangup/>",
        ))

    # Twilio 서명 검증 (프로덕션)
    import sys as _sys
    _ivr = _sys.modules[__name__]
    if getattr(_ivr, "VERIFY_TWILIO_SIGNATURE", False):
        signature = request.headers.get("X-Twilio-Signature", "")
        form_data = dict(await request.form())
        url = str(request.url)
        if not _verify_twilio_signature(url, form_data, signature):
            logger.warning("Twilio signature verification failed")
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    gather_inner = _twiml_say(
        DISCLAIMER_KO + " " + WELCOME_PROMPT
    )
    gather = _twiml_gather(
        action="/api/ivr/gather",
        finish_on_key="#",
        timeout=15,
        inner=gather_inner,
    )
    # 입력 없을 때 재시도
    fallback = _twiml_say(INVALID_INPUT)
    redirect = _twiml_redirect("/api/ivr/incoming")

    return _twiml_response(_build_twiml(gather, fallback, redirect))


@router.post("/gather", summary="DTMF 입력 처리 — 운세 계산")
async def ivr_gather(
    request: Request,
    Digits: str = Form(default=""),
    CallSid: str = Form(default=""),
):
    """
    생년월일 8자리 DTMF 입력 처리 → 운세 계산 → TTS 응답.

    Digits: Twilio가 전달하는 입력된 DTMF 문자열
    CallSid: 통화 고유 ID (로깅용)
    """
    # Twilio 서명 검증 (프로덕션)
    import sys as _sys; _ivr2 = _sys.modules[__name__]
    if getattr(_ivr2, "VERIFY_TWILIO_SIGNATURE", False):
        signature = request.headers.get("X-Twilio-Signature", "")
        form_data = dict(await request.form())
        url = str(request.url)
        if not _verify_twilio_signature(url, form_data, signature):
            logger.warning("Twilio signature verification failed for CallSid=%s", CallSid)
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    # ── CallSid 중복 방지 (R45 MEDIUM 해소) ─────────────────────────────────
    if _is_duplicate_callsid(CallSid):
        logger.warning("IVR gather: 중복 CallSid 감지, 무시 CallSid=%s", CallSid)
        return _twiml_response("")  # 중복 요청 무시

    digits = _sanitize_digits(Digits)
    logger.info("IVR gather: CallSid=%s digits_len=%d", CallSid, len(digits))

    # ── 위기 감지: DTMF에서는 텍스트 입력 없으므로 특정 단축키 지원 가능 ──
    # (추후 SpeechResult 연동 시 위기 키워드 감지 추가)

    # ── 생년월일 파싱 ──────────────────────────────────────────────────────────
    birthday = _parse_birthday(digits)

    if birthday is None:
        # 잘못된 입력 → 재입력 요청
        gather_inner = _twiml_say(
            INVALID_INPUT + " " + WELCOME_PROMPT
        )
        gather = _twiml_gather(
            action="/api/ivr/gather",
            finish_on_key="#",
            timeout=15,
            inner=gather_inner,
        )
        return _twiml_response(_build_twiml(gather, _twiml_redirect("/api/ivr/incoming")))

    # ── 운세 계산 ──────────────────────────────────────────────────────────────
    try:
        fortune_script = _build_fortune_script(birthday)
    except Exception as e:
        logger.error("Fortune calculation error: %s", e)
        fortune_script = "오늘도 좋은 하루 보내세요. 본 내용은 참고용 정보입니다."

    # ── 운세 읽기 + 메뉴 ──────────────────────────────────────────────────────
    fortune_say = _twiml_say(fortune_script)
    menu_say = _twiml_say(MENU_PROMPT)
    gather_menu = _twiml_gather(
        action="/api/ivr/menu",
        num_digits=1,
        timeout=8,
        finish_on_key="",
        inner=menu_say,
    )
    fallback_say = _twiml_say(GOODBYE)

    return _twiml_response(_build_twiml(
        fortune_say,
        gather_menu,
        fallback_say,
        "<Hangup/>",
    ))


@router.post("/menu", summary="사후 메뉴 처리 (다시듣기/처음/종료)")
async def ivr_menu(
    request: Request,
    Digits: str = Form(default=""),
    CallSid: str = Form(default=""),
):
    """
    운세 청취 후 메뉴 선택 처리.
    1 → 운세 다시 듣기 (gather로 redirect, 저장된 세션 없으면 처음부터)
    2 → 처음으로 (생년월일 재입력)
    9 → 종료
    기타 → 처음으로
    """
    import sys as _sys; _ivr3 = _sys.modules[__name__]
    if getattr(_ivr3, "VERIFY_TWILIO_SIGNATURE", False):
        signature = request.headers.get("X-Twilio-Signature", "")
        form_data = dict(await request.form())
        url = str(request.url)
        if not _verify_twilio_signature(url, form_data, signature):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    digit = _sanitize_digits(Digits)[:1]
    logger.info("IVR menu: CallSid=%s digit=%s", CallSid, digit)

    if digit == "9":
        return _twiml_response(_build_twiml(
            _twiml_say(GOODBYE),
            "<Hangup/>",
        ))
    elif digit in ("1", "2", ""):
        # 처음으로 (생년월일 재입력)
        return _twiml_response(_build_twiml(
            _twiml_redirect("/api/ivr/incoming"),
        ))
    else:
        return _twiml_response(_build_twiml(
            _twiml_redirect("/api/ivr/incoming"),
        ))


@router.post("/outbound", summary="사주담 → 사용자 능동 발신 (알림 전화)")
async def ivr_outbound(
    request: Request,
    phone: str = Form(...),
    message: str = Form(default=""),
):
    """
    사주담 서버가 직접 사용자에게 전화 발신 (Twilio REST API).
    용도: 중요 알림, 위기 팔로업 전화 (1393 안내 포함).

    보안: JWT 인증 미들웨어 + 발신번호 E.164 검증 필요.
    현재 구현: 기본 TwiML 메시지 발신 (MVP).
    """
    if not _is_twilio_configured():
        return {
            "status": "twilio_not_configured",
            "message": "전화 기능이 준비 중입니다. 관리자에게 문의하세요.",
        }

    # E.164 형식 검증 (한국: +82로 시작)
    import re
    phone_clean = phone.strip()
    if not re.match(r"^\+?[1-9]\d{7,14}$", phone_clean):
        raise HTTPException(status_code=400, detail="유효하지 않은 전화번호 형식입니다. (+82로 시작하는 E.164 형식)")

    try:
        from twilio.rest import Client  # type: ignore
    except ImportError:
        logger.error("twilio 패키지가 설치되지 않았습니다. pip install twilio")
        return {
            "status": "twilio_package_missing",
            "message": "전화 기능 패키지가 설치 중입니다. 잠시 후 다시 시도해주세요.",
        }

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        twiml = _build_twiml(
            _twiml_say(message or "안녕하세요, 사주담입니다. 오늘의 운세를 확인해보세요."),
            "<Hangup/>",
        )
        call = client.calls.create(
            twiml=twiml,
            to=phone_clean,
            from_=TWILIO_FROM_NUMBER,
        )
        logger.info("Outbound call created: CallSid=%s to=%s", call.sid, phone_clean[:6] + "****")
        return {"status": "call_initiated", "call_sid": call.sid}
    except Exception as e:
        logger.error("Outbound call failed: %s", str(e))
        raise HTTPException(status_code=503, detail=f"전화 발신 실패: {str(e)}")


@router.get("/status", summary="IVR 서비스 상태 확인")
async def ivr_status():
    """
    IVR 서비스 설정 상태 반환 (자격증명 값은 노출하지 않음).
    """
    return {
        "service": "사주담 IVR",
        "twilio_configured": _is_twilio_configured(),
        "account_sid_set": bool(TWILIO_ACCOUNT_SID),
        "auth_token_set": bool(TWILIO_AUTH_TOKEN),
        "from_number_set": bool(TWILIO_FROM_NUMBER),
        "signature_verification": VERIFY_TWILIO_SIGNATURE,
        "webhook_endpoints": {
            "incoming": "POST /api/ivr/incoming",
            "gather": "POST /api/ivr/gather",
            "menu": "POST /api/ivr/menu",
            "outbound": "POST /api/ivr/outbound",
        },
        "legal": "entertainment-lifestyle-service",
        "crisis_line": "1393 (자살예방상담전화, 24시간)",
    }
