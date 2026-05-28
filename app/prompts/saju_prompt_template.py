"""
사주담 통합 프롬프트 템플릿
사주팔자 + 오행 + 에너지인사이트 + 점성술 통합 표준 프롬프트 생성기

응답 포맷: {운세요약, 오행분석, 에너지인사이트, 오늘의조언, 별자리메시지} JSON

사용법:
    from app.prompts.saju_prompt_template import build_saju_prompt, SajuResponseSchema
    prompt = build_saju_prompt(ctx)
    # → LLM에 전달
    # 응답은 SajuResponseSchema 구조로 파싱
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
import json


# ─────────────────────────────────────────────
# 응답 스키마 (JSON 포맷 표준화)
# ─────────────────────────────────────────────

@dataclass
class FortuneResponseSchema:
    """
    LLM 응답 표준 스키마
    모든 사주 관련 AI 응답은 이 구조를 따름
    """
    운세요약: str = ""          # 오늘/이번 주의 전반적 운세 흐름 (2~3문장)
    오행분석: str = ""          # 오행 균형·강약 해석 (목화토금수 관점)
    에너지인사이트: str = ""     # 현재 에너지 상태에 맞는 자기이해 인사이트
    오늘의조언: str = ""        # 구체적 실천 행동 조언 (1~2가지)
    별자리메시지: str = ""      # 서양 별자리 + 동양 띠 통합 메시지
    disclaimer: str = "본 내용은 명리학·점성술 관점의 자기이해 도구이며 전문적 심리상담을 대체하지 않습니다."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FortuneResponseSchema":
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in d.items() if k in valid_keys}
        return cls(**filtered)

    @classmethod
    def from_json(cls, json_str: str) -> "FortuneResponseSchema":
        try:
            d = json.loads(json_str)
            return cls.from_dict(d)
        except (json.JSONDecodeError, TypeError):
            return cls()


# ─────────────────────────────────────────────
# 프롬프트 컨텍스트 (입력 데이터 컨테이너)
# ─────────────────────────────────────────────

@dataclass
class SajuPromptContext:
    """사주 프롬프트 생성에 필요한 컨텍스트 데이터"""
    # 기본 출생 정보
    birth_year: int = 0
    birth_month: int = 0
    birth_day: int = 0
    birth_hour: Optional[int] = None
    gender: Optional[str] = None
    lang: str = "ko"

    # 사주팔자 (4기둥)
    year_pillar: str = ""       # 예: "甲子"
    month_pillar: str = ""      # 예: "庚午"
    day_pillar: str = ""        # 예: "丁亥"
    hour_pillar: str = ""       # 예: "壬子" (선택)

    # 오행 정보
    primary_element: str = ""   # 주 오행 (목/화/토/금/수)
    element_distribution: Dict[str, int] = field(default_factory=dict)  # {'목': 2, '화': 3, ...}
    element_balance: str = ""   # balanced / moderate / imbalanced

    # 일주 해석
    day_pillar_personality: str = ""
    day_pillar_strengths: List[str] = field(default_factory=list)
    day_pillar_challenges: List[str] = field(default_factory=list)

    # 점성술 정보
    western_sign_ko: str = ""   # 예: "양자리"
    western_sign_en: str = ""   # 예: "Aries"
    eastern_zodiac_ko: str = "" # 예: "말"
    eastern_zodiac_en: str = "" # 예: "Horse"
    lunar_year: Optional[int] = None
    lunar_month: Optional[int] = None
    lunar_day: Optional[int] = None

    # 감정/기분 정보 (선택)
    mood_score: Optional[int] = None        # 1(매우힘듦) ~ 5(매우좋음)
    mood_label: Optional[str] = None        # 예: "보통"
    user_message: Optional[str] = None      # 사용자 입력 메시지

    # 오늘 일진
    today_pillar: str = ""
    today_element: str = ""


# ─────────────────────────────────────────────
# 언어별 프롬프트 시스템 메시지
# ─────────────────────────────────────────────

_SYSTEM_MESSAGES = {
    "ko": (
        "당신은 사주담(SajuDam)의 AI 사주 해석자입니다. "
        "명리학(사주팔자)과 서양 점성술을 통합하여 따뜻하고 공감적인 자기이해 메시지를 제공합니다. "
        "모든 내용은 문화·오락 서비스이며 심리상담·의료를 대체하지 않습니다. "
        "응답은 반드시 지정된 JSON 형식으로만 반환하세요."
    ),
    "ja": (
        "あなたはサジュダム(SajuDam)のAI四柱推命インサイトナビゲーターです。"
        "四柱推命と西洋占星術を融合し、温かく共感的な自己理解メッセージを提供します。"
        "すべての内容は文化・エンターテインメントサービスであり、"
        "心理カウンセリング・医療の代替ではありません。"
        "応答は必ず指定のJSON形式でのみ返してください。"
    ),
    "en": (
        "You are the AI fortune insight navigator of SajuDam. "
        "You integrate Four Pillars (Saju) and Western astrology to provide warm, empathetic self-understanding messages. "
        "All content is a cultural entertainment service and does not replace psychological counseling or medical advice. "
        "Always respond only in the specified JSON format."
    ),
}

# ─────────────────────────────────────────────
# JSON 응답 포맷 스키마 (프롬프트 내 지시용)
# ─────────────────────────────────────────────

_RESPONSE_FORMAT_KO = """{
  "운세요약": "오늘/이번 주의 전반적 운세 흐름 (2~3문장, 사주 오행 기반)",
  "오행분석": "오행 균형·강약 해석, 부족한 오행 보완 방법 제안",
  "에너지인사이트": "현재 에너지 상태에 맞는 자기이해 인사이트와 긍정적 제안",
  "오늘의조언": "구체적이고 실천 가능한 오늘의 행동 조언 1~2가지",
  "별자리메시지": "서양 별자리 + 동양 띠(12지신) 통합 메시지 (동서양 에너지 융합)",
  "disclaimer": "본 내용은 명리학·점성술 관점의 자기이해 도구이며 전문적 심리상담을 대체하지 않습니다."
}"""

_RESPONSE_FORMAT_JA = """{
  "運勢サマリー": "今日/今週の全体的な運勢の流れ（2〜3文、四柱五行ベース）",
  "五行分析": "五行のバランス・強弱の解釈、不足する五行の補完方法の提案",
  "感情インサイト": "現在のエネルギー状態に合った自己理解のインサイトとポジティブな提案",
  "今日のアドバイス": "具体的で実践可能な今日の行動アドバイス1〜2つ",
  "星座メッセージ": "西洋星座＋東洋の干支（十二支）統合メッセージ",
  "disclaimer": "本内容は命理学・占星術的観点の自己理解ツールであり、専門的な心理カウンセリングの代わりにはなりません。"
}"""

_RESPONSE_FORMAT_EN = """{
  "fortune_summary": "Overall fortune flow for today/this week (2-3 sentences, based on Five Elements)",
  "five_elements_analysis": "Analysis of Five Elements balance/imbalance, suggestions for補completing lacking elements",
  "energy_insight": "Self-understanding insights and positive suggestions matching current energy state",
  "today_advice": "1-2 specific and actionable behavioral advice for today",
  "zodiac_message": "Integrated message combining Western zodiac and Eastern 12 zodiac animals",
  "disclaimer": "This is a self-understanding tool based on Four Pillars and astrology. It does not replace professional counseling."
}"""

_RESPONSE_FORMATS = {
    "ko": _RESPONSE_FORMAT_KO,
    "ja": _RESPONSE_FORMAT_JA,
    "en": _RESPONSE_FORMAT_EN,
}


# ─────────────────────────────────────────────
# 프롬프트 빌더
# ─────────────────────────────────────────────

def build_saju_prompt(ctx: SajuPromptContext) -> Dict[str, str]:
    """
    사주팔자 + 오행 + 점성술 통합 프롬프트 생성

    Returns:
        {
            "system": "시스템 메시지",
            "user": "사용자 프롬프트 (컨텍스트 포함)",
            "response_format": "JSON 응답 형식 스키마"
        }
    """
    lang = ctx.lang if ctx.lang in ("ko", "ja", "en") else "ko"
    system = _SYSTEM_MESSAGES[lang]
    response_format = _RESPONSE_FORMATS[lang]

    if lang == "ko":
        user = _build_user_prompt_ko(ctx)
    elif lang == "ja":
        user = _build_user_prompt_ja(ctx)
    else:
        user = _build_user_prompt_en(ctx)

    return {
        "system": system,
        "user": user,
        "response_format": response_format,
        "lang": lang,
    }


def _build_user_prompt_ko(ctx: SajuPromptContext) -> str:
    """한국어 사용자 프롬프트 조립"""
    lines = [
        "## 사용자 사주 분석 요청",
        "",
        "### 📅 출생 정보",
        f"- 생년월일: {ctx.birth_year}년 {ctx.birth_month}월 {ctx.birth_day}일"
        + (f" {ctx.birth_hour}시" if ctx.birth_hour is not None else " (시각 미입력)"),
        f"- 성별: {ctx.gender or '미입력'}",
        "",
        "### 🀄 사주팔자 (四柱八字)",
        f"- 연주(年柱): {ctx.year_pillar or '계산 중'}",
        f"- 월주(月柱): {ctx.month_pillar or '계산 중'}",
        f"- 일주(日柱): {ctx.day_pillar or '계산 중'}" + (" ← 핵심 기준" if ctx.day_pillar else ""),
        f"- 시주(時柱): {ctx.hour_pillar or '미입력'}",
        "",
        "### 🌿 오행 분포",
        f"- 주 오행: {ctx.primary_element or '계산 중'}",
    ]

    if ctx.element_distribution:
        dist_str = ", ".join(f"{k}:{v}" for k, v in ctx.element_distribution.items())
        lines.append(f"- 오행 분포: {dist_str}")
    if ctx.element_balance:
        lines.append(f"- 균형 상태: {ctx.element_balance}")
    if ctx.day_pillar_personality:
        lines.append(f"- 일주 성격: {ctx.day_pillar_personality}")
    if ctx.day_pillar_strengths:
        lines.append(f"- 강점: {', '.join(ctx.day_pillar_strengths)}")
    if ctx.day_pillar_challenges:
        lines.append(f"- 과제: {', '.join(ctx.day_pillar_challenges)}")

    lines += [
        "",
        "### ⭐ 점성술 정보",
        f"- 서양 별자리: {ctx.western_sign_ko or '계산 중'} ({ctx.western_sign_en or ''})",
        f"- 동양 띠 (12지신): {ctx.eastern_zodiac_ko or '계산 중'} ({ctx.eastern_zodiac_en or ''})",
    ]

    if ctx.lunar_year:
        lines.append(f"- 음력 생일: {ctx.lunar_year}년 {ctx.lunar_month}월 {ctx.lunar_day}일")

    lines += ["", "### 🌙 오늘 일진"]
    if ctx.today_pillar:
        lines.append(f"- 오늘 일진: {ctx.today_pillar} ({ctx.today_element} 기운)")
    else:
        lines.append("- 오늘 일진: 시스템 계산 기준")

    if ctx.mood_score is not None:
        lines += [
            "",
            "### 💭 현재 감정 상태",
            f"- 기분 점수: {ctx.mood_score}/5 ({ctx.mood_label or ''})",
        ]
        if ctx.user_message:
            lines.append(f"- 사용자 메시지: \"{ctx.user_message}\"")

    lines += [
        "",
        "### 📋 응답 지시",
        "위 정보를 바탕으로 다음 JSON 형식으로만 응답하세요:",
        "```json",
        _RESPONSE_FORMAT_KO,
        "```",
        "",
        "⚠️ 주의: 심리상담, 의료 진단, 구체적 투자/재무 조언은 절대 포함하지 마세요.",
        "모든 내용은 긍정적·성장 지향적 자기이해 관점으로 작성하세요.",
    ]

    return "\n".join(lines)


def _build_user_prompt_ja(ctx: SajuPromptContext) -> str:
    """일본어 사용자 프롬프트 조립"""
    lines = [
        "## ユーザーの四柱分析リクエスト",
        "",
        "### 📅 生年月日情報",
        f"- 生年月日: {ctx.birth_year}年{ctx.birth_month}月{ctx.birth_day}日"
        + (f" {ctx.birth_hour}時" if ctx.birth_hour is not None else " (時刻未入力)"),
        f"- 性別: {ctx.gender or '未入力'}",
        "",
        "### 🀄 四柱八字",
        f"- 年柱: {ctx.year_pillar or '計算中'}",
        f"- 月柱: {ctx.month_pillar or '計算中'}",
        f"- 日柱: {ctx.day_pillar or '計算中'}",
        f"- 時柱: {ctx.hour_pillar or '未入力'}",
        "",
        "### 🌿 五行分布",
        f"- 主五行: {ctx.primary_element or '計算中'}",
    ]

    if ctx.element_distribution:
        dist_str = "、".join(f"{k}:{v}" for k, v in ctx.element_distribution.items())
        lines.append(f"- 五行分布: {dist_str}")
    if ctx.day_pillar_personality:
        lines.append(f"- 日柱性格: {ctx.day_pillar_personality}")

    lines += [
        "",
        "### ⭐ 占星術情報",
        f"- 西洋星座: {ctx.western_sign_ko or '計算中'} ({ctx.western_sign_en or ''})",
        f"- 東洋干支: {ctx.eastern_zodiac_ko or '計算中'} ({ctx.eastern_zodiac_en or ''})",
    ]

    if ctx.mood_score is not None:
        lines += [
            "",
            "### 💭 現在の感情状態",
            f"- 気分スコア: {ctx.mood_score}/5 ({ctx.mood_label or ''})",
        ]
        if ctx.user_message:
            lines.append(f"- ユーザーメッセージ: \"{ctx.user_message}\"")

    lines += [
        "",
        "### 📋 応答指示",
        "上記情報を基に以下のJSON形式のみで応答してください:",
        "```json",
        _RESPONSE_FORMAT_JA,
        "```",
    ]

    return "\n".join(lines)


def _build_user_prompt_en(ctx: SajuPromptContext) -> str:
    """영어 사용자 프롬프트 조립"""
    lines = [
        "## User Saju Analysis Request",
        "",
        "### 📅 Birth Information",
        f"- Date of Birth: {ctx.birth_year}/{ctx.birth_month:02d}/{ctx.birth_day:02d}"
        + (f" {ctx.birth_hour:02d}:00" if ctx.birth_hour is not None else " (birth hour unknown)"),
        f"- Gender: {ctx.gender or 'not specified'}",
        "",
        "### 🀄 Four Pillars (Saju Pallja)",
        f"- Year Pillar: {ctx.year_pillar or 'calculating...'}",
        f"- Month Pillar: {ctx.month_pillar or 'calculating...'}",
        f"- Day Pillar: {ctx.day_pillar or 'calculating...'}" + (" ← Key Reference" if ctx.day_pillar else ""),
        f"- Hour Pillar: {ctx.hour_pillar or 'not provided'}",
        "",
        "### 🌿 Five Elements Distribution",
        f"- Primary Element: {ctx.primary_element or 'calculating...'}",
    ]

    if ctx.element_distribution:
        dist_str = ", ".join(f"{k}:{v}" for k, v in ctx.element_distribution.items())
        lines.append(f"- Distribution: {dist_str}")
    if ctx.element_balance:
        lines.append(f"- Balance: {ctx.element_balance}")
    if ctx.day_pillar_personality:
        lines.append(f"- Day Pillar Personality: {ctx.day_pillar_personality}")

    lines += [
        "",
        "### ⭐ Astrology Information",
        f"- Western Zodiac: {ctx.western_sign_en or 'calculating...'} ({ctx.western_sign_ko or ''})",
        f"- Eastern Zodiac (12 Animals): {ctx.eastern_zodiac_en or 'calculating...'} ({ctx.eastern_zodiac_ko or ''})",
    ]

    if ctx.lunar_year:
        lines.append(f"- Lunar Birthday: {ctx.lunar_year}/{ctx.lunar_month}/{ctx.lunar_day}")

    if ctx.mood_score is not None:
        lines += [
            "",
            "### 💭 Current Emotional State",
            f"- Mood Score: {ctx.mood_score}/5 ({ctx.mood_label or ''})",
        ]
        if ctx.user_message:
            lines.append(f"- User Message: \"{ctx.user_message}\"")

    lines += [
        "",
        "### 📋 Response Instructions",
        "Based on the above information, respond ONLY in the following JSON format:",
        "```json",
        _RESPONSE_FORMAT_EN,
        "```",
        "",
        "⚠️ DO NOT include psychological counseling, medical diagnosis, or specific financial advice.",
        "Frame all content from a positive, growth-oriented self-understanding perspective.",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 편의 함수: 컨텍스트 자동 조립
# ─────────────────────────────────────────────

def build_context_from_saju_result(
    saju_result: Dict[str, Any],
    birth_year: int,
    birth_month: int,
    birth_day: int,
    birth_hour: Optional[int] = None,
    gender: Optional[str] = None,
    lang: str = "ko",
    mood_score: Optional[int] = None,
    user_message: Optional[str] = None,
    today_pillar: Optional[Dict[str, Any]] = None,
) -> SajuPromptContext:
    """
    saju_engine.get_saju() 결과 → SajuPromptContext 자동 변환
    astrology_info는 saju_calculator.get_astrology_info()로 별도 계산
    """
    from src.engine.saju_calculator import get_astrology_info

    ec = saju_result.get("eight_char", {})

    def _glyph(key: str) -> str:
        return ec.get(key, {}).get("glyph", "")

    def _element_ko(key: str, sub: str = "stem") -> str:
        return ec.get(key, {}).get("element", {}).get(sub, "")

    # 오행 분포
    dist_raw: Dict[str, int] = {}
    details = saju_result.get("element_distribution", {})
    if isinstance(details, dict):
        dist_raw = {k: v for k, v in details.items() if isinstance(v, int)}

    # 점성술 정보
    astro = get_astrology_info(birth_year, birth_month, birth_day, lang)
    western = astro.get("western", {})
    eastern = astro.get("eastern", {})
    lunar = astro.get("lunar_date", {})

    # 오늘 일진
    tp_glyph = ""
    tp_element = ""
    if today_pillar:
        tp_glyph = today_pillar.get("pillar", today_pillar.get("glyph", ""))
        tp_element = today_pillar.get("element", "")

    # ILJU_PERSONALITY 에서 일주 해석 추출 시도
    day_glyph = _glyph("day_pillar")
    personality = ""
    strengths: List[str] = []
    challenges: List[str] = []
    try:
        from saju_engine import ILJU_PERSONALITY
        ilju = ILJU_PERSONALITY.get(day_glyph, {})
        personality = ilju.get("summary", "")
        strengths = ilju.get("strengths", [])
        challenges = ilju.get("challenges", [])
    except ImportError:
        pass

    # 기분 레이블
    mood_label = None
    if mood_score is not None:
        _MOOD_LABELS = {1: "매우 힘듦", 2: "힘듦", 3: "보통", 4: "좋음", 5: "매우 좋음"}
        mood_label = _MOOD_LABELS.get(mood_score, "보통")

    return SajuPromptContext(
        birth_year=birth_year,
        birth_month=birth_month,
        birth_day=birth_day,
        birth_hour=birth_hour,
        gender=gender,
        lang=lang,
        year_pillar=_glyph("year_pillar"),
        month_pillar=_glyph("month_pillar"),
        day_pillar=day_glyph,
        hour_pillar=_glyph("hour_pillar") if birth_hour is not None else "",
        primary_element=_element_ko("year_pillar"),
        element_distribution=dist_raw,
        element_balance=saju_result.get("element_balance", ""),
        day_pillar_personality=personality,
        day_pillar_strengths=strengths,
        day_pillar_challenges=challenges,
        western_sign_ko=western.get("sign_ko", ""),
        western_sign_en=western.get("sign_en", ""),
        eastern_zodiac_ko=eastern.get("zodiac_ko", ""),
        eastern_zodiac_en=eastern.get("zodiac_en_label", ""),
        lunar_year=lunar.get("lunar_year"),
        lunar_month=lunar.get("lunar_month"),
        lunar_day=lunar.get("lunar_day"),
        mood_score=mood_score,
        mood_label=mood_label,
        user_message=user_message,
        today_pillar=tp_glyph,
        today_element=tp_element,
    )


def make_rule_based_response(ctx: SajuPromptContext) -> FortuneResponseSchema:
    """
    LLM 없이 규칙 기반으로 FortuneResponseSchema 생성
    AI API 미연결 시 폴백 응답용
    """
    lang = ctx.lang

    element_desc = {
        "ko": {
            "목": "성장과 창조의 목(木) 기운",
            "화": "열정과 소통의 화(火) 기운",
            "토": "안정과 신뢰의 토(土) 기운",
            "금": "결단과 완성의 금(金) 기운",
            "수": "지혜와 통찰의 수(水) 기운",
        },
        "ja": {
            "목": "成長と創造の木のエネルギー",
            "화": "情熱とコミュニケーションの火のエネルギー",
            "토": "安定と信頼の土のエネルギー",
            "금": "決断と完成の金のエネルギー",
            "수": "知恵と洞察の水のエネルギー",
        },
        "en": {
            "목": "Wood energy of growth and creation",
            "화": "Fire energy of passion and communication",
            "토": "Earth energy of stability and trust",
            "금": "Metal energy of decision and completion",
            "수": "Water energy of wisdom and insight",
        },
    }

    el = ctx.primary_element
    el_desc = element_desc.get(lang, element_desc["ko"]).get(el, f"{el} 기운")

    if lang == "ko":
        return FortuneResponseSchema(
            운세요약=(
                f"오늘은 {el_desc}이 흐르는 날입니다. "
                f"일주 {ctx.day_pillar}의 에너지와 오늘의 흐름이 교차하며 "
                f"새로운 가능성이 열립니다."
            ),
            오행분석=(
                f"주 오행 '{el}'은 {el_desc}을 상징합니다. "
                f"{'오행이 균형잡혀 있어 안정적인 흐름입니다.' if ctx.element_balance == 'balanced' else '오행 균형을 맞추는 노력이 도움이 됩니다.'}"
            ),
            에너지인사이트=(
                f"{'현재 힘든 시간을 보내고 있다면, ' if ctx.mood_score and ctx.mood_score <= 2 else ''}"
                f"당신 안에 {el_desc}의 힘이 있습니다. "
                f"자신을 믿고 한 걸음씩 나아가세요."
            ),
            오늘의조언=(
                f"오늘은 {el_desc}에 맞는 활동에 집중하세요. "
                f"작은 것부터 실천하면 큰 변화가 시작됩니다."
            ),
            별자리메시지=(
                f"서양 별자리 {ctx.western_sign_ko}과 동양 {ctx.eastern_zodiac_ko}띠의 "
                f"에너지가 오늘 당신에게 특별한 통찰을 선사합니다."
            ),
        )
    elif lang == "ja":
        return FortuneResponseSchema(
            운세요약=(
                f"今日は{el_desc}が流れる日です。"
                f"日柱{ctx.day_pillar}のエネルギーと今日の流れが交差し、"
                f"新たな可能性が開かれます。"
            ),
            오행분석=(
                f"主五行「{el}」は{el_desc}を象徴します。"
            ),
            에너지인사이트=(
                f"あなたの中に{el_desc}の力があります。"
                f"自分を信じて一歩ずつ進んでください。"
            ),
            오늘의조언=(
                f"今日は{el_desc}に合った活動に集中しましょう。"
            ),
            별자리메시지=(
                f"西洋星座{ctx.western_sign_ko}と東洋の{ctx.eastern_zodiac_ko}の"
                f"エネルギーが今日あなたに特別な洞察をもたらします。"
            ),
        )
    else:  # en
        return FortuneResponseSchema(
            운세요약=(
                f"Today flows with {el_desc}. "
                f"The Day Pillar {ctx.day_pillar} energy intersects with today's flow, "
                f"opening new possibilities."
            ),
            오행분석=(
                f"Your primary element '{el}' symbolizes {el_desc}. "
                f"{'Your Five Elements are balanced.' if ctx.element_balance == 'balanced' else 'Working to balance the Five Elements will be beneficial.'}"
            ),
            에너지인사이트=(
                f"You carry the power of {el_desc} within you. "
                f"Trust yourself and take it one step at a time."
            ),
            오늘의조언=(
                f"Focus on activities aligned with {el_desc} today. "
                f"Small steps lead to great changes."
            ),
            별자리메시지=(
                f"Your {ctx.western_sign_en} (Western) and {ctx.eastern_zodiac_en} (Eastern) "
                f"energies bring special insight to you today."
            ),
        )
