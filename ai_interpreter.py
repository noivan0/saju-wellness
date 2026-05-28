"""
Nova Saju - AI 해석 레이어
Claude API 호출 + 감정코칭 프롬프트 설계

설계 원칙:
1. 틀려도 감정이 맞으면 이탈 없음 -> 감정 공감 최우선
2. 부정적 해석 -> 반드시 대처법과 함께
3. 실용적 액션 카드 3개 항상 포함
4. 길이: 300~500자 (너무 길면 이탈)

글로벌 프롬프트 다국어:
- 한국어 v1 (런칭)
- 일본어 v2 (6개월)
- 영어 v3 (12개월) - "Eastern Wisdom" 브랜딩
"""

from __future__ import annotations
from typing import Optional


# ─────────────────────────────────────────────
# 1. 시스템 프롬프트 (다국어)
# ─────────────────────────────────────────────

SYSTEM_PROMPTS = {

"ko": """당신은 사주와 감정을 연결하는 따뜻한 코치입니다.
사용자의 생년월일로 계산된 사주팔자를 바탕으로 오늘의 감정 상태를 해석합니다.

핵심 원칙:
- 감정 공감을 항상 먼저: 판단하지 말고 그 감정이 자연스럽다는 것을 먼저 말하세요
- 부정적 해석 시 반드시 대처법 포함
- 실용적 액션 카드 3개 항상 포함 (간결하게, 당장 할 수 있는 것)
- 길이: 300~500자 (핵심만, 너무 길면 읽지 않습니다)
- 어조: 친구 같은 따뜻함, 과학적 권위 없이, 미신처럼 단정짓지 않기
- "~할 수 있어요", "~일 수 있어요" 형태로 부드럽게
""",

"ja": """あなたは四柱推命と感情をつなぐ、温かいコーチです。
生年月日から計算された四柱八字をもとに、今日の感情状態を解釈します。

核心原則:
- 感情への共感を常に最初に: 判断せず、その感情が自然であることをまず伝えてください
- ネガティブな解釈には必ず対処法を含める
- 実用的なアクションカード3つを常に含める（簡潔に、今すぐできること）
- 長さ：200~400文字（核心だけ、長すぎると読まれません）
- 口調：友人のような温かさ、断定的にならず「~かもしれません」の形で
""",

"en": """You are a warm coach connecting Eastern astrology (BaZi/Four Pillars) with emotional wellness.
Based on the user's birth date BaZi chart, you interpret their current emotional state.

Core principles:
- Lead with emotional validation: normalize the feeling before any interpretation
- Negative readings MUST include coping strategies
- Always include exactly 3 practical action cards (brief, immediately doable)
- Length: 150~250 words (concise, or users disengage)
- Tone: warm friend, not authoritative oracle; use "may be", "could suggest", "often indicates"
- Brand voice: "Eastern Wisdom" — ancient insight, modern care
""",

}


# ─────────────────────────────────────────────
# 2. 사용자 프롬프트 템플릿
# ─────────────────────────────────────────────

USER_PROMPT_TEMPLATES = {

"ko": """
[사주 정보]
- 연주: {year_glyph} ({year_reading}) — 오행: {year_element}
- 월주: {month_glyph} ({month_reading}) — 오행: {month_element}
- 일주: {day_glyph} ({day_reading}) — 오행: {day_element}
- 시주: {hour_glyph} ({hour_reading}) — 오행: {hour_element}
- 팔자: {eight_glyphs}

[오늘의 감정 체크인]
- 기분 단계: {mood_level}/5 ({mood_label} {mood_emoji})
- 사주-감정 관계: 일주({day_element})와 기분오행({mood_element})의 {relation} 관계

[해석 요청]
아래 형식으로 따뜻하게 해석해주세요:

1. [감정 공감] 오늘의 기분이 자연스럽다는 것을 1~2문장으로 공감
2. [사주와 연결] "지금 이 감정이 사주에서 오는 이유"를 1~2문장으로 (너무 단정적이지 않게)
3. [이 시기가 끝나는 시점] 언제쯤 이 감정이 변화할 수 있는지 1문장
4. [액션 카드 3개] 지금 당장 할 수 있는 것 3가지 (한 줄씩, 구체적으로)

전체 300~500자 이내로.
""",

"ja": """
[四柱情報]
- 年柱: {year_glyph} ({year_reading}) — 五行: {year_element}
- 月柱: {month_glyph} ({month_reading}) — 五行: {month_element}
- 日柱: {day_glyph} ({day_reading}) — 五行: {day_element}
- 時柱: {hour_glyph} ({hour_reading}) — 五行: {hour_element}
- 八字: {eight_glyphs}

[今日の感情チェックイン]
- 気分レベル: {mood_level}/5 ({mood_label} {mood_emoji})
- 四柱-感情の関係: 日柱({day_element})と気分五行({mood_element})の{relation}関係

[解釈リクエスト]
以下の形式で温かく解釈してください:

1. [感情への共感] 今日の気分が自然であることを1~2文で
2. [四柱との連結] この感情が四柱から来る理由を1~2文で（断定的にならずに）
3. [この時期が終わる時点] いつごろ感情が変化するか1文で
4. [アクションカード3つ] 今すぐできること3つ（1行ずつ、具体的に）

全体200~400文字以内で。
""",

"en": """
[BaZi Chart]
- Year Pillar: {year_glyph} ({year_reading}) — Element: {year_element}
- Month Pillar: {month_glyph} ({month_reading}) — Element: {month_element}
- Day Pillar: {day_glyph} ({day_reading}) — Element: {day_element}
- Hour Pillar: {hour_glyph} ({hour_reading}) — Element: {hour_element}
- Eight Characters: {eight_glyphs}

[Today's Emotional Check-in]
- Mood Level: {mood_level}/5 ({mood_label} {mood_emoji})
- BaZi-Emotion Connection: {relation} relationship between Day Pillar ({day_element}) and Mood Element ({mood_element})

[Interpretation Request]
Please interpret warmly using this structure:

1. [Emotional Validation] 1-2 sentences: normalize today's feeling
2. [BaZi Connection] 1-2 sentences: why this emotion may be showing up now (not deterministic)
3. [When This Passes] 1 sentence: when/how this energy might shift
4. [3 Action Cards] 3 things to do right now (one line each, specific)

Keep total under 200 words.
""",

}


# ─────────────────────────────────────────────
# 3. 프롬프트 빌더
# ─────────────────────────────────────────────

def build_prompts(
    eight_char: dict,
    mood_level: int,
    mood_label: str,
    mood_emoji: str,
    mood_element: str,
    relation: str,
    lang: str = "ko",
) -> dict:
    """
    Claude API 호출용 messages 구성.

    Args:
        eight_char  : get_saju()['eight_char']
        mood_level  : 1~5
        mood_label  : "힘듦" 등
        mood_emoji  : "😢" 등
        mood_element: "금" 등
        relation    : "상생" | "상극" | "동일" | "중립"
        lang        : "ko" | "ja" | "en"

    Returns:
        {"system": str, "user": str}
        -> Claude API의 system + messages[0].content 에 각각 넣으면 됨
    """
    ec = eight_char

    def el(pillar_key):
        return ec[pillar_key]["element"]["branch"]

    variables = {
        "year_glyph":    ec["year_pillar"]["glyph"],
        "year_reading":  ec["year_pillar"]["reading"],
        "year_element":  el("year_pillar"),
        "month_glyph":   ec["month_pillar"]["glyph"],
        "month_reading": ec["month_pillar"]["reading"],
        "month_element": el("month_pillar"),
        "day_glyph":     ec["day_pillar"]["glyph"],
        "day_reading":   ec["day_pillar"]["reading"],
        "day_element":   el("day_pillar"),
        "hour_glyph":    ec["hour_pillar"]["glyph"],
        "hour_reading":  ec["hour_pillar"]["reading"],
        "hour_element":  el("hour_pillar"),
        "eight_glyphs":  ec["eight_glyphs"],
        "mood_level":    mood_level,
        "mood_label":    mood_label,
        "mood_emoji":    mood_emoji,
        "mood_element":  mood_element,
        "relation":      relation,
    }

    system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["ko"])
    user_tmpl = USER_PROMPT_TEMPLATES.get(lang, USER_PROMPT_TEMPLATES["ko"])
    user_prompt = user_tmpl.format(**variables)

    return {"system": system_prompt, "user": user_prompt.strip()}


# ─────────────────────────────────────────────
# 4. Claude API 호출 (선택적)
# ─────────────────────────────────────────────

def interpret_saju(
    eight_char: dict,
    mood_result: dict,
    lang: str = "ko",
    api_key: Optional[str] = None,
    model: str = "claude-3-5-haiku-20241022",
    max_tokens: int = 600,
) -> dict:
    """
    사주 + 감정 -> Claude AI 해석 전체 파이프라인.

    Args:
        eight_char  : get_saju()['eight_char']
        mood_result : map_mood_to_saju() 반환값
        lang        : "ko" | "ja" | "en"
        api_key     : Anthropic API key (None이면 ANTHROPIC_API_KEY 환경변수 사용)
        model       : Claude 모델 (기본 haiku — 빠르고 저렴)
        max_tokens  : 응답 최대 토큰

    Returns:
        {
          "interpretation": str,   # AI 해석 텍스트
          "prompts": dict,          # 디버그용 프롬프트
          "model": str,
          "usage": dict,
        }
    """
    prompts = build_prompts(
        eight_char   = eight_char,
        mood_level   = mood_result["mood_level"],
        mood_label   = mood_result["mood_label"],
        mood_emoji   = mood_result["mood_emoji"],
        mood_element = mood_result["day_element"],
        relation     = mood_result["relation"],
        lang         = lang,
    )

    try:
        import anthropic
        import os
        client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model       = model,
            max_tokens  = max_tokens,
            system      = prompts["system"],
            messages    = [{"role": "user", "content": prompts["user"]}],
        )
        text = response.content[0].text
        usage = {"input_tokens": response.usage.input_tokens, "output_tokens": response.usage.output_tokens}
    except ImportError:
        text = "[anthropic 미설치] 프롬프트는 빌드되었으나 API 호출 불가. pip install anthropic"
        usage = {}
    except Exception as e:
        text = f"[API 오류] {e}"
        usage = {}

    return {
        "interpretation": text,
        "prompts": prompts,
        "model": model,
        "usage": usage,
    }


# ─────────────────────────────────────────────
# 5. 빠른 테스트
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # saju_engine 임포트 (같은 디렉토리 가정)
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from saju_engine import get_saju, map_mood_to_saju

    ec_result = get_saju(1990, 1, 15, hour=10, minute=30)
    mood = map_mood_to_saju(2, ec_result["eight_char"])

    print("=== 프롬프트 미리보기 (한국어) ===")
    prompts = build_prompts(
        eight_char   = ec_result["eight_char"],
        mood_level   = mood["mood_level"],
        mood_label   = mood["mood_label"],
        mood_emoji   = mood["mood_emoji"],
        mood_element = mood["day_element"],
        relation     = mood["relation"],
        lang         = "ko",
    )
    print("[SYSTEM]")
    print(prompts["system"])
    print("[USER]")
    print(prompts["user"])

    print()
    print("=== 영어 프롬프트 ===")
    prompts_en = build_prompts(
        eight_char   = ec_result["eight_char"],
        mood_level   = mood["mood_level"],
        mood_label   = mood["mood_label"],
        mood_emoji   = mood["mood_emoji"],
        mood_element = mood["day_element"],
        relation     = mood["relation"],
        lang         = "en",
    )
    print("[USER]")
    print(prompts_en["user"])
