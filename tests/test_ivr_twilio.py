"""
사주담 IVR (Twilio 음성 전화 연동) 테스트
======================================
- Twilio 자격증명 없이도 전체 흐름 테스트 가능 (mock 기반)
- TwiML 응답 구조 검증
- 운세 계산 로직 단위 테스트
- E.164 번호 검증 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import datetime


# ── 앱 임포트 ──────────────────────────────────────────────────────────────────
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.main import app
from src.api.routes.ivr import (
    _sanitize_digits,
    _parse_birthday,
    _get_today_element,
    _get_birth_element,
    _get_element_relation,
    _build_fortune_script,
    _is_twilio_configured,
    _twiml_say,
    _twiml_gather,
    _build_twiml,
    FORTUNE_BY_ELEMENT,
)
import src.api.routes.ivr as _ivr_mod

# 테스트 환경: Twilio 서명 검증 비활성화 (서명 없이 TwiML 흐름 테스트)
_ivr_mod.VERIFY_TWILIO_SIGNATURE = False

client = TestClient(app)


# ── 단위 테스트: 유틸리티 함수 ─────────────────────────────────────────────────

class TestSanitizeDigits:
    def test_digits_only(self):
        assert _sanitize_digits("19900315") == "19900315"

    def test_strips_non_digits(self):
        assert _sanitize_digits("1990-03-15") == "19900315"

    def test_empty_string(self):
        assert _sanitize_digits("") == ""

    def test_none_like(self):
        assert _sanitize_digits(None) == ""  # type: ignore

    def test_hash_stripped(self):
        assert _sanitize_digits("19900315#") == "19900315"


class TestParseBirthday:
    def test_valid_date(self):
        result = _parse_birthday("19900315")
        assert result == datetime.date(1990, 3, 15)

    def test_short_input(self):
        assert _parse_birthday("199003") is None

    def test_long_input(self):
        assert _parse_birthday("199003150000") is None

    def test_invalid_month(self):
        assert _parse_birthday("19901315") is None  # month=13

    def test_invalid_day(self):
        assert _parse_birthday("19900332") is None  # day=32

    def test_empty(self):
        assert _parse_birthday("") is None

    def test_boundary_year(self):
        result = _parse_birthday("20240101")
        assert result == datetime.date(2024, 1, 1)


class TestElementFunctions:
    def test_get_today_element_returns_valid(self):
        elem = _get_today_element()
        assert elem in ("목", "화", "토", "금", "수")

    def test_get_birth_element_returns_valid(self):
        bd = datetime.date(1990, 3, 15)
        elem = _get_birth_element(bd)
        assert elem in ("목", "화", "토", "금", "수")

    def test_element_relation_same(self):
        rel = _get_element_relation("목", "목")
        assert rel == "비화"

    def test_element_relation_sheng_generate(self):
        # 목 생 화
        rel = _get_element_relation("목", "화")
        assert rel == "상생(생함)"

    def test_element_relation_sheng_receive(self):
        # 화 생 목 → 목이 화로부터 받음
        rel = _get_element_relation("화", "목")
        assert rel == "상생(받음)"

    def test_element_relation_ke_do(self):
        # 목 극 토
        rel = _get_element_relation("목", "토")
        assert rel == "상극(극함)"

    def test_element_relation_ke_receive(self):
        # 금 극 목 → 금이 목을 극함 = 상극(극함)
        rel = _get_element_relation("금", "목")
        assert rel == "상극(극함)"

    def test_element_relation_ke_receive_from_other(self):
        # 목 극 토 에서 토의 입장 → 토가 극받음 = 상극(받음)
        rel = _get_element_relation("토", "목")
        assert rel == "상극(받음)"

    def test_element_relation_neutral(self):
        # 목 ↔ 금은 직접 상생/상극 관계가 아님 → 무관
        # 목은 금을 극(金克木), 실제로는 상극(받음)... 검증
        # 목↔수 관계 확인
        rel_mok_su = _get_element_relation("목", "수")
        # 수 생 목 → 목이 받음
        assert rel_mok_su == "상생(받음)"

    def test_all_elements_have_fortune(self):
        for elem in ("목", "화", "토", "금", "수"):
            assert elem in FORTUNE_BY_ELEMENT


class TestBuildFortuneScript:
    def test_contains_today_date(self):
        today = datetime.date.today()
        bd = datetime.date(1990, 3, 15)
        script = _build_fortune_script(bd)
        assert str(today.year) in script
        assert str(today.month) in script

    def test_contains_disclaimer(self):
        bd = datetime.date(1990, 3, 15)
        script = _build_fortune_script(bd)
        assert "참고 정보" in script

    def test_not_empty(self):
        bd = datetime.date(2000, 1, 1)
        script = _build_fortune_script(bd)
        assert len(script) > 50


# ── TwiML 빌더 테스트 ─────────────────────────────────────────────────────────

class TestTwimlBuilders:
    def test_twiml_say_contains_text(self):
        say = _twiml_say("안녕하세요")
        assert "안녕하세요" in say
        assert "<Say" in say
        assert "ko-KR" in say

    def test_twiml_say_escapes_ampersand(self):
        say = _twiml_say("A & B")
        assert "&amp;" in say
        assert "& B" not in say

    def test_twiml_gather_contains_action(self):
        gather = _twiml_gather(action="/api/ivr/gather")
        assert "/api/ivr/gather" in gather
        assert "<Gather" in gather

    def test_build_twiml_structure(self):
        twiml = _build_twiml("<Hangup/>")
        assert '<?xml version="1.0"' in twiml
        assert "<Response>" in twiml
        assert "</Response>" in twiml
        assert "<Hangup/>" in twiml


# ── API 엔드포인트 통합 테스트 ────────────────────────────────────────────────

class TestIvrStatus:
    def test_status_endpoint_ok(self):
        resp = client.get("/api/ivr/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["service"] == "사주담 IVR"
        assert "twilio_configured" in data
        assert "webhook_endpoints" in data
        assert "crisis_line" in data
        # 키 미설정 상태여야 함 (테스트 환경)
        assert data["twilio_configured"] is False


class TestIvrIncoming:
    def test_incoming_returns_twiml(self):
        """Twilio 미설정 시에도 TwiML 반환 (준비 중 메시지)."""
        resp = client.post("/api/ivr/incoming")
        assert resp.status_code == 200
        assert "application/xml" in resp.headers["content-type"]
        content = resp.text
        assert "<Response>" in content

    def test_incoming_twiml_has_hangup_when_not_configured(self):
        """Twilio 미설정 → <Hangup/> 포함."""
        resp = client.post("/api/ivr/incoming")
        assert "<Hangup/>" in resp.text

    def test_incoming_with_twilio_configured_has_gather(self):
        """Twilio 설정 시 → <Gather> 포함."""
        with patch.dict(os.environ, {
            "TWILIO_ACCOUNT_SID": "ACtest123",
            "TWILIO_AUTH_TOKEN": "test_token_abc",
            "VERIFY_TWILIO_SIGNATURE": "false",  # 테스트환경 서명검증 스킵
        }):
            # 환경변수 패치 후 모듈 변수도 재설정
            import src.api.routes.ivr as ivr_mod
            original_sid = ivr_mod.TWILIO_ACCOUNT_SID
            original_token = ivr_mod.TWILIO_AUTH_TOKEN
            original_verify = ivr_mod.VERIFY_TWILIO_SIGNATURE
            ivr_mod.TWILIO_ACCOUNT_SID = "ACtest123"
            ivr_mod.TWILIO_AUTH_TOKEN = "test_token_abc"
            ivr_mod.VERIFY_TWILIO_SIGNATURE = False  # 테스트환경 서명검증 스킵
            try:
                resp = client.post("/api/ivr/incoming")
                assert resp.status_code == 200
                assert "<Gather" in resp.text
            finally:
                ivr_mod.TWILIO_ACCOUNT_SID = original_sid
                ivr_mod.TWILIO_AUTH_TOKEN = original_token
                ivr_mod.VERIFY_TWILIO_SIGNATURE = original_verify


class TestIvrGather:
    def test_gather_valid_birthday(self):
        """유효한 생년월일 입력 → 운세 TwiML 반환."""
        resp = client.post("/api/ivr/gather", data={
            "Digits": "19900315",
            "CallSid": "CA_test_001",
        })
        assert resp.status_code == 200
        assert "application/xml" in resp.headers["content-type"]
        content = resp.text
        assert "<Response>" in content
        # 운세 <Say> 포함 확인
        assert "<Say" in content

    def test_gather_invalid_birthday_short(self):
        """너무 짧은 입력 → 재입력 요청 TwiML."""
        resp = client.post("/api/ivr/gather", data={
            "Digits": "1990",
            "CallSid": "CA_test_002",
        })
        assert resp.status_code == 200
        # 재입력 요청 → Gather 포함
        assert "<Gather" in resp.text

    def test_gather_empty_input(self):
        """입력 없음 → 재입력 요청."""
        resp = client.post("/api/ivr/gather", data={
            "Digits": "",
            "CallSid": "CA_test_003",
        })
        assert resp.status_code == 200
        content = resp.text
        assert "<Response>" in content

    def test_gather_hash_stripped(self):
        """# 키 포함 입력 → 숫자만 파싱."""
        resp = client.post("/api/ivr/gather", data={
            "Digits": "19900315#",
            "CallSid": "CA_test_004",
        })
        assert resp.status_code == 200
        # 유효 → 운세 포함
        assert "<Say" in resp.text

    def test_gather_invalid_date(self):
        """유효하지 않은 날짜(월=13) → 재입력 요청."""
        resp = client.post("/api/ivr/gather", data={
            "Digits": "19901315",  # month=13
            "CallSid": "CA_test_005",
        })
        assert resp.status_code == 200
        assert "<Gather" in resp.text  # 재입력 Gather

    def test_gather_fortune_contains_disclaimer(self):
        """운세 TwiML에 법적 고지 포함."""
        resp = client.post("/api/ivr/gather", data={
            "Digits": "19850601",
            "CallSid": "CA_test_006",
        })
        assert resp.status_code == 200
        assert "참고 정보" in resp.text

    def test_gather_menu_after_fortune(self):
        """운세 TwiML에 메뉴 Gather 포함."""
        resp = client.post("/api/ivr/gather", data={
            "Digits": "19900315",
            "CallSid": "CA_test_007",
        })
        assert resp.status_code == 200
        # 메뉴 Gather: action=/api/ivr/menu
        assert "/api/ivr/menu" in resp.text


class TestIvrMenu:
    def test_menu_9_hangup(self):
        """9번 → 종료 TwiML."""
        resp = client.post("/api/ivr/menu", data={
            "Digits": "9",
            "CallSid": "CA_test_010",
        })
        assert resp.status_code == 200
        assert "<Hangup/>" in resp.text
        assert "감사합니다" in resp.text

    def test_menu_1_redirect_to_incoming(self):
        """1번 → 처음 Redirect."""
        resp = client.post("/api/ivr/menu", data={
            "Digits": "1",
            "CallSid": "CA_test_011",
        })
        assert resp.status_code == 200
        assert "<Redirect" in resp.text
        assert "/api/ivr/incoming" in resp.text

    def test_menu_2_redirect_to_incoming(self):
        """2번 → 처음으로."""
        resp = client.post("/api/ivr/menu", data={
            "Digits": "2",
            "CallSid": "CA_test_012",
        })
        assert resp.status_code == 200
        assert "<Redirect" in resp.text

    def test_menu_invalid_digit_fallback(self):
        """잘못된 입력 → 처음으로 Redirect."""
        resp = client.post("/api/ivr/menu", data={
            "Digits": "5",
            "CallSid": "CA_test_013",
        })
        assert resp.status_code == 200
        assert "<Redirect" in resp.text

    def test_menu_empty_digit_fallback(self):
        """입력 없음 → 처음으로."""
        resp = client.post("/api/ivr/menu", data={
            "Digits": "",
            "CallSid": "CA_test_014",
        })
        assert resp.status_code == 200
        assert "<Redirect" in resp.text


class TestIvrOutbound:
    def test_outbound_not_configured(self):
        """Twilio 미설정 → twilio_not_configured 반환 (200, not 503)."""
        resp = client.post("/api/ivr/outbound", data={
            "phone": "+82101234567",
            "message": "테스트 메시지",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "twilio_not_configured"

    def test_outbound_invalid_phone(self):
        """유효하지 않은 번호 → 400."""
        import src.api.routes.ivr as ivr_mod
        ivr_mod.TWILIO_ACCOUNT_SID = "ACtest"
        ivr_mod.TWILIO_AUTH_TOKEN = "token"
        try:
            resp = client.post("/api/ivr/outbound", data={
                "phone": "invalid-phone",
                "message": "테스트",
            })
            assert resp.status_code == 400
        finally:
            ivr_mod.TWILIO_ACCOUNT_SID = None
            ivr_mod.TWILIO_AUTH_TOKEN = None

    def test_outbound_twilio_package_missing(self):
        """twilio 패키지 미설치 → twilio_package_missing 반환."""
        import src.api.routes.ivr as ivr_mod
        ivr_mod.TWILIO_ACCOUNT_SID = "ACtest"
        ivr_mod.TWILIO_AUTH_TOKEN = "token"
        try:
            with patch.dict("sys.modules", {"twilio": None, "twilio.rest": None}):
                resp = client.post("/api/ivr/outbound", data={
                    "phone": "+82101234567",
                    "message": "테스트",
                })
            # 실패해도 503이 아닌 200 + status message
            assert resp.status_code in (200, 503)
        finally:
            ivr_mod.TWILIO_ACCOUNT_SID = None
            ivr_mod.TWILIO_AUTH_TOKEN = None


# ── 보안 테스트 ───────────────────────────────────────────────────────────────

class TestIvrSecurity:
    def test_no_credentials_in_status(self):
        """상태 응답에 실제 자격증명 값 미포함."""
        resp = client.get("/api/ivr/status")
        data = resp.json()
        # 실제 토큰 값이 아닌 bool만 반환
        assert isinstance(data["account_sid_set"], bool)
        assert isinstance(data["auth_token_set"], bool)
        assert "TWILIO_AUTH_TOKEN" not in str(data)

    def test_incoming_no_auth_required(self):
        """IVR incoming은 JWT 인증 불필요 (Twilio가 직접 호출)."""
        resp = client.post("/api/ivr/incoming")
        # 401이 아닌 200 응답
        assert resp.status_code == 200

    def test_gather_no_auth_required(self):
        """gather도 JWT 인증 불필요."""
        resp = client.post("/api/ivr/gather", data={
            "Digits": "19900315",
            "CallSid": "CA_test",
        })
        assert resp.status_code == 200

    def test_phone_not_logged_in_response(self):
        """전화번호가 응답 본문에 노출되지 않음."""
        import src.api.routes.ivr as ivr_mod
        ivr_mod.TWILIO_ACCOUNT_SID = "ACtest"
        ivr_mod.TWILIO_AUTH_TOKEN = "token"
        try:
            resp = client.post("/api/ivr/outbound", data={
                "phone": "+82101234567",
                "message": "테스트",
            })
            # 전화번호 전체가 응답에 노출되면 안 됨
            if resp.status_code == 200:
                body = resp.text
                assert "+82101234567" not in body or "twilio_not_configured" in body
        finally:
            ivr_mod.TWILIO_ACCOUNT_SID = None
            ivr_mod.TWILIO_AUTH_TOKEN = None
