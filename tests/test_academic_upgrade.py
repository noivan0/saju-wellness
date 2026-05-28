"""
사주담 학술 강화 모듈 테스트 (v1.1)
헤르2 리서치 기반 핵심 검증 케이스
"""
import pytest
import sys
import os
# conftest.py가 PROJECT_ROOT를 sys.path에 추가하므로 src. prefix 사용
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from engine.academic_upgrade import (
    calc_day_pillar_accurate,
    calc_year_pillar_accurate,
    calc_daewoon,
    calc_ohaeng_strength,
    calc_gyeokguk,
    get_ohaeng_relation,
    get_academic_disclaimer,
    JIJANGGAN,
)


class TestJDNDayPillar:
    """JDN 기반 일주 정확도 테스트"""

    def test_known_date_1990_01_15(self):
        """1990-01-15 일주 계산"""
        result = calc_day_pillar_accurate(1990, 1, 15)
        assert "stem" in result
        assert "branch" in result
        assert result["confidence_level"] == "high"
        assert "JDN" in result["source"]

    def test_different_months_give_different_pillars(self):
        """같은 연도 다른 월 → 다른 일주 (기존 버그 해소)"""
        jan = calc_day_pillar_accurate(1990, 1, 15)
        jun = calc_day_pillar_accurate(1990, 6, 15)
        # 핵심: 기존 수식은 월을 무시해서 같은 값 → JDN 방식은 달라야 함
        assert jan["gapja_index"] != jun["gapja_index"], \
            "월이 다르면 일주가 달라야 합니다 (JDN 기반)"

    def test_consecutive_days_advance_by_one(self):
        """연속된 날짜는 갑자 인덱스가 1씩 증가"""
        d1 = calc_day_pillar_accurate(2024, 1, 1)
        d2 = calc_day_pillar_accurate(2024, 1, 2)
        assert (d2["gapja_index"] - d1["gapja_index"]) % 60 == 1

    def test_60_cycle_wraps(self):
        """60일 후 같은 간지"""
        from datetime import date, timedelta
        base = date(2024, 1, 1)
        later = base + timedelta(days=60)
        d1 = calc_day_pillar_accurate(2024, 1, 1)
        d2 = calc_day_pillar_accurate(later.year, later.month, later.day)
        assert d1["pillar"] == d2["pillar"]


class TestYearPillarIpchun:
    """입춘 기준 연주 테스트 — 헤르2 리서치 핵심 버그"""

    def test_before_ipchun_uses_previous_year(self):
        """입춘 이전 출생 → 전년도 간지"""
        # 2024년 입춘: 2월 4일
        result = calc_year_pillar_accurate(2024, 2, 3)  # 입춘 하루 전
        assert result["is_before_ipchun"] is True
        assert result["effective_year"] == 2023

    def test_on_ipchun_uses_current_year(self):
        """입춘 당일 출생 → 당년 간지"""
        result = calc_year_pillar_accurate(2024, 2, 4)
        assert result["is_before_ipchun"] is False
        assert result["effective_year"] == 2024

    def test_after_ipchun_uses_current_year(self):
        """입춘 이후 출생 → 당년 간지"""
        result = calc_year_pillar_accurate(2024, 3, 1)
        assert result["is_before_ipchun"] is False
        assert result["effective_year"] == 2024

    def test_jan_birth_uses_previous_year(self):
        """1월 출생은 항상 전년도 간지 (입춘 전)"""
        result = calc_year_pillar_accurate(2024, 1, 15)
        assert result["effective_year"] == 2023

    def test_confidence_level(self):
        result = calc_year_pillar_accurate(2024, 6, 15)
        assert result["confidence_level"] == "high"


class TestDaewoon:
    """대운 계산 테스트"""

    def test_forward_daewoon_male_yang_year(self):
        """양남(陽男) → 순행 대운"""
        result = calc_daewoon(1984, 1, 15, gender="male", year_stem="갑")
        assert result["direction"] == "순행"
        assert len(result["daewoons"]) == 10

    def test_reverse_daewoon_male_yin_year(self):
        """음남(陰男) → 역행 대운"""
        result = calc_daewoon(1985, 1, 15, gender="male", year_stem="을")
        assert result["direction"] == "역행"

    def test_daewoon_10_entries(self):
        """대운 10개 연속 계산"""
        result = calc_daewoon(1990, 5, 20, gender="female")
        assert len(result["daewoons"]) == 10

    def test_daewoon_ages_sequential(self):
        """대운 시작 나이 순서 확인"""
        result = calc_daewoon(1990, 5, 20, gender="female")
        daewoons = result["daewoons"]
        for i in range(9):
            assert daewoons[i+1]["start_age"] == daewoons[i]["end_age"] + 1


class TestJijanggan:
    """지장간 테이블 테스트"""

    def test_all_12_branches_exist(self):
        branches = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
        for b in branches:
            assert b in JIJANGGAN, f"{b} 지장간 없음"

    def test_ratios_sum_to_1(self):
        for branch, jjg_list in JIJANGGAN.items():
            total = sum(jg["ratio"] for jg in jjg_list)
            assert abs(total - 1.0) < 0.01, f"{branch} 지장간 비율 합계 오류: {total}"

    def test_ju_exists_in_all(self):
        """모든 지지에 주기(主氣)가 있어야 함"""
        for branch, jjg_list in JIJANGGAN.items():
            types = [jg["type"] for jg in jjg_list]
            assert "주기" in types, f"{branch}에 주기 없음"


class TestOhaengStrength:
    """오행 강도 계산 테스트"""

    def test_calc_returns_all_elements(self):
        result = calc_ohaeng_strength("갑", "인", "병", "오", "무", "진")
        assert set(result["strength"].keys()) == {"목", "화", "토", "금", "수"}

    def test_percentages_sum_to_100(self):
        result = calc_ohaeng_strength("갑", "인", "을", "묘", "갑", "인")
        total = sum(result["strength"].values())
        assert abs(total - 100.0) < 1.0

    def test_shingang_diagnosis(self):
        result = calc_ohaeng_strength("갑", "인", "병", "오", "무", "진")
        assert result["diagnosis"] in ("신강(身强)", "신약(身弱)")


class TestGyeokguk:
    """격국 판별 테스트"""

    def test_returns_gyeokguk_name(self):
        result = calc_gyeokguk("갑", "인")
        assert "격" in result["gyeokguk"]

    def test_all_stems_covered(self):
        stems = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
        branches = ["인", "묘", "사", "오", "신", "유"]
        for s in stems:
            for b in branches:
                result = calc_gyeokguk(s, b)
                assert result["gyeokguk"] is not None

    def test_disclaimer_present(self):
        result = calc_gyeokguk("갑", "자")
        assert "disclaimer" in result


class TestOhaengRelation:
    """상생상극 관계 테스트"""

    def test_sangsaeng_mok_hwa(self):
        """목 → 화 상생"""
        result = get_ohaeng_relation("목", "화")
        assert result["relation"] == "상생(相生)"
        assert result["beneficial"] is True

    def test_sanggeuk_mok_to(self):
        """목 → 토 상극"""
        result = get_ohaeng_relation("목", "토")
        assert result["relation"] == "상극(相克)"
        assert result["beneficial"] is False

    def test_bihwa_same_element(self):
        """동일 오행 → 비화"""
        result = get_ohaeng_relation("목", "목")
        assert result["relation"] == "비화(比和)"

    def test_all_sangsaeng_pairs(self):
        pairs = [("목", "화"), ("화", "토"), ("토", "금"), ("금", "수"), ("수", "목")]
        for a, b in pairs:
            result = get_ohaeng_relation(a, b)
            assert result["relation"] == "상생(相生)", f"{a}→{b} 상생 오류"

    def test_all_sanggeuk_pairs(self):
        pairs = [("목", "토"), ("토", "수"), ("수", "화"), ("화", "금"), ("금", "목")]
        for a, b in pairs:
            result = get_ohaeng_relation(a, b)
            assert result["relation"] == "상극(相克)", f"{a}→{b} 상극 오류"


class TestDisclaimers:
    """다국어 disclaimer 테스트"""

    def test_ko_disclaimer(self):
        d = get_academic_disclaimer("ko")
        assert "명리학" in d
        assert "자기이해" in d

    def test_ja_disclaimer(self):
        d = get_academic_disclaimer("ja")
        assert "命理" in d or "四柱" in d

    def test_en_disclaimer(self):
        d = get_academic_disclaimer("en")
        assert "Four Pillars" in d or "Saju" in d

    def test_fallback_to_ko(self):
        d = get_academic_disclaimer("zh")  # 미지원 언어
        assert len(d) > 0
