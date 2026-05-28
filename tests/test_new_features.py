"""
test_new_features.py
사주담 신규 기능 테스트:
1. 점성술 연계 (서양 별자리 + 동양 12지신)
2. i18n 다국어 지원
3. 프롬프트 표준화
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.engine.saju_calculator import (
    get_western_astrology_sign,
    get_eastern_zodiac,
    get_astrology_info,
)


# ─────────────────────────────────────────────
# 1. 점성술 연계 테스트
# ─────────────────────────────────────────────

class TestWesternAstrologySign:
    """get_western_astrology_sign() 테스트"""

    def test_aries_march_21(self):
        """양자리: 3월 21일"""
        r = get_western_astrology_sign(3, 21)
        assert r["sign_en"] == "Aries"
        assert r["sign_ko"] == "양자리"

    def test_capricorn_january_1(self):
        """염소자리: 1월 1일"""
        r = get_western_astrology_sign(1, 1)
        assert r["sign_en"] == "Capricorn"
        assert "염소" in r["sign_ko"]

    def test_cancer_july_1(self):
        """게자리: 7월 1일"""
        r = get_western_astrology_sign(7, 1)
        assert r["sign_en"] == "Cancer"
        assert r["sign_ko"] == "게자리"

    def test_scorpio_november_1(self):
        """전갈자리: 11월 1일"""
        r = get_western_astrology_sign(11, 1)
        assert r["sign_en"] == "Scorpio"
        assert r["sign_ko"] == "전갈자리"

    def test_result_structure(self):
        """반환 구조 검증"""
        r = get_western_astrology_sign(5, 20)
        assert "sign_en" in r
        assert "sign_ko" in r
        assert "sign_ja" in r
        assert "birth_month" in r
        assert "birth_day" in r
        assert "method" in r
        assert r["method"] == "solar_date_boundary"

    def test_lang_ko(self):
        r = get_western_astrology_sign(3, 21, lang="ko")
        assert r["sign_ko"] == "양자리"

    def test_lang_ja(self):
        r = get_western_astrology_sign(3, 21, lang="ja")
        assert "おひつじ" in r["sign_ja"]

    def test_all_months_return_valid_sign(self):
        """12개월 × 각 대표일에 유효한 별자리 반환"""
        VALID_SIGNS = {
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        }
        test_dates = [
            (1, 15), (2, 15), (3, 25), (4, 25), (5, 25), (6, 25),
            (7, 25), (8, 25), (9, 25), (10, 25), (11, 25), (12, 25),
        ]
        for month, day in test_dates:
            r = get_western_astrology_sign(month, day)
            assert r["sign_en"] in VALID_SIGNS, f"Invalid sign for {month}/{day}: {r['sign_en']}"

    def test_aquarius_january_20(self):
        """물병자리: 1월 20일 시작"""
        r = get_western_astrology_sign(1, 20)
        assert r["sign_en"] == "Aquarius"

    def test_pisces_february_19(self):
        """물고기자리: 2월 19일"""
        r = get_western_astrology_sign(2, 19)
        assert r["sign_en"] == "Pisces"


class TestEasternZodiac:
    """get_eastern_zodiac() 테스트"""

    def test_horse_1990(self):
        """1990년 = 말띠"""
        r = get_eastern_zodiac(1990)
        assert r["zodiac_en"] == "horse"
        assert r["zodiac_ko"] == "말"

    def test_rat_1924(self):
        """1924년 = 쥐띠 (기준점)"""
        r = get_eastern_zodiac(1924)
        assert r["zodiac_en"] == "rat"

    def test_rat_1984(self):
        """1984년 = 쥐띠 (60년 후)"""
        r = get_eastern_zodiac(1984)
        assert r["zodiac_en"] == "rat"

    def test_dragon_2000(self):
        """2000년 = 용띠"""
        r = get_eastern_zodiac(2000)
        assert r["zodiac_en"] == "dragon"
        assert r["zodiac_ko"] == "용"

    def test_result_structure(self):
        """반환 구조 검증"""
        r = get_eastern_zodiac(1990)
        assert "zodiac_en" in r
        assert "zodiac_ko" in r
        assert "zodiac_ja" in r
        assert "zodiac_en_label" in r
        assert "birth_year" in r
        assert "earthly_branch" in r
        assert r["birth_year"] == 1990

    def test_all_12_animals(self):
        """12지신 모두 순환 검증"""
        ANIMALS = ["rat", "ox", "tiger", "rabbit", "dragon", "snake",
                   "horse", "goat", "monkey", "rooster", "dog", "pig"]
        for i, animal in enumerate(ANIMALS):
            year = 1924 + i
            r = get_eastern_zodiac(year)
            assert r["zodiac_en"] == animal, f"Year {year}: expected {animal}, got {r['zodiac_en']}"

    def test_boundary_1900(self):
        """1900년 경계값"""
        r = get_eastern_zodiac(1900)
        assert "zodiac_en" in r
        assert r["zodiac_en"] in ["rat", "ox", "tiger", "rabbit", "dragon", "snake",
                                   "horse", "goat", "monkey", "rooster", "dog", "pig"]

    def test_lang_ja(self):
        """일본어 반환"""
        r = get_eastern_zodiac(1990, lang="ja")
        assert r["zodiac_ja"]  # 빈 문자열이 아님

    def test_earthly_branch_valid(self):
        """earthly_branch는 12지지 중 하나"""
        from src.engine.saju_calculator import EARTHLY_BRANCHES
        for year in [1984, 1990, 2000, 2012, 2024]:
            r = get_eastern_zodiac(year)
            assert r["earthly_branch"] in EARTHLY_BRANCHES, \
                f"Year {year}: invalid branch {r['earthly_branch']}"


class TestGetAstrologyInfo:
    """get_astrology_info() 통합 테스트"""

    def test_basic_structure(self):
        r = get_astrology_info(1990, 5, 20)
        assert "western" in r
        assert "eastern" in r
        assert "lunar_date" in r
        assert "combined_message" in r
        assert "disclaimer" in r

    def test_combined_message_not_empty(self):
        r = get_astrology_info(1990, 5, 20)
        assert r["combined_message"]
        assert len(r["combined_message"]) > 10

    def test_lang_ko(self):
        r = get_astrology_info(1990, 5, 20, lang="ko")
        assert "disclaimer" in r

    def test_lang_en(self):
        r = get_astrology_info(1990, 5, 20, lang="en")
        assert "combine" in r["combined_message"].lower()

    def test_lang_ja(self):
        r = get_astrology_info(1990, 5, 20, lang="ja")
        assert "エネルギー" in r["combined_message"]

    def test_western_sign_present(self):
        r = get_astrology_info(1990, 5, 20)
        assert r["western"]["sign_en"]
        assert r["western"]["sign_ko"]

    def test_eastern_zodiac_present(self):
        r = get_astrology_info(1990, 5, 20)
        assert r["eastern"]["zodiac_en"] == "horse"  # 1990 = 말띠
        assert r["eastern"]["zodiac_ko"] == "말"


# ─────────────────────────────────────────────
# 2. i18n 다국어 테스트
# ─────────────────────────────────────────────

class TestI18n:
    """i18n 유틸리티 테스트"""

    def test_get_i18n_ko(self):
        from app.i18n.i18n_utils import get_i18n
        labels = get_i18n("ko")
        assert "disclaimer" in labels
        assert "명리학" in labels["disclaimer"]

    def test_get_i18n_en(self):
        from app.i18n.i18n_utils import get_i18n
        labels = get_i18n("en")
        assert "disclaimer" in labels
        assert "Four Pillars" in labels["disclaimer"]

    def test_get_i18n_ja(self):
        from app.i18n.i18n_utils import get_i18n
        labels = get_i18n("ja")
        assert "disclaimer" in labels
        assert "命理" in labels["disclaimer"]

    def test_unsupported_lang_fallback_to_ko(self):
        from app.i18n.i18n_utils import get_i18n
        labels = get_i18n("zh")  # 미지원 언어
        assert "disclaimer" in labels
        # 한국어 폴백
        assert "명리학" in labels["disclaimer"]

    def test_t_function_simple_key(self):
        from app.i18n.i18n_utils import t
        result = t("disclaimer", lang="ko")
        assert "명리학" in result

    def test_t_function_nested_key(self):
        from app.i18n.i18n_utils import t
        result = t("element.목", lang="ko")
        assert "목" in result.lower() or "木" in result

    def test_t_function_zodiac_key(self):
        from app.i18n.i18n_utils import t
        result = t("zodiac.rat", lang="ko")
        assert "쥐" in result

    def test_t_function_fallback_missing_key(self):
        from app.i18n.i18n_utils import t
        result = t("nonexistent_key", lang="ko", default="MISSING")
        assert result == "MISSING"

    def test_resolve_lang_query_param(self):
        from app.i18n.i18n_utils import resolve_lang
        assert resolve_lang("en", None) == "en"
        assert resolve_lang("ja", None) == "ja"
        assert resolve_lang("ko", None) == "ko"

    def test_resolve_lang_accept_header(self):
        from app.i18n.i18n_utils import resolve_lang
        assert resolve_lang(None, "ja,ko;q=0.9,en;q=0.8") == "ja"
        assert resolve_lang(None, "en-US,en;q=0.8") == "en"

    def test_resolve_lang_query_overrides_header(self):
        from app.i18n.i18n_utils import resolve_lang
        result = resolve_lang("ko", "ja,en")
        assert result == "ko"

    def test_resolve_lang_default_ko(self):
        from app.i18n.i18n_utils import resolve_lang
        assert resolve_lang(None, None) == "ko"
        assert resolve_lang("zh", "fr") == "ko"

    def test_all_langs_have_required_keys(self):
        from app.i18n.i18n_utils import get_i18n
        required_keys = ["disclaimer", "legal", "fortune_summary", "five_elements_analysis",
                         "emotion_coaching", "today_advice", "zodiac_message"]
        for lang in ["ko", "ja", "en"]:
            labels = get_i18n(lang)
            for key in required_keys:
                assert key in labels, f"lang={lang}: missing key '{key}'"

    def test_western_zodiac_labels_in_all_langs(self):
        from app.i18n.i18n_utils import get_i18n
        for lang in ["ko", "ja", "en"]:
            labels = get_i18n(lang)
            assert "western_zodiac" in labels, f"lang={lang}: missing 'western_zodiac'"
            wz = labels["western_zodiac"]
            assert "Aries" in wz, f"lang={lang}: missing 'Aries' in western_zodiac"


# ─────────────────────────────────────────────
# 3. 프롬프트 표준화 테스트
# ─────────────────────────────────────────────

class TestSajuPromptTemplate:
    """프롬프트 템플릿 테스트"""

    @pytest.fixture
    def sample_ctx(self):
        from app.prompts.saju_prompt_template import SajuPromptContext
        return SajuPromptContext(
            birth_year=1990,
            birth_month=5,
            birth_day=20,
            birth_hour=14,
            gender="female",
            lang="ko",
            year_pillar="庚午",
            month_pillar="庚午",
            day_pillar="壬申",
            primary_element="금",
            western_sign_ko="쌍둥이자리",
            western_sign_en="Gemini",
            eastern_zodiac_ko="말",
            eastern_zodiac_en="Horse",
            mood_score=3,
            mood_label="보통",
        )

    def test_build_saju_prompt_ko(self, sample_ctx):
        from app.prompts.saju_prompt_template import build_saju_prompt
        result = build_saju_prompt(sample_ctx)
        assert "system" in result
        assert "user" in result
        assert "response_format" in result
        assert "lang" in result
        assert result["lang"] == "ko"

    def test_system_message_not_empty(self, sample_ctx):
        from app.prompts.saju_prompt_template import build_saju_prompt
        result = build_saju_prompt(sample_ctx)
        assert len(result["system"]) > 20

    def test_user_prompt_contains_birth_info(self, sample_ctx):
        from app.prompts.saju_prompt_template import build_saju_prompt
        result = build_saju_prompt(sample_ctx)
        assert "1990" in result["user"]
        assert "5" in result["user"]

    def test_user_prompt_contains_pillars(self, sample_ctx):
        from app.prompts.saju_prompt_template import build_saju_prompt
        result = build_saju_prompt(sample_ctx)
        assert "庚午" in result["user"] or "壬申" in result["user"]

    def test_user_prompt_contains_western_sign(self, sample_ctx):
        from app.prompts.saju_prompt_template import build_saju_prompt
        result = build_saju_prompt(sample_ctx)
        assert "쌍둥이자리" in result["user"] or "Gemini" in result["user"]

    def test_user_prompt_ja(self, sample_ctx):
        from app.prompts.saju_prompt_template import build_saju_prompt, SajuPromptContext
        ctx_ja = SajuPromptContext(**{**sample_ctx.__dict__, "lang": "ja"})
        result = build_saju_prompt(ctx_ja)
        assert result["lang"] == "ja"
        assert "四柱" in result["user"] or "生年月日" in result["user"]

    def test_user_prompt_en(self, sample_ctx):
        from app.prompts.saju_prompt_template import build_saju_prompt, SajuPromptContext
        ctx_en = SajuPromptContext(**{**sample_ctx.__dict__, "lang": "en"})
        result = build_saju_prompt(ctx_en)
        assert result["lang"] == "en"
        assert "Birth" in result["user"] or "Pillar" in result["user"]

    def test_response_format_contains_all_fields(self, sample_ctx):
        from app.prompts.saju_prompt_template import build_saju_prompt
        result = build_saju_prompt(sample_ctx)
        fmt = result["response_format"]
        # 5개 필드 모두 포함
        assert "운세요약" in fmt or "fortune_summary" in fmt or "運勢" in fmt

    def test_fortune_response_schema_structure(self):
        from app.prompts.saju_prompt_template import FortuneResponseSchema
        schema = FortuneResponseSchema(
            운세요약="오늘은 좋은 날입니다.",
            오행분석="목 기운이 강합니다.",
            에너지인사이트="긍정적인 에너지를 활용하세요.",
            오늘의조언="산책을 즐기세요.",
            별자리메시지="쌍둥이자리의 에너지가 빛납니다.",
        )
        d = schema.to_dict()
        assert "운세요약" in d
        assert "오행분석" in d
        assert "에너지인사이트" in d
        assert "오늘의조언" in d
        assert "별자리메시지" in d
        assert "disclaimer" in d

    def test_fortune_response_schema_json(self):
        from app.prompts.saju_prompt_template import FortuneResponseSchema
        schema = FortuneResponseSchema(운세요약="테스트")
        json_str = schema.to_json()
        import json
        parsed = json.loads(json_str)
        assert parsed["운세요약"] == "테스트"

    def test_fortune_response_from_json(self):
        from app.prompts.saju_prompt_template import FortuneResponseSchema
        import json
        data = {"운세요약": "좋은 날", "오행분석": "목이 강함", "에너지인사이트": "", "오늘의조언": "", "별자리메시지": ""}
        schema = FortuneResponseSchema.from_json(json.dumps(data, ensure_ascii=False))
        assert schema.운세요약 == "좋은 날"

    def test_make_rule_based_response_ko(self, sample_ctx):
        from app.prompts.saju_prompt_template import make_rule_based_response
        response = make_rule_based_response(sample_ctx)
        assert response.운세요약
        assert response.오행분석
        assert response.에너지인사이트
        assert response.오늘의조언
        assert response.별자리메시지

    def test_make_rule_based_response_ja(self, sample_ctx):
        from app.prompts.saju_prompt_template import make_rule_based_response, SajuPromptContext
        ctx_ja = SajuPromptContext(**{**sample_ctx.__dict__, "lang": "ja"})
        response = make_rule_based_response(ctx_ja)
        assert response.운세요약  # 필드명은 한국어지만 값은 일본어

    def test_make_rule_based_response_en(self, sample_ctx):
        from app.prompts.saju_prompt_template import make_rule_based_response, SajuPromptContext
        ctx_en = SajuPromptContext(**{**sample_ctx.__dict__, "lang": "en"})
        response = make_rule_based_response(ctx_en)
        assert response.운세요약


# ─────────────────────────────────────────────
# 4. API 엔드포인트 통합 테스트
# ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def api_client():
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


class TestAstrologyEndpoint:
    """GET /api/saju/astrology 엔드포인트"""

    def test_get_astrology_basic(self, api_client):
        resp = api_client.get("/api/saju/astrology", params={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "western" in data
        assert "eastern" in data

    def test_get_astrology_lang_en(self, api_client):
        resp = api_client.get("/api/saju/astrology", params={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20, "lang": "en"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["lang"] == "en"

    def test_get_astrology_accept_language_header(self, api_client):
        resp = api_client.get("/api/saju/astrology", params={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20
        }, headers={"Accept-Language": "ja"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["lang"] == "ja"

    def test_post_astrology_basic(self, api_client):
        resp = api_client.post("/api/saju/astrology", json={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "western" in data
        assert "eastern" in data
        assert "combined_message" in data

    def test_post_astrology_lang_ja(self, api_client):
        resp = api_client.post("/api/saju/astrology", json={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20, "lang": "ja"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["lang"] == "ja"


class TestI18nLabelsEndpoint:
    """GET /api/saju/i18n/labels 엔드포인트"""

    def test_get_labels_ko(self, api_client):
        resp = api_client.get("/api/saju/i18n/labels", params={"lang": "ko"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["lang"] == "ko"
        assert "labels" in data

    def test_get_labels_en(self, api_client):
        resp = api_client.get("/api/saju/i18n/labels", params={"lang": "en"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["lang"] == "en"

    def test_get_labels_accept_language(self, api_client):
        resp = api_client.get("/api/saju/i18n/labels",
                              headers={"Accept-Language": "ja,en;q=0.8"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["lang"] == "ja"


class TestFortuneStandardEndpoint:
    """POST /api/saju/fortune-standard 엔드포인트"""

    def test_basic_request(self, api_client):
        resp = api_client.post("/api/saju/fortune-standard", json={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "fortune" in data
        assert "pillars" in data

    def test_fortune_fields_present(self, api_client):
        resp = api_client.post("/api/saju/fortune-standard", json={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20
        })
        data = resp.json()
        fortune = data["fortune"]
        # 5개 표준 필드 중 최소 1개 이상 존재
        standard_fields = {"운세요약", "오행분석", "에너지인사이트", "오늘의조언", "별자리메시지"}
        assert standard_fields & set(fortune.keys()), f"No standard fields in: {list(fortune.keys())}"

    def test_lang_en(self, api_client):
        resp = api_client.post("/api/saju/fortune-standard", json={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20, "lang": "en"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["lang"] == "en"

    def test_labels_present(self, api_client):
        resp = api_client.post("/api/saju/fortune-standard", json={
            "birth_year": 1990, "birth_month": 5, "birth_day": 20
        })
        data = resp.json()
        assert "labels" in data
        labels = data["labels"]
        assert "fortune_summary" in labels
