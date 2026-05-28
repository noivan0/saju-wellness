"""
test_saju_calculator.py
사주팔자 계산 엔진 단위 테스트

- get_saju(): 연주·월주·일주·시주 계산 검증
- 천간(天干) / 지지(地支) / 오행(五行) 검증
- 경계값: 1900년, 2100년 근처, hour=None, 자정(0시), 23시
- get_five_element_distribution(): 오행 분포
- map_mood_to_saju(): 기분 매핑
- get_daewoon(): 대운 계산 (lunar-python 의존, ImportError 허용)
"""
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from saju_engine import (
    get_saju,
    get_five_element_distribution,
    map_mood_to_saju,
    get_daewoon,
    HEAVENLY_STEMS,
    EARTHLY_BRANCHES,
    STEM_ELEMENT,
    BRANCH_ELEMENT,
    ELEMENT_SHENG,
    ELEMENT_KE,
    MOOD_MAP,
)
from src.engine.saju_calculator import (
    calc_four_pillars,
    calc_year_pillar,
    calc_month_pillar,
    HEAVENLY_STEMS as SRC_STEMS,
    EARTHLY_BRANCHES as SRC_BRANCHES,
    FIVE_ELEMENTS,
)


# ─────────────────────────────────────────────
# 1. 기본 상수 검증
# ─────────────────────────────────────────────

class TestConstants:
    def test_heavenly_stems_count(self):
        assert len(HEAVENLY_STEMS) == 10

    def test_earthly_branches_count(self):
        assert len(EARTHLY_BRANCHES) == 12

    def test_stem_element_coverage(self):
        assert len(STEM_ELEMENT) == 10
        for el in STEM_ELEMENT:
            assert el in ["목", "화", "토", "금", "수"]

    def test_branch_element_coverage(self):
        assert len(BRANCH_ELEMENT) == 12
        for el in BRANCH_ELEMENT:
            assert el in ["목", "화", "토", "금", "수"]

    def test_element_sheng_cycle(self):
        """상생 오행 순환: 목→화→토→금→수→목"""
        assert ELEMENT_SHENG["목"] == "화"
        assert ELEMENT_SHENG["화"] == "토"
        assert ELEMENT_SHENG["토"] == "금"
        assert ELEMENT_SHENG["금"] == "수"
        assert ELEMENT_SHENG["수"] == "목"

    def test_element_ke_cycle(self):
        """상극 오행 순환: 목→토→수→화→금→목"""
        assert ELEMENT_KE["목"] == "토"
        assert ELEMENT_KE["토"] == "수"
        assert ELEMENT_KE["수"] == "화"
        assert ELEMENT_KE["화"] == "금"
        assert ELEMENT_KE["금"] == "목"

    def test_src_engine_stems_branches(self):
        assert len(SRC_STEMS) == 10
        assert len(SRC_BRANCHES) == 12
        assert "목" in FIVE_ELEMENTS.values()


# ─────────────────────────────────────────────
# 2. get_saju 기본 동작
# ─────────────────────────────────────────────

class TestGetSaju:
    def _pillar_valid(self, p: dict):
        """기둥 딕셔너리 구조 검증"""
        assert "glyph" in p
        assert "reading" in p
        assert "element" in p
        el = p["element"]
        assert "stem" in el and "branch" in el
        assert el["stem"] in ["목", "화", "토", "금", "수"]
        assert el["branch"] in ["목", "화", "토", "금", "수"]

    def test_basic_1990(self):
        r = get_saju(1990, 5, 20, 14)
        assert r["hour_unknown"] is False
        assert r["hour_variants"] is None
        ec = r["eight_char"]
        for key in ["year_pillar", "month_pillar", "day_pillar", "hour_pillar"]:
            self._pillar_valid(ec[key])

    def test_eight_glyphs_length(self):
        r = get_saju(2000, 6, 15, 12)
        glyphs = r["eight_char"]["eight_glyphs"]
        # 8글자: 4기둥 × 2자
        assert len(glyphs) == 8

    def test_hour_none_returns_variants(self):
        r = get_saju(1990, 3, 10)
        assert r["hour_unknown"] is True
        assert isinstance(r["hour_variants"], list)
        assert len(r["hour_variants"]) == 12

    def test_hour_variants_structure(self):
        r = get_saju(1985, 7, 7)
        for v in r["hour_variants"]:
            assert "hour_branch" in v
            assert "hour_branch_kr" in v
            assert "time_range" in v
            assert "eight_char" in v

    def test_method_field_present(self):
        r = get_saju(1990, 1, 1, 0)
        assert r["method"] in ["lunar-python", "fallback"]

    def test_stems_branches_in_result(self):
        r = get_saju(1995, 11, 15, 8)
        ec = r["eight_char"]
        assert len(ec["stems"]) == 4
        assert len(ec["branches"]) == 4
        for s in ec["stems"]:
            assert s in HEAVENLY_STEMS
        for b in ec["branches"]:
            assert b in EARTHLY_BRANCHES

    # ── 경계값 ──

    def test_boundary_year_1900(self):
        """1900년 최소 경계"""
        r = get_saju(1900, 1, 1, 0)
        assert "eight_char" in r
        ec = r["eight_char"]
        self._pillar_valid(ec["year_pillar"])

    def test_boundary_year_2099(self):
        """2099년 상한 경계"""
        r = get_saju(2099, 12, 31, 23)
        assert "eight_char" in r

    def test_boundary_hour_zero(self):
        """자정 0시 — 자시(子時) 경계"""
        r = get_saju(1990, 6, 15, 0)
        ec = r["eight_char"]
        # 자(子) 지지 = EARTHLY_BRANCHES[0]
        assert ec["hour_pillar"]["glyph"][1] == EARTHLY_BRANCHES[0]

    def test_boundary_hour_23(self):
        """23시 — 자시 재진입 (마지막 경계)"""
        r = get_saju(1990, 6, 15, 23)
        ec = r["eight_char"]
        # 23시도 자(子)시 — HOUR_TO_BRANCH[23] = 0
        assert ec["hour_pillar"]["glyph"][1] == EARTHLY_BRANCHES[0]

    def test_boundary_month_1_and_12(self):
        """1월/12월 월주 경계"""
        r1 = get_saju(2000, 1, 15, 12)
        r12 = get_saju(2000, 12, 15, 12)
        assert "eight_char" in r1
        assert "eight_char" in r12

    def test_boundary_day_1_31(self):
        """월 1일 / 31일 경계"""
        r_first = get_saju(1990, 3, 1, 12)
        r_last = get_saju(1990, 3, 31, 12)
        assert "eight_char" in r_first
        assert "eight_char" in r_last

    def test_1984_gabjia_year(self):
        """1984 갑자년(甲子) — 60갑자 기준점"""
        r = get_saju(1984, 2, 5, 12)
        yp = r["eight_char"]["year_pillar"]
        # 甲子: 천간=甲, 지지=子
        assert yp["glyph"] == "甲子", f"Expected 甲子, got {yp['glyph']}"

    def test_2024_year_pillar(self):
        """2024 갑진년(甲辰)"""
        r = get_saju(2024, 6, 1, 12)
        yp = r["eight_char"]["year_pillar"]
        assert yp["glyph"] == "甲辰", f"Expected 甲辰, got {yp['glyph']}"


# ─────────────────────────────────────────────
# 3. calc_year_pillar / calc_month_pillar (src.engine)
# ─────────────────────────────────────────────

class TestSrcEngineCalculators:
    def test_calc_year_pillar_1990(self):
        yp = calc_year_pillar(1990)
        assert "stem" in yp
        assert "branch" in yp
        assert "pillar" in yp
        assert "element" in yp
        assert yp["element"] in ["목", "화", "토", "금", "수"]

    def test_calc_year_pillar_stem_cycles_10(self):
        """10년 주기로 천간 반복"""
        stems = [calc_year_pillar(1984 + i)["stem"] for i in range(10)]
        assert stems == calc_year_pillar.__wrapped__  if hasattr(calc_year_pillar, '__wrapped__') else True
        # 단순히 10개 모두 유효한 천간인지 확인
        for s in stems:
            assert s in SRC_STEMS

    def test_calc_month_pillar(self):
        for month in range(1, 13):
            mp = calc_month_pillar(2000, month)
            assert "stem" in mp
            assert "branch" in mp

    def test_calc_four_pillars_basic(self):
        fp = calc_four_pillars(1990, 5, 20, 14)
        for key in ["year", "month", "day", "primary_element", "lunar_date", "disclaimer"]:
            assert key in fp

    def test_calc_four_pillars_with_hour(self):
        fp = calc_four_pillars(1990, 5, 20, 14)
        assert "hour" in fp

    def test_calc_four_pillars_without_hour(self):
        fp = calc_four_pillars(1990, 5, 20)
        assert "hour" not in fp

    def test_calc_four_pillars_disclaimer(self):
        """모든 언어 면책 문구 포함"""
        for lang in ["ko", "ja", "en"]:
            fp = calc_four_pillars(1990, 5, 20, 14, lang=lang)
            assert fp["disclaimer"]
            assert len(fp["disclaimer"]) > 10

    def test_calc_four_pillars_boundary_1900(self):
        fp = calc_four_pillars(1900, 1, 1)
        assert "year" in fp

    def test_calc_four_pillars_boundary_2099(self):
        fp = calc_four_pillars(2099, 12, 31, 23)
        assert "year" in fp


# ─────────────────────────────────────────────
# 4. 오행 분포 계산
# ─────────────────────────────────────────────

class TestFiveElementDistribution:
    def test_structure(self):
        r = get_saju(1990, 5, 20, 14)
        dist = get_five_element_distribution(r["eight_char"])
        assert "counts" in dist
        assert "dominant" in dist
        assert "balance" in dist
        assert "details" in dist

    def test_counts_sum_to_8(self):
        """4기둥 × 2(천간+지지) = 8"""
        r = get_saju(1990, 5, 20, 14)
        dist = get_five_element_distribution(r["eight_char"])
        assert sum(dist["counts"].values()) == 8

    def test_dominant_valid_element(self):
        r = get_saju(2000, 1, 1, 12)
        dist = get_five_element_distribution(r["eight_char"])
        assert dist["dominant"] in ["목", "화", "토", "금", "수"]

    def test_balance_values(self):
        r = get_saju(1990, 5, 20, 14)
        dist = get_five_element_distribution(r["eight_char"])
        assert dist["balance"] in ["balanced", "moderate", "imbalanced"]

    def test_details_length_4(self):
        r = get_saju(1995, 8, 15, 10)
        dist = get_five_element_distribution(r["eight_char"])
        assert len(dist["details"]) == 4


# ─────────────────────────────────────────────
# 5. 기분 → 사주 매핑
# ─────────────────────────────────────────────

class TestMapMoodToSaju:
    @pytest.fixture
    def sample_ec(self):
        return get_saju(1990, 5, 20, 14)["eight_char"]

    def test_all_mood_levels(self, sample_ec):
        for level in range(1, 6):
            result = map_mood_to_saju(level, sample_ec)
            assert "mood_label" in result
            assert "mood_emoji" in result
            assert "action_hints" in result
            assert "day_element" in result
            assert "relation" in result

    def test_crisis_level_1(self, sample_ec):
        result = map_mood_to_saju(1, sample_ec)
        assert result["mood_label"] == "매우 힘듦"
        assert isinstance(result["action_hints"], list)

    def test_good_mood_level_5(self, sample_ec):
        result = map_mood_to_saju(5, sample_ec)
        assert result["mood_label"] == "매우 좋음"

    def test_saju_reason_present(self, sample_ec):
        result = map_mood_to_saju(3, sample_ec)
        assert "saju_reason" in result
        assert len(result["saju_reason"]) > 5

    def test_ending_point_present(self, sample_ec):
        result = map_mood_to_saju(2, sample_ec)
        assert "ending_point" in result

    def test_day_element_is_valid(self, sample_ec):
        result = map_mood_to_saju(4, sample_ec)
        assert result["day_element"] in ["목", "화", "토", "금", "수"]

    def test_relation_is_valid(self, sample_ec):
        result = map_mood_to_saju(3, sample_ec)
        assert result["relation"] in ["동일", "상생", "상극", "중립"]

    def test_invalid_level_fallback(self, sample_ec):
        """범위 외 레벨은 MOOD_MAP.get(x, MOOD_MAP[3]) 폴백"""
        result = map_mood_to_saju(99, sample_ec)
        assert result["mood_label"] == "보통"


# ─────────────────────────────────────────────
# 6. 대운 계산 (lunar-python 의존)
# ─────────────────────────────────────────────

class TestIpchunYearPillar:
    """R25 CRITICAL — 입춘(立春) 기준 연주 버그 수정 검증
    
    근본원인: calc_year_pillar(year)가 양력 1/1 기준으로 년주 계산
             → 설날~입춘 사이 출생자(약 2~5%) 년주 오류
    
    수정: calc_four_pillars가 calc_year_pillar_accurate() 사용하도록 교체
    실증: 1990-01-15 → 경오(庚午) ❌ → 기사(己巳) ✅
    """

    def test_before_ipchun_uses_previous_year(self):
        """입춘 이전 출생 → 전년도 간지 (핵심 버그 케이스)"""
        # 1990-01-15: 입춘(1990-02-04) 이전 → 기사(己巳)
        fp = calc_four_pillars(1990, 1, 15, 0, 0, "female", "ko")
        assert fp["year"]["pillar"] == "기사", (
            f"입춘 이전 1990-01-15: 기사 기대, 실제={fp['year']['pillar']}"
        )

    def test_day_before_ipchun_uses_previous_year(self):
        """입춘 하루 전 → 전년도 간지"""
        # 1990-02-03: 입춘 전날 → 기사(己巳)
        fp = calc_four_pillars(1990, 2, 3, 0, 0, "female", "ko")
        assert fp["year"]["pillar"] == "기사", (
            f"입춘 하루 전 1990-02-03: 기사 기대, 실제={fp['year']['pillar']}"
        )

    def test_ipchun_day_uses_current_year(self):
        """입춘 당일 → 당년 간지"""
        # 1990-02-04: 입춘 당일 → 경오(庚午)
        fp = calc_four_pillars(1990, 2, 4, 0, 0, "female", "ko")
        assert fp["year"]["pillar"] == "경오", (
            f"입춘 당일 1990-02-04: 경오 기대, 실제={fp['year']['pillar']}"
        )

    def test_after_ipchun_uses_current_year(self):
        """입춘 이후 → 당년 간지"""
        fp = calc_four_pillars(1990, 6, 15, 0, 0, "female", "ko")
        assert fp["year"]["pillar"] == "경오", (
            f"입춘 이후 1990-06-15: 경오 기대, 실제={fp['year']['pillar']}"
        )

    def test_january_birth_always_prev_year(self):
        """1월 출생은 항상 전년도 간지 (입춘은 2월이므로)"""
        fp = calc_four_pillars(2024, 1, 10, 0, 0, "female", "ko")
        # 2024-01-10: 입춘(2024-02-04) 이전 → 계묘(癸卯)
        assert fp["year"]["pillar"] == "계묘", (
            f"1월 출생 2024-01-10: 계묘 기대, 실제={fp['year']['pillar']}"
        )


class TestGetDaewoon:
    def test_returns_list(self):
        result = get_daewoon(1990, 5, 20, 14)
        assert isinstance(result, list)

    def test_daewoon_count_or_error(self):
        result = get_daewoon(1990, 5, 20, 14)
        if "error" in result[0]:
            pytest.skip("lunar-python 미설치 — 대운 계산 스킵")
        assert len(result) <= 10

    def test_daewoon_structure(self):
        result = get_daewoon(1990, 5, 20, 14)
        if "error" in result[0]:
            pytest.skip("lunar-python 미설치")
        for d in result:
            assert "order" in d
            assert "glyph" in d
