"""
사주담 — AI 실시간 상세 해석 서비스
Claude API를 활용해 사주팔자, 에너지, 궁합을 깊이 있게 해석
"""
import os
import json
import anthropic
from functools import lru_cache

_client = None
_async_client = None


def _get_async_client():
    """AsyncAnthropic 클라이언트 (asyncio 환경용)"""
    global _async_client
    if _async_client is None:
        key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            return None
        try:
            _async_client = anthropic.AsyncAnthropic(
                api_key=key,
                base_url="https://h-chat-api.autoever.com/claude-code/v2",
            )
        except Exception:
            return None
    return _async_client


def _extract_json(raw: str) -> dict:
    """AI 응답에서 JSON 추출 — 코드블록·이스케이프 문자 내성 있는 파서. 잘린 JSON도 복구 시도."""
    if not raw:
        return {}
    import re
    # 1) 마크다운 코드블록 제거
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
        # 3) 잘린 JSON 복구: 닫히지 않은 중괄호/문자열 닫기
        truncated = raw[start:]
        # 열린 문자열 닫기
        if truncated.count('"') % 2 == 1:
            truncated += '"'
        # 열린 배열 닫기
        open_brackets = truncated.count('[') - truncated.count(']')
        if open_brackets > 0:
            truncated += ']' * open_brackets
        # 마지막 불완전한 키-값 쌍 제거 (콤마로 끝나거나 키만 있는 경우)
        truncated = re.sub(r',\s*"[^"]*"?\s*$', '', truncated)
        truncated = re.sub(r',\s*$', '', truncated)
        # 열린 중괄호 닫기
        open_braces = truncated.count('{') - truncated.count('}')
        if open_braces > 0:
            truncated += '}' * open_braces
        try:
            obj, _ = decoder.raw_decode(truncated, 0)
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
        import logging
        logging.warning("[SajuAI] client=None (ANTHROPIC_API_KEY 미설정?)")
        return ""
    try:
        create_kwargs = {
            "model": "claude-sonnet-4-6",
            "max_tokens": max_tokens,
            "timeout": 45.0,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            create_kwargs["system"] = system
        resp = client.messages.create(**create_kwargs)
        text = resp.content[0].text if resp.content else ""
        import logging
        logging.warning(f"[SajuAI] 응답 {len(text)}자, stop={resp.stop_reason}")
        print(f"[SajuAI] 응답 {len(text)}자, stop={resp.stop_reason}", flush=True)
        return text
    except Exception as e:
        import logging, traceback
        msg = f"[SajuAI] API 오류: {type(e).__name__}: {e}"
        logging.warning(msg)
        print(msg, flush=True)
        tb = traceback.format_exc()[-500:]
        logging.warning(f"[SajuAI] traceback: {tb}")
        print(f"[SajuAI] traceback: {tb}", flush=True)
        return ""


SAJU_SYSTEM = (
    "당신은 명리학 전문가입니다. "
    "반드시 순수 JSON만 반환하세요. 마크다운, 코드블록(```), 설명 텍스트, 헤더 절대 금지. "
    "첫 글자는 반드시 { 이어야 합니다."
)


# lru_cache 대신 dict 캐시 — 빈 결과는 캐싱하지 않음
_saju_full_cache: dict = {}

def _interpret_saju_full_cached(day_pillar: str, gender: str, year_pillar: str,
                                 month_pillar: str, year_el: str, month_el: str,
                                 day_el: str, hour_pillar: str, primary_el: str) -> str:
    """캐시 적용된 AI 사주 해석 — 동일 일주+성별 반복 요청 시 캐시 반환. 빈 결과는 캐싱 안함."""
    import logging
    cache_key = (day_pillar, gender, year_pillar, month_pillar, hour_pillar)
    if cache_key in _saju_full_cache:
        logging.info(f"[SajuAI] 캐시 히트: {cache_key[0]}/{cache_key[1]}")
        return _saju_full_cache[cache_key]

    gender_str = "남성" if gender == "male" else "여성"
    hour_str = f"시주: {hour_pillar}" if hour_pillar else "시주: 미입력"
    prompt = f"""다음 사주팔자를 가진 {gender_str}을 명리학으로 해석해주세요.

【사주】
- 년주: {year_pillar} ({year_el})
- 월주: {month_pillar} ({month_el})  
- 일주: {day_pillar} ({day_el}) ← 핵심
- {hour_str}
- 주 오행: {primary_el}

JSON 형식으로만 답변:
{{
  "core_nature": "일주 {day_pillar} 기질 (2문장 이내)",
  "strengths": ["강점1", "강점2", "강점3"],
  "growth_areas": ["성장과제1", "성장과제2"],
  "element_balance": "오행 균형 (1~2문장)",
  "relationship_style": "인간관계 패턴 (1~2문장)",
  "career_direction": "적성/진로 (1~2문장)",
  "year_2026": "2026년 흐름 (1문장)"
}}"""
    raw = _call_ai(prompt, system=SAJU_SYSTEM, max_tokens=1200)
    if raw:
        _saju_full_cache[cache_key] = raw
        if len(_saju_full_cache) > 60:
            oldest = next(iter(_saju_full_cache))
            del _saju_full_cache[oldest]
    return raw


def interpret_saju_full(pillars: dict, gender: str = "male") -> dict:
    """
    사주팔자 전체 상세 해석 (AI 생성)
    pillars: {year, month, day, hour, primary_element, ...}
    캐시 키: day_pillar + gender (최대 60개, 60갑자 기준)
    """
    year_p = pillars.get("year", {})
    month_p = pillars.get("month", {})
    day_p = pillars.get("day", {})
    hour_p = pillars.get("hour")

    day_pillar = day_p.get("pillar", "")
    primary_el = ELEMENTS_KR.get(pillars.get("primary_element", ""), pillars.get("primary_element", "")) or ""
    hour_pillar = hour_p.get("pillar", "") if hour_p else ""

    # 캐시 조회 (60갑자 기준 최대 60개 항목 메모리 캐시)
    raw = _interpret_saju_full_cached(
        day_pillar=day_pillar,
        gender=gender,
        year_pillar=year_p.get("pillar", ""),
        month_pillar=month_p.get("pillar", ""),
        year_el=year_p.get("element", ""),
        month_el=month_p.get("element", ""),
        day_el=day_p.get("element", ""),
        hour_pillar=hour_pillar,
        primary_el=primary_el,
    )
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
