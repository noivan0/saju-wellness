"""
[P3] 진태양시(眞太陽時) 보정 모듈 테스트
"""
import math
import pytest
from datetime import datetime, timezone, timedelta

from src.engine.true_solar_time import (
    correct_true_solar_time,
    get_city_suggestions,
    CITY_LONGITUDES,
    REFERENCE_LONGITUDE,
    MINUTES_PER_DEGREE,
    _equation_of_time_minutes,
)

KST = timezone(timedelta(hours=9))


# ---------------------------------------------------------------------------
# 균시차 테스트
# ---------------------------------------------------------------------------

class TestEquationOfTime:
    def test_returns_float(self):
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        eot = _equation_of_time_minutes(dt)
        assert isinstance(eot, float)

    def test_range_reasonable(self):
        """균시차는 일반적으로 -17분 ~ +17분 범위."""
        for month in range(1, 13):
            dt = datetime(2024, month, 15, 12, 0, tzinfo=KST)
            eot = _equation_of_time_minutes(dt)
            assert -20.0 <= eot <= 20.0, f"월 {month}: 균시차 {eot:.2f} 범위 초과"


# ---------------------------------------------------------------------------
# 경도 보정 핵심 로직
# ---------------------------------------------------------------------------

class TestLongitudeCorrection:
    def test_seoul_correction_negative(self):
        """서울(126.9778°) < 기준(135°) → 보정 음수 (더 느림)."""
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="seoul", apply_eot=False)
        assert result.longitude_correction_min < 0

    def test_tokyo_correction_positive(self):
        """도쿄(139.6917°) > 기준(135°) → 보정 양수 (더 빠름)."""
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="tokyo", apply_eot=False)
        assert result.longitude_correction_min > 0

    def test_osaka_near_zero(self):
        """오사카(135.5023°) ≒ 기준(135°) → 보정 거의 0."""
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="osaka", apply_eot=False)
        assert abs(result.longitude_correction_min) < 5.0

    def test_seoul_correction_magnitude(self):
        """서울 경도 보정값 근사 검증: (126.9778 - 135) × 4 ≈ -32.1분."""
        dt = datetime(2024, 1, 1, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="seoul", apply_eot=False)
        expected = (126.9778 - 135.0) * 4.0
        assert abs(result.longitude_correction_min - expected) < 0.1

    def test_explicit_longitude(self):
        """city_key 없이 longitude 직접 제공."""
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, longitude=127.0, apply_eot=False)
        assert result.longitude == 127.0
        assert result.city_name is None


# ---------------------------------------------------------------------------
# 결과 구조 검증
# ---------------------------------------------------------------------------

class TestTrueSolarTimeResult:
    def test_result_fields_complete(self):
        dt = datetime(2024, 6, 21, 12, 30, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="seoul")
        assert hasattr(result, "original_datetime")
        assert hasattr(result, "corrected_datetime")
        assert hasattr(result, "longitude_correction_min")
        assert hasattr(result, "eot_correction_min")
        assert hasattr(result, "total_correction_min")
        assert hasattr(result, "corrected_hour")
        assert hasattr(result, "corrected_minute")
        assert hasattr(result, "hour_branch_idx")
        assert hasattr(result, "note")

    def test_total_correction_equals_sum(self):
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="seoul")
        expected_total = result.longitude_correction_min + result.eot_correction_min
        assert abs(result.total_correction_min - expected_total) < 0.01

    def test_corrected_datetime_consistent(self):
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="seoul")
        diff_min = (result.corrected_datetime - dt).total_seconds() / 60
        assert abs(diff_min - result.total_correction_min) < 0.01

    def test_hour_branch_idx_range(self):
        """시지 인덱스는 0~11 범위."""
        for h in range(24):
            dt = datetime(2024, 6, 21, h, 0, tzinfo=KST)
            result = correct_true_solar_time(dt, city_key="seoul")
            assert 0 <= result.hour_branch_idx <= 11

    def test_to_dict_serializable(self):
        import json
        dt = datetime(2024, 6, 21, 14, 30, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="tokyo")
        d = result.to_dict()
        # JSON 직렬화 가능해야 함
        json.dumps(d)
        assert "original" in d
        assert "corrected" in d
        assert "longitude" in d
        assert "note" in d

    def test_eot_disabled(self):
        """apply_eot=False 시 균시차 보정 0."""
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="seoul", apply_eot=False)
        assert result.eot_correction_min == 0.0


# ---------------------------------------------------------------------------
# 에러 처리
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_no_longitude_raises(self):
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        with pytest.raises(ValueError, match="longitude 또는 city_key"):
            correct_true_solar_time(dt)

    def test_invalid_city_key_raises(self):
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        with pytest.raises(ValueError, match="알 수 없는 도시 키"):
            correct_true_solar_time(dt, city_key="atlantis")

    def test_longitude_out_of_range_raises(self):
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        with pytest.raises(ValueError, match="경도 범위 초과"):
            correct_true_solar_time(dt, longitude=200.0)

    def test_negative_longitude_valid(self):
        """서쪽 경도 (음수) 처리 가능."""
        dt = datetime(2024, 6, 21, 12, 0, tzinfo=KST)
        result = correct_true_solar_time(dt, city_key="new_york")
        assert result.longitude < 0


# ---------------------------------------------------------------------------
# 도시 프리셋
# ---------------------------------------------------------------------------

class TestCitySuggestions:
    def test_get_city_suggestions_list(self):
        suggestions = get_city_suggestions()
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_city_suggestion_keys(self):
        for s in get_city_suggestions():
            assert "key" in s
            assert "name" in s
            assert "longitude" in s

    def test_seoul_in_suggestions(self):
        keys = [s["key"] for s in get_city_suggestions()]
        assert "seoul" in keys

    def test_tokyo_in_suggestions(self):
        keys = [s["key"] for s in get_city_suggestions()]
        assert "tokyo" in keys

    def test_all_longitudes_valid_range(self):
        for s in get_city_suggestions():
            assert -180.0 <= s["longitude"] <= 180.0
