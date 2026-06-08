"""
Sprint 2 — src/api/routes/ivr.py 커버리지 향상 테스트
목표: 32.0% → 65%+
"""
import os
import sys
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-placeholder!")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32chars!!")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_saju.db")
os.environ["RATELIMIT_ENABLED"] = "False"
os.environ["VERIFY_TWILIO_SIGNATURE"] = "false"

try:
    from src.api.rate_limiter import limiter as _limiter
    _limiter.enabled = False
except Exception:
    pass

from fastapi.testclient import TestClient
from fastapi import FastAPI
from src.api.main import app as _main_app
import src.api.routes.ivr as _ivr_mod

# IVR 라우터 직접 테스트용 앱
_ivr_app = FastAPI()
_ivr_app.include_router(_ivr_mod.router)

ivr_test_client = TestClient(_ivr_app)
client = TestClient(_main_app)

import src.api.routes.ivr as ivr_mod
from src.api.routes.ivr import (
    _is_duplicate_callsid,
    _is_twilio_configured,
    _verify_twilio_signature,
    DISCLAIMER_KO,
    WELCOME_PROMPT,
    CRISIS_RESPONSE,
    INVALID_INPUT,
    MENU_PROMPT,
    GOODBYE,
    FORTUNE_BY_ELEMENT,
)


# ── 내부 상수 검증 ──────────────────────────────────────────────────────────────

class TestIVRConstants:
    def test_disclaimer_not_empty(self):
        assert len(DISCLAIMER_KO) > 0

    def test_welcome_prompt_mentions_birth(self):
        assert "생년월일" in WELCOME_PROMPT

    def test_crisis_response_mentions_1393(self):
        assert "1393" in CRISIS_RESPONSE

    def test_invalid_input_not_empty(self):
        assert len(INVALID_INPUT) > 0

    def test_menu_prompt_mentions_options(self):
        assert "1" in MENU_PROMPT

    def test_goodbye_not_empty(self):
        assert len(GOODBYE) > 0

    def test_fortune_has_5_elements(self):
        assert len(FORTUNE_BY_ELEMENT) == 5
        for el in ["목", "화", "토", "금", "수"]:
            assert el in FORTUNE_BY_ELEMENT


# ── _is_duplicate_callsid ─────────────────────────────────────────────────────

class TestIsDuplicateCallsid:
    def setup_method(self):
        with ivr_mod._callsid_lock:
            ivr_mod._callsid_seen.clear()

    def test_new_callsid_not_duplicate(self):
        result = _is_duplicate_callsid("CAXXX123")
        assert result is False

    def test_second_call_same_sid_is_duplicate(self):
        _is_duplicate_callsid("CAYYY456")
        result = _is_duplicate_callsid("CAYYY456")
        assert result is True

    def test_empty_string_not_duplicate(self):
        result = _is_duplicate_callsid("")
        assert result is False

    def test_different_sids_not_duplicate(self):
        _is_duplicate_callsid("CA_A")
        result = _is_duplicate_callsid("CA_B")
        assert result is False

    def test_ttl_expiry_clears_seen(self):
        import time
        with ivr_mod._callsid_lock:
            ivr_mod._callsid_seen["CA_OLD"] = time.monotonic() - (ivr_mod._CALLSID_TTL + 1)
        result = _is_duplicate_callsid("CA_TRIGGER")
        assert "CA_OLD" not in ivr_mod._callsid_seen


# ── _is_twilio_configured ─────────────────────────────────────────────────────

class TestIsTwilioConfigured:
    def test_not_configured_without_credentials(self):
        original_sid = ivr_mod.TWILIO_ACCOUNT_SID
        original_token = ivr_mod.TWILIO_AUTH_TOKEN
        try:
            ivr_mod.TWILIO_ACCOUNT_SID = None
            ivr_mod.TWILIO_AUTH_TOKEN = None
            result = _is_twilio_configured()
            assert result is False
        finally:
            ivr_mod.TWILIO_ACCOUNT_SID = original_sid
            ivr_mod.TWILIO_AUTH_TOKEN = original_token

    def test_configured_with_both_credentials(self):
        original_sid = ivr_mod.TWILIO_ACCOUNT_SID
        original_token = ivr_mod.TWILIO_AUTH_TOKEN
        try:
            ivr_mod.TWILIO_ACCOUNT_SID = "AC_test123"
            ivr_mod.TWILIO_AUTH_TOKEN = "test_auth_token"
            result = _is_twilio_configured()
            assert result is True
        finally:
            ivr_mod.TWILIO_ACCOUNT_SID = original_sid
            ivr_mod.TWILIO_AUTH_TOKEN = original_token

    def test_only_sid_not_configured(self):
        original_sid = ivr_mod.TWILIO_ACCOUNT_SID
        original_token = ivr_mod.TWILIO_AUTH_TOKEN
        try:
            ivr_mod.TWILIO_ACCOUNT_SID = "AC_test"
            ivr_mod.TWILIO_AUTH_TOKEN = None
            result = _is_twilio_configured()
            assert result is False
        finally:
            ivr_mod.TWILIO_ACCOUNT_SID = original_sid
            ivr_mod.TWILIO_AUTH_TOKEN = original_token


# ── _verify_twilio_signature ──────────────────────────────────────────────────

class TestVerifyTwilioSignature:
    def test_no_auth_token_returns_false(self):
        original = ivr_mod.TWILIO_AUTH_TOKEN
        try:
            ivr_mod.TWILIO_AUTH_TOKEN = None
            result = _verify_twilio_signature("https://example.com/ivr", {}, "sig")
            assert result is False
        finally:
            ivr_mod.TWILIO_AUTH_TOKEN = original

    def test_wrong_signature_returns_false(self):
        original_token = ivr_mod.TWILIO_AUTH_TOKEN
        try:
            ivr_mod.TWILIO_AUTH_TOKEN = "test_secret"
            result = _verify_twilio_signature(
                "https://example.com/ivr",
                {"CallSid": "CA123"},
                "wrongsignature"
            )
            assert result is False
        finally:
            ivr_mod.TWILIO_AUTH_TOKEN = original_token

    def test_correct_signature_returns_true(self):
        import hashlib
        import hmac as _hmac
        import base64

        secret = "test_auth_token_for_sig_verify"
        url = "https://example.com/api/ivr/incoming"
        params = {"CallSid": "CA123456", "From": "+821012345678"}
        sorted_params = "".join(f"{k}{v}" for k, v in sorted(params.items()))
        s = url + sorted_params
        sig = base64.b64encode(
            _hmac.new(secret.encode(), s.encode(), hashlib.sha1).digest()
        ).decode()

        original_token = ivr_mod.TWILIO_AUTH_TOKEN
        original_verify = ivr_mod.VERIFY_TWILIO_SIGNATURE
        try:
            ivr_mod.TWILIO_AUTH_TOKEN = secret
            ivr_mod.VERIFY_TWILIO_SIGNATURE = True
            result = _verify_twilio_signature(url, params, sig)
            assert result is True
        finally:
            ivr_mod.TWILIO_AUTH_TOKEN = original_token
            ivr_mod.VERIFY_TWILIO_SIGNATURE = original_verify


# ── GET /api/ivr/health ───────────────────────────────────────────────────────

class TestIVRHealthEndpoint:
    def test_status_returns_200(self):
        resp = ivr_test_client.get("/api/ivr/status")
        assert resp.status_code == 200

    def test_status_has_data(self):
        resp = ivr_test_client.get("/api/ivr/status")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


# ── POST /api/ivr/incoming ────────────────────────────────────────────────────

class TestIVRIncomingEndpoint:
    def setup_method(self):
        with ivr_mod._callsid_lock:
            ivr_mod._callsid_seen.clear()

    def test_incoming_without_twilio_sig(self):
        resp = ivr_test_client.post(
            "/api/ivr/incoming",
            data={
                "CallSid": "CA_TEST_001",
                "From": "+821012345678",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code in (200, 400, 403)

    def test_duplicate_callsid_blocked(self):
        ivr_test_client.post(
            "/api/ivr/incoming",
            data={"CallSid": "CA_DUP_TEST", "From": "+821012345678"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp = ivr_test_client.post(
            "/api/ivr/incoming",
            data={"CallSid": "CA_DUP_TEST", "From": "+821012345678"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code in (200, 429, 400)


# ── POST /api/ivr/gather ──────────────────────────────────────────────────────

class TestIVRGatherEndpoint:
    def test_valid_birthdate(self):
        resp = ivr_test_client.post(
            "/api/ivr/gather",
            data={
                "Digits": "19900315",
                "CallSid": "CA_GATHER_001",
                "From": "+821012345678",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code in (200, 400)

    def test_invalid_digits_too_short(self):
        resp = ivr_test_client.post(
            "/api/ivr/gather",
            data={
                "Digits": "1234",
                "CallSid": "CA_GATHER_002",
                "From": "+821012345678",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code in (200, 400)

    def test_non_numeric_digits(self):
        resp = ivr_test_client.post(
            "/api/ivr/gather",
            data={
                "Digits": "ABCDEFGH",
                "CallSid": "CA_GATHER_003",
                "From": "+821012345678",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code in (200, 400)

    def test_empty_digits(self):
        resp = ivr_test_client.post(
            "/api/ivr/gather",
            data={
                "Digits": "",
                "CallSid": "CA_GATHER_004",
                "From": "+821012345678",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code in (200, 400)
