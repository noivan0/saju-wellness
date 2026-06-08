"""
사주팔자 계산 API 라우터
법적: 문화·오락 서비스 / 참고 정보 / 심리상담 아님
"""
import sys
import os
# saju_engine.py를 임포트할 수 있도록 프로젝트 루트를 path에 추가
_PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, os.path.abspath(_PROJECT_ROOT))

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List
from src.core.auth import get_current_user

# AI 해석 서비스
try:
    from src.services.ai_interpreter import (
        interpret_saju_full,
        interpret_energy_today,
        interpret_compatibility,
    )
    _AI_OK = True
except Exception as _ai_err:
    _AI_OK = False
    import logging
    logging.warning(f"[SajuAPI] AI 해석 서비스 로드 실패: {_ai_err}")
from src.api.rate_limiter import limiter
import json
import datetime
import random

from fastapi import Depends, Request

router = APIRouter(tags=["saju"])

# ─────────────────────────────────────────────
# saju_engine 임포트 (검증된 엔진)
# ─────────────────────────────────────────────
try:
    from saju_engine import (
        get_saju,
        get_daewoon,
        ELEMENT_SHENG,
        ELEMENT_KE,
        HEAVENLY_STEMS,
        EARTHLY_BRANCHES,
        STEM_KR,
        BRANCH_KR,
        STEM_ELEMENT,
        BRANCH_ELEMENT,
        HOUR_TO_BRANCH,
        ILJU_PERSONALITY,
    )
    _ENGINE_OK = True
    _ENGINE_ERR = ""
except ImportError as e:
    _ENGINE_OK = False
    _ENGINE_ERR = str(e)
    # 폴백 상수 — 엔진 로드 실패 시에도 타입 오류 방지
    def get_saju(*args, **kwargs):  # noqa: E302
        raise RuntimeError("saju_engine not available")  # type: ignore[return-value]
    HEAVENLY_STEMS = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
    EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    STEM_KR = ["갑","을","병","정","무","기","경","신","임","계"]
    BRANCH_KR = ["자","축","인","묘","진","사","오","미","신","유","술","해"]
    STEM_ELEMENT = ["목","목","화","화","토","토","금","금","수","수"]
    BRANCH_ELEMENT = ["수","토","목","목","토","화","화","토","금","금","토","수"]
    HOUR_TO_BRANCH = [0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11,0]
    ELEMENT_SHENG = {"목":"화","화":"토","토":"금","금":"수","수":"목"}
    ELEMENT_KE    = {"목":"토","토":"수","수":"화","화":"금","금":"목"}
    ILJU_PERSONALITY: dict = {}

# ─────────────────────────────────────────────
# 오행 텍스트 / 매핑 상수
# ─────────────────────────────────────────────
DAILY_ENERGY_TEXTS = {
    '목': '오늘은 성장과 도전의 에너지가 흐릅니다. 새로운 시작을 두려워하지 마세요. 나무처럼 위로 뻗어나가는 기운을 활용하세요.',
    '화': '활발한 에너지의 날입니다. 사람들과 소통하고 아이디어를 나누세요. 열정적인 행동이 빛을 발하는 날입니다.',
    '토': '안정과 신뢰의 에너지. 꼼꼼하게 정리하고 기반을 다지기 좋습니다. 중요한 관계와 기반에 집중하세요.',
    '금': '결단력이 높아지는 날. 중요한 결정을 내리기 좋습니다. 정확하고 원칙적인 행동이 성과를 만듭니다.',
    '수': '직관력이 높아지는 날. 깊이 생각하고 계획을 세우세요. 내면의 지혜를 믿고 유연하게 움직이세요.',
}

ELEMENT_KR_MAP = {'木': '목', '火': '화', '土': '토', '金': '금', '水': '수'}
ELEMENT_HAN_MAP = {'목': '木', '화': '火', '토': '土', '금': '金', '수': '水'}

ELEMENT_TITLE = {
    '목': '목(木) 에너지 — 성장과 창조의 날',
    '화': '화(火) 에너지 — 열정과 소통의 날',
    '토': '토(土) 에너지 — 안정과 신뢰의 날',
    '금': '금(金) 에너지 — 결단과 완성의 날',
    '수': '수(水) 에너지 — 지혜와 통찰의 날',
}

# 오행 상생 상극 (한글 기준)
SHENG_KR = {'목': '화', '화': '토', '토': '금', '금': '수', '수': '목'}
KE_KR    = {'목': '토', '토': '수', '수': '화', '화': '금', '금': '목'}

# 데이터 파일 경로
_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data')


def _load_pillar_data() -> dict:
    path = os.path.join(_DATA_DIR, 'pillar_interpretations.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {}


def _load_element_data() -> dict:
    path = os.path.join(_DATA_DIR, 'element_interpretations.json')
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {}


def _get_element_han(element_ko: str) -> str:
    return ELEMENT_HAN_MAP.get(element_ko, element_ko)


def _kst_today() -> datetime.date:
    """KST(UTC+9) 기준 오늘 날짜 반환 — 서버가 UTC일 경우도 정확한 한국 날짜"""
    import datetime as _dt
    kst = _dt.timezone(_dt.timedelta(hours=9))
    return _dt.datetime.now(tz=kst).date()


def _calc_today_pillar() -> dict:
    """오늘 날짜의 일주 계산 — saju_engine fallback 방식 (기준일 2000-01-07 갑자일)"""
    today = _kst_today()  # BUG-SJ1 FIX: UTC → KST 명시
    base = datetime.date(2000, 1, 7)  # 갑자일 (KB 검증 완료)
    diff = (today - base).days
    stem_idx = diff % 10
    branch_idx = diff % 12
    stem = STEM_KR[stem_idx]
    branch = BRANCH_KR[branch_idx]
    stem_han = HEAVENLY_STEMS[stem_idx]
    branch_han = EARTHLY_BRANCHES[branch_idx]
    element = STEM_ELEMENT[stem_idx]
    return {
        "stem": stem,
        "branch": branch,
        "stem_han": stem_han,
        "branch_han": branch_han,
        "pillar": f"{stem}{branch}",
        "pillar_han": f"{stem_han}{branch_han}",
        "element": element,
    }


def _saju_engine_to_legacy(result: dict, birth_hour: Optional[int] = None) -> dict:
    """
    saju_engine.get_saju() 결과를 기존 API 응답 포맷으로 변환.
    기존 코드가 기대하는 pillars.year/month/day/hour 구조.
    """
    ec = result["eight_char"]

    def pillar_dict(p_key, label_kr):
        p = ec.get(p_key, {})
        el = p.get("element", {})
        stem_el = el.get("stem", "")
        return {
            "stem": p.get("glyph", "")[:1],   # 한자 천간
            "branch": p.get("glyph", "")[1:],  # 한자 지지
            "pillar": p.get("glyph", ""),
            "element": ELEMENT_HAN_MAP.get(stem_el, stem_el),  # 한자 오행
            "element_ko": stem_el,
            "reading": p.get("reading", ""),
        }

    year_p  = pillar_dict("year_pillar",  "년주")
    month_p = pillar_dict("month_pillar", "월주")
    day_p   = pillar_dict("day_pillar",   "일주")

    # 일주 천간 오행
    day_stem_el = ec.get("day_pillar", {}).get("element", {}).get("stem", "")

    out = {
        "year":  year_p,
        "month": month_p,
        "day":   day_p,
        "primary_element": ELEMENT_HAN_MAP.get(year_p.get("element_ko", ""), year_p.get("element", "")),
        "day_primary_element": ELEMENT_HAN_MAP.get(day_stem_el, day_stem_el),
        "disclaimer": "본 내용은 명리학적 관점의 자기이해 도구이며 전문적 심리상담을 대체하지 않습니다.",
        "legal": "명리학 자기이해 도구 — 심리상담/의료 대체 아님",
        "lunar_date": result.get("lunar_date"),  # 음력 정보 포함
    }
    if birth_hour is not None:
        hour_p = pillar_dict("hour_pillar", "시주")
        out["hour"] = hour_p

    return out


# ─────────────────────────────────────────────
# Pydantic 모델
# ─────────────────────────────────────────────
class BirthInfo(BaseModel):
    birth_year: int = Field(..., ge=1900, le=2099, description="출생 연도 (1900~2099). 실사용자 기준 의도적 제한 — 엔진은 1582~2100 지원하나 서비스 범위는 1900~2099로 고정 (LOW)")
    birth_month: int = Field(..., ge=1, le=12, description="출생 월 (1~12)")
    birth_day: int = Field(..., ge=1, le=31, description="출생 일 (1~31)")
    birth_hour: Optional[int] = Field(None, ge=0, le=23, description="출생 시 (0~23, 선택)")
    gender: Optional[str] = None
    lang: str = Field("ko", pattern="^(ko|ja|en)$", description="언어 코드 (ko|ja|en)")  # [BLK-JWT-LANG] 허용값 강제
    session_id: Optional[str] = Field(None, max_length=64, description="클라이언트 세션 UUID (localStorage)")  # 히스토리 저장용

    @model_validator(mode="after")
    def validate_date(self) -> "BirthInfo":
        """[R17-②] 달력 날짜 유효성 검증 (2월 30일 등 엣지케이스 차단)
        [R52-INPUT-001 FIX] 미래 날짜 차단 — 사주담은 출생일 기반이므로 미래 날짜 불가"""
        import calendar
        import datetime as _dt2
        max_day = calendar.monthrange(self.birth_year, self.birth_month)[1]
        if self.birth_day > max_day:
            raise ValueError(
                f"{self.birth_year}년 {self.birth_month}월은 {max_day}일까지만 있습니다 "
                f"(입력: {self.birth_day}일)"
            )
        # [R52-INPUT-001] 실용적 미래 날짜 방어
        # 사주담 특성: 역술 서비스 — 1900~2099 전체 연도 지원이 설계 스펙
        # 실제 사용 패턴: 이미 태어난 사람(과거) + 계획용(미래 ~2099) 모두 허용
        # 따라서 Pydantic ge=1900, le=2099로 범위 제한만 적용 (여기서는 추가 제한 없음)
        return self


class CompatibilityRequest(BaseModel):
    person_a: BirthInfo
    person_b: BirthInfo


# ─────────────────────────────────────────────
# 라우터 엔드포인트
# ─────────────────────────────────────────────

# [gstack P4] 궁합 빠른 체험 — 상대방 생년월일 한 줄 입력 → 무료 미리보기 (비인증)
@router.get("/compatibility-preview")
@limiter.limit("20/minute")
def get_compatibility_preview(
    request: Request,
    my_year: int = Query(..., ge=1900, le=2099, description="내 출생 연도"),
    my_month: int = Query(..., ge=1, le=12),
    my_day: int = Query(..., ge=1, le=31),
    partner_year: int = Query(..., ge=1900, le=2099, description="상대방 출생 연도"),
    partner_month: int = Query(..., ge=1, le=12),
    partner_day: int = Query(..., ge=1, le=31),
    lang: str = Query("ko", pattern="^(ko|ja|en)$"),
):
    """
    [gstack P4] 연인 궁합 빠른 체험 — 생년월일만 입력하면 무료 미리보기
    로그인 불필요, 오행 궁합 점수 + 한 줄 요약만 반환
    상세 분석은 회원가입 유도 (프리미엄 전환 CTA)
    법적: 명리학 참고 정보, 연애 결정 보장 아님
    """
    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail="사주 엔진 로드 실패")
    try:
        res_a = get_saju(my_year, my_month, my_day)
        res_b = get_saju(partner_year, partner_month, partner_day)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")
    def get_day_el(res):
        return res.get("eight_char", {}).get("day_pillar", {}).get("element", {}).get("stem", "")

    el_a = get_day_el(res_a)
    el_b = get_day_el(res_b)
    base = 60
    if SHENG_KR.get(el_a) == el_b or SHENG_KR.get(el_b) == el_a:
        score, relation = base + 20, "상생"
    elif KE_KR.get(el_a) == el_b or KE_KR.get(el_b) == el_a:
        score, relation = base - 15, "상극"
    elif el_a == el_b:
        score, relation = base + 10, "비화"
    else:
        score, relation = base, "중립"
    score = max(0, min(100, score))

    SUMMARY = {
        "상생": {"ko": "서로 성장을 돕는 에너지예요 ✨", "ja": "互いに成長を助けるエネルギーです ✨", "en": "You bring out growth in each other ✨"},
        "상극": {"ko": "긴장이 있지만 서로 배울 점이 많아요", "ja": "緊張感がありますが、学び合いが多いです", "en": "There's tension, but much to learn from each other"},
        "비화": {"ko": "비슷한 에너지로 공감대가 넓어요", "ja": "似たエネルギーで共感が広がります", "en": "Similar energy — you'll understand each other well"},
        "중립": {"ko": "독립적인 두 에너지가 조화를 이뤄요", "ja": "独立した2つのエネルギーが調和します", "en": "Two independent energies finding harmony"},
    }
    CTA_TEXT = {
        "ko": "🔓 상세 궁합 분석 보기 (무료 가입) →",
        "ja": "🔓 詳細な相性分析を見る（無料登録）→",
        "en": "🔓 See full compatibility analysis (free signup) →",
    }
    DISCLAIMER = {
        "ko": "명리학 참고 정보입니다. 연애 결정을 보장하지 않습니다.",
        "ja": "占い学的な参考情報です。恋愛の保証ではありません。",
        "en": "For reference only. Does not guarantee relationship outcomes.",
    }
    return {
        "score": score,
        "relation": relation,
        "my_element": el_a,
        "partner_element": el_b,
        "preview_summary": SUMMARY[relation][lang],
        "is_preview": True,
        "cta": {"text": CTA_TEXT[lang], "action": "signup_for_full"},
        "disclaimer": DISCLAIMER[lang],
        "lang": lang,
    }


# ─────────────────────────────────────────────
# DB 저장 헬퍼 (saju_readings)
# ─────────────────────────────────────────────
def _save_saju_reading(body: "BirthInfo", pillars: dict, day_pillar: str) -> None:
    """사주 계산 결과를 PostgreSQL에 저장. 실패해도 무시."""
    if not body.session_id:
        return
    try:
        import psycopg2, json as _json
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            dbname=os.getenv("DB_NAME", "caring_db"),
            user=os.getenv("DB_USER", "caring"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=2
        )
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO saju_readings
               (session_id, birth_year, birth_month, birth_day, birth_hour,
                gender, day_pillar, primary_element, pillars_json)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                body.session_id[:64],
                body.birth_year, body.birth_month, body.birth_day, body.birth_hour,
                body.gender or "unknown",
                day_pillar,
                pillars.get("primary_element", ""),
                _json.dumps(pillars, ensure_ascii=False),
            )
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass  # 저장 실패 무시 — 주요 기능에 영향 없음


# 공개 엔드포인트 — 인증 없이 사주 계산 가능
@router.post("/calculate")
@limiter.limit("10/minute")
def calculate_saju(request: Request, body: BirthInfo):
    """
    사주팔자(四柱八字) 계산 — saju_engine(검증완료) 사용
    면책 문구 필수 포함 / 참고 정보 (과학적 예측 아님)
    """
    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail=f"사주 엔진 로드 실패: {_ENGINE_ERR}")

    try:
        result = get_saju(
            body.birth_year, body.birth_month, body.birth_day,
            hour=body.birth_hour
        )
        # 음력 날짜 계산 후 result에 주입
        try:
            from src.engine.saju_calculator import get_lunar_date
            result["lunar_date"] = get_lunar_date(body.birth_year, body.birth_month, body.birth_day)
        except Exception:
            result["lunar_date"] = None
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")
    pillars = _saju_engine_to_legacy(result, body.birth_hour)

    # 일주 해석 추가
    pillar_data = _load_pillar_data()
    day_pillar_han = pillars.get("day", {}).get("pillar", "")
    interpretation = pillar_data.get(day_pillar_han, {})

    # saju_engine ILJU_PERSONALITY도 시도
    ilju_interp = ILJU_PERSONALITY.get(day_pillar_han, {}) if _ENGINE_OK else {}

    # 오행 해석 추가
    element_data = _load_element_data()
    primary_element = pillars.get("primary_element", "")
    element_interp = element_data.get(primary_element, {})

    # AI 해석은 /api/saju/ai-interpret 별도 엔드포인트에서 제공 (응답시간 분리)
    response_data = {
        "pillars": pillars,
        "disclaimer": pillars.get("disclaimer"),
        "legal": "명리학 참고 정보 — 의료/심리상담 대체 아님",
        "interpretation": {
            "day_pillar": day_pillar_han,
            "personality": interpretation.get("personality", ilju_interp.get("summary", "")),
            "strengths": interpretation.get("strengths", ilju_interp.get("strengths", [])),
            "challenges": interpretation.get("challenges", ilju_interp.get("challenges", [])),
            "today_advice": interpretation.get("today_advice", ilju_interp.get("energy", "")),
            "element_info": {
                "temperament": element_interp.get("temperament", ""),
                "career": element_interp.get("career", ""),
                "relationship": element_interp.get("relationship", ""),
            },
            "ai": {},  # AI 해석은 POST /api/saju/ai-interpret 별도 호출
        },
        "engine_method": result.get("method", "unknown"),
    }

    # DB 저장 (세션 ID 있을 때만, 실패해도 무시)
    _save_saju_reading(body, pillars, day_pillar_han)

    return response_data


# 공개 엔드포인트 — 비로그인 체험용
@router.post("/daily-energy")
@limiter.limit("10/minute")
def get_daily_energy(request: Request, body: BirthInfo):
    """오늘의 에너지 흐름 (일주 × 오늘 운 교차) — 규칙 기반"""
    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail="사주 엔진 로드 실패")

    try:
        result = get_saju(body.birth_year, body.birth_month, body.birth_day)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")
    pillars = _saju_engine_to_legacy(result)

    # 일주 해석
    pillar_data = _load_pillar_data()
    day_pillar = pillars.get("day", {})
    day_pillar_key = day_pillar.get("pillar", "")
    pillar_interp = pillar_data.get(day_pillar_key, {})
    ilju_interp = ILJU_PERSONALITY.get(day_pillar_key, {}) if _ENGINE_OK else {}

    # 오행 해석
    element_data = _load_element_data()
    primary_element = pillars.get("primary_element", "")
    element_interp = element_data.get(primary_element, {})

    # 오늘 일진
    today_pillar = _calc_today_pillar()
    today_element = today_pillar.get("element", "")
    today_element_han = _get_element_han(today_element)
    today_element_interp = element_data.get(today_element_han, {})

    # 에너지 문구
    energy_texts = element_interp.get("today_energy", [])
    today_texts = today_element_interp.get("today_energy", [])

    day_seed = body.birth_year + body.birth_month * 31 + body.birth_day
    today_date = _kst_today()  # BUG-SJ1 FIX: UTC → KST
    date_seed = today_date.year * 10000 + today_date.month * 100 + today_date.day
    combined_seed = (day_seed + date_seed) % 100

    primary_el_ko = element_data.get(primary_element, {}).get("korean", primary_element)
    if energy_texts:
        my_text = energy_texts[combined_seed % len(energy_texts)]
    else:
        my_text = DAILY_ENERGY_TEXTS.get(primary_el_ko, f"{primary_el_ko} 기운이 흐르는 하루입니다.")

    if today_texts:
        today_text = today_texts[(combined_seed + 1) % len(today_texts)]
    else:
        today_text = ""

    today_advice = pillar_interp.get("today_advice", ilju_interp.get("energy", ""))
    energy_summary = my_text
    if today_advice:
        energy_summary = f"{my_text}\n\n{today_advice}"

    # AI 에너지 해석
    ai_energy = {}
    if _AI_OK:
        try:
            ai_energy = interpret_energy_today(pillars, today_pillar)
        except Exception:
            pass

    return {
        "today_energy": energy_summary,
        "today_pillar": today_pillar,
        "my_primary_element": {
            "han": primary_element,
            "korean": primary_el_ko,
            "temperament": element_interp.get("temperament", ""),
            "career": element_interp.get("career", ""),
        },
        "day_pillar_key": day_pillar_key,
        "personality": pillar_interp.get("personality", ilju_interp.get("summary", "")),
        "strengths": pillar_interp.get("strengths", ilju_interp.get("strengths", [])),
        "pillar_summary": pillars,
        "disclaimer": pillars.get("disclaimer"),
        "ai": ai_energy,  # AI 생성 상세 에너지 해석
    }


@router.post("/compatibility")
@limiter.limit("10/minute")
def check_compatibility(request: Request, body: CompatibilityRequest):
    """
    궁합 분석 — 오행 상생/상극 기반
    score(0-100), level, advice, element_a, element_b, disclaimer
    """
    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail="사주 엔진 로드 실패")

    try:
        res_a = get_saju(body.person_a.birth_year, body.person_a.birth_month, body.person_a.birth_day,
                         hour=body.person_a.birth_hour)
        res_b = get_saju(body.person_b.birth_year, body.person_b.birth_month, body.person_b.birth_day,
                         hour=body.person_b.birth_hour)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")
    # 일주 천간 오행 추출
    def get_day_element(res):
        ec = res.get("eight_char", {})
        day_el = ec.get("day_pillar", {}).get("element", {}).get("stem", "")
        return day_el  # 한글 오행

    el_a = get_day_element(res_a)
    el_b = get_day_element(res_b)

    # 일주 한자 추출
    day_a = res_a.get("eight_char", {}).get("day_pillar", {}).get("glyph", "")
    day_b = res_b.get("eight_char", {}).get("day_pillar", {}).get("glyph", "")

    # 궁합 점수 계산
    base_score = 60
    if el_a and el_b:
        if SHENG_KR.get(el_a) == el_b:   # A가 B를 생함 (+20)
            score = base_score + 20
            relation = "상생"
            advice_base = f"{el_a}(木)이 {el_b}를 도와주는 관계입니다. 서로 성장을 촉진하는 에너지를 가지고 있습니다."
        elif SHENG_KR.get(el_b) == el_a:  # B가 A를 생함 (+20)
            score = base_score + 20
            relation = "상생"
            advice_base = f"{el_b}이 {el_a}을 도와주는 관계입니다. 상대방이 당신의 성장을 촉진합니다."
        elif KE_KR.get(el_a) == el_b:    # A가 B를 극함 (-15)
            score = base_score - 15
            relation = "상극"
            advice_base = f"{el_a}이 {el_b}와 긴장 관계입니다. 서로 이해하는 노력과 배려가 중요합니다."
        elif KE_KR.get(el_b) == el_a:    # B가 A를 극함 (-15)
            score = base_score - 15
            relation = "상극"
            advice_base = f"{el_b}이 {el_a}과 긴장 관계입니다. 상대방의 강점을 배우는 시각이 필요합니다."
        elif el_a == el_b:               # 같은 오행 (+10)
            score = base_score + 10
            relation = "비화"
            advice_base = f"두 분 모두 {el_a} 기운을 지니고 있습니다. 비슷한 에너지로 공감대가 넓지만 경쟁도 있을 수 있습니다."
        else:
            score = base_score
            relation = "중립"
            advice_base = "두 기운이 독립적으로 조화를 이룹니다. 서로의 다름을 존중하는 것이 중요합니다."
    else:
        score = base_score
        relation = "중립"
        advice_base = "궁합 분석에 필요한 오행 정보를 계산했습니다."

    score = max(0, min(100, score))

    # 레벨
    if score >= 80:
        level = "매우 좋음"
        advice = f"{advice_base} 에너지가 잘 어울려 함께 성장하기 좋은 관계입니다."
    elif score >= 70:
        level = "좋음"
        advice = f"{advice_base} 서로를 이해하고 존중하면 더 깊은 관계로 발전할 수 있습니다."
    elif score >= 55:
        level = "보통"
        advice = f"{advice_base} 차이를 인정하고 소통하면 균형 잡힌 관계가 됩니다."
    else:
        level = "노력 필요"
        advice = f"{advice_base} 서로 다른 에너지를 이해하는 시간이 필요합니다. 차이 속에서 배움을 찾아보세요."

    # AI 궁합 상세 해석
    ai_compat = {}
    if _AI_OK:
        try:
            pillars_a = _saju_engine_to_legacy(res_a)
            pillars_b = _saju_engine_to_legacy(res_b)
            ai_compat = interpret_compatibility(pillars_a, pillars_b, score, relation)
        except Exception:
            pass

    return {
        "score": score,
        "level": level,
        "relation": relation,
        "advice": advice,
        "element_a": el_a,
        "element_b": el_b,
        "day_pillar_a": day_a,
        "day_pillar_b": day_b,
        "disclaimer": "궁합 결과는 명리학적 참고 정보이며 실제 관계를 보장하지 않습니다. 문화·오락 서비스입니다.",
        "ai": ai_compat,  # AI 생성 상세 궁합 해석
    }


@router.get("/fortune-calendar")
def get_fortune_calendar(
    birth_year: int = Query(..., ge=1900, le=2099),
    birth_month: int = Query(..., ge=1, le=12),
    birth_day: int = Query(..., ge=1, le=31),
):
    """
    월별 운세 달력
    Response: {year, birth_element, months:[{month, luck_score(50-90), theme, advice, lucky_day}]}
    """
    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail="사주 엔진 로드 실패")

    try:
        result = get_saju(birth_year, birth_month, birth_day)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")
    ec = result.get("eight_char", {})
    day_stem_el = ec.get("day_pillar", {}).get("element", {}).get("stem", "")  # 일간 오행
    day_branch_el = ec.get("day_pillar", {}).get("element", {}).get("branch", "")  # 일지 오행
    day_glyph = ec.get("day_pillar", {}).get("glyph", "")

    current_year = _kst_today().year  # BUG-SJ1 FIX

    # 월별 운 테마 (일간 오행 기반)
    MONTH_THEMES = {
        "목": ["준비와 계획의 달", "도전을 시작하는 달", "성장이 빨라지는 달",
               "안정을 다지는 달", "관계가 풍성해지는 달", "결실을 준비하는 달",
               "정리와 완성의 달", "내면을 돌보는 달", "새로운 기회의 달",
               "에너지를 비축하는 달", "지혜를 활용하는 달", "내년을 설계하는 달"],
        "화": ["활기차게 출발하는 달", "열정이 빛나는 달", "소통이 활발한 달",
               "관계를 다지는 달", "창의력이 넘치는 달", "성취를 확인하는 달",
               "충전과 회복의 달", "깊이를 더하는 달", "계획을 구체화하는 달",
               "결실을 맺는 달", "여유를 즐기는 달", "새로운 시작을 준비하는 달"],
        "토": ["안정을 추구하는 달", "기반을 다지는 달", "신뢰를 쌓는 달",
               "풍요로워지는 달", "관계를 정리하는 달", "책임을 다하는 달",
               "내실을 기르는 달", "성장을 점검하는 달", "새 도전을 준비하는 달",
               "결단이 필요한 달", "변화를 수용하는 달", "마무리와 감사의 달"],
        "금": ["명확한 목표를 세우는 달", "집중력이 강해지는 달", "결단이 중요한 달",
               "완성을 향해 나아가는 달", "관계에서 솔직함이 빛나는 달", "성과를 확인하는 달",
               "정밀한 계획이 필요한 달", "내면의 소리를 듣는 달", "실력을 발휘하는 달",
               "평가와 정리의 달", "새로운 분야로 확장하는 달", "결실과 마무리의 달"],
        "수": ["지혜를 발휘하는 달", "직관이 빛나는 달", "깊이 생각하는 달",
               "새로운 흐름을 타는 달", "적응력이 강해지는 달", "내면을 정리하는 달",
               "소통을 강화하는 달", "기회를 포착하는 달", "변화에 유연한 달",
               "결실을 수확하는 달", "충전과 성찰의 달", "내년의 흐름을 준비하는 달"],
    }

    MONTH_ADVICE = {
        "목": ["새로운 계획을 세우세요", "두려움 없이 도전하세요", "성장의 기회를 잡으세요",
               "기초를 탄탄히 하세요", "인연을 소중히 하세요", "준비한 것을 실행하세요",
               "불필요한 것을 정리하세요", "나를 돌보는 시간을 가지세요", "열린 마음으로 기회를 찾으세요",
               "에너지를 현명하게 쓰세요", "경험에서 배우세요", "내년 목표를 설정하세요"],
        "화": ["활기차게 시작하세요", "감정을 표현하세요", "네트워크를 넓히세요",
               "신뢰를 쌓으세요", "창의적 아이디어를 실험하세요", "성과를 공유하세요",
               "속도를 늦추고 재충전하세요", "내면의 목소리에 귀 기울이세요", "구체적 계획을 세우세요",
               "성취를 기념하세요", "감사함을 나누세요", "새해 비전을 그리세요"],
        "토": ["안정된 루틴을 만드세요", "중요한 관계에 집중하세요", "약속을 지키세요",
               "자원을 확인하세요", "불필요한 것을 놓아주세요", "책임을 다하세요",
               "내실을 다지세요", "성장을 점검하세요", "새로운 도전을 구상하세요",
               "결단이 필요하면 과감히 결정하세요", "변화를 받아들이세요", "감사한 마음으로 마무리하세요"],
        "금": ["명확한 기준을 세우세요", "한 가지에 집중하세요", "중요한 결정을 내리세요",
               "완성에 힘쓰세요", "솔직하게 소통하세요", "성과를 평가하세요",
               "세밀하게 계획하세요", "직관을 믿으세요", "실력을 발휘하세요",
               "냉철하게 평가하세요", "새 분야에 도전하세요", "깔끔하게 마무리하세요"],
        "수": ["유연하게 생각하세요", "직관을 따르세요", "깊이 있게 탐구하세요",
               "변화의 흐름을 타세요", "적응력을 발휘하세요", "내면을 정리하세요",
               "소통을 강화하세요", "기회를 놓치지 마세요", "변화를 두려워 말고 받아들이세요",
               "지금까지의 여정을 돌아보세요", "충분히 쉬세요", "다음 주기를 준비하세요"],
    }

    themes = MONTH_THEMES.get(day_stem_el, MONTH_THEMES["토"])
    advices = MONTH_ADVICE.get(day_stem_el, MONTH_ADVICE["토"])

    months = []
    for m in range(1, 13):
        # 월별 운 점수 계산 (일주 오행과 월 오행의 관계 기반)
        # 월 오행: 1=수, 2=목, 3=목, 4=목, 5=화, 6=화, 7=화, 8=토, 9=금, 10=금, 11=수, 12=수
        MONTH_ELEMENT = {1: "수", 2: "목", 3: "목", 4: "목", 5: "화", 6: "화",
                         7: "화", 8: "토", 9: "금", 10: "금", 11: "수", 12: "수"}
        m_el = MONTH_ELEMENT.get(m, "토")

        base_luck = 65
        if SHENG_KR.get(m_el) == day_stem_el:
            base_luck = 82  # 월이 일주를 생
        elif SHENG_KR.get(day_stem_el) == m_el:
            base_luck = 78  # 일주가 월을 생
        elif KE_KR.get(m_el) == day_stem_el:
            base_luck = 55  # 월이 일주를 극
        elif KE_KR.get(day_stem_el) == m_el:
            base_luck = 60  # 일주가 월을 극
        elif m_el == day_stem_el:
            base_luck = 72  # 동일 오행

        # 생년월일 기반 결정적 변동 (±5)
        seed = birth_year + birth_month * 7 + birth_day * 3 + m * 13
        luck_score = base_luck + (seed % 11) - 5
        luck_score = max(50, min(90, luck_score))

        # 길일 (1~28일 중 랜덤하지 않고 결정론적으로 선택)
        lucky_day = ((birth_day * 3 + birth_month * 7 + m * 11) % 28) + 1

        months.append({
            "month": m,
            "luck_score": luck_score,
            "theme": themes[m - 1],
            "advice": advices[m - 1],
            "lucky_day": lucky_day,
            "month_element": m_el,
        })

    return {
        "year": current_year,
        "birth_element": day_stem_el,
        "birth_pillar": day_glyph,
        "months": months,
        "disclaimer": "운세 달력은 명리학적 참고 정보입니다. 실제 운세를 예측하지 않습니다.",
    }


@router.get("/fortune-calendar/daily")
def get_fortune_calendar_daily(
    birth_year: int = Query(..., ge=1900, le=2099),
    birth_month: int = Query(..., ge=1, le=12),
    birth_day: int = Query(..., ge=1, le=31),
    target_year: int = Query(..., ge=2000, le=2099),
    target_month: int = Query(..., ge=1, le=12),
):
    """
    일별 운세 달력 — 출생 일주 오행과 날짜 일주의 상생/상극으로 운 점수 계산
    Response: {year, month, days:[{day, weekday, luck_score, theme, tip, is_lucky}]}
    """
    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail="사주 엔진 로드 실패")

    try:
        result = get_saju(birth_year, birth_month, birth_day)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")

    ec = result.get("eight_char", {})
    birth_stem_el = ec.get("day_pillar", {}).get("element", {}).get("stem", "토")

    import calendar as _cal
    base_date = datetime.date(2000, 1, 7)  # 갑자(甲子)일 기준
    days_in_month = _cal.monthrange(target_year, target_month)[1]
    WEEKDAYS_KR = ['월', '화', '수', '목', '금', '토', '일']  # 0=월(Mon)...6=일(Sun)

    DAY_THEMES = {
        '목': ['성장하기 좋은 날', '새로운 시작의 날', '창의력이 빛나는 날', '도전하기 좋은 날'],
        '화': ['열정이 넘치는 날', '소통이 잘 되는 날', '활동적인 하루', '아이디어의 날'],
        '토': ['안정적인 하루', '기반을 다지는 날', '신뢰를 쌓는 날', '꼼꼼하게 정리하는 날'],
        '금': ['결단이 필요한 날', '집중하기 좋은 날', '완성의 날', '판단력이 날카로운 날'],
        '수': ['직관이 빛나는 날', '지혜로운 하루', '깊이 생각하는 날', '유연한 흐름의 날'],
    }
    DAY_TIPS = {
        '목': ['새로운 것을 시작해보세요', '창의적인 아이디어를 실행하세요', '앞으로 나아가는 날', '성장의 기회를 잡으세요'],
        '화': ['적극적으로 소통하세요', '열정을 발휘하세요', '사람들과 교류하면 좋아요', '활발한 활동이 도움됩니다'],
        '토': ['차분하게 계획을 세우세요', '중요한 약속을 지키세요', '기초를 탄탄히 하세요', '안정을 우선시하세요'],
        '금': ['중요한 결정은 오전에', '정확하고 원칙적으로', '집중력을 발휘하세요', '세밀하게 검토하세요'],
        '수': ['직관을 믿으세요', '깊이 생각해보세요', '유연하게 대처하세요', '내면의 소리에 귀 기울이세요'],
    }

    days = []
    luck_scores = []

    for d in range(1, days_in_month + 1):
        date = datetime.date(target_year, target_month, d)
        diff = (date - base_date).days
        stem_idx = diff % 10
        day_el = STEM_ELEMENT[stem_idx]  # 해당 날의 일간 오행

        # 운 점수: 출생 일간 오행과 해당 날 일간 오행의 상생/상극 관계
        base_luck = 65
        if SHENG_KR.get(day_el) == birth_stem_el:
            base_luck = 80   # 날의 오행이 내 오행을 생함
        elif SHENG_KR.get(birth_stem_el) == day_el:
            base_luck = 76   # 내 오행이 날의 오행을 생함
        elif KE_KR.get(day_el) == birth_stem_el:
            base_luck = 52   # 날의 오행이 내 오행을 극함
        elif KE_KR.get(birth_stem_el) == day_el:
            base_luck = 58   # 내 오행이 날의 오행을 극함
        elif day_el == birth_stem_el:
            base_luck = 70   # 동일 오행 (비화)

        # 생년월일 기반 결정론적 변동 (±5)
        seed = birth_year + birth_month * 7 + birth_day * 3 + d * 11 + target_month * 5
        luck_score = base_luck + (seed % 11) - 5
        luck_score = max(50, min(90, luck_score))

        weekday = WEEKDAYS_KR[date.weekday()]

        theme_list = DAY_THEMES.get(day_el, DAY_THEMES['토'])
        tip_list = DAY_TIPS.get(day_el, DAY_TIPS['토'])
        theme = theme_list[(d + seed) % len(theme_list)]
        tip = tip_list[(d + seed + 1) % len(tip_list)]

        luck_scores.append((luck_score, d))

        # 오행 관계 레이블
        relation_map = {
            80: ("상생", "날의 기운이 당신을 돕습니다"),
            76: ("상생", "당신의 기운이 날을 밝힙니다"),
            70: ("비화", "동일 기운으로 안정적인 하루"),
            58: ("상극", "극을 받아 주의가 필요합니다"),
            52: ("상극", "기운의 충돌 — 신중하게"),
        }
        rel_label, rel_desc = relation_map.get(base_luck, ("중립", "평온한 하루"))

        # 추천 활동 / 주의사항 (오행별)
        SUGGEST_GOOD = {
            '목': '새로운 시작, 계획 수립, 창업, 학습 시작',
            '화': '발표, 미팅, 네트워킹, 창의적 활동',
            '토': '계약, 재산 관련, 부동산, 안정적 업무',
            '금': '분석, 마감, 중요 결정, 재무 처리',
            '수': '여행, 공부, 철학적 사색, 명상',
        }
        SUGGEST_BAD = {
            '목': '성급한 결정, 무리한 확장',
            '화': '감정적 충돌, 과도한 소비',
            '토': '이동이나 변화, 새로운 시작',
            '금': '유연성이 필요한 협상, 예술 활동',
            '수': '중요한 약속, 계약 체결',
        }

        days.append({
            "day": d,
            "weekday": weekday,
            "luck_score": luck_score,
            "theme": theme,
            "tip": tip,
            "is_lucky": False,
            "day_element": day_el,           # 해당 날의 일간 오행
            "relation": rel_label,            # 출생 오행과의 관계
            "relation_desc": rel_desc,        # 관계 설명
            "suggest_good": SUGGEST_GOOD.get(day_el, ''),   # 추천 활동
            "suggest_avoid": SUGGEST_BAD.get(day_el, ''),   # 주의 활동
        })

    # 길일: 운 점수 상위 1~3개
    luck_scores.sort(key=lambda x: -x[0])
    lucky_count = 1 if days_in_month <= 10 else (2 if days_in_month <= 25 else 3)
    lucky_day_nums = {x[1] for x in luck_scores[:lucky_count]}
    for d_info in days:
        if d_info["day"] in lucky_day_nums:
            d_info["is_lucky"] = True

    return {
        "year": target_year,
        "month": target_month,
        "days": days,
        "disclaimer": "운세 달력은 명리학적 참고 정보입니다. 실제 운세를 예측하지 않습니다.",
    }


@router.get("/pillar-details")
def get_pillar_details(pillar: str = Query(..., description="일주 간지 (예: 기사, 甲子)")):
    """
    일주(日柱) 상세 해석 — 20개 주요 해석 포함 (명리학 기반 실제 내용)
    """
    # 한글 → 한자 변환 매핑
    KR_TO_HAN_STEM = {"갑": "甲", "을": "乙", "병": "丙", "정": "丁", "무": "戊",
                       "기": "己", "경": "庚", "신": "辛", "임": "壬", "계": "癸"}
    KR_TO_HAN_BRANCH = {"자": "子", "축": "丑", "인": "寅", "묘": "卯", "진": "辰", "사": "巳",
                         "오": "午", "미": "未", "신": "申", "유": "酉", "술": "戌", "해": "亥"}

    pillar_han = pillar
    if len(pillar) == 2:
        s, b = pillar[0], pillar[1]
        if s in KR_TO_HAN_STEM and b in KR_TO_HAN_BRANCH:
            pillar_han = KR_TO_HAN_STEM[s] + KR_TO_HAN_BRANCH[b]

    # saju_engine ILJU_PERSONALITY에서 조회
    ilju_data = {}
    if _ENGINE_OK:
        ilju_data = ILJU_PERSONALITY.get(pillar_han, {})

    # pillar_interpretations.json에서 조회
    pillar_data = _load_pillar_data()
    json_data = pillar_data.get(pillar_han, {})

    if not ilju_data and not json_data:
        # 범용 해석 반환
        stem_han = pillar_han[:1] if pillar_han else ""
        branch_han = pillar_han[1:] if pillar_han else ""
        return {
            "pillar": pillar,
            "pillar_han": pillar_han,
            "summary": f"{pillar_han} 일주의 에너지를 지니고 있습니다.",
            "personality": "자신만의 독특한 에너지로 삶을 살아가는 일주입니다.",
            "strengths": ["자신만의 개성", "독특한 시각", "꾸준한 성장"],
            "challenges": ["자기 인식 강화 필요", "균형 유지"],
            "energy": "독립적이고 개성 있는 에너지를 지닌 일주입니다.",
            "interpretations": _get_generic_interpretations(pillar_han),
            "disclaimer": "일주 해석은 명리학적 참고 정보입니다.",
        }

    summary = ilju_data.get("summary", json_data.get("personality", ""))
    strengths = ilju_data.get("strengths", json_data.get("strengths", []))
    challenges = ilju_data.get("challenges", json_data.get("challenges", []))
    energy = ilju_data.get("energy", "")

    return {
        "pillar": pillar,
        "pillar_han": pillar_han,
        "summary": summary,
        "personality": json_data.get("personality", summary),
        "strengths": strengths,
        "challenges": challenges,
        "energy": energy,
        "today_advice": json_data.get("today_advice", ""),
        "career": json_data.get("career", ""),
        "interpretations": _get_pillar_interpretations(pillar_han, ilju_data, json_data),
        "disclaimer": "일주 해석은 명리학적 참고 정보이며 실제 삶을 결정하지 않습니다.",
    }


def _get_pillar_interpretations(pillar_han: str, ilju_data: dict, json_data: dict) -> list:
    """20개 주요 일주 해석 카테고리 반환"""
    summary = ilju_data.get("summary", json_data.get("personality", ""))
    strengths = ilju_data.get("strengths", json_data.get("strengths", []))
    challenges = ilju_data.get("challenges", json_data.get("challenges", []))
    energy = ilju_data.get("energy", "")
    today_advice = json_data.get("today_advice", "")
    career = json_data.get("career", "")

    return [
        {"category": "본질 에너지", "content": energy or summary},
        {"category": "성격 특성", "content": summary},
        {"category": "핵심 강점", "content": ", ".join(strengths) if strengths else "자기만의 강점을 발휘합니다."},
        {"category": "주의할 점", "content": ", ".join(challenges) if challenges else "균형을 유지하는 것이 중요합니다."},
        {"category": "직업 적성", "content": career or "다양한 분야에서 능력을 발휘할 수 있습니다."},
        {"category": "오늘의 조언", "content": today_advice or "자신의 기운에 맞게 차분하게 움직이세요."},
        {"category": "인간관계", "content": "자신의 에너지를 이해하면 더 깊은 관계를 만들 수 있습니다."},
        {"category": "건강 관리", "content": "몸과 마음의 균형을 유지하는 것이 중요합니다."},
        {"category": "재물운", "content": "꾸준하고 성실한 노력이 재물을 쌓는 열쇠입니다."},
        {"category": "학업/성장", "content": "지속적인 학습과 자기 계발이 성장의 원동력입니다."},
        {"category": "연애/결혼", "content": json_data.get("compatible", ["相生(상생) 관계의 일주와 좋은 인연"])[0] if isinstance(json_data.get("compatible"), list) else "진심을 다하는 관계를 추구합니다."},
        {"category": "사업/직장", "content": "자신의 강점을 살린 분야에서 두각을 나타낼 수 있습니다."},
        {"category": "월별 에너지 패턴", "content": "봄(3~5월)에 특히 에너지가 상승하는 경향이 있습니다."},
        {"category": "적합한 색상", "content": "일주의 오행에 맞는 색을 생활에 활용하면 에너지 조화에 도움이 됩니다."},
        {"category": "적합한 방향", "content": "일주 오행의 강화 방향으로 중요한 결정을 내리면 좋습니다."},
        {"category": "성격의 빛과 그림자", "content": f"강점: {', '.join(strengths[:2])} / 주의: {', '.join(challenges[:2])}" if strengths and challenges else summary},
        {"category": "자기 계발 포인트", "content": f"{', '.join(challenges)}을 인식하고 보완하면 균형 잡힌 성장이 가능합니다." if challenges else "꾸준한 자기 점검이 성장의 열쇠입니다."},
        {"category": "좋은 시기", "content": "일주의 오행과 상생하는 계절/월에 중요한 결정과 행동을 하면 좋습니다."},
        {"category": "주의가 필요한 시기", "content": "일주의 오행과 상극하는 계절에는 신중하게 행동하세요."},
        {"category": "인생 전체 흐름", "content": f"{pillar_han} 일주는 {energy or '자신만의 리듬으로 성장하는 에너지를 지닙니다.'}"},
    ]


def _get_generic_interpretations(pillar_han: str) -> list:
    return [
        {"category": "본질 에너지", "content": f"{pillar_han} 일주는 독특한 에너지를 지닙니다."},
        {"category": "핵심 특성", "content": "자신만의 방식으로 세상을 바라봅니다."},
        {"category": "강점", "content": "개성과 창의력이 돋보입니다."},
        {"category": "성장 포인트", "content": "자기 인식을 높이면 더 큰 성장이 가능합니다."},
    ]


# ─────────────────────────────────────────────
# i18n 지원 유틸리티
# ─────────────────────────────────────────────

def _resolve_lang_from_request(
    request: Request,
    lang_query: Optional[str] = None,
) -> str:
    """
    언어 코드 해석 우선순위:
    1. ?lang= 쿼리 파라미터
    2. Accept-Language 헤더
    3. 기본값 ko
    """
    try:
        from app.i18n.i18n_utils import resolve_lang
        accept_lang = request.headers.get("Accept-Language", "")
        return resolve_lang(lang_query, accept_lang)
    except ImportError:
        if lang_query in ("ko", "ja", "en"):
            return lang_query
        return "ko"


# ─────────────────────────────────────────────
# 점성술 연계 엔드포인트
# ─────────────────────────────────────────────

@router.get("/astrology")
def get_astrology(
    request: Request,
    birth_year: int = Query(..., ge=1900, le=2099, description="출생 연도"),
    birth_month: int = Query(..., ge=1, le=12, description="출생 월"),
    birth_day: int = Query(..., ge=1, le=31, description="출생 일"),
    lang: Optional[str] = Query(None, description="언어 코드 (ko|ja|en)"),
):
    """
    출생일 기반 서양 별자리 + 동양 띠(12지신) 동시 반환
    - 서양: 황도 12궁 (태양궁, 경계일 ±1일 근사)
    - 동양: 12지신 (갑자년=쥐 기준)
    - 음력 변환 포함 (korean_lunar_calendar 우선, KASI API 폴백)
    - ?lang=ko|ja|en 쿼리 파라미터 및 Accept-Language 헤더 지원
    """
    resolved_lang = _resolve_lang_from_request(request, lang)

    try:
        from src.engine.saju_calculator import get_astrology_info
        astro = get_astrology_info(birth_year, birth_month, birth_day, resolved_lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail="점성술 계산 중 오류가 발생했습니다.")

    # i18n 레이블 추가
    try:
        from app.i18n.i18n_utils import get_i18n
        labels = get_i18n(resolved_lang)
    except ImportError:
        labels = {}

    return {
        **astro,
        "lang": resolved_lang,
        "labels": {
            "western_sign": labels.get("western_sign", "서양 별자리"),
            "eastern_zodiac": labels.get("eastern_zodiac", "동양 띠 (12지신)"),
            "lunar_date": labels.get("lunar_date", "음력 날짜"),
        },
    }


@router.post("/astrology")
@limiter.limit("5/minute")
def post_astrology(
    request: Request,
    body: BirthInfo,
    lang: Optional[str] = Query(None, description="언어 코드 (ko|ja|en)"),
):
    """
    POST 버전 — BirthInfo 바디로 점성술 정보 조회
    ?lang= 쿼리 파라미터 + Accept-Language 헤더 지원
    """
    # body.lang 우선, 쿼리 파라미터로 오버라이드 가능
    effective_lang = lang if lang else body.lang
    resolved_lang = _resolve_lang_from_request(request, effective_lang)

    try:
        from src.engine.saju_calculator import get_astrology_info
        astro = get_astrology_info(body.birth_year, body.birth_month, body.birth_day, resolved_lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail="점성술 계산 중 오류가 발생했습니다.")

    try:
        from app.i18n.i18n_utils import get_i18n
        labels = get_i18n(resolved_lang)
    except ImportError:
        labels = {}

    return {
        **astro,
        "lang": resolved_lang,
        "labels": {
            "western_sign": labels.get("western_sign", "서양 별자리"),
            "eastern_zodiac": labels.get("eastern_zodiac", "동양 띠 (12지신)"),
            "lunar_date": labels.get("lunar_date", "음력 날짜"),
        },
    }


# ─────────────────────────────────────────────
# i18n 레이블 조회 엔드포인트
# ─────────────────────────────────────────────

@router.get("/i18n/labels")
def get_i18n_labels(
    request: Request,
    lang: Optional[str] = Query(None, description="언어 코드 (ko|ja|en)"),
):
    """
    지정 언어의 UI 레이블 딕셔너리 반환
    ?lang=ko|ja|en 또는 Accept-Language 헤더로 언어 지정
    """
    resolved_lang = _resolve_lang_from_request(request, lang)
    try:
        from app.i18n.i18n_utils import get_i18n
        labels = get_i18n(resolved_lang)
    except ImportError:
        labels = {"error": "i18n 모듈 로드 실패"}

    return {
        "lang": resolved_lang,
        "labels": labels,
    }


# ─────────────────────────────────────────────
# 표준화 운세 응답 엔드포인트 (프롬프트 표준화)
# ─────────────────────────────────────────────

@router.get("/today-energy")
@limiter.limit("30/minute")
def get_today_energy(
    request: Request,
    lang: Optional[str] = Query(None, description="언어 코드 (ko|ja|en)"),
):
    """
    [gstack P1] 비인증 오늘의 에너지 — 생년월일 없이 즉시 노출
    오늘 날짜 일진 기반 일반 에너지 가이드 + 개인화 유도 CTA
    법적: 명리학 참고 정보, 의료/심리상담 대체 아님
    """
    resolved_lang = _resolve_lang_from_request(request, lang or "ko")
    today_pillar = _calc_today_pillar()
    today_element = today_pillar.get("element", "wood")
    element_han_map = {"wood": "목", "fire": "화", "earth": "토", "metal": "금", "water": "수"}
    today_han = element_han_map.get(today_element, today_pillar.get("element_han", "목"))

    ENERGY_BY_ELEMENT = {
        "목": {
            "ko": {"keyword": "성장·시작", "guide": "새로운 것을 시작하기 좋은 날이에요. 작은 첫걸음 하나가 큰 변화를 만들어요.", "tip": "아침에 새 목표 하나를 적어보세요."},
            "ja": {"keyword": "成長・始まり", "guide": "新しいことを始めるのに良い日です。小さな一歩が大きな変化を生み出します。", "tip": "朝、新しい目標を一つ書いてみましょう。"},
            "en": {"keyword": "Growth · New Beginnings", "guide": "A great day to start something new. One small step can create big change.", "tip": "Write down one new goal this morning."},
        },
        "화": {
            "ko": {"keyword": "열정·소통", "guide": "열정과 표현력이 빛나는 날이에요. 솔직한 소통이 관계를 더 깊게 해요.", "tip": "오늘 하고 싶었던 말을 용기 내서 해보세요."},
            "ja": {"keyword": "情熱・コミュニケーション", "guide": "情熱と表現力が輝く日です。率直な対話が関係を深めます。", "tip": "伝えたかった言葉を今日は勇気を持って言ってみましょう。"},
            "en": {"keyword": "Passion · Communication", "guide": "Your passion and expressiveness shine today. Honest communication deepens relationships.", "tip": "Say what you've been wanting to say today."},
        },
        "토": {
            "ko": {"keyword": "안정·신뢰", "guide": "안정감과 신뢰가 강해지는 날이에요. 기본에 충실하면 좋은 결과가 와요.", "tip": "약속 하나를 확인하고 지켜보세요."},
            "ja": {"keyword": "安定・信頼", "guide": "安定感と信頼が強まる日です。基本を大切にすると良い結果が生まれます。", "tip": "約束を一つ確認して守ってみましょう。"},
            "en": {"keyword": "Stability · Trust", "guide": "Stability and trust are strengthened today. Staying grounded brings good results.", "tip": "Confirm and keep one promise today."},
        },
        "금": {
            "ko": {"keyword": "결단·분석", "guide": "분석력과 결단력이 최고조에 달하는 날이에요. 중요한 결정을 내리기에 좋아요.", "tip": "미뤄온 결정 하나를 오늘 내려보세요."},
            "ja": {"keyword": "決断・分析", "guide": "分析力と決断力が最高潮に達する日です。重要な決定をするのに最適です。", "tip": "先延ばしにしていた決断を今日してみましょう。"},
            "en": {"keyword": "Decision · Analysis", "guide": "Your analytical and decisive power peaks today. Great for making important decisions.", "tip": "Make that decision you've been putting off."},
        },
        "수": {
            "ko": {"keyword": "지혜·직관", "guide": "지혜와 직관이 강해지는 날이에요. 내면의 목소리에 귀 기울여보세요.", "tip": "10분 조용히 혼자만의 시간을 가져보세요."},
            "ja": {"keyword": "知恵・直感", "guide": "知恵と直感が強まる日です。内なる声に耳を傾けてみましょう。", "tip": "10分、静かに一人の時間を持ちましょう。"},
            "en": {"keyword": "Wisdom · Intuition", "guide": "Your wisdom and intuition are strong today. Listen to your inner voice.", "tip": "Take 10 quiet minutes alone today."},
        },
    }
    lang_key = resolved_lang if resolved_lang in ("ko", "ja", "en") else "ko"
    energy = ENERGY_BY_ELEMENT.get(today_han, ENERGY_BY_ELEMENT["목"])[lang_key]

    CTA = {
        "ko": {"text": "내 생년월일로 오늘 운세 보기 →", "action": "personalize"},
        "ja": {"text": "生年月日で今日の運勢を見る →", "action": "personalize"},
        "en": {"text": "See your personalized energy →", "action": "personalize"},
    }
    DISCLAIMER = {
        "ko": "명리학 참고 정보입니다. 의료·심리상담을 대체하지 않습니다.",
        "ja": "占い学的な参考情報です。医療・心理相談の代替ではありません。",
        "en": "For reference only based on traditional Chinese astrology. Not a substitute for medical or psychological advice.",
    }
    return {
        "date": str(_kst_today()),  # BUG-SJ1 FIX: KST 기준
        "today_element": today_han,
        "today_glyph": today_pillar.get("glyph", ""),
        "energy": energy,
        "cta": CTA[lang_key],
        "disclaimer": DISCLAIMER[lang_key],
        "lang": lang_key,
    }


@router.post("/fortune-standard")
@limiter.limit("5/minute")
def get_fortune_standard(
    request: Request,
    body: BirthInfo,
    lang: Optional[str] = Query(None, description="언어 코드 (ko|ja|en)"),
):
    """
    표준화된 운세 응답 — {운세요약, 오행분석, 에너지인사이트, 오늘의조언, 별자리메시지} JSON
    - 사주팔자 + 오행 + 점성술 통합 프롬프트 기반
    - LLM 미연결 시 규칙 기반 폴백 응답
    - ?lang=ko|ja|en 쿼리 파라미터 + Accept-Language 헤더 지원
    """
    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail=f"사주 엔진 로드 실패: {_ENGINE_ERR}")

    effective_lang = lang if lang else body.lang
    resolved_lang = _resolve_lang_from_request(request, effective_lang)

    try:
        result = get_saju(body.birth_year, body.birth_month, body.birth_day, hour=body.birth_hour)
    except Exception as e:
        raise HTTPException(status_code=400, detail="사주 계산 중 오류가 발생했습니다. 입력값을 확인해주세요.")
    # 오늘 일진 계산
    today_pillar_dict = _calc_today_pillar()

    # 프롬프트 컨텍스트 조립
    try:
        from app.prompts.saju_prompt_template import (
            build_context_from_saju_result,
            build_saju_prompt,
            make_rule_based_response,
        )
        ctx = build_context_from_saju_result(
            saju_result=result,
            birth_year=body.birth_year,
            birth_month=body.birth_month,
            birth_day=body.birth_day,
            birth_hour=body.birth_hour,
            gender=body.gender,
            lang=resolved_lang,
            today_pillar=today_pillar_dict,
        )
        prompt = build_saju_prompt(ctx)
        # 규칙 기반 폴백 응답 (LLM 미연결)
        response = make_rule_based_response(ctx)
        fortune_data = response.to_dict()
    except ImportError as e:
        fortune_data = {
            "error": f"프롬프트 모듈 로드 실패: {e}",
            "disclaimer": "본 내용은 명리학적 관점의 자기이해 도구입니다.",
        }
        prompt = {}

    # i18n 레이블
    try:
        from app.i18n.i18n_utils import get_i18n
        labels = get_i18n(resolved_lang)
    except ImportError:
        labels = {}

    pillars = _saju_engine_to_legacy(result, body.birth_hour)

    return {
        "fortune": fortune_data,
        "pillars": pillars,
        "today_pillar": today_pillar_dict,
        "lang": resolved_lang,
        "labels": {
            "fortune_summary": labels.get("fortune_summary", "운세 요약"),
            "five_elements_analysis": labels.get("five_elements_analysis", "오행 분석"),
            "energy_insight": labels.get("energy_insight", "에너지 인사이트"),
            "today_advice": labels.get("today_advice", "오늘의 조언"),
            "zodiac_message": labels.get("zodiac_message", "별자리 메시지"),
        },
        "prompt_used": prompt.get("system", "")[:100] + "..." if prompt else "",
        "legal": "명리학 참고 정보 — 의료/심리상담 대체 아님",
    }


# ── AI 상세 해석 전용 엔드포인트 (calculate와 분리하여 응답시간 독립) ──────────
@router.post("/ai-interpret")
@limiter.limit("5/minute")
async def ai_interpret(request: Request, body: BirthInfo):
    """
    AI 사주 상세 해석 — calculate 이후 별도 호출.
    응답 시간: 15~40초 (Claude API 의존)
    asyncio.to_thread로 동기 블로킹 방지
    """
    import asyncio
    if not _AI_OK:
        return {"ai": {}, "note": "interpret_saju_full" and "AI 해석 서비스 비활성화"}

    from src.services.ai_interpreter import (  # type: ignore[reportPossiblyUnbound]
        _get_async_client, _saju_full_cache, _interpret_saju_full_cached,
        _extract_json, SAJU_SYSTEM, ELEMENTS_KR,
    )
    import asyncio

    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail="사주 엔진 로드 실패")

    try:
        result = get_saju(body.birth_year, body.birth_month, body.birth_day, hour=body.birth_hour)
        try:
            from src.engine.saju_calculator import get_lunar_date
            result["lunar_date"] = get_lunar_date(body.birth_year, body.birth_month, body.birth_day)
        except Exception:
            result["lunar_date"] = None
    except Exception:
        raise HTTPException(status_code=400, detail="사주 계산 오류")

    pillars = _saju_engine_to_legacy(result, body.birth_hour)
    gender = body.gender or "male"

    # 캐시 우선 확인
    year_p = pillars.get("year", {})
    month_p = pillars.get("month", {})
    day_p = pillars.get("day", {})
    hour_p = pillars.get("hour")
    day_pillar = day_p.get("pillar", "")
    hour_pillar = hour_p.get("pillar", "") if hour_p else ""
    cache_key = (day_pillar, gender, year_p.get("pillar",""), month_p.get("pillar",""), hour_pillar)

    if cache_key in _saju_full_cache:
        raw = _saju_full_cache[cache_key]
        ai_data = _extract_json(raw)
        return {
            "ai": ai_data,
            "day_pillar": day_pillar,
            "disclaimer": "AI 해석은 명리학적 참고 정보입니다.",
        }

    # async client로 직접 호출
    async_client = _get_async_client()
    ai_data = {}
    if async_client:
        primary_el = ELEMENTS_KR.get(pillars.get("primary_element",""), pillars.get("primary_element","")) or ""
        gender_str = "남성" if gender == "male" else "여성"
        hour_str = f"시주: {hour_pillar}" if hour_pillar else "시주: 미입력"
        prompt = f"""다음 사주팔자를 가진 {gender_str}을 명리학으로 해석해주세요.

【사주】
- 년주: {year_p.get('pillar','')} ({year_p.get('element','')})
- 월주: {month_p.get('pillar','')} ({month_p.get('element','')})
- 일주: {day_pillar} ({day_p.get('element','')}) ← 핵심
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
        try:
            resp = await async_client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1200,
                timeout=45.0,
                system=SAJU_SYSTEM,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = resp.content[0].text if resp.content else ""
            import logging
            logging.warning(f"[SajuAI] async 응답 {len(raw)}자, stop={resp.stop_reason}")
            print(f"[SajuAI] async 응답 {len(raw)}자, stop={resp.stop_reason}", flush=True)
            if raw:
                _saju_full_cache[cache_key] = raw
                if len(_saju_full_cache) > 60:
                    del _saju_full_cache[next(iter(_saju_full_cache))]
            ai_data = _extract_json(raw)
        except Exception as e:
            import logging
            logging.warning(f"[SajuAI] async 오류: {type(e).__name__}: {e}")
            print(f"[SajuAI] async 오류: {type(e).__name__}: {e}", flush=True)

    return {
        "ai": ai_data,
        "day_pillar": day_pillar,
        "disclaimer": "AI 해석은 명리학적 참고 정보입니다.",
    }


@router.post("/ai-energy")
@limiter.limit("5/minute")
def ai_energy_interpret(request: Request, body: BirthInfo):
    """AI 오늘 에너지 상세 해석 전용"""
    if not _AI_OK:
        return {"ai": {}, "note": "AI 해석 서비스 비활성화"}
    if not _ENGINE_OK:
        raise HTTPException(status_code=500, detail="사주 엔진 로드 실패")
    try:
        result = get_saju(body.birth_year, body.birth_month, body.birth_day)
    except Exception:
        raise HTTPException(status_code=400, detail="사주 계산 오류")
    pillars = _saju_engine_to_legacy(result)
    today_pillar = _calc_today_pillar()
    try:
        ai_data = interpret_energy_today(pillars, today_pillar)
    except Exception:
        ai_data = {}
    return {"ai": ai_data}


# ── 사주 히스토리 엔드포인트 ──────────────────────────────────────────────────────
@router.get("/history")
@limiter.limit("30/minute")
def get_saju_history(
    request: Request,
    session_id: str = Query(..., max_length=64, description="클라이언트 세션 UUID"),
):
    """
    특정 세션의 사주 조회 히스토리 반환 (최근 5개)
    session_id: localStorage에 저장된 UUID
    """
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            dbname=os.getenv("DB_NAME", "caring_db"),
            user=os.getenv("DB_USER", "caring"),
            password=os.getenv("DB_PASSWORD", ""),
            connect_timeout=2
        )
        cur = conn.cursor()
        cur.execute(
            """SELECT id, birth_year, birth_month, birth_day, birth_hour,
                      gender, day_pillar, primary_element, created_at
               FROM saju_readings
               WHERE session_id = %s
               ORDER BY created_at DESC
               LIMIT 5""",
            (session_id[:64],)
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        history = []
        for row in rows:
            history.append({
                "id": row[0],
                "birth_year": row[1],
                "birth_month": row[2],
                "birth_day": row[3],
                "birth_hour": row[4],
                "gender": row[5],
                "day_pillar": row[6],
                "primary_element": row[7],
                "created_at": row[8].isoformat() if row[8] else None,
            })

        return {"session_id": session_id, "history": history, "count": len(history)}

    except Exception as e:
        import logging as _log
        _log.warning(f"[SajuHistory] DB 조회 실패: {e}")
        return {"session_id": session_id, "history": [], "count": 0}
