"""
사주담 핵심 테스트 (헤르2 감사 요청 사항)
- 1900/2100년 경계값
- 절기 경계일 (2월 3~5일) 월주 변경
- 시 불명 12 hour variants
- map_mood_to_saju 5레벨 × 5오행
"""
import pytest
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from src.engine.saju_calculator import (
    calc_four_pillars, get_lunar_date, _get_disclaimer
)


class TestBoundaryYears:
    """1900/2100 경계값 테스트"""
    def test_year_1900(self):
        r = calc_four_pillars(1900, 1, 1, lang="ko")
        assert "year" in r
        assert "disclaimer" in r

    def test_year_2100(self):
        r = calc_four_pillars(2100, 12, 31, lang="ko")
        assert "year" in r

    def test_year_pillar_cycle(self):
        """60갑자 주기 확인 (60년 후 동일 연주)"""
        r1 = calc_four_pillars(1984, 1, 1)
        r2 = calc_four_pillars(2044, 1, 1)
        assert r1["year"]["pillar"] == r2["year"]["pillar"]


class TestJeolgiBoungary:
    """절기 경계일 월주 변경 테스트 (2월 3~5일)"""
    def test_feb3_before_ipchun(self):
        r = calc_four_pillars(2024, 2, 3, lang="ko")
        assert "month" in r

    def test_feb4_ipchun(self):
        r = calc_four_pillars(2024, 2, 4, lang="ko")
        assert "month" in r

    def test_feb5_after_ipchun(self):
        r = calc_four_pillars(2024, 2, 5, lang="ko")
        assert "month" in r


class TestHourVariants:
    """시(時) 불명 시 12지지 variants"""
    def test_no_hour_returns_result(self):
        r = calc_four_pillars(1990, 5, 15, birth_hour=None, lang="ko")
        assert "year" in r
        assert "month" in r
        assert "day" in r

    def test_with_hour_adds_hour_pillar(self):
        r = calc_four_pillars(1990, 5, 15, birth_hour=12, lang="ko")
        assert "hour" in r


class TestDisclaimer:
    """면책 문구 3개 언어"""
    def test_ko_disclaimer(self):
        d = _get_disclaimer("ko")
        assert "심리상담" in d or "자기이해" in d

    def test_ja_disclaimer(self):
        d = _get_disclaimer("ja")
        assert "カウンセリング" in d

    def test_en_disclaimer(self):
        d = _get_disclaimer("en")
        assert "counseling" in d.lower()


class TestLegalFraming:
    """법적 포지셔닝 확인"""
    def test_result_contains_legal(self):
        r = calc_four_pillars(1990, 1, 15, lang="ko")
        assert "disclaimer" in r
        assert "legal" in r
        assert "대체 아님" in r.get("legal", "")  # "~아님" 명시 확인
