"""
사주담 사용자 모델
법적: 문화·오락 서비스 (심리상담 아님)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, Index
from sqlalchemy.orm import declarative_base
import enum, datetime

Base = declarative_base()


class SubscriptionTier(enum.Enum):
    FREE = "free"
    PREMIUM_MONTHLY = "premium_monthly"
    PREMIUM_ANNUAL = "premium_annual"
    PREMIUM_PLUS = "premium_plus"  # 1회성 심층 세션


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True)
    lang = Column(String(5), default="ko")   # ko | ja | en

    # 사주 기본정보
    birth_year = Column(Integer)
    birth_month = Column(Integer)
    birth_day = Column(Integer)
    birth_hour = Column(Integer, nullable=True)
    gender = Column(String(10), nullable=True)

    subscription = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # 법적 필수
    disclaimer_accepted = Column(Boolean, default=False,
        comment="면책 문구 동의 (명리학 참고용, 심리상담 대체 아님)")
    crisis_protocol_enabled = Column(Boolean, default=True,
        comment="위기 키워드 감지 시 1393 안내")

    # P2 인덱스: 월간 에너지 집계 쿼리 성능 최적화
    __table_args__ = (
        Index("ix_users_subscription_created", "subscription", "created_at"),
    )


class InsightSession(Base):
    """
    AI 인사이트 세션 기록
    - "코칭 세션" 금지 → "인사이트 세션"
    - "상담" 금지 → "해석/분석"
    """
    __tablename__ = "insight_sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    session_type = Column(String(50))   # "daily_energy" | "decision_point" | "relationship"
    user_input = Column(Text)
    ai_response = Column(Text)
    crisis_detected = Column(Boolean, default=False)
    lang = Column(String(5), default="ko")
    disclaimer_appended = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # P2 인덱스: user_id + created_at 범위 쿼리 (월간 집계)
    __table_args__ = (
        Index("ix_insight_sessions_user_created", "user_id", "created_at"),
    )
