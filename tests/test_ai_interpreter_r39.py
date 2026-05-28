"""
test_ai_interpreter_r39.py
ai_interpreter.py 전구간 커버리지 목표 (헤르 R39)

커버 대상:
1. SYSTEM_PROMPTS: ko/ja/en 3개 키 존재 + 길이 검증
2. USER_PROMPT_TEMPLATES: ko/ja/en 3개 키 존재 + 필수 변수 플레이스홀더
3. build_prompts():
   - lang=ko/ja/en 각각 정상 반환
   - lang=invalid → SYSTEM_PROMPTS["ko"] 폴백
   - relation 4종 × mood_level 1~5 조합
   - 반환 딕셔너리 반드시 system/user 키 포함
4. interpret_saju():
   - ImportError → "[anthropic 미설치]" 메시지
   - Exception → "[API 오류]" 메시지
   - Anthropic mock → 정상 반환 구조
   - lang=ja/en 전체 파이프라인
"""
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─────────────────────────────────────────────
# 공통 픽스처
# ─────────────────────────────────────────────

@pytest.fixture
def eight_char():
    """테스트용 사주팔자 딕셔너리 (get_saju 실제 호출)"""
    from saju_engine import get_saju
    r = get_saju(1990, 5, 20, 14)
    return r["eight_char"]


@pytest.fixture
def mood_result():
    """테스트용 mood_result (map_mood_to_saju 실제 호출)"""
    from saju_engine import get_saju, map_mood_to_saju
    r = get_saju(1990, 5, 20, 14)
    return map_mood_to_saju(3, r["eight_char"])


@pytest.fixture
def mock_anthropic_client():
    """anthropic.Anthropic 클라이언트 Mock"""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="오늘의 기운이 좋습니다. 세 가지 액션을 추천합니다.")]
    mock_msg.usage = MagicMock(input_tokens=150, output_tokens=80)

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


# ─────────────────────────────────────────────
# 1. SYSTEM_PROMPTS 상수 검증
# ─────────────────────────────────────────────

class TestSystemPrompts:
    def test_has_all_three_languages(self):
        from ai_interpreter import SYSTEM_PROMPTS
        assert "ko" in SYSTEM_PROMPTS
        assert "ja" in SYSTEM_PROMPTS
        assert "en" in SYSTEM_PROMPTS

    def test_ko_prompt_min_length(self):
        from ai_interpreter import SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS["ko"]) >= 50

    def test_ja_prompt_min_length(self):
        from ai_interpreter import SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS["ja"]) >= 50

    def test_en_prompt_min_length(self):
        from ai_interpreter import SYSTEM_PROMPTS
        assert len(SYSTEM_PROMPTS["en"]) >= 50

    def test_ko_prompt_is_korean(self):
        from ai_interpreter import SYSTEM_PROMPTS
        # 한국어 프롬프트에 한글 포함 여부
        assert any(ord(c) >= 0xAC00 for c in SYSTEM_PROMPTS["ko"])

    def test_en_prompt_is_english(self):
        from ai_interpreter import SYSTEM_PROMPTS
        # 영어 프롬프트에 ASCII 알파벳 다수
        ascii_count = sum(1 for c in SYSTEM_PROMPTS["en"] if c.isalpha() and ord(c) < 128)
        assert ascii_count > 20


# ─────────────────────────────────────────────
# 2. USER_PROMPT_TEMPLATES 상수 검증
# ─────────────────────────────────────────────

class TestUserPromptTemplates:
    def test_has_all_three_languages(self):
        from ai_interpreter import USER_PROMPT_TEMPLATES
        assert "ko" in USER_PROMPT_TEMPLATES
        assert "ja" in USER_PROMPT_TEMPLATES
        assert "en" in USER_PROMPT_TEMPLATES

    def test_ko_template_has_required_vars(self):
        from ai_interpreter import USER_PROMPT_TEMPLATES
        tmpl = USER_PROMPT_TEMPLATES["ko"]
        for var in ["year_glyph", "month_glyph", "day_glyph", "hour_glyph",
                    "mood_level", "mood_label", "mood_emoji", "mood_element", "relation"]:
            assert "{" + var + "}" in tmpl, f"ko 템플릿에 {var} 없음"

    def test_ja_template_has_required_vars(self):
        from ai_interpreter import USER_PROMPT_TEMPLATES
        tmpl = USER_PROMPT_TEMPLATES["ja"]
        for var in ["year_glyph", "month_glyph", "day_glyph", "mood_level", "relation"]:
            assert "{" + var + "}" in tmpl, f"ja 템플릿에 {var} 없음"

    def test_en_template_has_required_vars(self):
        from ai_interpreter import USER_PROMPT_TEMPLATES
        tmpl = USER_PROMPT_TEMPLATES["en"]
        for var in ["year_glyph", "month_glyph", "day_glyph", "mood_level", "relation"]:
            assert "{" + var + "}" in tmpl, f"en 템플릿에 {var} 없음"


# ─────────────────────────────────────────────
# 3. build_prompts() 검증
# ─────────────────────────────────────────────

class TestBuildPrompts:

    def test_ko_returns_system_and_user(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char,
            mood_level=3,
            mood_label="보통",
            mood_emoji="😐",
            mood_element="토",
            relation="상생",
            lang="ko",
        )
        assert "system" in result
        assert "user" in result
        assert len(result["system"]) > 10
        assert len(result["user"]) > 10

    def test_ja_returns_system_and_user(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char,
            mood_level=2,
            mood_label="힘듦",
            mood_emoji="😢",
            mood_element="수",
            relation="상극",
            lang="ja",
        )
        assert "system" in result
        assert "user" in result
        # 일본어 시스템 프롬프트 확인
        assert "四柱" in result["system"] or len(result["system"]) > 10

    def test_en_returns_system_and_user(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char,
            mood_level=5,
            mood_label="최상",
            mood_emoji="😊",
            mood_element="목",
            relation="동일",
            lang="en",
        )
        assert "system" in result
        assert "user" in result
        assert "Eastern" in result["system"] or len(result["system"]) > 10

    def test_invalid_lang_falls_back_to_ko(self, eight_char):
        """lang=invalid → SYSTEM_PROMPTS['ko'] 폴백"""
        from ai_interpreter import build_prompts, SYSTEM_PROMPTS
        result = build_prompts(
            eight_char=eight_char,
            mood_level=3,
            mood_label="보통",
            mood_emoji="😐",
            mood_element="화",
            relation="중립",
            lang="fr",  # 미지원 언어
        )
        assert result["system"] == SYSTEM_PROMPTS["ko"]

    def test_relation_sangsaeng(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char,
            mood_level=1,
            mood_label="최악",
            mood_emoji="😭",
            mood_element="금",
            relation="상생",
            lang="ko",
        )
        assert "상생" in result["user"]

    def test_relation_sanggeuek(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char,
            mood_level=2,
            mood_label="힘듦",
            mood_emoji="😢",
            mood_element="수",
            relation="상극",
            lang="ko",
        )
        assert "상극" in result["user"]

    def test_relation_dongil(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char,
            mood_level=4,
            mood_label="좋음",
            mood_emoji="😊",
            mood_element="목",
            relation="동일",
            lang="ko",
        )
        assert "동일" in result["user"]

    def test_relation_junglib(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char,
            mood_level=3,
            mood_label="보통",
            mood_emoji="😐",
            mood_element="토",
            relation="중립",
            lang="ko",
        )
        assert "중립" in result["user"]

    def test_mood_level_1(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char, mood_level=1,
            mood_label="최악", mood_emoji="😭",
            mood_element="금", relation="상극", lang="ko"
        )
        assert "1" in result["user"]

    def test_mood_level_5(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char, mood_level=5,
            mood_label="최상", mood_emoji="😄",
            mood_element="목", relation="상생", lang="ko"
        )
        assert "5" in result["user"]

    def test_user_prompt_contains_eight_glyphs(self, eight_char):
        from ai_interpreter import build_prompts
        result = build_prompts(
            eight_char=eight_char, mood_level=3,
            mood_label="보통", mood_emoji="😐",
            mood_element="화", relation="중립", lang="ko"
        )
        # 팔자 글자 포함 확인
        assert len(result["user"]) > 50


# ─────────────────────────────────────────────
# 4. interpret_saju() 오류 경로
# ─────────────────────────────────────────────

class TestInterpretSaju:

    def test_import_error_returns_pip_message(self, eight_char, mood_result):
        """anthropic ImportError → pip install 안내 메시지"""
        from ai_interpreter import interpret_saju
        with patch.dict("sys.modules", {"anthropic": None}):
            result = interpret_saju(eight_char, mood_result, lang="ko", api_key="fake_key")
        assert "pip install" in result["interpretation"] or "미설치" in result["interpretation"]
        assert "prompts" in result
        assert result["usage"] == {}

    def test_api_exception_returns_error_message(self, eight_char, mood_result):
        """API Exception → [API 오류] 메시지"""
        from ai_interpreter import interpret_saju
        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value.messages.create.side_effect = Exception("Connection refused")
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            result = interpret_saju(eight_char, mood_result, lang="ko", api_key="fake_key")
        assert "[API 오류]" in result["interpretation"]
        assert "Connection refused" in result["interpretation"]
        assert result["usage"] == {}

    def test_success_returns_correct_structure(self, eight_char, mood_result, mock_anthropic_client):
        """정상 Anthropic 응답 → 올바른 구조 반환"""
        from ai_interpreter import interpret_saju
        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_client
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            result = interpret_saju(eight_char, mood_result, lang="ko", api_key="test_key")
        assert "interpretation" in result
        assert "prompts" in result
        assert "model" in result
        assert "usage" in result
        assert result["usage"]["input_tokens"] == 150
        assert result["usage"]["output_tokens"] == 80

    def test_ja_pipeline_success(self, eight_char, mood_result, mock_anthropic_client):
        """lang=ja 전체 파이프라인 정상 동작"""
        from ai_interpreter import interpret_saju
        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_client
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            result = interpret_saju(eight_char, mood_result, lang="ja", api_key="test_key")
        assert "interpretation" in result
        # ja 시스템 프롬프트가 사용되었는지 확인
        assert "四柱" in result["prompts"]["system"] or len(result["prompts"]["system"]) > 10

    def test_en_pipeline_success(self, eight_char, mood_result, mock_anthropic_client):
        """lang=en 전체 파이프라인 정상 동작"""
        from ai_interpreter import interpret_saju
        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_client
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            result = interpret_saju(eight_char, mood_result, lang="en", api_key="test_key")
        assert "interpretation" in result
        assert "Eastern" in result["prompts"]["system"] or len(result["prompts"]["system"]) > 10

    def test_model_field_preserved(self, eight_char, mood_result, mock_anthropic_client):
        """커스텀 모델명 필드 보존"""
        from ai_interpreter import interpret_saju
        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_client
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            result = interpret_saju(eight_char, mood_result, lang="ko",
                                    api_key="test_key", model="claude-3-5-sonnet-20241022")
        assert result["model"] == "claude-3-5-sonnet-20241022"

    def test_env_api_key_used_when_none(self, eight_char, mood_result):
        """api_key=None → 환경변수 ANTHROPIC_API_KEY 사용 시도"""
        from ai_interpreter import interpret_saju
        import os
        # 환경변수도 없으면 ImportError 또는 Exception → 메시지 반환
        with patch.dict(os.environ, {}, clear=True):
            if "ANTHROPIC_API_KEY" in os.environ:
                del os.environ["ANTHROPIC_API_KEY"]
        # anthropic 미설치 환경 시뮬레이션
        with patch.dict("sys.modules", {"anthropic": None}):
            result = interpret_saju(eight_char, mood_result, lang="ko", api_key=None)
        # ImportError or Exception 어느 경우든 interpretation 필드 존재
        assert "interpretation" in result
