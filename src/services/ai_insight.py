"""
사주 AI 해석 서비스 (Claude API)
법적 주의사항:
- "감정코칭", "상담", "치료" 표현 전면 금지
- 모든 응답에 면책 문구 자동 포함
- 위기 키워드 감지 시 각국 위기상담 안내
"""
import json
import logging
import os
import asyncio
from typing import Optional

_log = logging.getLogger(__name__)

# [BLK-H3] AI 동시 호출 제한 — Anthropic 과부하/요금 폭탄 방지
# [HIGH-1] Python 3.12 RuntimeError 방지: 모듈 레벨 Semaphore 제거 → lazy init
_AI_SEMAPHORE: "asyncio.Semaphore | None" = None  # lazy — 첫 async 호출 시 현재 loop에서 생성


def _get_semaphore() -> "asyncio.Semaphore":
    """현재 실행 중인 event loop에서 Semaphore를 lazy 생성한다.
    Python 3.12+에서 모듈 레벨 Semaphore() 생성 시 RuntimeError를 방지."""
    global _AI_SEMAPHORE
    if _AI_SEMAPHORE is None:
        _AI_SEMAPHORE = asyncio.Semaphore(5)
    return _AI_SEMAPHORE

# [LOW 해소] lazy client init — ANTHROPIC_API_KEY 없어도 서버 기동 안전
_client = None  # type: ignore[assignment]


def _get_client():
    """Anthropic 클라이언트 lazy 초기화 — 헤르 내부 게이트웨이 우선."""
    global _client
    if _client is None:
        import anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("HERMES_API_KEY", "")
        base_url = os.getenv(
            "ANTHROPIC_BASE_URL",
            "https://internal-apigw-kr.hmg-corp.io/hchat-in/api/v3/claude"
        )
        _client = anthropic.Anthropic(
            api_key=api_key,
            base_url=base_url,
        )
    return _client  # type: ignore[return-value]


# [LOW 해소 ②] 다국어 위기 키워드
CRISIS_KEYWORDS: dict[str, list[str]] = {
    "ko": ["죽고 싶", "사라지고 싶", "자살", "자해", "끝내고 싶"],
    "ja": ["死にたい", "消えたい", "自殺", "自傷", "消えてしまいたい"],
    "en": ["want to die", "kill myself", "suicide", "self-harm", "end my life"],
}

# [LOW 해소 ⑤] 다국어 위기상담 라인
CRISIS_LINES: dict[str, str] = {
    "ko": "자살예방상담전화 1393 (24시간)",
    "ja": "よりそいホットライン 0120-279-338 (24時間)",
    "en": "988 Suicide & Crisis Lifeline — call or text 988 (24h)",
}

# [LOW 해소 ③] 면책 기본 상수
DISCLAIMER_DEFAULT: dict[str, str] = {
    "ko": "본 서비스는 문화·오락 목적의 명리학 자기이해 도구입니다. 심리상담·의료 행위가 아닙니다.",
    "ja": "本サービスは文化・娯楽目的の命理学的自己理解ツールです。心理カウンセリング・医療行為ではありません。",
    "en": "This service is a cultural/entertainment tool for self-understanding. It is not psychological counseling or medical advice.",
}

SYSTEM_PROMPTS: dict[str, str] = {
    "ko": """당신은 사주 명리학 전문 해석가입니다.
사용자의 사주팔자를 분석해 오늘의 에너지 흐름과 자기이해 인사이트를 제공합니다.

절대 금지:
- "감정코칭", "심리상담", "치료", "진단", "상담사" 표현 사용 금지
- 의학적/과학적 사실인 것처럼 표현 금지
- [R27 자본시장법] "재물운 상승/하락", "투자하기 좋은 날", "사업 결정 좋은 날" 등 구체적 재무·투자 어드바이스 표현 금지
- [R27] "반드시 ~이다", "확실히 ~할 것이다" 등 단정 예언 표현 금지 → "~의 경향이 있습니다", "~를 살펴보시면 좋겠습니다"로 대체

반드시 포함:
- 마지막에 면책 문구 포함: "본 서비스는 문화·오락 목적입니다. 심리상담·의료 행위가 아닙니다."
- 따뜻하고 공감적인 톤 유지""",

    # [LOW 해소 ④] ja/en 면책 지시 추가
    "ja": """あなたは四柱推命の専門家です。
運命学的な観点から、今日のエネルギーの流れと自己理解のインサイトを提供します。
心理カウンセリング、診断、治療の表現は使用しないでください。

必ず含めること:
- 最後に免責文言を含めること: "本サービスは文化・娯楽目的の自己理解ツールです。心理カウンセリング・医療行為ではありません。"
- 温かく共感的なトーンを維持してください。""",

    "en": """You are a Four Pillars of Destiny specialist.
Provide insights about today's energy flow and self-understanding from an astrological perspective.
Never use terms like 'counseling', 'therapy', 'diagnosis', or 'treatment'.

Always include:
- A disclaimer at the end: "This service is for cultural/entertainment purposes only. It is not psychological counseling or medical advice."
- Maintain a warm and empathetic tone.""",
}

# [NOTICE 해소] 모델명 환경변수화
_DEFAULT_MODEL = "claude-sonnet-4-6"  # 헤르 게이트웨이 허용 모델 (2026-05-23)


def check_crisis_keywords(text: str, lang: str = "ko") -> bool:
    """위기 키워드 감지 — 다국어 지원."""
    keywords = CRISIS_KEYWORDS.get(lang, CRISIS_KEYWORDS["ko"])
    # 영어는 대소문자 무관
    if lang == "en":
        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)
    return any(kw in text for kw in keywords)


def _safe_saju_summary(saju_data: dict) -> str:
    """
    [NOTICE 해소] saju_data 핵심 필드만 JSON 직렬화.
    dict 직접 f-string 삽입 시 prompt injection 가능 → 구조화된 형식으로 방어.
    """
    safe = {
        "year_pillar": saju_data.get("year", {}).get("pillar", ""),
        "month_pillar": saju_data.get("month", {}).get("pillar", ""),
        "day_pillar": saju_data.get("day", {}).get("pillar", ""),
        "hour_pillar": saju_data.get("hour", {}).get("pillar", "") if "hour" in saju_data else "미입력",
        "primary_element": saju_data.get("primary_element", ""),
        "element_strength": saju_data.get("element_strength", {}),
        "personality_type": saju_data.get("personality_type", {}).get("type", ""),
    }
    return json.dumps(safe, ensure_ascii=False)


async def generate_daily_insight_async(
    saju_data: dict,
    user_message: str,
    lang: str = "ko",
) -> dict:
    """
    [BLK-H3] 세마포어 적용 async 래퍼 — AI 동시 호출 최대 5개 제한.
    async 컨텍스트(FastAPI async route)에서 사용하세요.
    [HIGH-1] _get_semaphore() lazy init + get_running_loop() 사용.
    [R21-SEM-001] asyncio.timeout(30) — Semaphore 무한 대기 방지.
    """
    try:
        # [PY310-COMPAT] asyncio.timeout()는 Python 3.11+ 전용 — 이 서버는 3.10 운영 중.
        # asyncio.wait_for()로 대체(3.8+ 호환). 세마포어 획득까지 포함해 15초 상한 유지.
        async def _run():
            async with _get_semaphore():
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(
                    None, lambda: generate_daily_insight(saju_data, user_message, lang)
                )
        # [R21-SEM-001][R77-PERF-001] 15초 상한 (30→15, P95<3s SLO 목표)
        return await asyncio.wait_for(_run(), timeout=15)
    except (TimeoutError, asyncio.TimeoutError):
        return {
            "insight": "AI 서비스가 일시적으로 지연되고 있습니다. 잠시 후 다시 시도해주세요.",
            "element": "unknown",
            "disclaimer": "이 서비스는 문화/오락 목적입니다.",
            "timeout": True,
        }


def generate_daily_insight(
    saju_data: dict,
    user_message: str,
    lang: str = "ko",
) -> dict:
    """
    사주 기반 오늘의 인사이트 생성 (동기 버전)
    - "코칭/상담" 아닌 "해석/인사이트" 표현 사용
    - async 컨텍스트에서는 generate_daily_insight_async() 사용 권장
    """
    # [LOW 해소 ①] user_message 길이 상한 + 기본 injection 방어
    user_message = user_message[:500]  # prompt injection 표면적 최소화

    # [LOW 해소 ②] 다국어 위기 키워드 선제 감지
    if check_crisis_keywords(user_message, lang=lang):
        crisis_line = CRISIS_LINES.get(lang, CRISIS_LINES["ko"])
        return {
            "type": "crisis_redirect",
            "message": {
                "ko": "힘드신 마음이 느껴집니다. 전문 상담사와 이야기해보세요.",
                "ja": "つらい気持ちが伝わります。専門家に相談してみてください。",
                "en": "It sounds like you're going through a hard time. Please reach out to a professional.",
            }.get(lang, "힘드신 마음이 느껴집니다. 전문 상담사와 이야기해보세요."),
            "crisis_line": crisis_line,
            "disclaimer": saju_data.get("disclaimer", DISCLAIMER_DEFAULT.get(lang, DISCLAIMER_DEFAULT["ko"])),
        }

    # [LOW 해소 ③] disclaimer 기본 상수 폴백
    disclaimer = saju_data.get("disclaimer", DISCLAIMER_DEFAULT.get(lang, DISCLAIMER_DEFAULT["ko"]))

    # 구조화된 사주 요약 (prompt injection 방어)
    saju_summary = _safe_saju_summary(saju_data)

    system = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["ko"])
    user_prompt = (
        f"사주 정보 (JSON):\n{saju_summary}\n\n"
        f"사용자 메시지: {user_message}\n\n"
        "오늘의 에너지 흐름과 자기이해 인사이트를 제공해주세요.\n"
        "반드시 면책 문구로 마무리하세요."
    )

    # [NOTICE 해소] 모델명 환경변수화
    model = os.getenv("SAJU_AI_MODEL", _DEFAULT_MODEL)

    client = _get_client()
    # [BLK-H1] Anthropic 장애 시 정적 Fallback 응답 (3개국어)
    FALLBACK_MESSAGES = {
        "ko": "현재 AI 해석 서비스에 일시적인 장애가 있습니다. 잠시 후 다시 시도해주세요. 사주 계산 결과는 정상 제공됩니다.",
        "ja": "現在AIサービスに一時的な障害が発生しています。しばらくしてから再度お試しください。",
        "en": "The AI interpretation service is temporarily unavailable. Please try again shortly. Saju calculation results are still available.",
    }
    try:
        response = client.messages.create(
            model=model,
            max_tokens=500,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        content = response.content[0].text  # type: ignore[union-attr]
    except Exception as ai_err:
        # [BLK-H1] Anthropic API 장애 → 정적 fallback (서비스 중단 방지)
        content = FALLBACK_MESSAGES.get(lang, FALLBACK_MESSAGES["ko"])
        # 장애 로그 (PII 없음)
        _log.warning("[AI-FALLBACK] %s — static response returned", type(ai_err).__name__)
    return {
        "type": "insight",
        "content": content,
        "lang": lang,
        "disclaimer": disclaimer,
    }
