"""
일간 운세 API 라우터
GET /api/fortune/daily  - 오늘(또는 특정일) 운세

법적 포지션: 문화·오락 서비스 (점술/심리상담 아님)
"""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
import datetime

from saju_engine import get_saju, ELEMENT_SHENG, ELEMENT_KE, MOOD_MAP, ACTION_MAP, DEFAULT_ACTIONS
from src.api.rate_limiter import limiter  # [R71-RATE-001] DDoS/비용 방어

router = APIRouter(tags=["운세"])

DISCLAIMER = {
    "ko": "본 내용은 명리학적 관점의 참고 정보이며 전문적 심리상담을 대체하지 않습니다.",
    "ja": "本内容は命理学的観点の参考情報であり、専門的な心理カウンセリングの代わりにはなりません。",
    "en": "This content is for entertainment purposes only and does not replace professional psychological counseling.",
}

# 오행별 에너지 흐름 설명
ENERGY_FLOW_MAP = {
    "비화": {
        "ko": "나의 기운과 오늘의 일진이 같은 흐름이에요. 자신감 있게 움직이기 좋은 날입니다.",
        "ja": "今日のエネルギーはあなたの本質と共鳴しています。自信を持って動きやすい日です。",
        "en": "Today's energy resonates with your core element. A good day to move with confidence.",
    },
    "상생(생함)": {
        "ko": "나의 기운이 오늘의 에너지를 키워주는 흐름이에요. 베풀고 도와주는 역할이 빛나는 날입니다.",
        "ja": "あなたのエネルギーが今日の流れを育てています。与えることが輝く日です。",
        "en": "Your energy nurtures today's flow. A day when giving and supporting shines.",
    },
    "상생(받음)": {
        "ko": "오늘의 일진이 나를 응원하는 흐름이에요. 에너지를 받아 하고 싶은 일을 추진하기 좋습니다.",
        "ja": "今日のエネルギーがあなたを後押ししています。やりたいことを推進するのに良い日です。",
        "en": "Today's energy supports you. A good day to pursue what you've been wanting to do.",
    },
    "상극(극함)": {
        "ko": "나의 기운이 오늘의 흐름과 부딪히는 날이에요. 신중하게, 한 발씩 나아가는 게 유리합니다.",
        "ja": "今日の流れはあなたのエネルギーと緊張関係にあります。慎重に一歩ずつ進むのが賢明です。",
        "en": "Some tension between your energy and today's flow. Proceed carefully and steadily.",
    },
    "상극(받음)": {
        "ko": "오늘 일진의 기운이 내 에너지에 자극을 주는 날이에요. 자극을 성장의 계기로 삼아보세요.",
        "ja": "今日のエネルギーがあなたに刺激を与えています。その刺激を成長のきっかけにしてください。",
        "en": "Today's energy challenges yours. Use the friction as a catalyst for growth.",
    },
    "무관": {
        "ko": "오늘 일진과 나의 기운이 독립적으로 작용하는 날이에요. 내 페이스대로 움직이면 됩니다.",
        "ja": "今日のエネルギーとあなたのエネルギーは独立して動いています。自分のペースで動きましょう。",
        "en": "Your energy and today's flow operate independently. Simply move at your own pace.",
    },
}

LUCKY_ELEMENT_MSG = {
    "목": {"ko": "목(木) — 녹색 계열, 동쪽 방향", "ja": "木 — 緑系、東方向", "en": "Wood — green tones, east direction"},
    "화": {"ko": "화(火) — 붉은 계열, 남쪽 방향", "ja": "火 — 赤系、南方向", "en": "Fire — red tones, south direction"},
    "토": {"ko": "토(土) — 황토색 계열, 중앙", "ja": "土 — 黄土色系、中央", "en": "Earth — earthy tones, center"},
    "금": {"ko": "금(金) — 흰색/은색 계열, 서쪽 방향", "ja": "金 — 白・銀系、西方向", "en": "Metal — white/silver tones, west direction"},
    "수": {"ko": "수(水) — 검은색/파란색 계열, 북쪽 방향", "ja": "水 — 黒・青系、北方向", "en": "Water — dark/blue tones, north direction"},
}

ACTION_CARDS_MULTILANG = {
    # 목 + 좋음 → 한국어 액션 카드 예시 (English/Japanese expand later)
    "목": {
        "ko": ["자연 속에서 짧은 산책", "창의적인 아이디어 메모하기", "새로운 계획 한 줄 시작"],
        "en": ["Short walk in nature", "Jot down a creative idea", "Start one line of a new plan"],
        "ja": ["自然の中を短く散歩", "창의적인アイデアをメモ", "新しい計画を一行書いてみる"],
    },
    "화": {
        "ko": ["좋아하는 음악 크게 듣기", "따뜻한 음식 한 끼 챙기기", "오늘의 감정 한 줄 기록"],
        "en": ["Play your favorite music loud", "Enjoy a warm, nourishing meal", "Write one sentence about today's feeling"],
        "ja": ["好きな音楽を大音量で", "温かい食事を一食しっかり", "今日の気持ちを一行記録"],
    },
    "토": {
        "ko": ["오늘 할 일 3가지만 정하기", "주변 정리정돈 5분", "규칙적인 식사 챙기기"],
        "en": ["Pick just 3 tasks for today", "5 minutes of tidying up", "Have a regular, balanced meal"],
        "ja": ["今日のタスクを3つだけ決める", "5分間の片付け", "規則正しい食事を一食"],
    },
    "금": {
        "ko": ["불필요한 파일·물건 1개 정리", "오늘 완료한 일 체크리스트", "10분 조용한 집중 시간"],
        "en": ["Clear out one unnecessary item", "Check off completed tasks", "10 minutes of quiet focused time"],
        "ja": ["不要なものを一つ整理", "今日の完了タスクをチェック", "10分の静かな集中時間"],
    },
    "수": {
        "ko": ["오늘 느낀 것 일기로 기록", "충분한 수분 섭취", "새로운 것 하나 배워보기"],
        "en": ["Write a journal entry about today", "Stay well hydrated", "Learn one new small thing"],
        "ja": ["今日感じたことを日記に記録", "水分をしっかり摂る", "何か新しいことを一つ学ぶ"],
    },
}


def _get_element_relation(e1: str, e2: str) -> str:
    """오행 관계 판정 (6종)"""
    if e1 == e2:
        return "비화"
    if ELEMENT_SHENG.get(e1) == e2:
        return "상생(생함)"
    if ELEMENT_SHENG.get(e2) == e1:
        return "상생(받음)"
    if ELEMENT_KE.get(e1) == e2:
        return "상극(극함)"
    if ELEMENT_KE.get(e2) == e1:
        return "상극(받음)"
    return "무관"


@router.get(
    "/daily",
    summary="일간 운세",
    description="생년월일시와 오늘 날짜를 기반으로 에너지 흐름·행운 오행·액션 카드를 반환합니다.",
)
@limiter.limit("30/minute")  # [R71-RATE-001] DDoS/과도한 스크래핑 방어
def get_daily_fortune(
    request: Request,
    year: int = Query(..., ge=1900, le=2100, description="생년 (양력)"),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: Optional[int] = Query(None, ge=0, le=23),
    lang: str = Query("ko", pattern="^(ko|ja|en)$"),
    target_date: Optional[str] = Query(
        None,
        description="운세 날짜 (YYYY-MM-DD). 미입력 시 오늘(KST)"
    ),
):
    # 1. 운세 대상 날짜 파싱
    if target_date and isinstance(target_date, str):
        try:
            td = datetime.date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="target_date 형식 오류. YYYY-MM-DD 사용")
    else:
        import pytz
        kst = pytz.timezone("Asia/Seoul")
        td = datetime.datetime.now(kst).date()

    # 2. 나의 사주 계산
    try:
        my_saju = get_saju(year, month, day, hour=hour)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")

    my_day_el = my_saju["eight_char"]["day_pillar"]["element"]["branch"]

    # 3. 오늘(target_date)의 일주 계산
    try:
        today_saju = get_saju(td.year, td.month, td.day, hour=12)
    except Exception as e:
        raise HTTPException(status_code=500, detail="오늘 일주 계산 중 오류가 발생했습니다.")

    today_day_el = today_saju["eight_char"]["day_pillar"]["element"]["branch"]
    today_pillar = today_saju["eight_char"]["day_pillar"]

    # 4. 에너지 흐름 분석
    relation = _get_element_relation(my_day_el, today_day_el)
    energy_flow = ENERGY_FLOW_MAP.get(relation, ENERGY_FLOW_MAP["무관"]).get(lang, "")

    # 5. 행운/주의 오행
    lucky_el = ELEMENT_SHENG.get(my_day_el, my_day_el)   # 내 오행이 생하는 오행 = 에너지 방향
    caution_el = ELEMENT_KE.get(my_day_el, my_day_el)     # 내 오행이 극하는 오행 = 과잉 주의

    # 6. 액션 카드
    action_pool = ACTION_CARDS_MULTILANG.get(my_day_el, ACTION_CARDS_MULTILANG["토"])
    action_cards = action_pool.get(lang, action_pool["ko"])

    return {
        "target_date": td.isoformat(),
        "daily_pillar": {
            "glyph": today_pillar["glyph"],
            "reading": today_pillar["reading"],
            "element": today_pillar["element"],
        },
        "my_day_element": my_day_el,
        "element_relation": relation,
        "energy_flow": energy_flow,
        "action_cards": action_cards,
        "lucky_element": LUCKY_ELEMENT_MSG.get(lucky_el, {}).get(lang, lucky_el),
        "caution_element": LUCKY_ELEMENT_MSG.get(caution_el, {}).get(lang, caution_el),
        "disclaimer": DISCLAIMER.get(lang, DISCLAIMER["ko"]),
    }
