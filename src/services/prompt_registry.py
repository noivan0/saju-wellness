"""
사주담 KO/JA/EN 분리 프롬프트 레지스트리
=====================================================
- 언어별 SYSTEM PROMPT 완전 분리
- 응답 스키마 언어별 필드명 정규화
- 문화권별 표현 최적화 (KO: 따뜻한 한국어 / JA: 敬語+공감 / EN: 직접적 영어)
- 프롬프트 인젝션 방어: user_message[:500] 상한 + JSON only 강제

사용법:
    from src.services.prompt_registry import PromptRegistry
    registry = PromptRegistry()
    system_msg = registry.system_prompt("ja")
    user_msg = registry.build_user_message(ctx, lang="ja")
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────
# 다국어 응답 스키마 정의
# ─────────────────────────────────────────────

RESPONSE_SCHEMA: Dict[str, Dict[str, str]] = {
    "ko": {
        "summary": "운세요약",          # 오늘/이번 주 전반적 흐름 (2~3문장)
        "element": "오행분석",          # 오행 균형·강약 해석
        "emotion": "에너지인사이트",      # 에너지 상태 자기이해 인사이트
        "advice": "오늘의조언",         # 구체적 실천 조언 1~2가지
        "astro": "별자리메시지",        # 서양+동양 통합 메시지
        "disclaimer": "법적고지",
    },
    "ja": {
        "summary": "運勢サマリー",
        "element": "五行分析",
        "emotion": "感情コーチング",
        "advice": "今日のアドバイス",
        "astro": "星座メッセージ",
        "disclaimer": "免責事項",
    },
    "en": {
        "summary": "fortune_summary",
        "element": "element_analysis",
        "emotion": "energy_insight",
        "advice": "todays_advice",
        "astro": "astrology_message",
        "disclaimer": "disclaimer",
    },
}

DISCLAIMERS: Dict[str, str] = {
    "ko": "본 내용은 명리학·점성술 관점의 자기이해 도구이며 전문적 심리상담을 대체하지 않습니다.",
    "ja": "本内容は命理学・占星術の観点の自己理解ツールであり、専門的な心理カウンセリングの代わりにはなりません。",
    "en": "This content is a self-understanding tool based on Four Pillars and astrology. It does not replace professional counseling.",
}

# ─────────────────────────────────────────────
# 언어별 SYSTEM PROMPT (완전 분리)
# ─────────────────────────────────────────────

_SYSTEM_PROMPTS: Dict[str, str] = {
    "ko": (
        "당신은 사주담(SajuDam)의 AI 사주 해석자입니다.\n"
        "명리학(사주팔자)과 서양 점성술을 통합하여 따뜻하고 공감적인 자기이해 메시지를 제공합니다.\n\n"
        "【응답 규칙】\n"
        "1. 반드시 아래 JSON 형식으로만 응답. 다른 텍스트 일절 불가.\n"
        "2. 한국어로 응답. 공감적·따뜻한 어조 유지.\n"
        "3. 운세요약: 2~3문장. 오행·절기 기반 오늘의 에너지 흐름.\n"
        "4. 오행분석: 목화토금수 균형·강약을 구체적으로. 과다/부족 오행 명시.\n"
        "5. 에너지인사이트: 오늘의 에너지와 사주를 연결한 자기이해 인사이트. 긍정적 행동 제안.\n"
        "6. 오늘의조언: 1~2개 구체적 실천사항. '오늘 ~ 해보세요' 형식.\n"
        "7. 별자리메시지: 서양 별자리 + 동양 띠 통합 메시지 1~2문장.\n"
        "8. 모든 내용은 문화·오락 목적. 심리상담/의료 진단 절대 금지.\n"
        "9. [R27 자본시장법] 재물운 상승/하락·투자·사업 결정 등 구체적 재무 어드바이스 절대 금지.\n"
        "10. [R27] '반드시', '확실히' 등 단정 예언 표현 금지. '~경향', '~살펴보시길' 등 완화 표현 사용.\n\n"
        "【출력 예시】\n"
        '{"운세요약": "...", "오행분석": "...", "에너지인사이트": "...", '
        '"오늘의조언": "...", "별자리메시지": "...", "법적고지": "..."}'
    ),
    "ja": (
        "あなたはサジュダム(SajuDam)のAI四柱推命インサイトナビゲーターです。\n"
        "四柱推命と西洋占星術を融合し、温かく共感的な自己理解メッセージを提供します。\n\n"
        "【応答ルール】\n"
        "1. 必ず下記のJSON形式のみで応答すること。その他のテキストは一切不可。\n"
        "2. 日本語で応答。敬語を使用。温かく共感的なトーン。\n"
        "3. 運勢サマリー: 2〜3文。五行・節気に基づく今日のエネルギーの流れ。\n"
        "4. 五行分析: 木火土金水のバランス・強弱を具体的に。過多/不足の五行を明示。\n"
        "5. 感情インサイト: 今日のエネルギーと四柱を繋いだ自己理解インサイト。ポジティブな行動提案。\n"
        "6. 今日のアドバイス: 1〜2個の具体的な実践事項。「今日は〜してみてください」形式。\n"
        "7. 星座メッセージ: 西洋星座+東洋干支の統合メッセージ1〜2文。\n"
        "8. すべての内容は文化・エンターテインメント目的。心理カウンセリング/医療診断は絶対禁止。\n\n"
        "【出力例】\n"
        '{"運勢サマリー": "...", "五行分析": "...", "感情インサイト": "...", '
        '"今日のアドバイス": "...", "星座メッセージ": "...", "免責事項": "..."}'
    ),
    "en": (
        "You are the AI fortune insight navigator of SajuDam.\n"
        "You combine Four Pillars (Saju/BaZi) and Western astrology to deliver warm, empathetic self-insight.\n\n"
        "【Response Rules】\n"
        "1. Respond ONLY in the JSON format below. No other text allowed.\n"
        "2. Use English. Warm, empathetic, direct tone.\n"
        "3. fortune_summary: 2~3 sentences on today's energy flow based on elements and solar terms.\n"
        "4. element_analysis: Specific Wood/Fire/Earth/Metal/Water balance. Name dominant/deficient elements.\n"
        "5. energy_insight: Self-understanding insight connecting today's energy to Four Pillars. Suggest positive action.\n"
        "6. todays_advice: 1~2 concrete action items. Format: 'Try ... today'.\n"
        "7. astrology_message: 1~2 sentences integrating Western sign + Eastern zodiac.\n"
        "8. All content is for entertainment/cultural purposes only. Never provide medical or psychological diagnosis.\n\n"
        "【Output Example】\n"
        '{"fortune_summary": "...", "element_analysis": "...", "energy_insight": "...", '
        '"todays_advice": "...", "astrology_message": "...", "disclaimer": "..."}'
    ),
}


# ─────────────────────────────────────────────
# 사주 컨텍스트 (빌더 입력)
# ─────────────────────────────────────────────

@dataclass
class SajuContext:
    """프롬프트 빌드에 필요한 최소 컨텍스트."""
    birth_year: int = 0
    birth_month: int = 0
    birth_day: int = 0
    birth_hour: Optional[int] = None
    gender: Optional[str] = None
    lang: str = "ko"

    year_pillar: str = ""
    month_pillar: str = ""
    day_pillar: str = ""
    hour_pillar: str = ""

    primary_element: str = ""
    element_distribution: Dict[str, int] = field(default_factory=dict)

    western_sign_ko: str = ""
    western_sign_en: str = ""
    western_sign_ja: str = ""
    eastern_zodiac_ko: str = ""
    eastern_zodiac_en: str = ""
    eastern_zodiac_ja: str = ""

    today_pillar: str = ""
    today_element: str = ""
    jeolgi: str = ""

    mood_score: Optional[int] = None
    mood_label: Optional[str] = None
    user_message: Optional[str] = None  # 500자 상한 강제


# ─────────────────────────────────────────────
# 프롬프트 레지스트리
# ─────────────────────────────────────────────

class PromptRegistry:
    """
    언어별 프롬프트 생성기.
    system_prompt() + build_user_message() 조합으로 사용.
    """

    SUPPORTED_LANGS = {"ko", "ja", "en"}

    def system_prompt(self, lang: str = "ko") -> str:
        """언어별 시스템 프롬프트 반환."""
        lang = lang if lang in self.SUPPORTED_LANGS else "ko"
        return _SYSTEM_PROMPTS[lang]

    def response_schema(self, lang: str = "ko") -> Dict[str, str]:
        """언어별 응답 스키마 반환."""
        lang = lang if lang in self.SUPPORTED_LANGS else "ko"
        return RESPONSE_SCHEMA[lang]

    def disclaimer(self, lang: str = "ko") -> str:
        """언어별 면책 문구."""
        return DISCLAIMERS.get(lang, DISCLAIMERS["ko"])

    def build_user_message(self, ctx: SajuContext) -> str:
        """
        사주 컨텍스트 → 언어별 USER 프롬프트 빌드.
        프롬프트 인젝션 방어: user_message 500자 상한.
        """
        lang = ctx.lang if ctx.lang in self.SUPPORTED_LANGS else "ko"
        schema = RESPONSE_SCHEMA[lang]

        # 안전한 user_message 처리
        safe_user_msg = ""
        if ctx.user_message:
            safe_user_msg = str(ctx.user_message)[:500]

        if lang == "ko":
            return self._build_ko(ctx, safe_user_msg, schema)
        elif lang == "ja":
            return self._build_ja(ctx, safe_user_msg, schema)
        else:
            return self._build_en(ctx, safe_user_msg, schema)

    def _build_ko(self, ctx: SajuContext, user_msg: str, schema: Dict[str, str]) -> str:
        elem_dist = "·".join(f"{k} {v}개" for k, v in ctx.element_distribution.items()) if ctx.element_distribution else "미입력"
        mood_str = f"현재 기분: {ctx.mood_score}/5 ({ctx.mood_label})" if ctx.mood_score else "기분 미입력"
        user_str = f"\n사용자 메시지: {user_msg}" if user_msg else ""

        return (
            f"[생년월일] {ctx.birth_year}년 {ctx.birth_month}월 {ctx.birth_day}일"
            + (f" {ctx.birth_hour}시" if ctx.birth_hour is not None else "")
            + (f" ({ctx.gender})" if ctx.gender else "")
            + f"\n[사주팔자] 연주:{ctx.year_pillar} 월주:{ctx.month_pillar} 일주:{ctx.day_pillar}"
            + (f" 시주:{ctx.hour_pillar}" if ctx.hour_pillar else "")
            + f"\n[오행] 주원소:{ctx.primary_element} | 분포:{elem_dist}"
            + f"\n[별자리] {ctx.western_sign_ko}({ctx.western_sign_en}) | 띠:{ctx.eastern_zodiac_ko}"
            + (f"\n[절기] {ctx.jeolgi}" if ctx.jeolgi else "")
            + (f"\n[오늘 일진] {ctx.today_pillar} ({ctx.today_element})" if ctx.today_pillar else "")
            + f"\n[{mood_str}]"
            + user_str
            + f"\n\n위 정보를 바탕으로 JSON 응답을 생성하세요."
            + f'\n필수 키: {list(schema.values())}'
            + f'\n법적고지 값: "{self.disclaimer("ko")}"'
        )

    def _build_ja(self, ctx: SajuContext, user_msg: str, schema: Dict[str, str]) -> str:
        elem_dist = "·".join(f"{k} {v}個" for k, v in ctx.element_distribution.items()) if ctx.element_distribution else "未入力"
        mood_str = f"現在の気分: {ctx.mood_score}/5 ({ctx.mood_label})" if ctx.mood_score else "気分未入力"
        user_str = f"\nユーザーメッセージ: {user_msg}" if user_msg else ""

        return (
            f"[生年月日] {ctx.birth_year}年{ctx.birth_month}月{ctx.birth_day}日"
            + (f" {ctx.birth_hour}時" if ctx.birth_hour is not None else "")
            + (f" ({ctx.gender})" if ctx.gender else "")
            + f"\n[四柱] 年柱:{ctx.year_pillar} 月柱:{ctx.month_pillar} 日柱:{ctx.day_pillar}"
            + (f" 時柱:{ctx.hour_pillar}" if ctx.hour_pillar else "")
            + f"\n[五行] 主元素:{ctx.primary_element} | 分布:{elem_dist}"
            + f"\n[星座] {ctx.western_sign_ja}({ctx.western_sign_en}) | 干支:{ctx.eastern_zodiac_ja}"
            + (f"\n[節気] {ctx.jeolgi}" if ctx.jeolgi else "")
            + (f"\n[今日の日柱] {ctx.today_pillar} ({ctx.today_element})" if ctx.today_pillar else "")
            + f"\n[{mood_str}]"
            + user_str
            + f"\n\n上記の情報をもとにJSON応答を生成してください。"
            + f'\n必須キー: {list(schema.values())}'
            + f'\n免責事項の値: "{self.disclaimer("ja")}"'
        )

    def _build_en(self, ctx: SajuContext, user_msg: str, schema: Dict[str, str]) -> str:
        elem_dist = ", ".join(f"{k}: {v}" for k, v in ctx.element_distribution.items()) if ctx.element_distribution else "not provided"
        mood_str = f"Current mood: {ctx.mood_score}/5 ({ctx.mood_label})" if ctx.mood_score else "mood not provided"
        user_str = f"\nUser message: {user_msg}" if user_msg else ""

        return (
            f"[Birth Date] {ctx.birth_year}-{ctx.birth_month:02d}-{ctx.birth_day:02d}"
            + (f" {ctx.birth_hour:02d}:00" if ctx.birth_hour is not None else "")
            + (f" ({ctx.gender})" if ctx.gender else "")
            + f"\n[Four Pillars] Year:{ctx.year_pillar} Month:{ctx.month_pillar} Day:{ctx.day_pillar}"
            + (f" Hour:{ctx.hour_pillar}" if ctx.hour_pillar else "")
            + f"\n[Elements] Primary:{ctx.primary_element} | Distribution:{elem_dist}"
            + f"\n[Astrology] {ctx.western_sign_en} | Eastern Zodiac:{ctx.eastern_zodiac_en}"
            + (f"\n[Solar Term] {ctx.jeolgi}" if ctx.jeolgi else "")
            + (f"\n[Today's Pillar] {ctx.today_pillar} ({ctx.today_element})" if ctx.today_pillar else "")
            + f"\n[{mood_str}]"
            + user_str
            + f"\n\nGenerate a JSON response based on the above information."
            + f"\nRequired keys: {list(schema.values())}"
            + f'\nDisclaimer value: "{self.disclaimer("en")}"'
        )

    def parse_response(self, raw: str, lang: str = "ko") -> Dict[str, Any]:
        """
        LLM 응답 JSON 파싱 + 면책 문구 강제 삽입.
        파싱 실패 시 빈 스키마 반환.
        """
        schema = RESPONSE_SCHEMA.get(lang, RESPONSE_SCHEMA["ko"])
        try:
            # JSON 블록 추출 (```json ... ``` 처리)
            text = raw.strip()
            if "```" in text:
                start = text.find("{")
                end = text.rfind("}") + 1
                text = text[start:end]
            result = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            result = {}

        # 면책 문구 강제
        disclaimer_key = schema.get("disclaimer", "disclaimer")
        result[disclaimer_key] = self.disclaimer(lang)

        return result
