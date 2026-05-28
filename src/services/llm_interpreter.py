"""
사주담 헤르 API 연동 모듈 (config/hermes_api.py 기반)
- Claude 엔드포인트로 모든 LLM 해석 처리
- base_url: https://h-chat-api.autoever.com/claude-code/v2
- api_key: HERMES_API_KEY 환경변수
- 프롬프트 파일 로더 포함
"""
import os
import re
import json
from pathlib import Path
from typing import Optional, Any

# ─────────────────────────────────────────────────────────
# [HIGH] Prompt Injection 방어
# ─────────────────────────────────────────────────────────
SYSTEM_INJECTION_PATTERNS = [
    r'(?i)(ignore|forget|disregard).{0,20}(previous|above|prior)',
    r'(?i)you are now',
    r'(?i)act as',
    r'(?i)jailbreak',
    r'(?i)\\n\\n(system|human|assistant):',
    r'(?i)</?system>',
    r'(?i)\[INST\]',
]


def sanitize_user_input(text: str) -> str:
    """각 user 입력을 LLM에 전달하기 전 프롬프트 인젝션 유사 키워드 필터링.

    검출 시 ValueError 발생 → 라우터에서 HTTP 400으로 변환할 것.
    최대 1000자로 截斷 (과도한 토큰 소비 방지).
    """
    for pattern in SYSTEM_INJECTION_PATTERNS:
        if re.search(pattern, text):
            raise ValueError("Invalid input: potential prompt injection detected")
    # 최대 길이 제한 (1000자)
    return text[:1000]

try:
    from openai import OpenAI as _OpenAI  # type: ignore[import-untyped]
    _OPENAI_OK = True
except ImportError:
    _OpenAI = None  # type: ignore[assignment,misc]
    _OPENAI_OK = False

OpenAI = _OpenAI  # type: ignore[assignment]

# ─────────────────────────────────────────────────────────
# 헤르 API 설정 (config/hermes_api.py와 동기화)
# ─────────────────────────────────────────────────────────
HERMES_API_BASE_CLAUDE = os.getenv(
    "ANTHROPIC_BASE_URL",
    os.getenv("HERMES_API_BASE_CLAUDE",
              "https://internal-apigw-kr.hmg-corp.io/hchat-in/api/v3/claude")
)
HERMES_MODEL_CLAUDE = os.getenv("AI_MODEL", os.getenv("HERMES_MODEL_CLAUDE", "claude-sonnet-4-6"))
HERMES_API_KEY = os.getenv("ANTHROPIC_API_KEY", os.getenv("HERMES_API_KEY", ""))

# 프롬프트 파일 경로 베이스
_PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
_ACADEMIC_DIR = _PROMPTS_DIR / "academic"

# i18n 파일 경로
_I18N_DIR = Path(__file__).parent.parent / "i18n"


def get_client() -> Optional[Any]:
    """헤르 Claude API 클라이언트 반환. 키 없으면 None."""
    if not _OPENAI_OK:
        return None
    api_key = HERMES_API_KEY
    if not api_key:
        return None
    return OpenAI(api_key=api_key, base_url=HERMES_API_BASE_CLAUDE)


def load_prompt(prompt_name: str) -> str:
    """
    프롬프트 파일 로드
    prompt_name 예시:
      - "daily_fortune" → prompts/daily_fortune.txt
      - "academic/bazi_interpretation" → prompts/academic/bazi_interpretation.txt
      - "academic/astrology_interpretation"
      - "academic/integrated_reading"
    """
    if "/" in prompt_name:
        path = _PROMPTS_DIR / (prompt_name + ".txt")
    else:
        path = _PROMPTS_DIR / (prompt_name + ".txt")

    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"# 프롬프트 파일 없음: {prompt_name}"


def load_i18n(lang: str = "ko") -> dict:
    """i18n JSON 파일 로드. 없으면 빈 dict."""
    path = _I18N_DIR / f"{lang}.json"
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def interpret_bazi(
    saju_data: dict,
    request: str = "전체 해석",
    lang: str = "ko",
    depth: str = "full",
) -> dict:
    """
    명리학 정통 해석 요청
    - 프롬프트: prompts/academic/bazi_interpretation.txt
    - LLM: 헤르 Claude API
    
    Args:
        saju_data: calc_four_pillars() 또는 saju_engine.get_saju() 결과
        request: 해석 요청 항목 (예: "용신 분석", "대운 해석", "전체 격국")
        lang: ko/ja/en
        depth: brief/full
    
    Returns:
        {content, lang, source, model, error(있으면)}
    """
    client = get_client()
    system_prompt = load_prompt("academic/bazi_interpretation")

    # 시스템 프롬프트에서 [SYSTEM] 섹션 추출 (언어별)
    system_text = _extract_system_prompt(system_prompt, lang)

    # 사주 데이터 포맷팅
    pillars = saju_data.get("pillars", saju_data)
    user_content = _format_bazi_user_msg(pillars, request, lang)

    if client is None:
        return {
            "content": f"[헤르 API 미연결] 요청: {request}\n사주: {json.dumps(saju_data, ensure_ascii=False)[:200]}...",
            "lang": lang,
            "source": "bazi",
            "model": "offline",
            "error": "HERMES_API_KEY 미설정 또는 openai 패키지 없음",
        }

    try:
        max_tokens = 800 if depth == "full" else 350
        response = client.chat.completions.create(
            model=HERMES_MODEL_CLAUDE,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_content},
            ],
        )
        content = response.choices[0].message.content or ""
        return {
            "content": content,
            "lang": lang,
            "source": "bazi",
            "model": HERMES_MODEL_CLAUDE,
        }
    except Exception as e:
        return {
            "content": "",
            "lang": lang,
            "source": "bazi",
            "model": HERMES_MODEL_CLAUDE,
            "error": str(e),
        }


def interpret_astrology(
    chart_data: dict,
    request: str = "출생 차트 전체 해석",
    lang: str = "ko",
    depth: str = "full",
) -> dict:
    """
    서양 점성술 해석 요청
    - 프롬프트: prompts/academic/astrology_interpretation.txt
    """
    client = get_client()
    system_prompt = load_prompt("academic/astrology_interpretation")
    system_text = _extract_system_prompt(system_prompt, lang)
    user_content = _format_astrology_user_msg(chart_data, request, lang)

    if client is None:
        return {
            "content": f"[헤르 API 미연결] 서양 점성술 해석 요청: {request}",
            "lang": lang,
            "source": "astrology",
            "model": "offline",
            "error": "HERMES_API_KEY 미설정",
        }

    try:
        max_tokens = 800 if depth == "full" else 350
        response = client.chat.completions.create(
            model=HERMES_MODEL_CLAUDE,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_content},
            ],
        )
        content = response.choices[0].message.content or ""
        return {
            "content": content,
            "lang": lang,
            "source": "astrology",
            "model": HERMES_MODEL_CLAUDE,
        }
    except Exception as e:
        return {
            "content": "",
            "lang": lang,
            "source": "astrology",
            "model": HERMES_MODEL_CLAUDE,
            "error": str(e),
        }


def interpret_integrated(
    saju_data: dict,
    chart_data: dict,
    request: str = "동서양 통합 해석",
    lang: str = "ko",
    depth: str = "full",
) -> dict:
    """
    동서양 통합 해석 요청
    - 프롬프트: prompts/academic/integrated_reading.txt
    """
    client = get_client()
    system_prompt = load_prompt("academic/integrated_reading")
    system_text = _extract_system_prompt(system_prompt, lang)
    user_content = _format_integrated_user_msg(saju_data, chart_data, request, lang, depth)

    if client is None:
        return {
            "content": f"[헤르 API 미연결] 통합 해석 요청: {request}",
            "lang": lang,
            "source": "integrated",
            "model": "offline",
            "error": "HERMES_API_KEY 미설정",
        }

    try:
        max_tokens = 1000 if depth == "full" else 400
        response = client.chat.completions.create(
            model=HERMES_MODEL_CLAUDE,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_content},
            ],
        )
        content = response.choices[0].message.content or ""
        return {
            "content": content,
            "lang": lang,
            "source": "integrated",
            "model": HERMES_MODEL_CLAUDE,
        }
    except Exception as e:
        return {
            "content": "",
            "lang": lang,
            "source": "integrated",
            "model": HERMES_MODEL_CLAUDE,
            "error": str(e),
        }


# ─────────────────────────────────────────────────────────
# 내부 헬퍼
# ─────────────────────────────────────────────────────────
def _extract_system_prompt(full_prompt: str, lang: str) -> str:
    """프롬프트 파일에서 언어별 [SYSTEM] 섹션 추출"""
    lang_markers = {
        "ko": "[SYSTEM — 한국어]",
        "ja": "[SYSTEM — 日本語]",
        "en": "[SYSTEM — English]",
    }
    marker_ko = "[SYSTEM — 명리학 정통 해석 엔진]"
    marker_astro = "[SYSTEM — 서양 점성술 정통 해석 엔진]"
    marker_integrated = "[SYSTEM — 동서양 통합 해석 엔진]"

    # 전문 시스템 프롬프트 (언어 무관)
    for m in [marker_ko, marker_astro, marker_integrated]:
        if m in full_prompt:
            start = full_prompt.index(m)
            end_markers = ["\n---\n", "\n[USER"]
            end = len(full_prompt)
            for em in end_markers:
                pos = full_prompt.find(em, start + len(m))
                if pos != -1:
                    end = min(end, pos)
            return full_prompt[start:end].strip()

    # 언어별 [SYSTEM] 섹션
    marker = lang_markers.get(lang, lang_markers["ko"])
    if marker in full_prompt:
        start = full_prompt.index(marker) + len(marker)
        next_section_markers = ["[SYSTEM —", "[USER ", "---"]
        end = len(full_prompt)
        for nm in next_section_markers:
            pos = full_prompt.find(nm, start + 10)
            if pos != -1:
                end = min(end, pos)
        return full_prompt[start:end].strip()

    return full_prompt[:2000]  # 기본: 앞 2000자


def _format_bazi_user_msg(pillars: dict, request: str, lang: str) -> str:
    """사주 데이터 → 명리학 해석 요청 메시지"""
    year = pillars.get("year", {})
    month = pillars.get("month", {})
    day = pillars.get("day", {})
    hour = pillars.get("hour", {})

    yp = year.get("pillar", year.get("glyph", "?"))
    mp = month.get("pillar", month.get("glyph", "?"))
    dp = day.get("pillar", day.get("glyph", "?"))
    hp = hour.get("pillar", hour.get("glyph", "미상")) if hour else "미상"
    el = pillars.get("primary_element", "")

    if lang == "ko":
        return (
            f"사주 정보:\n"
            f"- 연주(年柱): {yp}\n"
            f"- 월주(月柱): {mp}\n"
            f"- 일주(日柱): {dp}\n"
            f"- 시주(時柱): {hp}\n"
            f"- 주요 오행: {el}\n\n"
            f"요청: {request}\n"
            f"위 사주를 명리학 정통 규칙에 따라 학문적으로 해석해주세요."
        )
    elif lang == "ja":
        return (
            f"四柱情報:\n"
            f"- 年柱: {yp}\n- 月柱: {mp}\n- 日柱: {dp}\n- 時柱: {hp}\n- 主五行: {el}\n\n"
            f"リクエスト: {request}"
        )
    else:
        return (
            f"Four Pillars:\n"
            f"- Year: {yp}\n- Month: {mp}\n- Day: {dp}\n- Hour: {hp}\n- Primary Element: {el}\n\n"
            f"Request: {request}"
        )


def _format_astrology_user_msg(chart_data: dict, request: str, lang: str) -> str:
    """점성술 차트 → 해석 요청 메시지"""
    planets = chart_data.get("planets", {})
    sun = planets.get("sun", {})
    moon = planets.get("moon", {})
    asc = chart_data.get("ascendant", {})
    aspects = chart_data.get("aspects", [])[:5]  # 상위 5개

    sun_sign = sun.get("sign_ko" if lang == "ko" else "sign_en", "?")
    moon_sign = moon.get("sign_ko" if lang == "ko" else "sign_en", "?")
    asc_sign = asc.get("sign_ko" if lang == "ko" else "sign_en", "미상") if asc else "미상"
    aspects_str = ", ".join([f"{a.get('planet1')} {a.get('aspect')} {a.get('planet2')}" for a in aspects])

    if lang == "ko":
        return (
            f"출생 차트:\n"
            f"- 태양궁: {sun_sign}\n"
            f"- 달궁: {moon_sign}\n"
            f"- 어센던트: {asc_sign}\n"
            f"- 주요 어스펙트: {aspects_str or '없음'}\n\n"
            f"요청: {request}"
        )
    elif lang == "ja":
        return (
            f"ネイタルチャート:\n"
            f"- 太陽星座: {sun.get('sign_ja', '?')}\n"
            f"- 月星座: {moon.get('sign_ja', '?')}\n"
            f"- アセンダント: {asc.get('sign_ja', '不明') if asc else '不明'}\n"
            f"- 主アスペクト: {aspects_str or 'なし'}\n\n"
            f"リクエスト: {request}"
        )
    else:
        return (
            f"Natal Chart:\n"
            f"- Sun Sign: {sun.get('sign_en', '?')}\n"
            f"- Moon Sign: {moon.get('sign_en', '?')}\n"
            f"- Ascendant: {asc.get('sign_en', 'Unknown') if asc else 'Unknown'}\n"
            f"- Key Aspects: {aspects_str or 'None'}\n\n"
            f"Request: {request}"
        )


def _format_integrated_user_msg(
    saju_data: dict,
    chart_data: dict,
    request: str,
    lang: str,
    depth: str,
) -> str:
    """통합 해석 요청 메시지"""
    bazi_msg = _format_bazi_user_msg(saju_data.get("pillars", saju_data), "통합해석용", lang)
    astro_msg = _format_astrology_user_msg(chart_data, "통합해석용", lang)

    if lang == "ko":
        return (
            f"[명리학 정보]\n{bazi_msg}\n\n"
            f"[서양 점성술 정보]\n{astro_msg}\n\n"
            f"언어: {lang} | 해석 깊이: {depth}\n"
            f"요청: {request}\n"
            f"동서양 통합 관점에서 해석해주세요."
        )
    elif lang == "ja":
        return (
            f"[四柱推命情報]\n{bazi_msg}\n\n"
            f"[西洋占星術情報]\n{astro_msg}\n\n"
            f"言語: {lang} | 解釈の深さ: {depth}\n"
            f"リクエスト: {request}"
        )
    else:
        return (
            f"[Four Pillars Info]\n{bazi_msg}\n\n"
            f"[Western Astrology Info]\n{astro_msg}\n\n"
            f"Language: {lang} | Depth: {depth}\n"
            f"Request: {request}"
        )
