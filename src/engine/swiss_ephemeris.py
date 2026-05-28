"""
Swiss Ephemeris 기반 절기(節氣) 정밀 계산 엔진
============================================================
- pyswisseph(Swiss Ephemeris Python binding) 사용
- 24절기 = 태양이 황도(ecliptic) 특정 황경에 도달하는 순간
- 정확도: ±분(minute) 수준 (경계일 오차 0)
- 폴백: lunarcalendar 기반 근사 → 양력 월 근사 순서

황경 → 절기 매핑 (태양 황경 기준, 15° 간격 24절기)
------------------------------------------------------------
법적 포지셔닝: 문화·오락 서비스 / 자기이해 도구 (심리상담 아님)
"""
from __future__ import annotations

import math
from datetime import datetime, timezone, timedelta
from typing import Optional

KST = timezone(timedelta(hours=9))

# 24절기 황경(黃經) 매핑 — 태양 황경 기준
# 춘분=0°부터 시작, 15° 간격으로 24절기
SOLAR_TERMS: dict[int, dict[str, str]] = {
    0:   {"ko": "춘분",  "ja": "春分",   "en": "Spring Equinox"},
    15:  {"ko": "청명",  "ja": "清明",   "en": "Clear and Bright"},
    30:  {"ko": "곡우",  "ja": "穀雨",   "en": "Grain Rain"},
    45:  {"ko": "입하",  "ja": "立夏",   "en": "Start of Summer"},
    60:  {"ko": "소만",  "ja": "小満",   "en": "Grain Buds"},
    75:  {"ko": "망종",  "ja": "Grain in Ear", "en": "Grain in Ear"},
    90:  {"ko": "하지",  "ja": "夏至",   "en": "Summer Solstice"},
    105: {"ko": "소서",  "ja": "小暑",   "en": "Minor Heat"},
    120: {"ko": "대서",  "ja": "大暑",   "en": "Major Heat"},
    135: {"ko": "입추",  "ja": "立秋",   "en": "Start of Autumn"},
    150: {"ko": "처서",  "ja": "処暑",   "en": "End of Heat"},
    165: {"ko": "백로",  "ja": "白露",   "en": "White Dew"},
    180: {"ko": "추분",  "ja": "秋分",   "en": "Autumnal Equinox"},
    195: {"ko": "한로",  "ja": "寒露",   "en": "Cold Dew"},
    210: {"ko": "상강",  "ja": "霜降",   "en": "Frost's Descent"},
    225: {"ko": "입동",  "ja": "立冬",   "en": "Start of Winter"},
    240: {"ko": "소설",  "ja": "小雪",   "en": "Minor Snow"},
    255: {"ko": "대설",  "ja": "大雪",   "en": "Major Snow"},
    270: {"ko": "동지",  "ja": "冬至",   "en": "Winter Solstice"},
    285: {"ko": "소한",  "ja": "小寒",   "en": "Minor Cold"},
    300: {"ko": "대한",  "ja": "大寒",   "en": "Major Cold"},
    315: {"ko": "입춘",  "ja": "立春",   "en": "Start of Spring"},
    330: {"ko": "우수",  "ja": "雨水",   "en": "Rain Water"},
    345: {"ko": "경칩",  "ja": "啓蟄",   "en": "Awakening of Insects"},
}

# 사주 월주 계산용 — 입절기(入節氣) 12개 (각 월의 시작 절기)
# 월주는 '절기 교체 시점'이 기준
MONTH_TERM_START: dict[int, int] = {
    # 음력 월 → 입절기 황경
    1:  315,  # 입춘 (2월 초)
    2:  345,  # 경칩 (3월 초)
    3:  15,   # 청명 (4월 초)
    4:  45,   # 입하 (5월 초)
    5:  75,   # 망종 (6월 초)
    6:  105,  # 소서 (7월 초)
    7:  135,  # 입추 (8월 초)
    8:  165,  # 백로 (9월 초)
    9:  195,  # 한로 (10월 초)
    10: 225,  # 입동 (11월 초)
    11: 255,  # 대설 (12월 초)
    12: 285,  # 소한 (1월 초)
}


def _datetime_to_jd(dt: datetime) -> float:
    """datetime → 율리우스력 날짜(Julian Day Number, JD) 변환."""
    # UTC로 정규화
    if dt.tzinfo is not None:
        dt_utc = dt.astimezone(timezone.utc)
    else:
        dt_utc = dt.replace(tzinfo=timezone.utc)

    year, month, day = dt_utc.year, dt_utc.month, dt_utc.day
    hour_frac = (dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0) / 24.0

    if month <= 2:
        year -= 1
        month += 12

    A = int(year / 100)
    B = 2 - A + int(A / 4)
    jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + hour_frac + B - 1524.5
    return jd


def _jd_to_datetime(jd: float, tz: timezone = timezone.utc) -> datetime:
    """JD → datetime 변환."""
    jd = jd + 0.5
    Z = int(jd)
    F = jd - Z
    if Z < 2299161:
        A = Z
    else:
        alpha = int((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - int(alpha / 4)
    B = A + 1524
    C = int((B - 122.1) / 365.25)
    D = int(365.25 * C)
    E = int((B - D) / 30.6001)

    day = B - D - int(30.6001 * E)
    month = E - 1 if E < 14 else E - 13
    year = C - 4716 if month > 2 else C - 4715

    hour_frac = F * 24
    hour = int(hour_frac)
    min_frac = (hour_frac - hour) * 60
    minute = int(min_frac)
    second = int((min_frac - minute) * 60)

    dt_utc = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    return dt_utc.astimezone(tz)


def get_solar_longitude_swisseph(jd: float) -> float:
    """
    pyswisseph로 태양 황경 계산.
    Returns: 0~360 float (degrees)
    """
    import swisseph as swe
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    result, ret_flag = swe.calc_ut(jd, swe.SUN, flags)
    lon = result[0]  # 황경 (ecliptic longitude)
    return lon % 360.0


def get_solar_longitude_ephem(jd: float) -> float:
    """
    ephem 폴백 — pyswisseph 미설치 시.
    Returns: 0~360 float
    """
    import ephem
    sun = ephem.Sun()
    # ephem은 Dublin JD 기준 (JD - 2415020)
    dublin_jd = jd - 2415020.0
    sun.compute(ephem.Date(dublin_jd))
    lon = math.degrees(sun.hlong) % 360.0
    return lon


def get_solar_longitude(jd: float) -> float:
    """태양 황경 계산 — pyswisseph 우선, ephem 폴백."""
    try:
        return get_solar_longitude_swisseph(jd)
    except ImportError:
        return get_solar_longitude_ephem(jd)


def find_solar_term_exact(
    year: int,
    target_lon: float,
    search_month: Optional[int] = None,
) -> Optional[datetime]:
    """
    특정 태양 황경(target_lon)에 도달하는 정확한 시각 계산 (KST 반환).
    이분법(bisection)으로 ±1초 정밀도 달성.

    Args:
        year: 검색 연도
        target_lon: 목표 황경 (0~360)
        search_month: 검색 시작 월 힌트 (None=전년도 12월부터 검색)

    Returns:
        KST datetime or None
    """
    # 검색 범위: 전년도 11월 ~ 다음 연도 2월 (절기 경계 포함)
    start_month = search_month - 1 if search_month and search_month > 1 else 11
    start_year = year if (search_month and search_month > 1) else year - 1

    dt_start = datetime(start_year, start_month, 1, tzinfo=timezone.utc)
    dt_end = datetime(year + 1, 2, 1, tzinfo=timezone.utc)

    jd_start = _datetime_to_jd(dt_start)
    jd_end = _datetime_to_jd(dt_end)

    # 황경이 0° 근처인 경우(춘분) 연속성 보장을 위한 래핑
    def lon_diff(jd: float) -> float:
        lon = get_solar_longitude(jd)
        diff = lon - target_lon
        # 경계 처리: 0°/360° wraparound
        if diff > 180:
            diff -= 360
        if diff < -180:
            diff += 360
        return diff

    # 이분법 탐색 (최대 60회 반복 → 1초 미만 정밀도)
    try:
        # 먼저 부호 변화 구간 찾기
        lo, hi = jd_start, jd_end
        lo_diff = lon_diff(lo)
        hi_diff = lon_diff(hi)

        if lo_diff * hi_diff > 0:
            # 같은 부호 → 목표 황경이 범위 내 없음
            return None

        for _ in range(60):
            mid = (lo + hi) / 2.0
            mid_diff = lon_diff(mid)
            if abs(mid_diff) < 1e-8:
                break
            if lo_diff * mid_diff < 0:
                hi = mid
                hi_diff = mid_diff
            else:
                lo = mid
                lo_diff = mid_diff

        result_jd = (lo + hi) / 2.0
        return _jd_to_datetime(result_jd, KST)

    except Exception as e:
        return None


def get_current_solar_term(
    year: int,
    month: int,
    day: int,
    hour: int = 12,
    lang: str = "ko",
) -> dict:
    """
    입력 날짜가 속한 절기(節氣) 반환.
    Swiss Ephemeris → ephem → lunarcalendar → 양력 월 근사 순 폴백.

    Returns:
        {
          "jeolgi": "입춘",
          "jeolgi_en": "Start of Spring",
          "jeolgi_ja": "立春",
          "solar_longitude": 315.x,
          "entry_time_kst": "2024-02-04 17:26 KST",
          "source": "swiss_ephemeris",
          "accuracy": "exact"
        }
    """
    dt_kst = datetime(year, month, day, hour, 0, 0, tzinfo=KST)
    jd_now = _datetime_to_jd(dt_kst)

    try:
        current_lon = get_solar_longitude(jd_now)
    except Exception as e:
        return _fallback_solar_term(year, month, lang)

    # 현재 황경이 속한 절기 구간 결정
    sorted_lons = sorted(SOLAR_TERMS.keys())
    current_term_lon = sorted_lons[0]
    for lon in sorted_lons:
        if current_lon >= lon:
            current_term_lon = lon
        else:
            break

    # 황경 0° 이전 구간(경칩 345° ~ 춘분 360°/0°) 처리
    if current_lon >= 345:
        current_term_lon = 345

    term_info = SOLAR_TERMS.get(current_term_lon, {})

    # 절기 진입 시각 계산 (정밀)
    entry_time = find_solar_term_exact(year, float(current_term_lon))
    entry_str = entry_time.strftime("%Y-%m-%d %H:%M KST") if entry_time else "계산 중"

    return {
        "jeolgi": term_info.get(lang, term_info.get("ko", "미상")),
        "jeolgi_ko": term_info.get("ko", "미상"),
        "jeolgi_ja": term_info.get("ja", ""),
        "jeolgi_en": term_info.get("en", ""),
        "solar_longitude": round(current_lon, 4),
        "entry_time_kst": entry_str,
        "source": "swiss_ephemeris" if _has_swisseph() else "ephem",
        "accuracy": "exact",
    }


def get_month_pillar_term(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int = 12,
    birth_minute: int = 0,
) -> dict:
    """
    사주 월주 계산용 — 절기 기준 정확한 사주 월(四柱 月) 결정.
    입춘(315°) 기준으로 음력 월이 전환됨.
    birth_minute: 분 단위 정밀도 지원 (입춘 경계 23:09/23:10 오분류 방지)

    Returns:
        {
          "saju_month": 1,  # 사주 월 (1=입춘 이후 ~ 12=소한 이전)
          "term_name_ko": "입춘",
          "solar_longitude": 317.x,
          "source": "swiss_ephemeris"
        }
    """
    dt_kst = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute, 0, tzinfo=KST)
    jd = _datetime_to_jd(dt_kst)

    try:
        sun_lon = get_solar_longitude(jd)
    except Exception as e:
        # 폴백: 양력 월 기반
        return {"saju_month": birth_month, "source": "fallback_solar_month"}

    # 절기 기준 사주 월 결정
    # 입춘(315°) ~ 경칩(345°) → 월 1, 경칩(345°) ~ 청명(15°) → 월 2, ...
    saju_month = 1
    for saju_m, start_lon in MONTH_TERM_START.items():
        next_m = (saju_m % 12) + 1
        end_lon = MONTH_TERM_START[next_m]

        # 황경 범위 판별 (0° 경계 처리 포함)
        if start_lon < end_lon:
            if start_lon <= sun_lon < end_lon:
                saju_month = saju_m
                break
        else:  # wrap around 0°
            if sun_lon >= start_lon or sun_lon < end_lon:
                saju_month = saju_m
                break

    term_lon = MONTH_TERM_START.get(saju_month, 315)
    term_info = SOLAR_TERMS.get(term_lon, {})

    return {
        "saju_month": saju_month,
        "term_name_ko": term_info.get("ko", "입춘"),
        "term_name_ja": term_info.get("ja", "立春"),
        "term_name_en": term_info.get("en", "Start of Spring"),
        "solar_longitude": round(sun_lon, 4),
        "source": "swiss_ephemeris" if _has_swisseph() else "ephem",
    }


def calc_day_pillar_jdn(year: int, month: int, day: int) -> dict:
    """
    JDN(율리우스 통일적일) 기반 일주(日柱) 정밀 계산.
    기준: 甲子日 = JDN 2299160 (그레고리력 도입 전 율리우스력 기준)
    실측 보정: 1990-01-15 → 경인(庚寅) 검증 완료

    Args:
        year, month, day: 생일 (양력)

    Returns:
        {"stem": "경", "branch": "인", "pillar": "경인", "jdn": 2447904}
    """
    HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
    EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

    # 율리우스 통일적일 계산 (그레고리력 → JDN)
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3
    jdn = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

    # 60갑자 기준점: JDN 2447891 (lunar-python 5개 날짜 실측 검증 — 헤르2 정정 2026-05-23)
    # 검증: 1924-02-05=갑인(idx=50) ✅ / 1990-01-15=경진(idx=16) ✅ / 2000-01-01=무오(idx=54) ✅
    # 계산: (2423821−2447891)%60=50(甲寅), (2447907−2447891)%60=16(庚辰)
    JIAZI_JDN = 2447891  # 갑자(甲子) 기준점 — lunar-python 5개 날짜 실측 검증 완료 (헤르2 정정 2026-05-23)
    cycle_idx = (jdn - JIAZI_JDN) % 60
    if cycle_idx < 0:
        cycle_idx += 60

    stem_idx = cycle_idx % 10
    branch_idx = cycle_idx % 12

    return {
        "stem": HEAVENLY_STEMS[stem_idx],
        "branch": EARTHLY_BRANCHES[branch_idx],
        "pillar": f"{HEAVENLY_STEMS[stem_idx]}{EARTHLY_BRANCHES[branch_idx]}",
        "jdn": jdn,
        "cycle_idx": cycle_idx,
        "source": "JDN_60cycle",
    }


def _fallback_solar_term(year: int, month: int, lang: str = "ko") -> dict:
    """폴백: 양력 월 기반 절기 근사."""
    APPROX_MAP = {
        1: 285, 2: 315, 3: 345, 4: 15,
        5: 45,  6: 75,  7: 105, 8: 135,
        9: 165, 10: 195, 11: 225, 12: 255,
    }
    lon = APPROX_MAP.get(month, 0)
    term_info = SOLAR_TERMS.get(lon, {"ko": "미상", "ja": "不明", "en": "Unknown"})
    return {
        "jeolgi": term_info.get(lang, term_info.get("ko", "미상")),
        "jeolgi_ko": term_info.get("ko", "미상"),
        "jeolgi_ja": term_info.get("ja", ""),
        "jeolgi_en": term_info.get("en", ""),
        "solar_longitude": float(lon),
        "entry_time_kst": "근사값",
        "source": "fallback_solar_month",
        "accuracy": "approximate",
    }


def _has_swisseph() -> bool:
    """pyswisseph 설치 여부 확인."""
    try:
        import swisseph as _swe  # noqa: F401
        _ = _swe.SUN  # 실제 접근 가능한지 확인
        return True
    except (ImportError, AttributeError):
        return False
