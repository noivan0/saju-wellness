"""
진태양시(眞太陽時, True Solar Time) 보정 모듈 (P3)

출생지 경도(longitude) 기반 ±30분 시각 보정.
사주팔자 시주(時柱) 계산의 정밀도를 높인다.

원리:
    진태양시 = 평균태양시(KST) + 균시차(Equation of Time) + 경도 보정
    경도 보정 = (경도 - 135°) × 4분/도  (동경 135° = KST 기준)

적용 범위:
    - 한/일: 동경 UTC+9, 바로 적용 가능
    - 글로벌: 출생지 경도 필수
    - 한국 내: 서울(126.9778°) ↔ 동경 135° → 약 -32.1분 보정
    - 일본 도쿄(139.6917°) ↔ 동경 135° → 약 +18.8분 보정

법적 포지셔닝: 문화·오락 서비스 (심리상담/점술 대체 아님)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional


KST = timezone(timedelta(hours=9))
REFERENCE_LONGITUDE = 135.0   # KST(UTC+9) 기준 경도
MINUTES_PER_DEGREE = 4.0      # 경도 1°당 4분 차이


# ---------------------------------------------------------------------------
# 대표 도시 경도 프리셋 (빠른 입력용)
# ---------------------------------------------------------------------------

CITY_LONGITUDES: dict[str, tuple[str, float]] = {
    # 한국
    "seoul": ("서울", 126.9778),
    "busan": ("부산", 129.0756),
    "daegu": ("대구", 128.6014),
    "incheon": ("인천", 126.7052),
    "gwangju": ("광주", 126.8514),
    "daejeon": ("대전", 127.3845),
    "jeju": ("제주", 126.5312),
    # 일본
    "tokyo": ("東京", 139.6917),
    "osaka": ("大阪", 135.5023),
    "kyoto": ("京都", 135.7681),
    "nagoya": ("名古屋", 136.9066),
    "sapporo": ("札幌", 141.3544),
    "fukuoka": ("福岡", 130.4017),
    # 글로벌 주요 도시
    "new_york": ("New York", -74.0059),
    "los_angeles": ("Los Angeles", -118.2437),
    "london": ("London", -0.1276),
    "paris": ("Paris", 2.3522),
    "beijing": ("北京", 116.3912),
    "shanghai": ("上海", 121.4737),
    "singapore": ("Singapore", 103.8198),
    "sydney": ("Sydney", 151.2093),
}


# ---------------------------------------------------------------------------
# 균시차(Equation of Time) 근사 계산
# ---------------------------------------------------------------------------

def _equation_of_time_minutes(date: datetime) -> float:
    """
    균시차 근사값 (분 단위).
    Spencer(1971) 근사식 사용 — 최대 오차 ±1분 (사주 시주 계산에 충분).

    Returns:
        균시차 (분). 양수=평균태양시보다 진태양시 빠름, 음수=느림.
    """
    day_of_year = date.timetuple().tm_yday
    B = 2 * math.pi * (day_of_year - 1) / 365.0
    eot = (
        229.18 * (
            0.000075
            + 0.001868 * math.cos(B)
            - 0.032077 * math.sin(B)
            - 0.014615 * math.cos(2 * B)
            - 0.04089 * math.sin(2 * B)
        )
    )
    return eot


# ---------------------------------------------------------------------------
# 보정 결과 데이터 구조
# ---------------------------------------------------------------------------

@dataclass
class TrueSolarTimeResult:
    """진태양시 보정 결과."""
    original_datetime: datetime          # 입력 시각 (KST 또는 로컬)
    corrected_datetime: datetime         # 보정된 진태양시
    longitude: float                     # 출생지 경도
    city_name: Optional[str]             # 도시명 (프리셋 사용 시)
    longitude_correction_min: float      # 경도 보정 (분)
    eot_correction_min: float            # 균시차 보정 (분)
    total_correction_min: float          # 총 보정 (분)
    corrected_hour: int                  # 보정 후 시(時)
    corrected_minute: int                # 보정 후 분(分)
    hour_branch_idx: int                 # 시지(時支) 인덱스 (0~11)
    note: str                            # 보정 설명

    def to_dict(self) -> dict:
        return {
            "original": self.original_datetime.strftime("%Y-%m-%d %H:%M"),
            "corrected": self.corrected_datetime.strftime("%Y-%m-%d %H:%M"),
            "longitude": self.longitude,
            "city_name": self.city_name,
            "longitude_correction_min": round(self.longitude_correction_min, 1),
            "eot_correction_min": round(self.eot_correction_min, 1),
            "total_correction_min": round(self.total_correction_min, 1),
            "corrected_hour": self.corrected_hour,
            "corrected_minute": self.corrected_minute,
            "hour_branch_idx": self.hour_branch_idx,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# 핵심 보정 함수
# ---------------------------------------------------------------------------

def correct_true_solar_time(
    birth_dt: datetime,
    longitude: Optional[float] = None,
    city_key: Optional[str] = None,
    apply_eot: bool = True,
) -> TrueSolarTimeResult:
    """
    진태양시 보정.

    ⚠️ TIMEZONE 계약 (글로벌 사용 시 필독):
        이 함수의 경도 보정 공식은 birth_dt가 **KST(UTC+9) 기준**일 때만 정확합니다.
        경도 보정 = (경도 - 135°) × 4분 → 기준점이 KST 기준 경도(동경 135°)이기 때문.

        올바른 사용법:
            # 반드시 KST timezone-aware datetime으로 변환 후 전달
            KST = timezone(timedelta(hours=9))
            birth_dt = datetime(year, month, day, hour, minute, tzinfo=KST)

        글로벌 사용자(예: 뉴욕 EST 입력) 처리:
            → 사용자의 **현지 시각을 KST로 변환하지 말 것** — 사주는 출생지 현지 시각 기준
            → 대신 longitude를 출생지 경도로 전달하면 이 함수가 KST 기준점 대비 차이를 자동 보정
            → 예: 뉴욕(−74°) → lng_correction = (−74 − 135) × 4 = −836분 → 이 값이 KST offset 포함

        현재 라우터 구현: datetime(y, m, d, h, min, tzinfo=KST) 강제 지정 → 정상 동작 ✅

    Args:
        birth_dt: 출생 시각. KST(UTC+9) timezone-aware datetime 필수.
                  timezone-naive 전달 시 KST로 가정하여 동작하나, 명시적 지정 권장.
        longitude: 출생지 경도 (-180~180). city_key와 둘 중 하나 필수.
        city_key: CITY_LONGITUDES 키 (예: "seoul", "tokyo")
        apply_eot: 균시차 보정 적용 여부 (기본 True)

    Returns:
        TrueSolarTimeResult

    Raises:
        ValueError: longitude와 city_key 모두 미제공 시, 또는 범위 초과
    """
    # 경도 결정
    city_name: Optional[str] = None
    if city_key is not None:
        city_key_lower = city_key.lower()
        if city_key_lower not in CITY_LONGITUDES:
            raise ValueError(
                f"알 수 없는 도시 키: '{city_key}'. "
                f"사용 가능: {list(CITY_LONGITUDES.keys())}"
            )
        city_name, longitude = CITY_LONGITUDES[city_key_lower]
    elif longitude is None:
        raise ValueError("longitude 또는 city_key 중 하나는 필수입니다.")

    if not (-180.0 <= longitude <= 180.0):
        raise ValueError(f"경도 범위 초과: {longitude} (유효 범위: -180~180)")

    # 1. 경도 보정 (분)
    lng_correction_min = (longitude - REFERENCE_LONGITUDE) * MINUTES_PER_DEGREE

    # 2. 균시차 보정 (분)
    eot_min = _equation_of_time_minutes(birth_dt) if apply_eot else 0.0

    # 3. 총 보정
    total_correction_min = lng_correction_min + eot_min

    # 4. 보정된 시각
    corrected_dt = birth_dt + timedelta(minutes=total_correction_min)

    # 5. 시주(時柱) 인덱스 계산 (0=자시 23~1시, 1=축시 1~3시, ...)
    h = corrected_dt.hour
    m = corrected_dt.minute
    # 자시(子時): 23:00~01:00 → branch_idx=0
    hour_branch_idx = ((h + 1) // 2) % 12

    # 6. 보정 설명 생성
    direction = "빠름" if total_correction_min > 0 else "느림"
    note = (
        f"경도 {longitude}° 기준: "
        f"경도보정 {lng_correction_min:+.1f}분, "
        f"균시차 {eot_min:+.1f}분 → "
        f"총 {total_correction_min:+.1f}분({direction})"
    )

    return TrueSolarTimeResult(
        original_datetime=birth_dt,
        corrected_datetime=corrected_dt,
        longitude=longitude,
        city_name=city_name,
        longitude_correction_min=lng_correction_min,
        eot_correction_min=eot_min,
        total_correction_min=total_correction_min,
        corrected_hour=corrected_dt.hour,
        corrected_minute=corrected_dt.minute,
        hour_branch_idx=hour_branch_idx,
        note=note,
    )


def get_city_suggestions() -> list[dict]:
    """UI 도시 선택 드롭다운용 데이터."""
    return [
        {"key": k, "name": v[0], "longitude": v[1]}
        for k, v in CITY_LONGITUDES.items()
    ]


# ---------------------------------------------------------------------------
# 사주 엔진 연동 헬퍼
# ---------------------------------------------------------------------------

def calc_hour_pillar_with_tst(
    birth_dt: datetime,
    day_stem_idx: int,
    longitude: Optional[float] = None,
    city_key: Optional[str] = None,
) -> dict:
    """
    진태양시 보정 적용 시주(時柱) 계산.

    saju_calculator.calc_four_pillars()에서 birth_hour 대신 이 함수 사용.

    Args:
        birth_dt: 출생 시각
        day_stem_idx: 일간(日干) 인덱스 (연주 계산에서 전달)
        longitude: 출생지 경도 (선택)
        city_key: 도시 키 (선택)

    Returns:
        시주 dict (stem, branch, pillar, tst_correction)
    """
    from .saju_calculator import HEAVENLY_STEMS, EARTHLY_BRANCHES

    if longitude is not None or city_key is not None:
        tst = correct_true_solar_time(birth_dt, longitude=longitude, city_key=city_key)
        hour_branch_idx = tst.hour_branch_idx
        tst_info = tst.to_dict()
    else:
        # 보정 없음: 기존 방식
        hour_branch_idx = ((birth_dt.hour + 1) // 2) % 12
        tst_info = None

    hour_stem_idx = (day_stem_idx * 2 + hour_branch_idx) % 10

    return {
        "stem": HEAVENLY_STEMS[hour_stem_idx],
        "branch": EARTHLY_BRANCHES[hour_branch_idx],
        "pillar": f"{HEAVENLY_STEMS[hour_stem_idx]}{EARTHLY_BRANCHES[hour_branch_idx]}",
        "tst_correction": tst_info,  # None이면 보정 미적용
    }
