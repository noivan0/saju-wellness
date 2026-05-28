"""
서양 점성술 계산 엔진 (Western Astrology Calculator)
- 태양궁/달궁/어센던트 계산
- 10행성 × 12하우스 배치
- 에픽시클 계산 (Placidus 하우스 시스템 표준)
- 동양 사주팔자 일간(日干)과 크로스 해석: 일간(日干) ↔ 태양궁 대응표
- 라이브러리: ephem (pip install ephem)
법적 포지셔닝: 문화·오락 서비스 / 자기이해 도구 (점술/예언 아님)
"""
import math
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    import ephem as _ephem  # type: ignore[import-untyped]
    _EPHEM_OK = True
except ImportError:
    _ephem = None  # type: ignore[assignment]
    _EPHEM_OK = False

# 편의 별칭 (타입 체커용 — 런타임에는 _EPHEM_OK 가드 필수)
ephem = _ephem  # type: ignore[assignment]

KST = timezone(timedelta(hours=9))

# ─────────────────────────────────────────────────────────
# 황도 12궁 (태양궁)
# ─────────────────────────────────────────────────────────
ZODIAC_SIGNS = [
    "양자리", "황소자리", "쌍둥이자리", "게자리", "사자자리", "처녀자리",
    "천칭자리", "전갈자리", "사수자리", "염소자리", "물병자리", "물고기자리",
]
ZODIAC_SIGNS_JA = [
    "おひつじ座", "おうし座", "ふたご座", "かに座", "しし座", "おとめ座",
    "てんびん座", "さそり座", "いて座", "やぎ座", "みずがめ座", "うお座",
]
ZODIAC_SIGNS_EN = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# 어센던트 계산을 위한 궁 명칭
HOUSE_LABELS_KO = [
    "1하우스(자아)", "2하우스(재물)", "3하우스(소통)", "4하우스(가정)",
    "5하우스(창조)", "6하우스(건강)", "7하우스(파트너)", "8하우스(변환)",
    "9하우스(철학)", "10하우스(커리어)", "11하우스(공동체)", "12하우스(잠재)",
]

# ─────────────────────────────────────────────────────────
# 동양 일간(日干) ↔ 서양 태양궁 대응표
# 명리학 오행 방위 + 계절성 기반 크로스 해석
# ─────────────────────────────────────────────────────────
ILGAN_TO_SOLAR = {
    # 목(木) 계열
    "갑": {"solar_signs": ["양자리", "사자자리"], "keyword": "성장·도전·양기 목"},
    "을": {"solar_signs": ["황소자리", "처녀자리"], "keyword": "유연·인내·음기 목"},
    # 화(火) 계열
    "병": {"solar_signs": ["사자자리", "사수자리"], "keyword": "열정·표현·양기 화"},
    "정": ["게자리", "전갈자리"],  # 음기 화
    # 토(土) 계열
    "무": {"solar_signs": ["황소자리", "사수자리"], "keyword": "안정·신뢰·양기 토"},
    "기": {"solar_signs": ["처녀자리", "황소자리"], "keyword": "세심·완성·음기 토"},
    # 금(金) 계열
    "경": {"solar_signs": ["양자리", "천칭자리"], "keyword": "결단·원칙·양기 금"},
    "신": {"solar_signs": ["처녀자리", "천칭자리"], "keyword": "정밀·절제·음기 금"},
    # 수(水) 계열
    "임": {"solar_signs": ["물병자리", "사수자리"], "keyword": "지혜·유동·양기 수"},
    "계": {"solar_signs": ["물고기자리", "전갈자리"], "keyword": "직관·깊이·음기 수"},
}

# 행성 목록
PLANETS = ["sun", "moon", "mercury", "venus", "mars",
           "jupiter", "saturn", "uranus", "neptune", "pluto"]

PLANET_NAMES_KO = {
    "sun": "태양", "moon": "달", "mercury": "수성", "venus": "금성",
    "mars": "화성", "jupiter": "목성", "saturn": "토성",
    "uranus": "천왕성", "neptune": "해왕성", "pluto": "명왕성",
}

PLANET_NAMES_JA = {
    "sun": "太陽", "moon": "月", "mercury": "水星", "venus": "金星",
    "mars": "火星", "jupiter": "木星", "saturn": "土星",
    "uranus": "天王星", "neptune": "海王星", "pluto": "冥王星",
}

PLANET_NAMES_EN = {
    "sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
    "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
    "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto",
}

# 어스펙트 각도 (허용 오차 orb)
ASPECTS = [
    {"name": "합(Conjunction)", "angle": 0, "orb": 8, "nature": "강화"},
    {"name": "육분(Sextile)", "angle": 60, "orb": 6, "nature": "조화"},
    {"name": "방(Square)", "angle": 90, "orb": 8, "nature": "긴장"},
    {"name": "삼분(Trine)", "angle": 120, "orb": 8, "nature": "조화"},
    {"name": "대립(Opposition)", "angle": 180, "orb": 8, "nature": "긴장"},
]


def _ecl_lon_to_sign(lon_deg: float) -> dict:
    """황도 경도(0~360) → 황도 12궁 정보"""
    lon_deg = lon_deg % 360
    idx = int(lon_deg // 30)
    degree_in_sign = lon_deg % 30
    return {
        "sign_ko": ZODIAC_SIGNS[idx],
        "sign_ja": ZODIAC_SIGNS_JA[idx],
        "sign_en": ZODIAC_SIGNS_EN[idx],
        "sign_idx": idx,
        "degree": round(degree_in_sign, 2),
        "total_degree": round(lon_deg, 2),
    }


def _get_planet(name: str) -> Optional[object]:
    """ephem 행성 객체 반환"""
    if not _EPHEM_OK:
        return None
    mapping = {
        "sun": ephem.Sun,
        "moon": ephem.Moon,
        "mercury": ephem.Mercury,
        "venus": ephem.Venus,
        "mars": ephem.Mars,
        "jupiter": ephem.Jupiter,
        "saturn": ephem.Saturn,
        "uranus": ephem.Uranus,
        "neptune": ephem.Neptune,
        "pluto": ephem.Pluto,
    }
    cls = mapping.get(name)
    return cls() if cls else None


def _compute_asc(observer: object) -> Optional[float]:
    """
    어센던트(ASC) 근사 계산
    Placidus 정밀 계산은 전용 라이브러리 필요.
    여기서는 RAMC(Right Ascension of Midheaven) + 위도 보정 근사값 사용.
    """
    if not _EPHEM_OK:
        return None
    try:
        # 현지 항성시 (Local Sidereal Time) 기반 어센던트 근사
        lst = float(observer.sidereal_time())  # 라디안
        lat_rad = float(observer.lat)
        # 어센던트 황도 경도 근사 공식
        # tan(ASC) = -cos(RAMC) / (sin(RAMC)*cos(ε) + tan(φ)*sin(ε))
        # ε = 황도경사각 ≈ 23.43°
        epsilon = math.radians(23.43)
        ramc = lst  # 라디안
        numerator = -math.cos(ramc)
        denominator = math.sin(ramc) * math.cos(epsilon) + math.tan(lat_rad) * math.sin(epsilon)
        if abs(denominator) < 1e-10:
            return None
        asc_rad = math.atan(numerator / denominator)
        asc_deg = math.degrees(asc_rad)
        # 사분면 보정
        if denominator < 0:
            asc_deg += 180
        asc_deg = asc_deg % 360
        return asc_deg
    except Exception:
        return None


def calc_natal_chart(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int = 12,
    birth_minute: int = 0,
    lat: float = 37.5665,   # 서울 기본값
    lon: float = 126.9780,
    lang: str = "ko",
) -> dict:
    """
    출생 날짜/시각/장소 → 서양 점성술 출생차트 계산
    - 10행성 황도 위치 (궁·도수)
    - 어센던트 (Placidus 근사)
    - 주요 어스펙트

    Returns:
        {
          "sun": {"sign_ko": ..., "degree": ...},
          "moon": {...},
          ...
          "ascendant": {...},
          "aspects": [...],
          "planet_names": {...},
          "disclaimer": "...",
          "method": "ephem" | "fallback"
        }
    """
    if not _EPHEM_OK:
        return _fallback_chart(birth_year, birth_month, birth_day, lang)

    try:
        # ephem 날짜 (UTC 변환 — KST 입력 기준 -9h)
        dt_kst = datetime(birth_year, birth_month, birth_day,
                          birth_hour, birth_minute, tzinfo=KST)
        dt_utc = dt_kst.astimezone(timezone.utc)
        ephem_date = ephem.Date(
            f"{dt_utc.year}/{dt_utc.month}/{dt_utc.day} "
            f"{dt_utc.hour}:{dt_utc.minute}:00"
        )

        # 관측자 설정
        observer = ephem.Observer()
        observer.lat = str(lat)
        observer.lon = str(lon)
        observer.date = ephem_date
        observer.pressure = 0  # 대기 굴절 무시

        # 에클립틱 좌표로 변환하기 위한 에포크
        epoch = ephem.J2000

        planet_positions = {}
        planet_lons = {}
        for pname in PLANETS:
            body = _get_planet(pname)
            if body is None:
                continue
            body.compute(ephem_date, epoch=epoch)
            # 황도 좌표 (ecliptic longitude)
            ecl = ephem.Ecliptic(body, epoch=epoch)
            lon_deg = math.degrees(float(ecl.lon)) % 360
            planet_lons[pname] = lon_deg
            sign_info = _ecl_lon_to_sign(lon_deg)

            pname_local = PLANET_NAMES_KO.get(pname, pname) if lang == "ko" else \
                          PLANET_NAMES_JA.get(pname, pname) if lang == "ja" else \
                          PLANET_NAMES_EN.get(pname, pname)

            planet_positions[pname] = {
                **sign_info,
                "planet_name": pname_local,
                "ecliptic_lon": round(lon_deg, 4),
            }

        # 어센던트 계산
        asc_deg = _compute_asc(observer)
        ascendant = _ecl_lon_to_sign(asc_deg) if asc_deg is not None else None
        if ascendant:
            ascendant["label"] = "어센던트(상승궁)"

        # 어스펙트 계산 (주요 6행성 간)
        aspects = _calc_aspects(planet_lons)

        # 하우스 배치 (ASC 기준 Equal House 근사)
        houses = []
        if asc_deg is not None:
            for i in range(12):
                house_cusp = (asc_deg + i * 30) % 360
                houses.append({
                    "house": i + 1,
                    "label": HOUSE_LABELS_KO[i],
                    "cusp_degree": round(house_cusp, 2),
                    "sign": _ecl_lon_to_sign(house_cusp)["sign_ko" if lang == "ko" else
                                                           "sign_ja" if lang == "ja" else "sign_en"],
                })
            # 어느 행성이 어느 하우스에 있는지 배치
            for pname, pos in planet_positions.items():
                p_lon = planet_lons[pname]
                house_num = _find_house(p_lon, asc_deg)
                pos["house"] = house_num

        return {
            "planets": planet_positions,
            "ascendant": ascendant,
            "aspects": aspects,
            "houses": houses,
            "method": "ephem",
            "birth_utc": dt_utc.isoformat(),
            "disclaimer": _get_disclaimer(lang),
        }

    except Exception as e:
        return {**_fallback_chart(birth_year, birth_month, birth_day, lang), "error": str(e)}


def _find_house(planet_lon: float, asc_lon: float) -> int:
    """행성 황도 경도 → 하우스 번호 (Equal House 근사)"""
    diff = (planet_lon - asc_lon) % 360
    return int(diff // 30) + 1


def _calc_aspects(planet_lons: dict) -> list:
    """행성 간 주요 어스펙트 계산"""
    results = []
    planet_list = [p for p in PLANETS if p in planet_lons]
    for i, p1 in enumerate(planet_list):
        for p2 in planet_list[i + 1:]:
            diff = abs(planet_lons[p1] - planet_lons[p2]) % 360
            if diff > 180:
                diff = 360 - diff
            for asp in ASPECTS:
                if abs(diff - asp["angle"]) <= asp["orb"]:
                    results.append({
                        "planet1": PLANET_NAMES_KO.get(p1, p1),
                        "planet2": PLANET_NAMES_KO.get(p2, p2),
                        "aspect": asp["name"],
                        "angle_diff": round(diff, 2),
                        "orb": round(abs(diff - asp["angle"]), 2),
                        "nature": asp["nature"],
                    })
                    break
    return results


def _fallback_chart(year: int, month: int, day: int, lang: str) -> dict:
    """ephem 없을 때 태양궁만 계산 (근사)"""
    # 태양궁 근사: 월별 기준 + 일 보정
    MONTH_SIGN = {
        1: (10, "염소자리"), 2: (9, "물병자리"), 3: (10, "물고기자리"),
        4: (10, "양자리"), 5: (10, "황소자리"), 6: (10, "쌍둥이자리"),
        7: (10, "게자리"), 8: (10, "사자자리"), 9: (10, "처녀자리"),
        10: (10, "천칭자리"), 11: (10, "전갈자리"), 12: (10, "사수자리"),
    }
    cutoff, sign = MONTH_SIGN.get(month, (10, "양자리"))
    if day < cutoff:
        prev_month = month - 1 if month > 1 else 12
        _, sign = MONTH_SIGN.get(prev_month, (10, "염소자리"))

    idx = ZODIAC_SIGNS.index(sign) if sign in ZODIAC_SIGNS else 0
    sign_name = (ZODIAC_SIGNS if lang == "ko" else
                 ZODIAC_SIGNS_JA if lang == "ja" else ZODIAC_SIGNS_EN)[idx]
    return {
        "planets": {
            "sun": {
                "sign_ko": ZODIAC_SIGNS[idx],
                "sign_ja": ZODIAC_SIGNS_JA[idx],
                "sign_en": ZODIAC_SIGNS_EN[idx],
                "sign_idx": idx,
                "degree": 0,
                "planet_name": "태양",
            }
        },
        "ascendant": None,
        "aspects": [],
        "houses": [],
        "method": "fallback_solar_only",
        "disclaimer": _get_disclaimer(lang),
    }


def get_sun_sign(birth_month: int, birth_day: int, lang: str = "ko") -> dict:
    """
    태양궁(Sun Sign) 간편 계산 — ephem 불필요
    월·일만으로 12궁 결정 (절기 정밀 보정 없음, 경계일 ±1일 오차 가능)
    """
    # 각 달의 태양궁 전환일 (양력 기준)
    SIGN_DATES = [
        (1, 20, "물병자리"), (2, 19, "물고기자리"), (3, 21, "양자리"),
        (4, 20, "황소자리"), (5, 21, "쌍둥이자리"), (6, 21, "게자리"),
        (7, 23, "사자자리"), (8, 23, "처녀자리"), (9, 23, "천칭자리"),
        (10, 23, "전갈자리"), (11, 22, "사수자리"), (12, 22, "염소자리"),
    ]
    sign_ko = "염소자리"
    for m, d, s in SIGN_DATES:
        if (birth_month == m and birth_day >= d) or (birth_month == m + 1 and birth_day < d):
            sign_ko = s
            break
        if birth_month == m and birth_day < d:
            # 이전 달 궁
            prev_idx = SIGN_DATES.index((m, d, s)) - 1
            if prev_idx >= 0:
                sign_ko = SIGN_DATES[prev_idx][2]
            break

    idx = ZODIAC_SIGNS.index(sign_ko) if sign_ko in ZODIAC_SIGNS else 0
    return {
        "sign_ko": ZODIAC_SIGNS[idx],
        "sign_ja": ZODIAC_SIGNS_JA[idx],
        "sign_en": ZODIAC_SIGNS_EN[idx],
        "sign_idx": idx,
    }


def cross_interpret_ilgan_solar(ilgan: str, solar_sign_ko: str, lang: str = "ko") -> dict:
    """
    동양 일간(日干) × 서양 태양궁 크로스 해석
    - 일간: 갑/을/병/정/무/기/경/신/임/계
    - solar_sign_ko: 태양궁 한국어명

    Returns: 통합 해석 텍스트 + 공통 키워드 + 강화 요소
    """
    ilgan_info = ILGAN_TO_SOLAR.get(ilgan, {})
    if isinstance(ilgan_info, list):
        ilgan_info = {"solar_signs": ilgan_info, "keyword": ""}

    aligned_signs = ilgan_info.get("solar_signs", [])
    ilgan_keyword = ilgan_info.get("keyword", "")

    is_aligned = solar_sign_ko in aligned_signs
    is_tension = not is_aligned and len(aligned_signs) > 0

    if is_aligned:
        harmony = "강화"
        harmony_text = (
            f"{ilgan} 일간과 {solar_sign_ko}의 에너지가 잘 공명합니다. "
            f"동·서양 모두 '{ilgan_keyword}' 키워드를 공유하여 자기 표현이 일관됩니다."
        )
    elif is_tension:
        harmony = "보완"
        harmony_text = (
            f"{ilgan} 일간({ilgan_keyword})과 {solar_sign_ko}는 서로 다른 에너지입니다. "
            f"동양의 {ilgan_keyword} 성질을 서양 궁의 특성이 보완하여 균형 잡힌 개성을 만듭니다."
        )
    else:
        harmony = "중립"
        harmony_text = f"{ilgan} 일간과 {solar_sign_ko}는 독립적인 에너지를 지닙니다."

    return {
        "ilgan": ilgan,
        "solar_sign": solar_sign_ko,
        "alignment": harmony,
        "interpretation": harmony_text,
        "ilgan_keyword": ilgan_keyword,
        "aligned_solar_signs": aligned_signs,
    }


def _get_disclaimer(lang: str) -> str:
    d = {
        "ko": "본 내용은 서양 점성술 관점의 자기이해 참고 정보이며 과학적 예측이나 전문 상담을 대체하지 않습니다.",
        "ja": "本内容は西洋占星術的観点の自己理解参考情報であり、科学的予測や専門的カウンセリングの代わりにはなりません。",
        "en": "This is self-understanding reference material from a Western astrology perspective. It does not replace scientific prediction or professional counseling.",
    }
    return d.get(lang, d["ko"])
