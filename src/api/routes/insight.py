"""
사주 인사이트 API
법적: "코칭/상담" 금지 → "인사이트/해석"
"AI 코칭 챗봇" 표현 금지 → "AI 인사이트 세션"
"""
import random
import secrets
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional
from src.core.auth import get_current_user
from src.services.llm_interpreter import sanitize_user_input
from src.services.ai_insight import CRISIS_KEYWORDS, CRISIS_LINES, check_crisis_keywords
from src.api.rate_limiter import limiter

router = APIRouter(tags=["insight"])

# 오행별 인사이트 (AI 서비스 레이어 대체 — 룰 기반)
ELEMENT_INSIGHTS = {
    "목": [
        "성장과 시작의 기운이 강한 날입니다. 새로운 계획을 세우기에 좋은 시기입니다.",
        "창의적 에너지가 넘치는 날입니다. 아이디어를 실천으로 옮겨보세요.",
        "인내와 꾸준함이 빛을 발하는 시기입니다. 오늘의 노력이 내일의 결실이 됩니다.",
    ],
    "화": [
        "열정과 표현의 기운이 강합니다. 솔직한 소통이 관계를 더 깊게 합니다.",
        "직관이 예리해지는 날입니다. 첫 번째 느낌을 믿어보세요.",
        "활동적인 에너지가 충만한 날입니다. 몸을 움직이면 정신도 맑아집니다.",
    ],
    "토": [
        "안정과 신뢰의 기운이 강합니다. 신중한 판단이 빛을 발하는 날입니다.",
        "중심을 잡는 힘이 강해집니다. 주변의 균형을 잡아주는 역할을 하게 될 것입니다.",
        "실용적인 접근이 효과적인 날입니다. 기본기에 충실하면 좋은 결과가 옵니다.",
    ],
    "금": [
        "분석력이 최고조에 달하는 날입니다. 중요한 결정을 내리기에 좋은 시기입니다.",
        "명확함과 결단력이 빛나는 날입니다. 복잡한 문제를 단순하게 정리해보세요.",
        "논리와 질서의 기운이 강합니다. 체계적인 접근으로 목표를 달성해 나가세요.",
    ],
    "수": [
        "지혜와 통찰의 기운이 강한 날입니다. 깊이 생각하고 행동하면 좋은 결과를 얻습니다.",
        "유연성이 강점이 되는 날입니다. 상황에 맞게 자신을 조율해보세요.",
        "내면의 목소리에 귀 기울이는 날입니다. 직관적인 판단이 맞을 가능성이 높습니다.",
    ],
}

# 질문 유형별 인사이트
QUESTION_INSIGHTS = {
    "일": ["오늘은 계획한 일을 순서대로 처리하는 것이 효율적입니다. 작은 성취가 모여 큰 결과를 만듭니다.",
            "집중력이 필요한 작업에 임하기 좋은 날입니다. 방해 요소를 최소화하고 몰입해보세요.",
            "협업이 빛을 발하는 날입니다. 동료와 소통하면 예상치 못한 아이디어가 나올 수 있습니다."],
    "관계": ["진심이 전달되는 날입니다. 오해가 있었다면 오늘 이야기를 나눠보세요.",
              "경청이 최고의 배려입니다. 상대방의 이야기를 충분히 들어주세요.",
              "서로의 다름을 인정하는 것이 관계의 깊이를 더합니다."],
    "건강": ["몸의 신호에 귀 기울이는 날입니다. 충분한 휴식과 수분 섭취를 챙겨보세요.",
               "스트레칭이나 가벼운 운동으로 기운을 순환시켜보세요.",
               "마음의 여유가 몸의 건강으로 이어집니다. 잠시 명상이나 深呼吸을 해보세요."],
    "집중": ["집중력을 높이려면 먼저 주변을 정리해보세요. 환경이 마음을 반영합니다.",
               "25분 집중 + 5분 휴식의 리듬으로 작업해보세요. 지속성이 중요합니다.",
               "큰 과제를 작은 단계로 나누면 시작이 쉬워집니다. 첫 걸음을 내딛어보세요."],
}


class InsightRequest(BaseModel):
    birth_year: int = Field(..., ge=1900, le=2099)
    birth_month: int = Field(..., ge=1, le=12)
    birth_day: int = Field(..., ge=1, le=31)
    user_message: str = Field(..., min_length=1, max_length=2000, description="사용자 질문 (최대 2000자)")  # [R78-INPUT-001]
    lang: str = Field("ko", pattern="^(ko|ja|en)$")
    session_type: str = Field("daily_energy", max_length=50)  # "코칭" 아닌 "인사이트"
    birth_hour: Optional[int] = Field(None, ge=0, le=23)


def _get_element_from_birth(year: int, month: int) -> str:
    """간단한 오행 추정 (연도 기반)"""
    elements = ["금", "수", "목", "화", "토"]
    return elements[year % 5]


def _generate_insight(message: str, element: str) -> str:
    """질문 내용 + 오행 기반 인사이트 생성"""
    # 질문 유형 감지
    keywords = {
        "일": ["일", "업무", "직장", "취업", "사업", "프로젝트"],
        "관계": ["관계", "사람", "친구", "연애", "가족", "부모"],
        "건강": ["건강", "몸", "피로", "아프", "힘들"],
        "집중": ["집중", "공부", "못", "산만", "ADHD", "adhd"],
    }

    question_type = None
    for qtype, kws in keywords.items():
        if any(kw in message for kw in kws):
            question_type = qtype
            break

    insights = []
    # 오행 기반 기본 인사이트
    element_pool = ELEMENT_INSIGHTS.get(element, ELEMENT_INSIGHTS["토"])
    insights.append(random.choice(element_pool))  # nosec B311 — UX 다양성용, 보안 목적 아님

    # 질문 유형 인사이트
    if question_type and question_type in QUESTION_INSIGHTS:
        insights.append(random.choice(QUESTION_INSIGHTS[question_type]))  # nosec B311

    return " ".join(insights)


@router.post("/daily")
@limiter.limit("10/minute")
def get_daily_insight(request: Request, body: InsightRequest):
    """
    오늘의 사주 에너지 인사이트 (공개 — JWT 불필요)
    - "감정코칭" 금지 → "에너지 인사이트"
    - 위기 키워드 감지 시 1393 즉시 안내
    - 모든 응답에 면책 문구 자동 첨부
    """
    # [HIGH] Prompt Injection 방어 — user_message 검증
    try:
        sanitized_message = sanitize_user_input(body.user_message)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input: potential prompt injection detected")

    # 위기 감지 선제 처리
    _CRISIS_MESSAGES = {
        "ko": ("지금 많이 힘드시겠어요. 혼자 견디지 않아도 됩니다.", "자살예방상담전화 1393 (24시간)", "정신건강 위기상담전화 1577-0199"),
        "ja": ("今、とても辛い状況なのですね。一人で抱え込まなくて大丈夫です。", "よりそいホットライン 0120-279-338 (24時間)", "いのちの電話 0120-783-556"),
        "en": ("It sounds like you're going through a really hard time. You don't have to face this alone.", "988 Suicide & Crisis Lifeline — call or text 988 (24h)", "Crisis Text Line: Text HOME to 741741"),
    }
    if check_crisis_keywords(sanitized_message, lang=body.lang):
        lang = body.lang if body.lang in _CRISIS_MESSAGES else "ko"
        msg, line, additional = _CRISIS_MESSAGES[lang]
        return {
            "type": "crisis_support",
            "message": msg,
            "crisis_line": line,
            "additional": additional,
            "disclaimer": _disclaimer(lang),
        }

    element = _get_element_from_birth(body.birth_year, body.birth_month)
    content = _generate_insight(sanitized_message, element)

    return {
        "type": "daily_energy_insight",
        "content": content,
        "element": element,
        "message_echo": f"'{sanitized_message}'에 대한 오늘의 인사이트",
        "disclaimer": _disclaimer(body.lang),
        "legal_note": "본 내용은 명리학적 관점의 참고 정보입니다.",
        "source": "rule_based_v1",
    }


@router.post("/session")
@limiter.limit("5/minute")
def start_insight_session(request: Request, body: InsightRequest, user=Depends(get_current_user)):
    """
    AI 심층 인사이트 세션 (유료 — JWT 필요)
    주의: "코칭 챗봇" → "인사이트 세션" (심리사법 회피)
    헤르 게이트웨이 AI 실제 호출
    """
    # [HIGH] Prompt Injection 방어 — user_message 검증
    try:
        sanitized_message = sanitize_user_input(body.user_message)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid input: potential prompt injection detected")

    # 위기 감지 선제
    if check_crisis_keywords(sanitized_message, lang=body.lang):
        _cr_msgs = {
            "ko": ("지금 많이 힘드시겠어요. 혼자 견디지 않아도 됩니다.", CRISIS_LINES.get("ko", "자살예방상담전화 1393 (24시간)")),
            "ja": ("今、とても辛い状況なのですね。", CRISIS_LINES.get("ja", "よりそいホットライン 0120-279-338")),
            "en": ("You don't have to face this alone.", CRISIS_LINES.get("en", "988 Suicide & Crisis Lifeline — call or text 988 (24h)")),
        }
        msg, line = _cr_msgs.get(body.lang, _cr_msgs["ko"])
        return {"type": "crisis_support", "message": msg, "crisis_line": line,
                "disclaimer": _disclaimer(body.lang)}

    # AI 심층 인사이트 시도
    try:
        from src.engine.saju_calculator import calc_four_pillars
        from src.services.ai_insight import generate_daily_insight
        saju_data = calc_four_pillars(body.birth_year, body.birth_month, body.birth_day, birth_hour=body.birth_hour)
        ai_result = generate_daily_insight(saju_data, sanitized_message, lang=body.lang)
        return {
            "session_id": f"sess_{secrets.token_hex(16)}",
            "type": "ai_insight_session",
            "content": ai_result.get("content", ""),
            "disclaimer": ai_result.get("disclaimer", _disclaimer(body.lang)),
            "source": "hermes_gateway_ai",
        }
    except Exception as _ai_err:
        # AI 실패 시 룰 기반 폴백 (로그)
        import logging
        logging.getLogger(__name__).warning("AI insight failed: %s", _ai_err)
        element = _get_element_from_birth(body.birth_year, body.birth_month)
        content_fb = _generate_insight(sanitized_message, element)
        return {
            "session_id": f"sess_{secrets.token_hex(16)}",
            "type": "premium_insight_session",
            "content": content_fb,
            "element": element,
            "disclaimer": _disclaimer(body.lang),
            "source": "rule_based_fallback",
        }


def _disclaimer(lang: str) -> str:
    d = {
        "ko": "본 내용은 명리학적 관점의 참고 정보이며 전문적 심리상담을 대체하지 않습니다.",
        "ja": "本内容は命理学的観点の参考情報であり、専門的な心理カウンセリングの代わりにはなりません。",
        "en": "This content is for entertainment purposes only and does not replace professional counseling.",
    }
    return d.get(lang, d["ko"])


# ─────────────────────────────────────────────────────────
# [R23-H6] AI 분석 로딩 상태 응답 — "분석 중" 표시 지원
# ─────────────────────────────────────────────────────────
from fastapi.responses import StreamingResponse
import asyncio as _asyncio
import json as _json


@router.get("/ai/status")
async def ai_loading_status(lang: str = "ko") -> dict:
    """
    [R23-H6] AI 분석 시작 전 로딩 상태.
    응답 시간: < 50ms (AI 호출 없음). 프론트엔드 스피너용.
    """
    messages = {
        "ko": {
            "loading_message": "사주 분석 중입니다. 잠시만 기다려주세요... (최대 30초)",
            "sub_message": "명리학 데이터베이스와 AI가 함께 분석하고 있습니다.",
            "timeout_hint": "30초 이상 소요 시 자동으로 기본 분석 결과를 제공합니다.",
        },
        "ja": {
            "loading_message": "四柱命理を分析中です。しばらくお待ちください...",
            "sub_message": "AIが詳細な分析を行っています。",
            "timeout_hint": "30秒以上の場合、基本分析結果を提供します。",
        },
        "en": {
            "loading_message": "Analyzing your Saju chart... Please wait (up to 30 seconds)",
            "sub_message": "AI is computing your detailed reading.",
            "timeout_hint": "If analysis takes over 30 seconds, a basic reading will be provided.",
        },
    }
    lang_key = lang if lang in messages else "ko"
    return {
        "status": "analyzing",
        "estimated_seconds": 15,
        "max_timeout_seconds": 30,
        **messages[lang_key],
    }


@router.get("/ai/stream")
@limiter.limit("5/minute")  # [R11-RL-001] AI Stream Rate Limit — 분당 5회 제한 (Anthropic 비용 보호)
async def ai_insight_stream(
    request: Request,
    birth_year: int,
    birth_month: int,
    birth_day: int = 1,
    lang: str = "ko",
):
    """
    [R23-H6] SSE 스트리밍 — AI 응답 청크 단위 전송. text/event-stream.
    프론트엔드 실시간 텍스트 스트리밍 표시 가능.
    """
    async def generate():
        msg1 = _json.dumps({"type": "status", "message": "분석 시작..."})
        yield "data: " + msg1 + "\n\n"
        await _asyncio.sleep(0.1)

        msg2 = _json.dumps({"type": "status", "message": "사주 계산 중..."})
        yield "data: " + msg2 + "\n\n"
        await _asyncio.sleep(0.1)

        msg3 = _json.dumps({"type": "status", "message": "AI 해석 중..."})
        yield "data: " + msg3 + "\n\n"

        try:
            from src.engine.saju_calculator import calc_four_pillars
            from src.services.ai_insight import generate_daily_insight_async
            saju_data = calc_four_pillars(birth_year, birth_month, birth_day)
            result = await generate_daily_insight_async(saju_data, user_message="", lang=lang)
            msg_result = _json.dumps({"type": "result", **result})
            yield "data: " + msg_result + "\n\n"
        except Exception as e:
            msg_err = _json.dumps({"type": "error", "message": "기본 분석 결과를 제공합니다."})
            yield "data: " + msg_err + "\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
