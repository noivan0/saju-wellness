"""
test_ai_insight.py
AI 인사이트 서비스 테스트

- generate_daily_insight() 프롬프트 출력 포맷 검증
- 위기 키워드 감지 로직
- 면책 문구 포함 여부
- Anthropic API 미설치 시 graceful fallback 확인
- 실제 API 호출 없이 mocking 방식으로 출력 포맷 검증
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ─────────────────────────────────────────────
# 공통 픽스처
# ─────────────────────────────────────────────

@pytest.fixture
def sample_saju_data():
    from saju_engine import get_saju
    r = get_saju(1990, 5, 20, 14)
    r["disclaimer"] = "본 내용은 명리학적 관점의 참고 정보이며 전문적 심리상담을 대체하지 않습니다."
    return r


@pytest.fixture
def mock_anthropic_response():
    """Anthropic API 응답 Mock"""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=(
        "오늘의 에너지 흐름을 안내드립니다. "
        "금(金) 기운이 강한 날로, 정밀하고 논리적인 활동에 유리합니다.\n"
        "본 내용은 명리학적 관점의 참고 정보이며 전문적 심리상담을 대체하지 않습니다."
    ))]
    return mock_msg


# ─────────────────────────────────────────────
# 1. 위기 키워드 감지
# ─────────────────────────────────────────────

class TestCrisisKeywordDetection:
    def test_check_crisis_dead(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("죽고 싶어") is True

    def test_check_crisis_suicide(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("자살 생각이 든다") is True

    def test_check_crisis_self_harm(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("자해를 했어") is True

    def test_check_crisis_disappear(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("사라지고 싶다") is True

    def test_check_crisis_end(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("모든 걸 끝내고 싶어") is True

    def test_no_crisis_normal_message(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("오늘 날씨가 좋아요") is False

    def test_no_crisis_energy_message(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("기운이 없어요") is False

    def test_empty_message_no_crisis(self):
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("") is False

    def test_partial_match(self):
        """부분 매칭 — '죽고 싶' 포함"""
        from src.services.ai_insight import check_crisis_keywords
        assert check_crisis_keywords("죽고 싶은 생각은 아닌데 힘들어") is True


# ─────────────────────────────────────────────
# 2. 위기 응답 포맷
# ─────────────────────────────────────────────

class TestCrisisResponse:
    def test_crisis_redirect_type(self, sample_saju_data):
        """위기 키워드 감지 시 crisis_redirect 타입 반환"""
        with patch("src.services.ai_insight._get_client") as mock_client:
            from src.services.ai_insight import generate_daily_insight
            result = generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="죽고 싶다",
                lang="ko",
            )
        assert result["type"] == "crisis_redirect"

    def test_crisis_line_1393(self, sample_saju_data):
        """1393 위기 상담 전화 포함"""
        with patch("src.services.ai_insight._get_client"):
            from src.services.ai_insight import generate_daily_insight
            result = generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="자살 생각이 들어요",
                lang="ko",
            )
        assert "1393" in result["crisis_line"]

    def test_crisis_no_api_call(self, sample_saju_data):
        """위기 키워드 감지 시 API 호출 없이 즉시 반환"""
        with patch("src.services.ai_insight._get_client") as mock_client:
            from src.services.ai_insight import generate_daily_insight
            generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="자해하고 싶어",
            )
        mock_client.return_value.messages.create.assert_not_called()

    def test_crisis_disclaimer_present(self, sample_saju_data):
        with patch("src.services.ai_insight._get_client"):
            from src.services.ai_insight import generate_daily_insight
            result = generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="사라지고 싶다",
            )
        # disclaimer 필드는 있어야 함
        assert "disclaimer" in result


# ─────────────────────────────────────────────
# 3. 정상 응답 포맷 (API mock)
# ─────────────────────────────────────────────

class TestNormalInsightFormat:
    def test_insight_type(self, sample_saju_data, mock_anthropic_response):
        with patch("src.services.ai_insight._get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_anthropic_response
            from src.services.ai_insight import generate_daily_insight
            result = generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="오늘 기분이 좋아요",
                lang="ko",
            )
        assert result["type"] == "insight"

    def test_content_present(self, sample_saju_data, mock_anthropic_response):
        with patch("src.services.ai_insight._get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_anthropic_response
            from src.services.ai_insight import generate_daily_insight
            result = generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="좋은 하루",
                lang="ko",
            )
        assert "content" in result
        assert len(result["content"]) > 10

    def test_disclaimer_in_content(self, sample_saju_data, mock_anthropic_response):
        """AI 응답 내 면책 문구 포함 여부"""
        with patch("src.services.ai_insight._get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_anthropic_response
            from src.services.ai_insight import generate_daily_insight
            result = generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="오늘 에너지는?",
                lang="ko",
            )
        # content 또는 disclaimer 중 하나에 면책 문구 포함
        has_disclaimer = (
            "심리상담" in result.get("content", "") or
            "참고" in result.get("content", "") or
            result.get("disclaimer", "")
        )
        assert has_disclaimer

    def test_lang_field_returned(self, sample_saju_data, mock_anthropic_response):
        with patch("src.services.ai_insight._get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_anthropic_response
            from src.services.ai_insight import generate_daily_insight
            result = generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="오늘 에너지 알려줘",
                lang="ja",
            )
        assert result["lang"] == "ja"

    def test_system_prompt_used(self, sample_saju_data, mock_anthropic_response):
        """API 호출 시 system 프롬프트가 전달되는지"""
        with patch("src.services.ai_insight._get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_anthropic_response
            from src.services.ai_insight import generate_daily_insight
            generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="좋은 날",
                lang="ko",
            )
        call_kwargs = mock_client.return_value.messages.create.call_args
        assert call_kwargs is not None
        kwargs = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
        assert "system" in kwargs
        assert len(kwargs["system"]) > 10

    def test_model_specified(self, sample_saju_data, mock_anthropic_response):
        """claude-3-5-sonnet 모델 지정 확인"""
        with patch("src.services.ai_insight._get_client") as mock_client:
            mock_client.return_value.messages.create.return_value = mock_anthropic_response
            from src.services.ai_insight import generate_daily_insight
            generate_daily_insight(
                saju_data=sample_saju_data,
                user_message="좋은 날",
                lang="ko",
            )
        kwargs = mock_client.return_value.messages.create.call_args.kwargs
        assert "claude" in kwargs.get("model", "")


# ─────────────────────────────────────────────
# 4. 금지 표현 검증 (시스템 프롬프트)
# ─────────────────────────────────────────────

class TestSystemPromptCompliance:
    def test_system_prompts_exist(self):
        from src.services.ai_insight import SYSTEM_PROMPTS
        assert "ko" in SYSTEM_PROMPTS
        assert "ja" in SYSTEM_PROMPTS
        assert "en" in SYSTEM_PROMPTS

    def test_ko_prompt_forbids_counseling(self):
        from src.services.ai_insight import SYSTEM_PROMPTS
        ko = SYSTEM_PROMPTS["ko"]
        # 금지 표현이 "금지"로 명시되어야 함
        assert "금지" in ko or "하지 마" in ko or "사용 금지" in ko

    def test_ko_prompt_forbids_treatment(self):
        from src.services.ai_insight import SYSTEM_PROMPTS
        ko = SYSTEM_PROMPTS["ko"]
        # "치료" 관련 금지 명시
        assert "치료" in ko or "진단" in ko

    def test_en_prompt_forbids_therapy(self):
        from src.services.ai_insight import SYSTEM_PROMPTS
        en = SYSTEM_PROMPTS["en"]
        assert "therapy" in en.lower() or "counseling" in en.lower()

    def test_crisis_keywords_list_not_empty(self):
        from src.services.ai_insight import CRISIS_KEYWORDS
        # [LOW 해소 ②] CRISIS_KEYWORDS가 다국어 dict로 변경 — 각 언어별 키워드 존재 확인
        for lang in ["ko", "ja", "en"]:
            assert lang in CRISIS_KEYWORDS
            assert len(CRISIS_KEYWORDS[lang]) >= 4
        # 핵심 위기 키워드 포함
        assert "자살" in CRISIS_KEYWORDS["ko"]
        assert "자해" in CRISIS_KEYWORDS["ko"]


# ─────────────────────────────────────────────
# 5. insight API 라우터 (src.api.routes.insight)
# ─────────────────────────────────────────────

class TestInsightRouterFormat:
    """src.api.routes.insight — FastAPI TestClient로 포맷 검증"""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from src.api.main import app
        return TestClient(app)

    def test_daily_insight_response_format(self, client):
        resp = client.post("/api/insight/daily", json={
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 20,
            "user_message": "오늘 하루 어떤가요",
        })
        assert resp.status_code == 200
        data = resp.json()
        # 필수 필드
        assert "type" in data
        assert "disclaimer" in data

    def test_session_endpoint_format(self, client):
        # /insight/session = 유료 JWT 보호 엔드포인트 (설계 의도 — 401 정상)
        resp = client.post("/api/insight/session", json={
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 20,
            "user_message": "심층 세션 원합니다",
        })
        # 미인증 접근 → 401/403 (정상 동작: HTTPBearer auto_error=True → 헤더 없으면 403)
        assert resp.status_code in (200, 401, 403)
        if resp.status_code == 200:
            data = resp.json()
            assert "session_id" in data
            assert "disclaimer" in data
            assert "코칭" not in data.get("type", "")

    def test_crisis_type_in_route(self, client):
        resp = client.post("/api/insight/daily", json={
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 20,
            "user_message": "자살하고 싶어요",
        })
        data = resp.json()
        assert data["type"] == "crisis_support"
        assert "1393" in data.get("crisis_line", "")
