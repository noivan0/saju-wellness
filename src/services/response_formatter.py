"""
사주담 일관된 응답 포맷 시스템
- 모든 사주/점성 답변: 섹션 고정 (성격/재운/애정/건강/올해운세)
- 각 섹션: 학문적 근거 1줄 → 현대적 해석 2~3줄 → 실천 조언 1줄
- 법적 면책: 모든 응답 끝에 자동 추가
- 언어별 포맷 분리 (ko/ja/en)
"""
from typing import Optional
import os


# ─────────────────────────────────────────────────────────
# 섹션 정의 — 언어별
# ─────────────────────────────────────────────────────────
SECTIONS_KO = [
    {"id": "personality", "title": "💫 성격 에너지"},
    {"id": "fortune",     "title": "💰 재운·사업운"},
    {"id": "love",        "title": "❤️ 애정·관계운"},
    {"id": "health",      "title": "🌿 건강 에너지"},
    {"id": "yearly",      "title": "🌟 올해 운세"},
]
SECTIONS_JA = [
    {"id": "personality", "title": "💫 性格エネルギー"},
    {"id": "fortune",     "title": "💰 財運・仕事運"},
    {"id": "love",        "title": "❤️ 恋愛・人間関係"},
    {"id": "health",      "title": "🌿 健康エネルギー"},
    {"id": "yearly",      "title": "🌟 今年の運勢"},
]
SECTIONS_EN = [
    {"id": "personality", "title": "💫 Personality Energy"},
    {"id": "fortune",     "title": "💰 Wealth & Career"},
    {"id": "love",        "title": "❤️ Love & Relationships"},
    {"id": "health",      "title": "🌿 Health Energy"},
    {"id": "yearly",      "title": "🌟 This Year's Fortune"},
]

# 섹션 매핑
_SECTIONS_MAP = {"ko": SECTIONS_KO, "ja": SECTIONS_JA, "en": SECTIONS_EN}

# ─────────────────────────────────────────────────────────
# 법적 면책 문구 — 언어별
# ─────────────────────────────────────────────────────────
_DISCLAIMERS = {
    "ko": (
        "※ 본 내용은 명리학 및 점성술 관점의 자기이해 참고 정보입니다. "
        "과학적 예측이나 전문적 심리상담·의료 서비스를 대체하지 않습니다."
    ),
    "ja": (
        "※ 本内容は命理学および占星術的観点の自己理解参考情報です。"
        "科学的予測や専門的な心理カウンセリング・医療サービスの代わりにはなりません。"
    ),
    "en": (
        "※ This content is self-understanding reference material from a Four Pillars and "
        "astrology perspective. It does not replace scientific prediction or professional "
        "counseling and medical services."
    ),
}

# ─────────────────────────────────────────────────────────
# 섹션별 학문적 근거 레이블 — 언어별
# ─────────────────────────────────────────────────────────
_ACADEMIC_LABELS = {
    "ko": "📚 학문적 근거",
    "ja": "📚 学術的根拠",
    "en": "📚 Academic Basis",
}
_MODERN_LABELS = {
    "ko": "💡 현대적 해석",
    "ja": "💡 現代的解釈",
    "en": "💡 Modern Interpretation",
}
_ACTION_LABELS = {
    "ko": "✅ 실천 조언",
    "ja": "✅ 実践アドバイス",
    "en": "✅ Practical Advice",
}


def format_section(
    section_id: str,
    academic_basis: str,
    modern_interpretation: str,
    practical_advice: str,
    lang: str = "ko",
) -> dict:
    """
    단일 섹션 포맷팅
    Returns: {id, title, academic_basis, modern_interpretation, practical_advice, formatted_text}
    """
    sections = _SECTIONS_MAP.get(lang, SECTIONS_KO)
    section_meta = next((s for s in sections if s["id"] == section_id), {"id": section_id, "title": section_id})

    formatted_text = (
        f"{section_meta['title']}\n"
        f"{_ACADEMIC_LABELS[lang]}: {academic_basis}\n"
        f"{_MODERN_LABELS[lang]}: {modern_interpretation}\n"
        f"{_ACTION_LABELS[lang]}: {practical_advice}"
    )

    return {
        "id": section_id,
        "title": section_meta["title"],
        "academic_basis": academic_basis,
        "modern_interpretation": modern_interpretation,
        "practical_advice": practical_advice,
        "formatted_text": formatted_text,
    }


def format_full_response(
    sections_data: dict,
    lang: str = "ko",
    include_disclaimer: bool = True,
    source_info: Optional[str] = None,
) -> dict:
    """
    전체 응답 포맷팅 — 5개 섹션 고정 구조
    
    Args:
        sections_data: {
            "personality": {"academic_basis": ..., "modern_interpretation": ..., "practical_advice": ...},
            "fortune": {...},
            "love": {...},
            "health": {...},
            "yearly": {...},
        }
        lang: ko/ja/en
        include_disclaimer: 면책 문구 포함 여부 (기본 True, 항상 권장)
        source_info: "bazi" | "astrology" | "integrated"
    
    Returns:
        {
          "sections": [...],
          "full_text": "섹션 전체 텍스트",
          "disclaimer": "...",
          "lang": "ko",
          "source": "bazi"
        }
    """
    sections_meta = _SECTIONS_MAP.get(lang, SECTIONS_KO)
    formatted_sections = []
    full_parts = []

    for s in sections_meta:
        sid = s["id"]
        data = sections_data.get(sid, {})
        if not data:
            continue

        academic = data.get("academic_basis", "")
        modern = data.get("modern_interpretation", "")
        advice = data.get("practical_advice", "")

        section = format_section(sid, academic, modern, advice, lang)
        formatted_sections.append(section)
        full_parts.append(section["formatted_text"])

    disclaimer = _DISCLAIMERS.get(lang, _DISCLAIMERS["ko"])
    full_text = "\n\n".join(full_parts)
    if include_disclaimer:
        full_text += f"\n\n{disclaimer}"

    return {
        "sections": formatted_sections,
        "full_text": full_text,
        "disclaimer": disclaimer,
        "lang": lang,
        "source": source_info or "bazi",
        "section_count": len(formatted_sections),
    }


def format_daily_insight(
    energy_text: str,
    pillar_info: str,
    advice: str,
    lang: str = "ko",
) -> dict:
    """
    오늘의 인사이트 간단 포맷 (daily-energy 엔드포인트용)
    """
    disclaimer = _DISCLAIMERS.get(lang, _DISCLAIMERS["ko"])

    templates = {
        "ko": f"✨ 오늘의 에너지\n{energy_text}\n\n🧭 일주 인사이트\n{pillar_info}\n\n💫 오늘의 조언\n{advice}\n\n{disclaimer}",
        "ja": f"✨ 今日のエネルギー\n{energy_text}\n\n🧭 日柱インサイト\n{pillar_info}\n\n💫 今日のアドバイス\n{advice}\n\n{disclaimer}",
        "en": f"✨ Today's Energy\n{energy_text}\n\n🧭 Day Pillar Insight\n{pillar_info}\n\n💫 Today's Advice\n{advice}\n\n{disclaimer}",
    }

    return {
        "formatted": templates.get(lang, templates["ko"]),
        "disclaimer": disclaimer,
        "lang": lang,
    }


def format_compatibility_response(
    score: int,
    level: str,
    relation: str,
    advice: str,
    element_a: str,
    element_b: str,
    lang: str = "ko",
) -> dict:
    """
    궁합 응답 포맷
    """
    disclaimer = _DISCLAIMERS.get(lang, _DISCLAIMERS["ko"])

    headers = {
        "ko": {
            "title": "💑 궁합 분석",
            "score_label": "궁합 점수",
            "level_label": "궁합 레벨",
            "relation_label": "오행 관계",
            "advice_label": "조언",
        },
        "ja": {
            "title": "💑 相性分析",
            "score_label": "相性スコア",
            "level_label": "相性レベル",
            "relation_label": "五行の関係",
            "advice_label": "アドバイス",
        },
        "en": {
            "title": "💑 Compatibility Analysis",
            "score_label": "Score",
            "level_label": "Level",
            "relation_label": "Five Elements Relation",
            "advice_label": "Advice",
        },
    }
    h = headers.get(lang, headers["ko"])

    formatted = (
        f"{h['title']}\n"
        f"{h['score_label']}: {score}/100\n"
        f"{h['level_label']}: {level}\n"
        f"{h['relation_label']}: {element_a} × {element_b} ({relation})\n"
        f"{h['advice_label']}: {advice}\n\n"
        f"{disclaimer}"
    )

    return {
        "formatted": formatted,
        "score": score,
        "level": level,
        "relation": relation,
        "advice": advice,
        "disclaimer": disclaimer,
        "lang": lang,
    }


def get_disclaimer(lang: str = "ko") -> str:
    """면책 문구 반환 (단독 사용용)"""
    return _DISCLAIMERS.get(lang, _DISCLAIMERS["ko"])


def get_sections_template(lang: str = "ko") -> list:
    """섹션 구조 템플릿 반환"""
    return _SECTIONS_MAP.get(lang, SECTIONS_KO)
