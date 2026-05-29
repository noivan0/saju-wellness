"""
사주담 — AI 실시간 상세 해석 서비스
Claude API를 활용해 사주팔자, 에너지, 궁합을 깊이 있게 해석
"""
import os
import json
import anthropic
from functools import lru_cache

_client = None


def _extract_json(raw: str) -> dict:
    """AI 응답에서 JSON 추출 — 코드블록·이스케이프 문자 내성 있는 파서"""
    if not raw:
        return {}
    # 1) 마크다운 코드블록 제거
    import re
    raw = re.sub(r'```(?:json)?\s*', '', raw).strip()
    raw = re.sub(r'```\s*$', '', raw).strip()
    # 2) json.JSONDecoder.raw_decode 로 첫 JSON 객체 추출
    decoder = json.JSONDecoder()
    start = raw.find('{')
    if start == -1:
        return {}
    try:
        obj, _ = decoder.raw_decode(raw, start)
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        return {}


def _get_client():
    global _client
    if _client is None:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return None
        try:
            _client = anthropic.Anthropic(
                api_key=key,
                base_url="https://h-chat-api.autoever.com/claude-code/v2",
            )
        except Exception:
            return None
    return _client


HEAVENLY_STEMS_KR = {
    "甲":"갑","乙":"을","丙":"병","丁":"정","戊":"무",
    "己":"기","庚":"경","辛":"신","壬":"임","癸":"계"
}
EARTHLY_BRANCHES_KR = {
    "子":"자","丑":"축","寅":"인","卯":"묘","辰":"진","巳":"사",
    "午":"오","未":"미","申":"신","酉":"유","戌":"술","亥":"해"
}
ELEMENTS_KR = {"木":"목","火":"화","土":"토","金":"금","水":"수"}


def _call_ai(prompt: str, system: str = None, max_tokens: int = 800) -> str:
    """AI 호출 공통 함수. 실패 시 빈 문자열 반환."""
    client = _get_client()
    if not client:
        return ""
    try:
        create_kwargs = {
            "model": "claude-sonnet-4-6",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            create_kwargs["system"] = system
        resp = client.messages.create(**create_kwargs)
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        import logging
        logging.warning(f"[SajuAI] API 오류: {e}")
        return ""


SAJU_SYSTEM = (
    "당신은 명리학 전문가입니다. "
    "반드시 순수 JSON만 반환하세요. 마크다운, 코드블록(```), 설명 텍스트, 헤더 절대 금지. "
    "첫 글자는 반드시 { 이어야 합니다."
)


def interpret_saju_full(pillars: dict, gender: str = "male") -> dict:
    """
    사주팔자 전체 상세 해석 (AI 생성)
    pillars: {year, month, day, hour, primary_element, ...}
    """
    year_p = pillars.get("year", {})
    month_p = pillars.get("month", {})
    day_p = pillars.get("day", {})
    hour_p = pillars.get("hour")
    
    gender_str = "남성" if gender == "male" else "여성"
    day_pillar = day_p.get("pillar", "")
    day_stem = day_p.get("stem", "")
    day_branch = day_p.get("branch", "")
    primary_el = ELEMENTS_KR.get(pillars.get("primary_element", ""), pillars.get("primary_element", ""))
    
    hour_str = f"시주: {hour_p.get('pillar','')}" if hour_p else "시주: 미입력"

    prompt = f"""다음 사주팔자를 가진 {gender_str}을 명리학으로 해석해주세요.

【사주】
- 년주: {year_p.get('pillar','')} ({year_p.get('element','')})
- 월주: {month_p.get('pillar','')} ({month_p.get('element','')})  
- 일주: {day_p.get('pillar','')} ({day_p.get('element','')}) ← 핵심
- {hour_str}
- 주 오행: {primary_el}

JSON 형식으로만 답변:
{{
  "core_nature": "일주 {day_pillar}만의 독특한 기질 (3~4문장, 구체적으로)",
  "strengths": ["강점1 — 구체적 상황 예시", "강점2", "강점3"],
  "growth_areas": ["성장과제1 — 긍정 관점", "성장과제2"],
  "element_balance": "오행 균형 분석 (2~3문장)",
  "relationship_style": "인간관계 패턴 (2~3문장)",
  "career_direction": "적성/진로 방향 (2~3문장)",
  "year_2026": "2026년 흐름과 필요한 에너지 (2문장)"
}}"""

    raw = _call_ai(prompt, system=SAJU_SYSTEM, max_tokens=1500)
    if not raw:
        return {}
    return _extract_json(raw)


def interpret_energy_today(pillars: dict, today_pillar: dict) -> dict:
    """오늘의 에너지 상세 해석 (AI 생성)"""
    day_p = pillars.get("day", {})
    year_p = pillars.get("year", {})
    day_pillar = day_p.get("pillar", "")
    today = today_pillar.get("pillar", "")
    my_el = ELEMENTS_KR.get(pillars.get("primary_element", ""), "")
    today_el = ELEMENTS_KR.get(today_pillar.get("element", ""), "")

    prompt = f"""명리학 관점에서 오늘의 에너지를 해석해주세요.

【내 사주 정보】
- 일주(日柱): {day_pillar} (주 오행: {my_el})
- 년주: {year_p.get('pillar','')}

【오늘 날짜 정보】
- 오늘 일진: {today} (오행: {today_el})

다음을 구체적으로 2~3문장씩 해석해주세요:

1. **오늘의 에너지 흐름** (내 일주와 오늘 일진의 상호작용)
2. **추천 활동** (오늘 하면 좋은 것 3가지, 이유 포함)
3. **주의할 점** (오늘 피해야 할 상황이나 행동)
4. **오늘의 한마디** (짧고 강렬한 오늘 메시지, 20자 이내)

JSON 형식으로만:
{{
  "energy_flow": "...",
  "recommended_activities": ["...", "...", "..."],
  "cautions": "...",
  "daily_message": "..."
}}"""

    raw = _call_ai(prompt, system=SAJU_SYSTEM, max_tokens=700)
    if not raw:
        return {}
    
    return _extract_json(raw)


def interpret_compatibility(pillars_a: dict, pillars_b: dict, score: int, relation: str) -> dict:
    """궁합 상세 해석 (AI 생성)"""
    a_day = pillars_a.get("day", {}).get("pillar", "")
    b_day = pillars_b.get("day", {}).get("pillar", "")
    a_el = ELEMENTS_KR.get(pillars_a.get("primary_element",""), "")
    b_el = ELEMENTS_KR.get(pillars_b.get("primary_element",""), "")

    prompt = f"""두 사람의 사주 궁합을 상세하게 분석해주세요.

【A (나)】
- 일주: {a_day} (주 오행: {a_el})
- 년주: {pillars_a.get('year',{}).get('pillar','')}

【B (상대)】
- 일주: {b_day} (주 오행: {b_el})
- 년주: {pillars_b.get('year',{}).get('pillar','')}

【기본 분석】
- 궁합 점수: {score}점
- 오행 관계: {relation} ({a_el} ↔ {b_el})

다음을 각각 2~3문장으로 구체적으로 분석해주세요:

1. **두 사람의 에너지 역학** (어떻게 서로 영향을 주고받는지)
2. **잘 맞는 부분** (구체적 상황 예시)
3. **갈등 가능한 부분** (왜 생기는지, 어떻게 나타나는지)
4. **관계 발전 조언** (함께 성장하기 위한 실질적 제안 3가지)
5. **함께하면 좋은 활동** (두 오행의 시너지를 살리는 활동)
6. **장기적 전망** (이 관계가 가진 가능성)

JSON 형식으로만:
{{
  "energy_dynamics": "...",
  "compatibility_strengths": "...",
  "potential_conflicts": "...",
  "relationship_advice": ["...", "...", "..."],
  "recommended_activities": "...",
  "long_term_outlook": "..."
}}"""

    raw = _call_ai(prompt, system=SAJU_SYSTEM, max_tokens=900)
    if not raw:
        return {}
    
    return _extract_json(raw)


def interpret_compatibility_api(pillars_a: dict, pillars_b: dict, score: int, relation: str) -> dict:
    """상성보기(API 기반 궁합) 해석"""
    return interpret_compatibility(pillars_a, pillars_b, score, relation)
