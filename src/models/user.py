"""
사주담 데이터 모델
법적 포지션: 문화·오락 서비스 (심리상담 아님)
"""
from __future__ import annotations
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import datetime


# ─────────────────────────────────────────────
# 요청 모델
# ─────────────────────────────────────────────

class SajuRequest(BaseModel):
    """사주 계산 요청"""
    year: int = Field(..., ge=1900, le=2100, description="생년 (양력)")
    month: int = Field(..., ge=1, le=12, description="생월 (양력)")
    day: int = Field(..., ge=1, le=31, description="생일 (양력)")
    hour: Optional[int] = Field(None, ge=0, le=23, description="생시 (0~23). 미입력 시 낮 12시 기본값")
    minute: int = Field(0, ge=0, le=59, description="분 (기본 0)")
    gender: str = Field("female", pattern="^(male|female)$", description="성별 (대운 계산용)")
    lang: str = Field("ko", pattern="^(ko|ja|en)$", description="응답 언어")

    @field_validator("day")
    @classmethod
    def validate_day(cls, v, info):
        # 간단한 날짜 범위 검증 (월별 세밀 검증은 datetime에서 처리)
        return v


class SajuAnalyzeRequest(BaseModel):
    """사주 해석 요청 (AI 인사이트)"""
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: Optional[int] = Field(None, ge=0, le=23)
    minute: int = Field(0, ge=0, le=59)
    gender: str = Field("female", pattern="^(male|female)$")
    lang: str = Field("ko", pattern="^(ko|ja|en)$")
    user_message: str = Field("", max_length=500, description="사용자 자유 입력 (선택)")
    mood_level: Optional[int] = Field(None, ge=1, le=5, description="현재 기분 (1=매우힘듦 ~ 5=매우좋음)")


class FortuneRequest(BaseModel):
    """일간 운세 요청"""
    year: int = Field(..., ge=1900, le=2100)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    hour: Optional[int] = Field(None, ge=0, le=23)
    lang: str = Field("ko", pattern="^(ko|ja|en)$")
    target_date: Optional[str] = Field(
        None,
        description="운세 대상 날짜 (YYYY-MM-DD). 미입력 시 오늘"
    )


# ─────────────────────────────────────────────
# 응답 모델
# ─────────────────────────────────────────────

class PillarResponse(BaseModel):
    """사주 한 기둥 응답"""
    glyph: str       # 甲子
    reading: str     # 갑자
    element: dict    # {stem, branch, yin_yang_stem, yin_yang_branch}


class EightCharResponse(BaseModel):
    """사주팔자 8글자 응답"""
    year_pillar: PillarResponse
    month_pillar: PillarResponse
    day_pillar: PillarResponse
    hour_pillar: PillarResponse
    eight_glyphs: str  # 甲子乙丑...
    stems: List[str]
    branches: List[str]


class SajuResponse(BaseModel):
    """사주 계산 응답"""
    eight_char: dict
    hour_unknown: bool
    hour_variants: Optional[List[dict]] = None
    method: str       # "lunar-python" | "fallback"
    note: str
    element_scores: dict           # {목,화,토,금,수: 점수%}
    element_strength: dict         # strongest/weakest/dominant/depleted/balanced
    personality_type: dict         # 일주 기반 성격 유형
    disclaimer: str


class MoodInsightResponse(BaseModel):
    """기분 체크인 + 사주 기반 감정 안내"""
    mood_level: int
    mood_label: str
    mood_emoji: str
    saju_reason: str
    ending_point: str
    action_hints: List[str]
    day_element: str
    relation: str
    disclaimer: str
    crisis_redirect: Optional[dict] = None  # 위기 키워드 감지 시


class FortuneResponse(BaseModel):
    """일간 운세 응답"""
    target_date: str
    daily_pillar: dict      # 오늘의 일주
    element_relation: str   # 나의 일주 × 오늘 일진 관계
    energy_flow: str        # 에너지 흐름 설명
    action_cards: List[str] # 추천 액션 3개
    lucky_element: str
    caution_element: str
    disclaimer: str


class SajuAnalyzeResponse(BaseModel):
    """사주 AI 해석 응답"""
    saju: dict
    insight: dict           # generate_daily_insight 결과
    mood_insight: Optional[dict] = None  # mood_level 입력 시


# ─────────────────────────────────────────────
# 공통 응답
# ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    service: str
    legal: str
    version: str


# ─────────────────────────────────────────────
# 유저 모델 (미래 확장용 — 현재 DB 불필요)
# ─────────────────────────────────────────────

class User(BaseModel):
    """앱 사용자 (익명 포함)"""
    user_id: str = Field(..., description="UUID 또는 디바이스 ID")
    lang: str = Field("ko")
    subscription_tier: str = Field("free", pattern="^(free|basic|premium)$")
    birth_year: Optional[int] = None
    birth_month: Optional[int] = None
    birth_day: Optional[int] = None
    birth_hour: Optional[int] = None
    gender: Optional[str] = None
    created_at: Optional[str] = None


class SajuReading(BaseModel):
    """사주 독해 결과 저장 모델"""
    reading_id: str
    user_id: str
    birth_date: str          # ISO 8601
    eight_glyphs: str
    element_scores: dict
    method: str
    created_at: str
    lang: str = "ko"
    mood_level: Optional[int] = None
