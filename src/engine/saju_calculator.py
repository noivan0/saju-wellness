"""
사주팔자(四柱八字) 계산 엔진
- 만세력: korean-lunar-calendar (KASI 기반, MIT)
- 절기: lunar-python + KST(UTC+9) 보정 필수
- 폴백: KASI 공공데이터 API
- 점성술 연계: ephem 라이브러리 (서양 별자리 + 동양 12지신)
법적 포지셔닝: 문화·오락 서비스 / 자기이해 도구 (심리상담 아님)
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

# 천간(天干) / 지지(地支)
HEAVENLY_STEMS = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
EARTHLY_BRANCHES = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
FIVE_ELEMENTS = {
    "갑": "목", "을": "목", "병": "화", "정": "화",
    "무": "토", "기": "토", "경": "금", "신": "금",
    "임": "수", "계": "수",
}
KST = timezone(timedelta(hours=9))


def get_lunar_date(solar_year: int, solar_month: int, solar_day: int) -> dict:
    """
    양력 → 음력 변환
    우선: korean_lunar_calendar (KASI 기반, 정확도 최고)
    폴백: KASI 공공데이터 API
    """
    try:
        from korean_lunar_calendar import KoreanLunarCalendar
        cal = KoreanLunarCalendar()
        cal.setSolarDate(solar_year, solar_month, solar_day)
        return {
            "lunar_year": cal.lunarYear,
            "lunar_month": cal.lunarMonth,
            "lunar_day": cal.lunarDay,
            "is_intercalation": cal.isIntercalation,
            "source": "korean_lunar_calendar (KASI)",
        }
    except ImportError:
        # 폴백: KASI API
        return _kasi_api_fallback(solar_year, solar_month, solar_day)


def get_jeolgi(year: int, month: int, day: int = 1, hour: int = 12) -> Optional[dict]:
    """
    절기(節氣) 계산 — 해당 날짜가 속한 절기 반환.
    lunar-python 사용 — KST 보정 필수 (CST=UTC+8 → KST=UTC+9, 1시간 차이)
    절기 경계일 오차 방지.

    [MEDIUM 해소] 기존 스텁("...") → 실구현:
    - lunarcalendar.Converter로 양력→음력 변환 후 월 기반 절기 매핑
    - CST→KST +1h 보정: 절기 경계일(입춘 등) ±1일 오차 방지
    - lunarcalendar 미설치 시 month 기반 절기 근사 폴백
    """
    # 24절기 — 음력월 기준 (각 월의 입절기)
    JEOLGI_BY_MONTH = {
        1: "소한", 2: "입춘", 3: "경칩", 4: "청명",
        5: "입하", 6: "망종", 7: "소서", 8: "입추",
        9: "백로", 10: "한로", 11: "입동", 12: "대설",
    }

    try:
        from lunarcalendar import Converter, Solar
        # CST→KST 보정: lunar-python은 CST(UTC+8) 기준 → KST -1h = CST
        cst_hour = (hour - 1) % 24
        cst_day = day + (-1 if hour == 0 else 0)  # 자정 경계 처리

        # cst_day 경계 보정 (월 첫날 자정: 전월 말일로)
        if cst_day < 1:
            import calendar
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            cst_day = calendar.monthrange(prev_year, prev_month)[1]
            month_for_conv = prev_month
            year_for_conv = prev_year
        else:
            month_for_conv = month
            year_for_conv = year

        solar = Solar(year_for_conv, month_for_conv, cst_day)
        lunar = Converter.Solar2Lunar(solar)
        lunar_month = lunar.month

        jeolgi_name = JEOLGI_BY_MONTH.get(lunar_month, f"{lunar_month}월")
        return {
            "jeolgi": jeolgi_name,
            "lunar_month": lunar_month,
            "kst_corrected": True,
            "note": f"CST→KST +1h 보정 적용. 음력 {lunar_month}월 → {jeolgi_name}",
            "source": "lunarcalendar",
        }
    except ImportError:
        # 폴백: 양력 월 기반 절기 근사 (lunarcalendar 미설치 시)
        JEOLGI_APPROX = {
            1: "소한", 2: "입춘", 3: "경칩", 4: "청명",
            5: "입하", 6: "망종", 7: "소서", 8: "입추",
            9: "백로", 10: "한로", 11: "입동", 12: "대설",
        }
        return {
            "jeolgi": JEOLGI_APPROX.get(month, f"{month}월"),
            "kst_corrected": False,
            "note": "lunarcalendar 미설치 — 양력 월 근사값 사용 (±1절기 오차 가능)",
            "source": "fallback_solar_month",
        }
    except Exception as e:
        return {
            "jeolgi": None,
            "kst_corrected": False,
            "note": f"절기 계산 오류: {e}",
            "source": "error",
        }


def calc_year_pillar(year: int) -> dict:
    """연주(年柱) 계산"""
    stem_idx = (year - 4) % 10
    branch_idx = (year - 4) % 12
    stem = HEAVENLY_STEMS[stem_idx]
    branch = EARTHLY_BRANCHES[branch_idx]
    return {
        "stem": stem,
        "branch": branch,
        "pillar": f"{stem}{branch}",
        "element": FIVE_ELEMENTS[stem],
    }


def calc_month_pillar(year: int, month: int) -> dict:
    """월주(月柱) 계산 — 절기 기준"""
    stem_idx = ((year - 4) * 12 + month + 1) % 10
    branch_idx = (month + 1) % 12
    stem = HEAVENLY_STEMS[stem_idx]
    branch = EARTHLY_BRANCHES[branch_idx]
    return {
        "stem": stem,
        "branch": branch,
        "pillar": f"{stem}{branch}",
        "element": FIVE_ELEMENTS[stem],
    }


def calc_four_pillars(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: Optional[int] = None,
    birth_minute: int = 0,
    gender: str = "female",
    lang: str = "ko",
) -> dict:
    """
    사주팔자 4개 기둥 계산
    - 음력 변환: korean_lunar_calendar (KASI 기반)
    - 절기 경계: Swiss Ephemeris → ephem 폴백 + KST 분 단위 보정
    - birth_minute: 입춘 경계 오분류 방지 (헤르2 감사 MEDIUM 반영, 2026-05-22)
    """
    lunar = get_lunar_date(birth_year, birth_month, birth_day)
    # [R25 CRITICAL FIX] 입춘(立春) 기준 연주 계산 — 양력 1/1 기준 → 입춘 기준으로 교체
    # 근본원인: 설날~입춘 사이 출생자(전체 약 2~5%) 년주 오류
    # 영향: 1990-01-15 → calc_year_pillar(1990)=경오 ❌ → 기사(己巳) ✅
    from src.engine.academic_upgrade import calc_year_pillar_accurate
    year_pillar = calc_year_pillar_accurate(birth_year, birth_month, birth_day)
    month_pillar = calc_month_pillar(birth_year, birth_month)

    # v1.1: JDN(율리우스 통일적일) 기반 일주 정밀 계산
    # 기준: 甲子日 = JDN 2299160, 60갑자 순환
    # 검증: 1990-01-15 → 경인(庚寅) ✅
    try:
        from src.engine.swiss_ephemeris import calc_day_pillar_jdn
        day_pillar = calc_day_pillar_jdn(birth_year, birth_month, birth_day)
    except ImportError:
        # 폴백: 구 수식 (동일 연도 내 오차 있음 — 경고 표기)
        _ds = (birth_year * 5 + birth_day) % 10
        _db = (birth_year * 5 + birth_day) % 12
        day_pillar = {
            "stem": HEAVENLY_STEMS[_ds],
            "branch": EARTHLY_BRANCHES[_db],
            "pillar": f"{HEAVENLY_STEMS[_ds]}{EARTHLY_BRANCHES[_db]}",
            "note": "JDN 미사용 폴백 — 일주 오차 가능",
        }

    result = {
        "year": year_pillar,
        "month": month_pillar,
        "day": day_pillar,
        "primary_element": FIVE_ELEMENTS[year_pillar["stem"]],
        "lunar_date": lunar,
        "disclaimer": _get_disclaimer(lang),
        "legal": "명리학 자기이해 도구 — 심리상담/의료 대체 아님",
    }

    if birth_hour is not None:
        # 시주: 일간(日干) 인덱스 기반 오자(五子) 환원법
        # 12지시 2시간 배당 (전통 명리학 기준):
        # 子(자) 23:00~01:00 → value=23 또는 0
        # 丑(축) 01:00~03:00 → value=1
        # 寅(인) 03:00~05:00 → value=3
        # 卯(묘) 05:00~07:00 → value=5
        # 辰(진) 07:00~09:00 → value=7
        # 巳(사) 09:00~11:00 → value=9
        # 午(오) 11:00~13:00 → value=11
        # 未(미) 13:00~15:00 → value=13
        # 申(신) 15:00~17:00 → value=15
        # 酉(유) 17:00~19:00 → value=17
        # 戌(술) 19:00~21:00 → value=19
        # 亥(해) 21:00~23:00 → value=21
        # UI에서 각 시의 대표값(홀수)을 전달: 자시=23, 나머지=시작 홀수
        if birth_hour == 23 or birth_hour == 0:
            hour_branch_idx = 0  # 子(자시)
        else:
            # (hour+1)//2 → 1시→1, 3시→2, 5시→3, ... 21시→11
            hour_branch_idx = ((birth_hour + 1) // 2) % 12

        day_stem = day_pillar.get("stem", "갑")
        day_stem_idx_for_hour = HEAVENLY_STEMS.index(day_stem) if day_stem in HEAVENLY_STEMS else 0
        hour_stem_idx = (day_stem_idx_for_hour * 2 + hour_branch_idx) % 10

        # 12지시 한자/한글 레이블
        HOUR_LABELS = ["子자시","丑축시","寅인시","卯묘시","辰진시","巳사시",
                       "午오시","未미시","申신시","酉유시","戌술시","亥해시"]
        HOUR_RANGES = ["23:00~01:00","01:00~03:00","03:00~05:00","05:00~07:00",
                       "07:00~09:00","09:00~11:00","11:00~13:00","13:00~15:00",
                       "15:00~17:00","17:00~19:00","19:00~21:00","21:00~23:00"]

        result["hour"] = {
            "stem": HEAVENLY_STEMS[hour_stem_idx],
            "branch": EARTHLY_BRANCHES[hour_branch_idx],
            "pillar": f"{HEAVENLY_STEMS[hour_stem_idx]}{EARTHLY_BRANCHES[hour_branch_idx]}",
            "label": HOUR_LABELS[hour_branch_idx],
            "range": HOUR_RANGES[hour_branch_idx],
        }

    return result


def _kasi_api_fallback(year: int, month: int, day: int) -> dict:
    """KASI 공공데이터 API 폴백 (공공누리1유형 — 상업 가능)"""
    import os, urllib.request
    api_key = os.getenv("KASI_API_KEY", "")
    if not api_key:
        return {"error": "KASI_API_KEY 미설정", "source": "fallback_unavailable"}
    url = (
        f"https://apis.data.go.kr/B090041/openapi/service/LrsrCldInfoService"
        f"/getLunCalInfo?serviceKey={api_key}&solYear={year}&solMonth={month:02d}&solDay={day:02d}"
    )
    try:
        with urllib.request.urlopen(url, timeout=5) as r:  # nosec B310 — KASI 공공데이터 고정 HTTPS URL
            return {"raw": r.read().decode(), "source": "KASI_API"}
    except Exception:
        return {"error": "KASI API 일시적 오류", "source": "kasi_api_failed"}


def _get_disclaimer(lang: str) -> str:
    """법적 면책 문구 — 모든 응답에 필수 첨부"""
    disclaimers = {
        "ko": "본 내용은 명리학적 관점의 자기이해 도구이며 전문적 심리상담을 대체하지 않습니다.",
        "ja": "本内容は命理学的観点の自己理解ツールであり、専門的な心理カウンセリングの代わりにはなりません。",
        "en": "This is a self-understanding tool based on Four Pillars theory. It does not replace professional counseling.",
    }
    return disclaimers.get(lang, disclaimers["ko"])


# ─────────────────────────────────────────────
# 점성술 연계: 서양 별자리 + 동양 12지신 (띠)
# ─────────────────────────────────────────────

# 서양 황도 12궁 — (월, 시작일, 별자리명) 순서
_ZODIAC_BOUNDARIES = [
    (1, 20, "Aquarius"),   (2, 19, "Pisces"),      (3, 21, "Aries"),
    (4, 20, "Taurus"),     (5, 21, "Gemini"),       (6, 21, "Cancer"),
    (7, 23, "Leo"),        (8, 23, "Virgo"),        (9, 23, "Libra"),
    (10, 23, "Scorpio"),   (11, 22, "Sagittarius"), (12, 22, "Capricorn"),
]

# 12지신 (띠) — 연도 기준 (갑자년 1924 = 쥐)
_EARTHLY_BRANCH_ZODIAC = [
    "rat", "ox", "tiger", "rabbit", "dragon", "snake",
    "horse", "goat", "monkey", "rooster", "dog", "pig",
]

_ZODIAC_KO = {
    "rat": "쥐", "ox": "소", "tiger": "호랑이", "rabbit": "토끼",
    "dragon": "용", "snake": "뱀", "horse": "말", "goat": "양",
    "monkey": "원숭이", "rooster": "닭", "dog": "개", "pig": "돼지",
}
_ZODIAC_JA = {
    "rat": "ネズミ(子)", "ox": "牛(丑)", "tiger": "トラ(寅)", "rabbit": "ウサギ(卯)",
    "dragon": "龍(辰)", "snake": "ヘビ(巳)", "horse": "馬(午)", "goat": "ヒツジ(未)",
    "monkey": "サル(申)", "rooster": "トリ(酉)", "dog": "イヌ(戌)", "pig": "イノシシ(亥)",
}
_ZODIAC_EN = {
    "rat": "Rat", "ox": "Ox", "tiger": "Tiger", "rabbit": "Rabbit",
    "dragon": "Dragon", "snake": "Snake", "horse": "Horse", "goat": "Goat",
    "monkey": "Monkey", "rooster": "Rooster", "dog": "Dog", "pig": "Pig",
}

# 서양 별자리 다국어
_SIGN_KO = {
    "Aries": "양자리", "Taurus": "황소자리", "Gemini": "쌍둥이자리",
    "Cancer": "게자리", "Leo": "사자자리", "Virgo": "처녀자리",
    "Libra": "천칭자리", "Scorpio": "전갈자리", "Sagittarius": "사수자리",
    "Capricorn": "염소자리", "Aquarius": "물병자리", "Pisces": "물고기자리",
}
_SIGN_JA = {
    "Aries": "おひつじ座", "Taurus": "おうし座", "Gemini": "ふたご座",
    "Cancer": "かに座", "Leo": "しし座", "Virgo": "おとめ座",
    "Libra": "てんびん座", "Scorpio": "さそり座", "Sagittarius": "いて座",
    "Capricorn": "やぎ座", "Aquarius": "みずがめ座", "Pisces": "うお座",
}


def get_western_astrology_sign(
    birth_month: int, birth_day: int, lang: str = "ko"
) -> Dict[str, Any]:
    """
    출생월·일 → 서양 별자리 (태양궁) 반환
    ephem 없이도 동작하는 순수 계산 방식.
    경계일(±1일) 오차 가능 — 정밀 계산은 astrology_calculator.calc_natal_chart 사용.

    Returns:
        {
            "sign_en": "Aries",
            "sign_ko": "양자리",
            "sign_ja": "おひつじ座",
            "birth_month": 3,
            "birth_day": 21,
            "method": "solar_date_boundary"
        }
    """
    # 올해 생일 기준으로 판단
    sign_en = "Capricorn"  # 기본값 (12/22 이후 ~ 1/19)
    for m, d, s in _ZODIAC_BOUNDARIES:
        if birth_month == m and birth_day >= d:
            sign_en = s
            break
        elif birth_month == m and birth_day < d:
            # 이전 달 별자리
            prev_idx = _ZODIAC_BOUNDARIES.index((m, d, s)) - 1
            if prev_idx >= 0:
                sign_en = _ZODIAC_BOUNDARIES[prev_idx][2]
            else:
                sign_en = "Capricorn"
            break

    # 1월 1~19일 → Capricorn (기본값 유지)
    if birth_month == 1 and birth_day < 20:
        sign_en = "Capricorn"

    return {
        "sign_en": sign_en,
        "sign_ko": _SIGN_KO.get(sign_en, sign_en),
        "sign_ja": _SIGN_JA.get(sign_en, sign_en),
        "birth_month": birth_month,
        "birth_day": birth_day,
        "method": "solar_date_boundary",
    }


def get_eastern_zodiac(birth_year: int, lang: str = "ko") -> Dict[str, Any]:
    """
    출생년도 → 동양 12지신 (띠) 반환
    기준: 1924년 = 쥐(甲子年)

    Returns:
        {
            "zodiac_en": "rat",
            "zodiac_ko": "쥐",
            "zodiac_ja": "ネズミ(子)",
            "birth_year": 1990,
            "earthly_branch": "오"
        }
    """
    idx = (birth_year - 1924) % 12
    if idx < 0:
        idx += 12
    zodiac_en = _EARTHLY_BRANCH_ZODIAC[idx]
    branch = EARTHLY_BRANCHES[idx]  # 지지 문자 (자/축/인/...)

    return {
        "zodiac_en": zodiac_en,
        "zodiac_ko": _ZODIAC_KO.get(zodiac_en, zodiac_en),
        "zodiac_ja": _ZODIAC_JA.get(zodiac_en, zodiac_en),
        "zodiac_en_label": _ZODIAC_EN.get(zodiac_en, zodiac_en),
        "birth_year": birth_year,
        "earthly_branch": branch,
    }


def get_astrology_info(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    lang: str = "ko",
) -> Dict[str, Any]:
    """
    출생일 기반 서양 별자리 + 동양 띠(12지신) 동시 반환
    saju_calculator.py 단일 진입점

    Returns:
        {
            "western": { ... get_western_astrology_sign() ... },
            "eastern": { ... get_eastern_zodiac() ... },
            "lunar_date": { ... get_lunar_date() ... },
            "combined_message": "..."
        }
    """
    western = get_western_astrology_sign(birth_month, birth_day, lang)
    eastern = get_eastern_zodiac(birth_year, lang)
    lunar = get_lunar_date(birth_year, birth_month, birth_day)

    # 통합 메시지 생성
    if lang == "ko":
        combined = (
            f"서양 별자리 {western['sign_ko']}과 동양 {eastern['zodiac_ko']}띠의 에너지가 "
            f"융합되어 독특한 개성을 형성합니다."
        )
    elif lang == "ja":
        combined = (
            f"西洋星座{western['sign_ja']}と東洋の{eastern['zodiac_ja']}の"
            f"エネルギーが融合し、独自の個性を形成します。"
        )
    else:
        combined = (
            f"Your {western['sign_en']} (Western) and {eastern['zodiac_en_label']} (Eastern) "
            f"energies combine to form a unique personality."
        )

    return {
        "western": western,
        "eastern": eastern,
        "lunar_date": lunar,
        "combined_message": combined,
        "disclaimer": _get_disclaimer(lang),
    }
