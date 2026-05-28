"""
학술 명리학 정밀 분석 모듈 (Academic-Level Miriok Engine)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

기반 이론:
  - 적천수(滴天髓), 자평진전(子平眞詮), 명리정종(命理正宗)
  - 현대 명리학: 박재완, 이석영 계열 이론 종합

포함 기능:
  1. 지장간(支藏干) — 각 지지에 내장된 천간
  2. 오행 상생상극 정밀 로직
  3. 월령(月令) 득령/실령 가중치 계산
  4. 오행 강도 점수 종합
  5. 격국(格局) 8格 판별
  6. 억부용신(抑扶用神) 신강/신약 판별
  7. 대운(大運) 정밀 계산 (lunar_python 기반)
  8. 신뢰도(confidence_level) 및 출처 명시

법적 포지셔닝: 학문적 참고 도구 — 전문 상담 대체 불가
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any

# ─────────────────────────────────────────────
# 1. 기본 상수 — 학술 기준
# ─────────────────────────────────────────────

# 천간 한자 ↔ 한글 매핑
HANJA_TO_KR_STEM = {
    "甲": "갑", "乙": "을", "丙": "병", "丁": "정", "戊": "무",
    "己": "기", "庚": "경", "辛": "신", "壬": "임", "癸": "계",
}
KR_TO_HANJA_STEM = {v: k for k, v in HANJA_TO_KR_STEM.items()}

# 지지 한자 ↔ 한글 매핑
HANJA_TO_KR_BRANCH = {
    "子": "자", "丑": "축", "寅": "인", "卯": "묘", "辰": "진", "巳": "사",
    "午": "오", "未": "미", "申": "신", "酉": "유", "戌": "술", "亥": "해",
}
KR_TO_HANJA_BRANCH = {v: k for k, v in HANJA_TO_KR_BRANCH.items()}

# 천간 오행 배속 (학술 기준)
STEM_ELEMENT_MAP: Dict[str, str] = {
    "甲": "목", "乙": "목",   # 木 — 甲(양목), 乙(음목)
    "丙": "화", "丁": "화",   # 火 — 丙(양화), 丁(음화)
    "戊": "토", "己": "토",   # 土 — 戊(양토), 己(음토)
    "庚": "금", "辛": "금",   # 金 — 庚(양금), 辛(음금)
    "壬": "수", "癸": "수",   # 水 — 壬(양수), 癸(음수)
}

# 지지 오행 배속 (학술 기준)
BRANCH_ELEMENT_MAP: Dict[str, str] = {
    "子": "수",   # 子水
    "丑": "토",   # 丑土 (수장간)
    "寅": "목",   # 寅木
    "卯": "목",   # 卯木
    "辰": "토",   # 辰土 (수장간)
    "巳": "화",   # 巳火
    "午": "화",   # 午火
    "未": "토",   # 未土 (화장간)
    "申": "금",   # 申金
    "酉": "금",   # 酉金
    "戌": "토",   # 戌土 (화장간)
    "亥": "수",   # 亥水
}

# 음양 배속
STEM_YIN_YANG: Dict[str, str] = {
    "甲": "양", "乙": "음", "丙": "양", "丁": "음", "戊": "양",
    "己": "음", "庚": "양", "辛": "음", "壬": "양", "癸": "음",
}
BRANCH_YIN_YANG: Dict[str, str] = {
    "子": "양", "丑": "음", "寅": "양", "卯": "음", "辰": "양", "巳": "음",
    "午": "양", "未": "음", "申": "양", "酉": "음", "戌": "양", "亥": "음",
}

# ─────────────────────────────────────────────
# 2. 지장간(支藏干) — 각 지지에 숨겨진 천간
# 출처: 명리학 정통 이론 기준 (적천수·자평진전)
# 형식: {"여기(餘氣)": 간, "중기(中氣)": 간, "정기(正氣)": 간}
# ─────────────────────────────────────────────

JIJANGGAN: Dict[str, Dict[str, str]] = {
    # 子: 정기=癸, 여기/중기 없음
    "子": {"정기": "癸"},
    # 丑: 여기=癸, 중기=辛, 정기=己
    "丑": {"여기": "癸", "중기": "辛", "정기": "己"},
    # 寅: 여기=戊, 중기=丙, 정기=甲
    "寅": {"여기": "戊", "중기": "丙", "정기": "甲"},
    # 卯: 정기=乙, 여기/중기 없음
    "卯": {"정기": "乙"},
    # 辰: 여기=乙, 중기=癸, 정기=戊
    "辰": {"여기": "乙", "중기": "癸", "정기": "戊"},
    # 巳: 여기=戊, 중기=庚, 정기=丙
    "巳": {"여기": "戊", "중기": "庚", "정기": "丙"},
    # 午: 여기=丙, 정기=丁  (중기=己라 보는 설도 있음)
    "午": {"여기": "丙", "중기": "己", "정기": "丁"},
    # 未: 여기=丁, 중기=乙, 정기=己
    "未": {"여기": "丁", "중기": "乙", "정기": "己"},
    # 申: 여기=戊, 중기=壬, 정기=庚
    "申": {"여기": "戊", "중기": "壬", "정기": "庚"},
    # 酉: 정기=辛
    "酉": {"정기": "辛"},
    # 戌: 여기=辛, 중기=丁, 정기=戊
    "戌": {"여기": "辛", "중기": "丁", "정기": "戊"},
    # 亥: 여기=戊, 정기=壬
    "亥": {"여기": "戊", "정기": "壬"},
}

# 지장간 일수 비율 (지지 30일 기준, 정기가 주력)
JIJANGGAN_DAYS: Dict[str, Dict[str, int]] = {
    "子": {"정기": 30},
    "丑": {"여기": 9, "중기": 3, "정기": 18},
    "寅": {"여기": 7, "중기": 7, "정기": 16},
    "卯": {"정기": 30},
    "辰": {"여기": 9, "중기": 3, "정기": 18},
    "巳": {"여기": 7, "중기": 7, "정기": 16},
    "午": {"여기": 10, "중기": 10, "정기": 10},
    "未": {"여기": 9, "중기": 3, "정기": 18},
    "申": {"여기": 7, "중기": 7, "정기": 16},
    "酉": {"정기": 30},
    "戌": {"여기": 9, "중기": 3, "정기": 18},
    "亥": {"여기": 7, "정기": 23},
}

# ─────────────────────────────────────────────
# 3. 오행 상생(相生) / 상극(相克)
# ─────────────────────────────────────────────

# 상생: 목→화→토→금→수→목
ELEMENT_SHENG: Dict[str, str] = {
    "목": "화", "화": "토", "토": "금", "금": "수", "수": "목",
}
# 상생 역방향 (누가 나를 생해주는가)
ELEMENT_SHENG_FROM: Dict[str, str] = {v: k for k, v in ELEMENT_SHENG.items()}

# 상극: 목→토, 토→수, 수→화, 화→금, 금→목
ELEMENT_KE: Dict[str, str] = {
    "목": "토", "토": "수", "수": "화", "화": "금", "금": "목",
}
# 상극 역방향 (누가 나를 극하는가)
ELEMENT_KE_FROM: Dict[str, str] = {v: k for k, v in ELEMENT_KE.items()}


def get_element_relation(e1: str, e2: str) -> str:
    """두 오행 간 관계 반환 (e1 → e2 관점)"""
    if e1 == e2:
        return "비화(比和)"
    if ELEMENT_SHENG.get(e1) == e2:
        return "상생(生)"
    if ELEMENT_SHENG_FROM.get(e1) == e2:
        return "수생(受生)"
    if ELEMENT_KE.get(e1) == e2:
        return "상극(克)"
    if ELEMENT_KE_FROM.get(e1) == e2:
        return "수극(受克)"
    return "중립"


# ─────────────────────────────────────────────
# 4. 월령(月令) 득령/실령 가중치
# 각 지지(월지)별로 오행 왕상휴수사(旺相休囚死) 배속
# 출처: 명리학 정통 이론 기준
# 旺=4, 相=3, 休=2, 囚=1, 死=0 (강도 계수)
# ─────────────────────────────────────────────

# 월지별 오행 강도 계수: MONTH_ELEMENT_STRENGTH[월지지한자][오행] = 강도계수
MONTH_ELEMENT_STRENGTH: Dict[str, Dict[str, int]] = {
    # 寅月(입춘~경칩): 목왕
    "寅": {"목": 4, "화": 3, "토": 1, "금": 0, "수": 2},
    # 卯月(경칩~청명): 목왕
    "卯": {"목": 4, "화": 3, "토": 1, "금": 0, "수": 2},
    # 辰月(청명~입하): 토왕, 목여기
    "辰": {"목": 2, "화": 3, "토": 4, "금": 1, "수": 0},
    # 巳月(입하~망종): 화왕
    "巳": {"목": 2, "화": 4, "토": 3, "금": 1, "수": 0},
    # 午月(망종~소서): 화왕
    "午": {"목": 2, "화": 4, "토": 3, "금": 0, "수": 1},
    # 未月(소서~입추): 토왕, 화여기
    "未": {"목": 0, "화": 2, "토": 4, "금": 3, "수": 1},
    # 申月(입추~백로): 금왕
    "申": {"목": 0, "화": 1, "토": 3, "금": 4, "수": 2},
    # 酉月(백로~한로): 금왕
    "酉": {"목": 0, "화": 1, "토": 3, "금": 4, "수": 2},
    # 戌月(한로~입동): 토왕, 금여기
    "戌": {"목": 1, "화": 2, "토": 4, "금": 3, "수": 0},
    # 亥月(입동~대설): 수왕
    "亥": {"목": 3, "화": 0, "토": 1, "금": 2, "수": 4},
    # 子月(대설~소한): 수왕
    "子": {"목": 3, "화": 0, "토": 1, "금": 2, "수": 4},
    # 丑月(소한~입춘): 토왕, 수여기
    "丑": {"목": 1, "화": 0, "토": 4, "금": 3, "수": 2},
}

# 왕상휴수사 라벨
STRENGTH_LABEL: Dict[int, str] = {4: "왕(旺)", 3: "상(相)", 2: "휴(休)", 1: "수(囚)", 0: "사(死)"}

# ─────────────────────────────────────────────
# 5. 십신(十神) 관계 도출
# 일간(日干)을 기준으로 다른 천간의 십신 관계를 계산
# ─────────────────────────────────────────────

# 십신 계산: (일간 오행, 대상 오행, 대상 음양) → 십신명
def _get_sipshin(ilgan_hanja: str, target_hanja: str) -> str:
    """
    일간(日干)과 대상 천간의 십신(十神) 관계 계산
    
    십신 체계:
      比肩(비견), 劫財(겁재)   — 동일 오행
      食神(식신), 傷官(상관)   — 일간이 생하는 오행
      正財(정재), 偏財(편재)   — 일간이 극하는 오행
      正官(정관), 偏官(편관)   — 일간을 극하는 오행
      正印(정인), 偏印(편인)   — 일간을 생하는 오행
    """
    ilgan_el = STEM_ELEMENT_MAP.get(ilgan_hanja, "")
    target_el = STEM_ELEMENT_MAP.get(target_hanja, "")
    ilgan_yy = STEM_YIN_YANG.get(ilgan_hanja, "양")
    target_yy = STEM_YIN_YANG.get(target_hanja, "양")
    same_yy = (ilgan_yy == target_yy)

    if ilgan_el == target_el:
        return "비견(比肩)" if same_yy else "겁재(劫財)"
    if ELEMENT_SHENG.get(ilgan_el) == target_el:
        return "식신(食神)" if same_yy else "상관(傷官)"
    if ELEMENT_KE.get(ilgan_el) == target_el:
        return "편재(偏財)" if same_yy else "정재(正財)"
    if ELEMENT_KE.get(target_el) == ilgan_el:
        return "편관(偏官)" if same_yy else "정관(正官)"
    if ELEMENT_SHENG.get(target_el) == ilgan_el:
        return "편인(偏印)" if same_yy else "정인(正印)"
    return "불명"


# ─────────────────────────────────────────────
# 6. 격국(格局) 판별
# 월지(月支) 지장간 정기를 기준으로 격국을 결정
# ─────────────────────────────────────────────

# 격국 이름 매핑: 십신 → 격국명
SIPSHIN_TO_GYEOK: Dict[str, str] = {
    "정관(正官)": "正官格(정관격)",
    "편관(偏官)": "偏官格(편관격)",
    "정재(正財)": "正財格(정재격)",
    "편재(偏財)": "偏財格(편재격)",
    "식신(食神)": "食神格(식신격)",
    "상관(傷官)": "傷官格(상관격)",
    "정인(正印)": "正印格(정인격)",
    "편인(偏印)": "偏印格(편인격)",
}


def determine_gyeokguk(
    ilgan_hanja: str,
    month_branch_hanja: str,
) -> Dict[str, Any]:
    """
    격국(格局) 판별 — 월지 정기(正氣) 기준 8格
    
    Args:
        ilgan_hanja: 일간 한자 (예: '甲')
        month_branch_hanja: 월지 한자 (예: '巳')
    
    Returns:
        {
          "gyeokguk": "食神格(식신격)",
          "sipshin": "식신(食神)",
          "month_branch": "巳",
          "jeong_gi": "丙",      # 월지 정기
          "jeong_gi_element": "화",
          "confidence_level": "high",
          "source": "명리학 정통 이론 기준",
          "note": "..."
        }
    """
    jijang = JIJANGGAN.get(month_branch_hanja, {})
    # 정기(正氣) 우선
    jeong_gi = jijang.get("정기")
    if not jeong_gi:
        # 정기 없으면 중기
        jeong_gi = jijang.get("중기")

    if not jeong_gi:
        return {
            "gyeokguk": "불명",
            "sipshin": "불명",
            "month_branch": month_branch_hanja,
            "jeong_gi": None,
            "jeong_gi_element": None,
            "confidence_level": "low",
            "source": "명리학 정통 이론 기준",
            "note": "월지 지장간 정기를 찾지 못했습니다.",
        }

    sipshin = _get_sipshin(ilgan_hanja, jeong_gi)
    gyeokguk = SIPSHIN_TO_GYEOK.get(sipshin, f"기타({sipshin})")
    jeong_gi_el = STEM_ELEMENT_MAP.get(jeong_gi, "")

    # 비견·겁재는 특수격으로 분류
    is_special = sipshin in ("비견(比肩)", "겁재(劫財)")
    if is_special:
        gyeokguk = "특수격(建祿·羊刃格 등)"

    return {
        "gyeokguk": gyeokguk,
        "sipshin": sipshin,
        "month_branch": month_branch_hanja,
        "jeong_gi": jeong_gi,
        "jeong_gi_element": jeong_gi_el,
        "confidence_level": "high" if not is_special else "medium",
        "source": "명리학 정통 이론 기준",
        "note": (
            f"월지 {month_branch_hanja}의 정기 {jeong_gi}({jeong_gi_el})와 "
            f"일간 {ilgan_hanja}의 십신 관계: {sipshin} → {gyeokguk}"
        ),
        "disclaimer": _get_academic_disclaimer(),
    }


# ─────────────────────────────────────────────
# 7. 오행 강도 종합 계산 (월령 가중치 포함)
# ─────────────────────────────────────────────

def calc_element_strength(
    year_stem: str,    # 한자
    year_branch: str,
    month_stem: str,
    month_branch: str,
    day_stem: str,
    day_branch: str,
    hour_stem: Optional[str] = None,
    hour_branch: Optional[str] = None,
) -> Dict[str, Any]:
    """
    오행 강도 종합 계산 — 월령(月令) 득령/실령 가중치 반영
    
    계산 방식:
      - 각 기둥의 천간(×1), 지지(×1) 기본 점수 집계
      - 일간은 본인 강화를 위해 ×2 계수 (일간 중심 명리학)
      - 월지 득령 여부: 오행 강도 계수(0~4) × 0.5 보너스 점수
      - 지장간 정기: 0.5점 추가
    
    Returns:
        {
          "raw_counts": {오행: 기본 횟수},
          "weighted_scores": {오행: 가중 점수},
          "month_strength": {오행: 월령계수},
          "dominant_element": "목",
          "lacking_elements": ["화"],
          "balance": "신강|신약|균형",
          "day_stem_element": "목",
          "confidence_level": "medium",
          "source": "명리학 정통 이론 기준",
        }
    """
    elements = ["목", "화", "토", "금", "수"]
    raw_counts: Dict[str, float] = {e: 0.0 for e in elements}
    
    pillars = [
        (year_stem, year_branch, 1.0),
        (month_stem, month_branch, 1.0),
        (day_stem, day_branch, 1.0),
    ]
    if hour_stem and hour_branch:
        pillars.append((hour_stem, hour_branch, 1.0))

    # 기본 집계 (천간 × 1, 지지 × 1)
    for stem, branch, _ in pillars:
        el_s = STEM_ELEMENT_MAP.get(stem, "")
        el_b = BRANCH_ELEMENT_MAP.get(branch, "")
        if el_s in raw_counts:
            raw_counts[el_s] += 1.0
        if el_b in raw_counts:
            raw_counts[el_b] += 1.0

    # 지장간 정기 부분 반영 (×0.5)
    all_branches = [year_branch, month_branch, day_branch]
    if hour_branch:
        all_branches.append(hour_branch)
    for branch in all_branches:
        jijang = JIJANGGAN.get(branch, {})
        jgi = jijang.get("정기")
        if jgi:
            el = STEM_ELEMENT_MAP.get(jgi, "")
            if el in raw_counts:
                raw_counts[el] += 0.5

    # 월령 가중치 보정
    month_strength = MONTH_ELEMENT_STRENGTH.get(month_branch, {e: 2 for e in elements})
    weighted_scores: Dict[str, float] = {}
    for el in elements:
        ms = month_strength.get(el, 2)
        # 월령 계수 반영: 왕=+0.5 extra, 사=−0.3 extra
        bonus = {4: 0.5, 3: 0.2, 2: 0.0, 1: -0.1, 0: -0.3}.get(ms, 0.0)
        weighted_scores[el] = round(raw_counts[el] + bonus, 2)
        if weighted_scores[el] < 0:
            weighted_scores[el] = 0.0

    # 일간 오행 (자신)
    day_el = STEM_ELEMENT_MAP.get(day_stem, "")
    
    # 신강/신약 판별
    # 일간을 생하거나 돕는 오행(인성+비겁) vs 일간이 생하거나 극하는 오행(식상+재성+관성)
    # 단순 기준: 일간 오행 점수 + 인성(일간을 생하는 오행) 점수
    sheng_day_el = ELEMENT_SHENG_FROM.get(day_el, "")  # 나를 생하는 오행
    day_support = weighted_scores.get(day_el, 0) + weighted_scores.get(sheng_day_el, 0)
    total_score = sum(weighted_scores.values())
    
    if total_score > 0:
        support_ratio = day_support / total_score
        if support_ratio >= 0.45:
            balance = "신강(身强)"
        elif support_ratio <= 0.30:
            balance = "신약(身弱)"
        else:
            balance = "중화(中和)"
    else:
        balance = "중화(中和)"

    dominant = max(weighted_scores, key=weighted_scores.get) if weighted_scores else None
    lacking = [e for e in elements if weighted_scores.get(e, 0) == 0]

    return {
        "raw_counts": {k: round(v, 2) for k, v in raw_counts.items()},
        "weighted_scores": weighted_scores,
        "month_strength": {e: STRENGTH_LABEL.get(month_strength.get(e, 2), "?") for e in elements},
        "dominant_element": dominant,
        "lacking_elements": lacking,
        "balance": balance,
        "day_stem_element": day_el,
        "confidence_level": "medium",
        "source": "명리학 정통 이론 기준",
        "note": "월령 득령/실령 가중치 및 지장간 정기 반영 (적천수·자평진전 기반)",
        "disclaimer": _get_academic_disclaimer(),
    }


# ─────────────────────────────────────────────
# 8. 억부용신(抑扶用神) 도출
# ─────────────────────────────────────────────

def calc_yongshin(element_strength_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    억부용신(抑扶用神) 기초 도출
    
    신강(身强): 식상·재성·관성 중 용신 선택 (일간 억제)
    신약(身弱): 인성·비겁 중 용신 선택 (일간 부조)
    중화(中和): 통관(通關) 기준으로 판단
    
    Returns:
        {
          "balance": "신강|신약|중화",
          "yongshin_element": "금",    # 용신 오행
          "hukshin_element": "목",     # 기신(忌神) 오행
          "yongshin_reason": "...",
          "confidence_level": "medium",
          "source": "현대 명리학 통계 기반",
          "disclaimer": "..."
        }
    """
    balance = element_strength_result.get("balance", "중화(中和)")
    day_el = element_strength_result.get("day_stem_element", "")
    ws = element_strength_result.get("weighted_scores", {})

    if not day_el:
        return {
            "balance": balance,
            "yongshin_element": None,
            "hukshin_element": None,
            "yongshin_reason": "일간 오행을 특정할 수 없습니다.",
            "confidence_level": "low",
            "source": "현대 명리학 통계 기반",
            "disclaimer": _get_academic_disclaimer(),
        }

    # 오행별 역할 분류 (일간 기준)
    sheng_me = ELEMENT_SHENG_FROM.get(day_el, "")    # 나를 생(生)하는 오행 = 인성
    i_sheng = ELEMENT_SHENG.get(day_el, "")           # 내가 생(生)하는 오행 = 식상
    i_ke = ELEMENT_KE.get(day_el, "")                 # 내가 극(克)하는 오행 = 재성
    ke_me = ELEMENT_KE_FROM.get(day_el, "")           # 나를 극(克)하는 오행 = 관성
    same_el = day_el                                   # 나와 같은 오행 = 비겁

    if "신강" in balance:
        # 신강: 억제 필요 — 관성>재성>식상 순 용신 후보
        candidates = [ke_me, i_ke, i_sheng]
        reason_prefix = "신강 사주로, 일간의 기운을 억제(抑)하는"
        hukshin = sheng_me  # 인성은 기신
    elif "신약" in balance:
        # 신약: 부조 필요 — 인성>비겁 순 용신 후보
        candidates = [sheng_me, same_el]
        reason_prefix = "신약 사주로, 일간의 기운을 도와주는(扶)"
        hukshin = i_ke  # 재성은 기신 (일간 소모)
    else:
        # 중화: 가장 부족한 오행 보완
        min_score = min(ws.values()) if ws else 0
        lacking = [e for e, s in ws.items() if s == min_score]
        candidates = lacking[:1] if lacking else [i_sheng]
        reason_prefix = "중화 사주로, 오행 균형을 위한"
        hukshin = max(ws, key=lambda k: ws.get(k, 0.0)) if ws else day_el

    # 후보 중 점수가 낮은 것이 우선 (보강 필요)
    yongshin = None
    for cand in candidates:
        if cand and cand in ws:
            yongshin = cand
            break

    reason = (
        f"{reason_prefix} '{yongshin}' 오행이 용신입니다. "
        f"(억부용신론 기준, {balance})"
    ) if yongshin else "용신 도출에 추가 분석이 필요합니다."

    return {
        "balance": balance,
        "yongshin_element": yongshin,
        "hukshin_element": hukshin if hukshin != yongshin else None,
        "yongshin_reason": reason,
        "confidence_level": "medium",
        "source": "현대 명리학 통계 기반",
        "note": "억부용신 기초 도출. 격국·희신·기신 종합 분석은 전문 명리사 상담 권장.",
        "disclaimer": _get_academic_disclaimer(),
    }


# ─────────────────────────────────────────────
# 9. 대운(大運) 정밀 계산
# ─────────────────────────────────────────────

def calc_daewoon_academic(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: int = 12,
    is_male: bool = True,
    count: int = 10,
) -> Dict[str, Any]:
    """
    대운(大運) 정밀 계산 — lunar_python 기반
    
    원리:
      - 양명(陽命) 남자 / 음명(陰命) 여자: 순행(順行)
      - 음명(陰命) 남자 / 양명(陽命) 여자: 역행(逆行)
      - 대운수: 출생일~다음(역행: 이전) 절기까지 일수 ÷ 3
    
    Args:
        birth_year, birth_month, birth_day: 양력 생년월일
        birth_hour: 생시 (0~23)
        is_male: 남자=True, 여자=False
        count: 대운 개수 (기본 10개)
    
    Returns:
        {
          "daewoon_list": [...],
          "is_forward": bool,
          "start_solar": "YYYY-MM-DD",
          "start_age": N,
          "method": "lunar_python",
          "confidence_level": "high",
          "source": "명리학 정통 이론 기준",
          "disclaimer": "..."
        }
    """
    try:
        from lunar_python import Solar

        solar = Solar.fromYmdHms(birth_year, birth_month, birth_day, birth_hour, 0, 0)
        lunar = solar.getLunar()
        ec = lunar.getEightChar()
        # lunar_python: getYun(1=남자, 0=여자)
        yun = ec.getYun(1 if is_male else 0)

        is_forward = yun.isForward()
        start_solar = yun.getStartSolar()
        start_age = yun.getStartYear()

        daewoon_list = []
        for i, dy in enumerate(yun.getDaYun()[:count]):
            gz = dy.getGanZhi()
            if not gz:
                continue  # 첫 대운이 빈 문자열인 경우 스킵
            stem_hj = gz[0] if len(gz) >= 1 else ""
            branch_hj = gz[1] if len(gz) >= 2 else ""
            stem_el = STEM_ELEMENT_MAP.get(stem_hj, "")
            branch_el = BRANCH_ELEMENT_MAP.get(branch_hj, "")
            jijang = JIJANGGAN.get(branch_hj, {})

            daewoon_list.append({
                "order": len(daewoon_list) + 1,
                "ganzhi": gz,
                "ganzhi_kr": (
                    HANJA_TO_KR_STEM.get(stem_hj, stem_hj) +
                    HANJA_TO_KR_BRANCH.get(branch_hj, branch_hj)
                ),
                "stem": stem_hj,
                "branch": branch_hj,
                "stem_element": stem_el,
                "branch_element": branch_el,
                "jijanggan": jijang,
                "start_year": dy.getStartYear(),
                "end_year": dy.getEndYear(),
                "start_age": dy.getStartAge(),
                "end_age": dy.getEndAge(),
            })

        return {
            "daewoon_list": daewoon_list,
            "is_forward": is_forward,
            "start_solar": start_solar.toYmd() if start_solar else None,
            "start_age": start_age,
            "method": "lunar_python",
            "confidence_level": "high",
            "source": "명리학 정통 이론 기준",
            "note": f"{'순행' if is_forward else '역행'} 대운 — lunar_python(만세력 기반) 절기 계산",
            "disclaimer": _get_academic_disclaimer(),
        }

    except ImportError:
        return {
            "daewoon_list": [],
            "error": "lunar_python 미설치 — pip install lunar-python 필요",
            "confidence_level": "low",
            "source": "명리학 정통 이론 기준",
            "disclaimer": _get_academic_disclaimer(),
        }
    except Exception as e:
        return {
            "daewoon_list": [],
            "error": str(e),
            "confidence_level": "low",
            "source": "명리학 정통 이론 기준",
            "disclaimer": _get_academic_disclaimer(),
        }


# ─────────────────────────────────────────────
# 10. 종합 학술 분석 API
# ─────────────────────────────────────────────

def get_academic_analysis(
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: Optional[int] = None,
    gender: str = "female",
    include_daewoon: bool = True,
    lang: str = "ko",
) -> Dict[str, Any]:
    """
    학술 명리학 종합 분석 — 기존 API 필드 보존 + 신규 필드 추가

    Args:
        birth_year, birth_month, birth_day: 양력 생년월일
        birth_hour: 생시 (0~23, None이면 12시 기본)
        gender: "male" | "female"
        include_daewoon: 대운 계산 포함 여부
        lang: "ko" | "ja" | "en"

    Returns dict (신규 필드, 기존 API와 병렬):
        jijanggan_info   — 각 기둥 지장간
        element_strength — 오행 강도 (월령 가중치 포함)
        gyeokguk         — 격국 판별
        yongshin         — 억부용신
        daewoon_academic — 대운 정밀 계산
        confidence_level — "high" | "medium" | "low"
        source           — 출처 명시
        disclaimer       — 학문적 참고 문구
    """
    effective_hour = birth_hour if birth_hour is not None else 12
    is_male = (gender == "male")

    # lunar_python으로 사주팔자 계산
    try:
        from lunar_python import Solar
        sol = Solar.fromYmdHms(
            birth_year, birth_month, birth_day, effective_hour, 0, 0
        )
        lun = sol.getLunar()
        ec = lun.getEightChar()

        year_gz = ec.getYear()    # e.g. "庚午"
        month_gz = ec.getMonth()  # e.g. "辛巳"
        day_gz = ec.getDay()      # e.g. "乙酉"
        hour_gz = ec.getTime()    # e.g. "癸未"

        def parse_gz(gz: str):
            if len(gz) >= 2:
                return gz[0], gz[1]
            return "", ""

        ys, yb = parse_gz(year_gz)
        ms, mb = parse_gz(month_gz)
        ds, db = parse_gz(day_gz)
        hs, hb = parse_gz(hour_gz)

        pillars_hanja = {
            "year": {"stem": ys, "branch": yb, "ganzhi": year_gz},
            "month": {"stem": ms, "branch": mb, "ganzhi": month_gz},
            "day": {"stem": ds, "branch": db, "ganzhi": day_gz},
            "hour": {"stem": hs, "branch": hb, "ganzhi": hour_gz},
        }
        calc_source = "lunar_python"

    except Exception as e:
        # 폴백: 기존 saju_engine 결과 활용 불가 시 None 반환
        pillars_hanja = None
        calc_source = "unavailable"

    if pillars_hanja is None:
        return {
            "error": "사주 계산 실패 (lunar_python 필요)",
            "confidence_level": "low",
            "source": "명리학 정통 이론 기준",
            "disclaimer": _get_academic_disclaimer(),
        }

    # 지장간 정보
    jijanggan_info = {}
    for pillar_name, pdata in pillars_hanja.items():
        branch_hj = pdata["branch"]
        jijang = JIJANGGAN.get(branch_hj, {})
        jijang_days = JIJANGGAN_DAYS.get(branch_hj, {})
        jijanggan_info[pillar_name] = {
            "branch": branch_hj,
            "branch_kr": HANJA_TO_KR_BRANCH.get(branch_hj, branch_hj),
            "jijanggan": {
                role: {
                    "stem_hanja": stem_hj,
                    "stem_kr": HANJA_TO_KR_STEM.get(stem_hj, stem_hj),
                    "element": STEM_ELEMENT_MAP.get(stem_hj, ""),
                    "days": jijang_days.get(role, 0),
                }
                for role, stem_hj in jijang.items()
            },
        }

    # 오행 강도
    ys, yb = pillars_hanja["year"]["stem"], pillars_hanja["year"]["branch"]
    ms, mb = pillars_hanja["month"]["stem"], pillars_hanja["month"]["branch"]
    ds, db = pillars_hanja["day"]["stem"], pillars_hanja["day"]["branch"]
    hs, hb = pillars_hanja["hour"]["stem"], pillars_hanja["hour"]["branch"]

    element_strength = calc_element_strength(ys, yb, ms, mb, ds, db, hs, hb)

    # 격국 판별
    ilgan = pillars_hanja["day"]["stem"]
    month_branch = pillars_hanja["month"]["branch"]
    gyeokguk = determine_gyeokguk(ilgan, month_branch)

    # 용신 도출
    yongshin = calc_yongshin(element_strength)

    # 십신 분석 (천간 4개)
    sipshin_map = {}
    for pillar_name, pdata in pillars_hanja.items():
        stem_hj = pdata["stem"]
        if stem_hj and pillar_name != "day":  # 일간 자신 제외
            sipshin_map[pillar_name] = {
                "stem": stem_hj,
                "stem_kr": HANJA_TO_KR_STEM.get(stem_hj, stem_hj),
                "sipshin": _get_sipshin(ilgan, stem_hj),
            }

    # 대운
    daewoon_result = None
    if include_daewoon:
        daewoon_result = calc_daewoon_academic(
            birth_year, birth_month, birth_day, effective_hour, is_male
        )

    return {
        # 메타
        "pillars_hanja": pillars_hanja,
        "calc_source": calc_source,
        # 지장간
        "jijanggan_info": jijanggan_info,
        # 오행 강도
        "element_strength": element_strength,
        # 십신 분석
        "sipshin_analysis": sipshin_map,
        # 격국
        "gyeokguk": gyeokguk,
        # 용신
        "yongshin": yongshin,
        # 대운
        "daewoon_academic": daewoon_result,
        # 신뢰도 및 출처
        "confidence_level": "medium",
        "source_primary": "명리학 정통 이론 기준",
        "source_secondary": "현대 명리학 통계 기반",
        "disclaimer": _get_academic_disclaimer(),
    }


# ─────────────────────────────────────────────
# 11. 헬퍼 함수
# ─────────────────────────────────────────────

def _get_academic_disclaimer() -> str:
    """학문적 참고용 표준 면책 문구"""
    return (
        "본 분석은 명리학(命理學) 이론에 기반한 학문적 참고 자료입니다. "
        "사주팔자 해석은 동양 철학의 자기이해 도구이며, "
        "의학적 진단·법률적 판단·재정 조언을 대체하지 않습니다. "
        "중요한 의사결정은 관련 전문가(의사·법률가·재무설계사)와 상담하시기 바랍니다."
    )


def get_confidence_label(confidence_level: str, lang: str = "ko") -> str:
    """신뢰도 레이블 다국어 반환"""
    labels = {
        "high": {"ko": "높음(정통 이론 기반)", "en": "High (Classical Theory)", "ja": "高(正統理論基準)"},
        "medium": {"ko": "보통(현대 명리학 기반)", "en": "Medium (Modern Theory)", "ja": "中(現代命理学基準)"},
        "low": {"ko": "낮음(참고용)", "en": "Low (Reference Only)", "ja": "低(参考用)"},
    }
    return labels.get(confidence_level, labels["medium"]).get(lang, labels["medium"]["ko"])
