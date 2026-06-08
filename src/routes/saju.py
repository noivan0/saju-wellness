"""
사주팔자 API 라우터
GET  /api/saju          - 사주팔자 계산
POST /api/saju/analyze  - 사주 + AI 해석 (감정 인사이트)

법적 포지션: 문화·오락 서비스 (심리상담 대체 불가)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional
from src.api.rate_limiter import limiter  # [R71-RATE-001]

from saju_engine import (
    get_saju,
    get_daewoon,
    map_mood_to_saju,
    ELEMENT_SHENG,
    ELEMENT_KE,
)
from src.models.user import (
    SajuRequest,
    SajuAnalyzeRequest,
    SajuResponse,
    SajuAnalyzeResponse,
    MoodInsightResponse,
)

router = APIRouter(tags=["사주"])

DISCLAIMER = {
    "ko": "본 내용은 명리학적 관점의 참고 정보이며 전문적 심리상담을 대체하지 않습니다.",
    "ja": "本内容は命理学的観点の参考情報であり、専門的な心理カウンセリングの代わりにはなりません。",
    "en": "This content is for entertainment purposes only and does not replace professional psychological counseling.",
}

# ─────────────────────────────────────────────
# 오행 점수 / 성격 유형
# ─────────────────────────────────────────────

STEM_ELEMENT = ["목", "목", "화", "화", "토", "토", "금", "금", "수", "수"]
BRANCH_ELEMENT = ["수", "토", "목", "목", "토", "화", "화", "토", "금", "금", "토", "수"]
HEAVENLY_STEMS_KR = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]

# 일주 기반 성격 유형 (10천간 × 간략)
PERSONALITY_MAP = {
    "목": {
        "type": "성장형",
        "traits": ["창의적", "진취적", "친화력 강함"],
        "strength": "새로운 일을 시작하고 사람을 이끄는 힘",
        "challenge": "마무리보다 시작에 에너지 쏟는 경향",
        "career_hint": "기획·창업·교육·예술",
    },
    "화": {
        "type": "표현형",
        "traits": ["열정적", "직관적", "카리스마"],
        "strength": "감정을 밝게 표현하고 분위기를 이끄는 힘",
        "challenge": "감정 기복, 과열 주의",
        "career_hint": "마케팅·연예·리더십·디자인",
    },
    "토": {
        "type": "안정형",
        "traits": ["신뢰감", "책임감", "포용력"],
        "strength": "중심을 잡고 사람들을 안정시키는 힘",
        "challenge": "변화에 느린 적응",
        "career_hint": "경영·행정·부동산·요리",
    },
    "금": {
        "type": "완성형",
        "traits": ["원칙적", "정확함", "결단력"],
        "strength": "정밀하게 일을 마무리하는 힘",
        "challenge": "완벽주의로 인한 스트레스",
        "career_hint": "법률·의료·회계·엔지니어링",
    },
    "수": {
        "type": "탐구형",
        "traits": ["지혜로움", "적응력", "깊은 내면"],
        "strength": "깊이 생각하고 흐름을 읽는 힘",
        "challenge": "우유부단, 과도한 걱정",
        "career_hint": "연구·철학·상담·IT",
    },
}


def _calc_element_scores(eight_char: dict) -> dict:
    """8글자에서 오행 점수(%) 계산"""
    scores = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    pillars = [
        eight_char["year_pillar"],
        eight_char["month_pillar"],
        eight_char["day_pillar"],
        eight_char["hour_pillar"],
    ]
    for p in pillars:
        el = p["element"]
        scores[el["stem"]] += 10
        scores[el["branch"]] += 15
    total = sum(scores.values())
    return {k: round(v / total * 100, 1) for k, v in scores.items()}


def _assess_strength(scores: dict) -> dict:
    """오행 강약 판정"""
    avg = 20.0
    return {
        "strongest": max(scores, key=scores.get),
        "weakest": min(scores, key=scores.get),
        "dominant": [k for k, v in scores.items() if v > avg * 1.5],
        "depleted": [k for k, v in scores.items() if v < avg * 0.5],
        "balanced": all(avg * 0.7 <= v <= avg * 1.3 for v in scores.values()),
    }


def _get_personality(eight_char: dict) -> dict:
    """일주(日柱) 천간 오행 기반 성격 유형"""
    day_stem_el = eight_char["day_pillar"]["element"]["stem"]
    info = PERSONALITY_MAP.get(day_stem_el, PERSONALITY_MAP["토"])
    return {
        "day_element": day_stem_el,
        "day_glyph": eight_char["day_pillar"]["glyph"],
        **info,
    }


# ─────────────────────────────────────────────
# 라우터
# ─────────────────────────────────────────────

@router.get(
    "",
    summary="사주팔자 계산",
    description="생년월일시를 입력하면 사주팔자·오행 점수·성격 유형을 반환합니다.",
)
@limiter.limit("30/minute")  # [R71-RATE-001] DDoS/과도한 스크래핑 방어
def get_saju_endpoint(
    request: Request,
    year: int = Query(..., ge=1900, le=2100, description="생년 (양력)"),
    month: int = Query(..., ge=1, le=12, description="생월"),
    day: int = Query(..., ge=1, le=31, description="생일"),
    hour: Optional[int] = Query(None, ge=0, le=23, description="생시 (미입력 가능)"),
    minute: int = Query(0, ge=0, le=59),
    gender: str = Query("female", pattern="^(male|female)$"),
    lang: str = Query("ko", pattern="^(ko|ja|en)$"),
    longitude: Optional[float] = Query(None, ge=-180.0, le=180.0, description="[P3] 진태양시 보정용 경도"),
    city_key: Optional[str] = Query(None, description="[P3] 도시 프리셋 (seoul/tokyo/etc.)"),
):
    try:
        result = get_saju(year, month, day, hour=hour, minute=minute)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")

    # [P3] 진태양시 보정 (hour 입력 + 경도 제공 시)
    tst_info = None
    if hour is not None and (longitude is not None or city_key is not None):
        try:
            from src.engine.true_solar_time import correct_true_solar_time
            from datetime import datetime, timezone, timedelta
            birth_dt = datetime(year, month, day, hour, minute, tzinfo=timezone(timedelta(hours=9)))
            tst = correct_true_solar_time(birth_dt, longitude=longitude, city_key=city_key)
            tst_info = tst.to_dict()
            # 보정된 시주 반영
            if "four_pillars" in result and "hour" in result["four_pillars"]:
                result["four_pillars"]["hour"]["tst_correction"] = tst_info
        except Exception as e:
            tst_info = {"error": str(e)}

    ec = result["eight_char"]
    scores = _calc_element_scores(ec)
    strength = _assess_strength(scores)
    personality = _get_personality(ec)

    return {
        **result,
        "element_scores": scores,
        "element_strength": strength,
        "personality_type": personality,
        "disclaimer": DISCLAIMER.get(lang, DISCLAIMER["ko"]),
        "tst_correction": tst_info,  # [P3] 진태양시 보정 결과 (None=미적용)
    }


@router.post(
    "/analyze",
    summary="사주 + AI 해석 + 감정 인사이트",
    description="사주 계산 + 선택적 기분 체크인 + AI 인사이트를 반환합니다.",
)
@limiter.limit("10/minute")  # [R71-RATE-001] AI 호출 비용 방어 (10회/분)
def analyze_saju(request: Request, req: SajuAnalyzeRequest):
    # 1. 사주 계산
    try:
        saju_result = get_saju(req.year, req.month, req.day, hour=req.hour, minute=req.minute)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")

    ec = saju_result["eight_char"]
    scores = _calc_element_scores(ec)
    strength = _assess_strength(scores)
    personality = _get_personality(ec)
    saju_result.update({
        "element_scores": scores,
        "element_strength": strength,
        "personality_type": personality,
        "disclaimer": DISCLAIMER.get(req.lang, DISCLAIMER["ko"]),
    })

    # 2. AI 인사이트 (anthropic 패키지가 있을 때만)
    insight_result = {}
    try:
        from src.services.ai_insight import generate_daily_insight
        insight_result = generate_daily_insight(
            saju_data=saju_result,
            user_message=req.user_message or "",
            lang=req.lang,
        )
    except ImportError:
        insight_result = {
            "type": "unavailable",
            "content": "AI 해석 서비스를 사용하려면 anthropic 패키지를 설치하세요.",
        }
    except Exception as e:
        insight_result = {"type": "error", "content": str(e)}

    # 3. 감정 코칭 (기분 입력 시)
    mood_result = None
    if req.mood_level is not None:
        mood_raw = map_mood_to_saju(req.mood_level, ec)
        mood_result = {
            **mood_raw,
            "disclaimer": DISCLAIMER.get(req.lang, DISCLAIMER["ko"]),
        }

    return {
        "saju": saju_result,
        "insight": insight_result,
        "mood_insight":  mood_result,
        "mood_coaching": mood_result,   # alias — 이전 테스트 호환 (deprecated, v2에서 제거 예정)
    }
