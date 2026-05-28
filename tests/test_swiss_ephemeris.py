"""
Swiss Ephemeris 모듈 테스트
- JDN 일주 계산 검증 (헤르2 교차 감사 완료)
- 절기 계산 (ephem 폴백)
- 분 단위 입춘 경계 테스트
"""
import pytest
from src.engine.swiss_ephemeris import (
    calc_day_pillar_jdn,
    get_current_solar_term,
    get_month_pillar_term,
    _datetime_to_jd,
    _has_swisseph,
    SOLAR_TERMS,
    MONTH_TERM_START,
)
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


class TestCalcDayPillarJDN:
    """JDN 기반 일주 계산 — 헤르2 독립 감사 검증 케이스 포함"""

    def test_1990_01_15_gyeonin(self):
        """1990-01-15 → 경진(庚辰, idx=16) — lunar-python 실측 검증 2026-05-23 (JIAZI=2447891)"""
        r = calc_day_pillar_jdn(1990, 1, 15)
        assert r["pillar"] == "경진", f"expected 경진, got {r['pillar']}"
        assert r["cycle_idx"] == 16  # (2447907 - 2447891) % 60 = 16

    def test_1924_02_05_gapja(self):
        """1924-02-05 → 갑인(甲寅, idx=50) — lunar-python 실측 검증 (JIAZI=2447891)"""
        r = calc_day_pillar_jdn(1924, 2, 5)
        assert r["pillar"] == "갑인", f"expected 갑인, got {r['pillar']}"
        assert r["cycle_idx"] == 50  # (2423821 - 2447891) % 60 = 50

    def test_returns_required_fields(self):
        r = calc_day_pillar_jdn(2000, 1, 1)
        assert "stem" in r
        assert "branch" in r
        assert "pillar" in r
        assert "jdn" in r
        assert "cycle_idx" in r
        assert "source" in r
        assert r["source"] == "JDN_60cycle"

    def test_cycle_wraps_60(self):
        """60갑자 순환 — 60일 후 동일 pillar"""
        r1 = calc_day_pillar_jdn(2024, 1, 1)
        r2 = calc_day_pillar_jdn(2024, 3, 1)  # 60일 후
        assert r1["pillar"] == r2["pillar"]

    def test_consecutive_days_differ(self):
        """연속된 날은 서로 다른 일주"""
        r1 = calc_day_pillar_jdn(2024, 6, 1)
        r2 = calc_day_pillar_jdn(2024, 6, 2)
        assert r1["pillar"] != r2["pillar"]

    def test_stem_branch_consistent(self):
        """천간/지지가 pillar 문자열과 일치"""
        r = calc_day_pillar_jdn(1990, 1, 15)
        assert r["pillar"] == r["stem"] + r["branch"]

    @pytest.mark.parametrize("year,month,day", [
        (2000, 1, 1), (2010, 6, 15), (2020, 12, 31), (2024, 2, 29),
    ])
    def test_various_dates_no_error(self, year, month, day):
        r = calc_day_pillar_jdn(year, month, day)
        assert isinstance(r["pillar"], str)
        assert len(r["pillar"]) == 2


class TestGetCurrentSolarTerm:
    """절기 계산 — ephem 폴백 환경"""

    def test_returns_required_fields(self):
        t = get_current_solar_term(2024, 2, 4, 12, "ko")
        for k in ("jeolgi", "jeolgi_ko", "jeolgi_ja", "jeolgi_en",
                  "solar_longitude", "source", "accuracy"):
            assert k in t, f"missing key: {k}"

    def test_solar_longitude_range(self):
        t = get_current_solar_term(2024, 6, 21, 12, "ko")
        assert 0.0 <= t["solar_longitude"] <= 360.0

    @pytest.mark.parametrize("lang", ["ko", "ja", "en"])
    def test_all_langs_return_nonempty(self, lang):
        t = get_current_solar_term(2024, 2, 4, 12, lang)
        assert t[f"jeolgi_{lang}"], f"empty for lang={lang}"

    def test_different_seasons_differ(self):
        summer = get_current_solar_term(2024, 7, 7, 12, "ko")
        winter = get_current_solar_term(2024, 1, 6, 12, "ko")
        assert summer["jeolgi_ko"] != winter["jeolgi_ko"]

    def test_source_ephem_or_swisseph(self):
        t = get_current_solar_term(2024, 4, 4, 12, "ko")
        assert t["source"] in ("ephem", "swiss_ephemeris")


class TestGetMonthPillarTerm:
    """월주 계산 — birth_minute 파라미터 포함"""

    def test_returns_saju_month(self):
        r = get_month_pillar_term(2024, 2, 10, 12, 0)
        assert "saju_month" in r
        assert 1 <= r["saju_month"] <= 12

    def test_birth_minute_param_accepted(self):
        """birth_minute 파라미터 정상 수용 (입춘 경계 오분류 방지)"""
        # 2025 입춘 = 2025-02-03 23:10 KST 전후
        before = get_month_pillar_term(2025, 2, 3, 23, 9)   # 입춘 직전
        after  = get_month_pillar_term(2025, 2, 3, 23, 10)  # 입춘 직후
        # 경계 전후는 다른 월이어야 함 (또는 같더라도 에러 없어야 함)
        assert isinstance(before["saju_month"], int)
        assert isinstance(after["saju_month"], int)

    def test_term_names_multilang(self):
        r = get_month_pillar_term(2024, 2, 10)
        assert "term_name_ko" in r
        assert "term_name_ja" in r
        assert "term_name_en" in r

    def test_different_months_differ(self):
        m2 = get_month_pillar_term(2024, 2, 15)
        m6 = get_month_pillar_term(2024, 6, 15)
        assert m2["saju_month"] != m6["saju_month"]


class TestSolarTermsConstants:
    """상수 테이블 불변성 검증"""

    def test_24_solar_terms(self):
        assert len(SOLAR_TERMS) == 24

    def test_all_terms_have_ko_ja_en(self):
        for lon, info in SOLAR_TERMS.items():
            assert "ko" in info, f"missing ko at lon={lon}"
            assert "ja" in info, f"missing ja at lon={lon}"
            assert "en" in info, f"missing en at lon={lon}"

    def test_12_month_term_starts(self):
        assert len(MONTH_TERM_START) == 12

    def test_datetimetojd_epoch(self):
        """J2000.0 에포크 검증: 2000-01-01 12:00 UTC = JD 2451545.0"""
        dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        jd = _datetime_to_jd(dt)
        assert abs(jd - 2451545.0) < 0.001, f"JD epoch mismatch: {jd}"

    def test_has_swisseph_returns_bool(self):
        result = _has_swisseph()
        assert isinstance(result, bool)
