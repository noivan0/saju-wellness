"""
사주팔자(四柱八字) 계산 엔진
Nova Saju Project B - 사주+감정코칭

의존: pip install lunar-python
fallback 알고리즘 내장 (lunar-python 없어도 동작, 단 월주 절기 반영 안됨)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import datetime


# ─────────────────────────────────────────────
# 1. 기본 상수
# ─────────────────────────────────────────────

HEAVENLY_STEMS   = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
EARTHLY_BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
STEM_KR   = ["갑","을","병","정","무","기","경","신","임","계"]
BRANCH_KR = ["자","축","인","묘","진","사","오","미","신","유","술","해"]

# [P2 헤르2 리서치 반영] 3개국어 용어 대응표
STEM_JA   = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEM_EN   = ["Jiǎ","Yǐ","Bǐng","Dīng","Wù","Jǐ","Gēng","Xīn","Rén","Guǐ"]

BRANCH_JA = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BRANCH_EN = ["Rat","Ox","Tiger","Rabbit","Dragon","Snake",
             "Horse","Goat","Monkey","Rooster","Dog","Pig"]

ELEMENT_KR = ["목","화","토","금","수"]
ELEMENT_JA = ["木","火","土","金","水"]
ELEMENT_EN = ["Wood","Fire","Earth","Metal","Water"]

# 앱 핵심 용어 (법적: 의료 표현 회피)
TERMS_I18N = {
    "일주": {"ko": "일주(日柱)", "ja": "日柱(にっちゅう)", "en": "Day Pillar"},
    "대운": {"ko": "대운(大運)", "ja": "大運(だいうん)",    "en": "Major Cycle"},
    "상생": {"ko": "상생(相生)", "ja": "相生(そうせい)",    "en": "Generative Cycle"},
    "상극": {"ko": "상극(相剋)", "ja": "相剋(そうこく)",    "en": "Controlling Cycle"},
    "음양": {"ko": "음양(陰陽)", "ja": "陰陽(いんよう)",    "en": "Yin and Yang"},
    "에너지": {"ko": "기운·흐름", "ja": "運気(うんき)·流れ", "en": "energy patterns·life rhythm"},
}
STEM_ELEMENT   = ["목","목","화","화","토","토","금","금","수","수"]
BRANCH_ELEMENT = ["수","토","목","목","토","화","화","토","금","금","토","수"]
STEM_YIN_YANG   = ["양","음","양","음","양","음","양","음","양","음"]
BRANCH_YIN_YANG = ["양","음","양","음","양","음","양","음","양","음","양","음"]

# 시(時) -> 지지 인덱스 (자=0 ~ 해=11), 인덱스=hour(0~23)
# 전통 명리학 12지시 2시간 배당 (KST 기준):
# 子자시 23:00~01:00 → 0,1시 = index 0  (23시는 배열 끝에서 처리)
# 丑축시 01:00~03:00 → 단, 01:00은 자시에 포함 → 02,03시 = index 1
# 寅인시 03:00~05:00 → 04,05시 = index 2  (03:00은 인시 시작이지만 관행상 02,03 = 축시)
# 실제 전통 기준: 자시 23~01, 축시 01~03, ... (1시 = 자시 경계, 관습에 따라 다름)
# 가장 보편적 기준 적용: 각 시의 시작 정각 기준
# 자시: 23, 0 / 축시: 1, 2 / 인시: 3, 4 / ... / 해시: 21, 22
HOUR_TO_BRANCH = [0,0,1,1,2,2,3,3,4,4,5,5,6,6,7,7,8,8,9,9,10,10,11,11]
# 인덱스 0(0시)=자, 1(1시)=자, 2(2시)=축, 3(3시)=축, ...
# 23시는 자시(0): 별도 처리 필요 - get_saju()의 h 전달 시 23→자시

ELEMENT_SHENG = {"목":"화","화":"토","토":"금","금":"수","수":"목"}
ELEMENT_KE    = {"목":"토","토":"수","수":"화","화":"금","금":"목"}


# ─────────────────────────────────────────────
# 2. 데이터 클래스
# ─────────────────────────────────────────────

@dataclass
class Pillar:
    stem_idx: int
    branch_idx: int

    @property
    def stem(self) -> str:
        return HEAVENLY_STEMS[self.stem_idx]

    @property
    def branch(self) -> str:
        return EARTHLY_BRANCHES[self.branch_idx]

    @property
    def glyph(self) -> str:
        return self.stem + self.branch

    @property
    def reading(self) -> str:
        return STEM_KR[self.stem_idx] + BRANCH_KR[self.branch_idx]

    @property
    def element(self) -> dict:
        return {
            "stem": STEM_ELEMENT[self.stem_idx],
            "branch": BRANCH_ELEMENT[self.branch_idx],
            "yin_yang_stem": STEM_YIN_YANG[self.stem_idx],
            "yin_yang_branch": BRANCH_YIN_YANG[self.branch_idx],
        }

    def to_dict(self) -> dict:
        return {"glyph": self.glyph, "reading": self.reading, "element": self.element}


@dataclass
class EightChar:
    year: Pillar
    month: Pillar
    day: Pillar
    hour: Pillar

    @property
    def eight_glyphs(self) -> str:
        return "".join(p.glyph for p in [self.year, self.month, self.day, self.hour])

    @property
    def stems(self) -> list:
        return [p.stem for p in [self.year, self.month, self.day, self.hour]]

    @property
    def branches(self) -> list:
        return [p.branch for p in [self.year, self.month, self.day, self.hour]]

    def to_dict(self) -> dict:
        return {
            "year_pillar":  self.year.to_dict(),
            "month_pillar": self.month.to_dict(),
            "day_pillar":   self.day.to_dict(),
            "hour_pillar":  self.hour.to_dict(),
            "eight_glyphs": self.eight_glyphs,
            "stems":        self.stems,
            "branches":     self.branches,
        }


# ─────────────────────────────────────────────
# 3. 계산 함수
# ─────────────────────────────────────────────

def _calc_lunar_python(y, m, d, h, mi) -> EightChar:
    """lunar-python 라이브러리 (절기 기준, 정확)"""
    from lunar_python import Solar
    solar = Solar.fromYmdHms(y, m, d, h, mi, 0)
    ec = solar.getLunar().getEightChar()

    def parse(s):
        return Pillar(HEAVENLY_STEMS.index(s[0]), EARTHLY_BRANCHES.index(s[1]))

    return EightChar(parse(ec.getYear()), parse(ec.getMonth()), parse(ec.getDay()), parse(ec.getTime()))


def _calc_fallback(y, m, d, h, mi=0) -> EightChar:
    """간지 순환 fallback (절기 미반영, 오차 가능)"""
    y_stem = (y - 4) % 10
    y_branch = (y - 4) % 12
    ms = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0][y_stem]
    m_stem = (ms + m - 1) % 10
    m_branch = (2 + m - 1) % 12
    base = datetime.date(2000, 1, 7)
    diff = (datetime.date(y, m, d) - base).days
    d_stem = diff % 10
    d_branch = diff % 12
    h_branch = HOUR_TO_BRANCH[h]
    ts = [0, 2, 4, 6, 8, 0, 2, 4, 6, 8][d_stem]
    h_stem = (ts + h_branch) % 10
    return EightChar(
        Pillar(y_stem, y_branch),
        Pillar(m_stem, m_branch),
        Pillar(d_stem, d_branch),
        Pillar(h_stem, h_branch),
    )


def _calc(y, m, d, h, mi=0):
    # 자시(子時) 처리: 23시는 다음날 0시로 취급 (전통 명리학)
    # 자시 = 23:00~01:00. 23시는 당일 자시로 계산 (일주 변경 없음)
    # lunar-python은 hour=23 그대로 전달하면 자시로 계산함
    try:
        return _calc_lunar_python(y, m, d, h, mi), "lunar-python"
    except Exception:
        return _calc_fallback(y, m, d, h, mi), "fallback"


def _branch_time_range(idx):
    starts = [23, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
    ends = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
    return f"{starts[idx]:02d}:00~{ends[idx]:02d}:00"


# ─────────────────────────────────────────────
# 4. 메인 API
# ─────────────────────────────────────────────

def get_saju(year, month, day, hour=None, minute=0, longitude: float = 127.0):
    """
    사주팔자 계산 메인 API.

    Args:
        year, month, day: 생년월일 (양력)
        hour: 생시 (0~23). None이면 시 불명 처리
        minute: 분 (기본 0)
        longitude: 출생지 경도 (기본 127.0 = 서울). 진태양시 보정용.
                   글로벌 확장 시 필수. 일본(135°), 한국(127°), 중국(120°).
                   [헤르2 리서치 반영] ±30분 보정 범위, P2 활성화

    Returns dict:
        eight_char    - EightChar.to_dict()
        hour_unknown  - bool
        hour_variants - 12개 지지 변형 (시 불명 시), else None
        method        - "lunar-python" | "fallback"
        note          - 안내 문자열
    """
    # [MEDIUM FIX] 입력 범위 검증 — lunar-python 1582 미만 overflow 방지
    if not (1582 <= year <= 2100):
        raise ValueError(f"year 범위 초과 (1582~2100): {year}")
    if not (1 <= month <= 12):
        raise ValueError(f"month 범위 초과 (1~12): {month}")
    if not (1 <= day <= 31):
        raise ValueError(f"day 범위 초과 (1~31): {day}")
    if hour is not None and not (0 <= hour <= 23):
        raise ValueError(f"hour 범위 초과 (0~23): {hour}")
    if not (0 <= minute <= 59):
        raise ValueError(f"minute 범위 초과 (0~59): {minute}")

    # [P2] 진태양시(眞太陽時) 보정 — 경도 기반 (글로벌 확장 시 활성)
    # 표준시(KST=135°) vs 출생지 경도 차이 → 시간 보정
    # Korea: 127° (표준시 135° 기준 -8분), Japan: 135° (표준시와 일치)
    # 현재 MVP: 보정값 계산만, hour는 기존 방식 유지
    _solar_offset_min = (longitude - 135.0) * 4  # 1°당 4분
    # P2 완전 적용 시: hour += _solar_offset_min // 60 처리 추가 예정

    if hour is None:
        rh = [23, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
        variants = []
        for i in range(12):
            ec, _ = _calc(year, month, day, rh[i], 0)
            variants.append({
                "hour_branch":    EARTHLY_BRANCHES[i],
                "hour_branch_kr": BRANCH_KR[i],
                "time_range":     _branch_time_range(i),
                "eight_char":     ec.to_dict(),
            })
        default_ec, meth = _calc(year, month, day, 12, 0)
        return {
            "eight_char":    default_ec.to_dict(),
            "hour_unknown":  True,
            "hour_variants": variants,
            "method":        meth,
            "note":          "시(時) 미입력. 낮 12시(午時) 기본값. hour_variants에서 시주 선택 가능.",
        }

    ec, meth = _calc(year, month, day, hour, minute)
    return {
        "eight_char":    ec.to_dict(),
        "hour_unknown":  False,
        "hour_variants": None,
        "method":        meth,
        "note":          "",
    }


# ─────────────────────────────────────────────
# 5. 대운 계산
# ─────────────────────────────────────────────

def get_daewoon(year, month, day, hour=12, is_male=True):
    """대운 10개 (lunar-python 필요)"""
    try:
        from lunar_python import Solar
        solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
        yun = solar.getLunar().getEightChar().getYun(1 if is_male else 0)
        start = yun.getStartYear()
        return [
            {"order": i + 1, "age": start + i * 10, "glyph": dy.getGanZhi(),
             "start_year": dy.getStartYear(), "end_year": dy.getEndYear()}
            for i, dy in enumerate(yun.getDaYun()[:10])
        ]
    except Exception as e:
        return [{"error": str(e), "note": "lunar-python 미설치 시 대운 계산 불가"}]


# ─────────────────────────────────────────────
# 6. 감정 체크인 연동
# ─────────────────────────────────────────────

MOOD_MAP = {
    1: {"label": "매우 힘듦", "emoji": "😔", "elements": ["수", "토"]},
    2: {"label": "힘듦",      "emoji": "😢", "elements": ["금", "수"]},
    3: {"label": "보통",      "emoji": "😐", "elements": ["토"]},
    4: {"label": "좋음",      "emoji": "🙂", "elements": ["목", "화"]},
    5: {"label": "매우 좋음", "emoji": "😊", "elements": ["화", "목"]},
}

ACTION_MAP = {
    ("목", "매우 힘듦"): ["10분 산책 (나무 가까이)", "숨 크게 3번 내쉬기", "오늘 한 가지만 해내기"],
    ("목", "힘듦"):      ["스트레칭 5분", "좋아하는 차 한 잔", "소리 내어 책 한 쪽 읽기"],
    ("화", "매우 힘듦"): ["따뜻한 물 한 잔", "조명 바꿔 분위기 환기", "신뢰하는 한 명에게 짧은 안부"],
    ("화", "힘듦"):      ["음악 들으며 움직이기", "감사한 것 3가지 적기", "따뜻한 음식 먹기"],
    ("토", "매우 힘듦"): ["발 땅에 붙이고 천천히 숨쉬기", "단순 반복 집안일", "내일 할 일 1가지만 정하기"],
    ("토", "힘듦"):      ["규칙적인 식사 챙기기", "오늘 잠자리 정돈", "작은 완료 목록 만들기"],
    ("금", "매우 힘듦"): ["감정 종이에 적어 접기", "조용한 곳에서 10분 혼자 앉아 있기", "완벽하지 않아도 된다고 말하기"],
    ("금", "힘듦"):      ["불필요한 물건 1개 정리", "짧은 명상", "내가 잘한 것 1가지 인정하기"],
    ("수", "매우 힘듦"): ["따뜻한 물로 샤워 또는 족욕", "밝은 조명 켜기", "오늘 하루 생존한 자신 인정하기"],
    ("수", "힘듦"):      ["일기 또는 감정 기록", "내가 두려운 것 한 줄로 적기", "신체 따뜻하게 유지"],
}

DEFAULT_ACTIONS = {
    "매우 힘듦": ["오늘 버틴 것만으로 충분해요", "아무것도 안 해도 괜찮아요", "작은 위안 하나 찾아보기"],
    "힘듦":      ["짧은 산책", "좋아하는 것 먹기", "충분히 자기"],
    "보통":      ["평소 하던 일 유지", "새로운 작은 시도 하나", "가까운 사람에게 연락"],
    "좋음":      ["계획했던 일 실행하기", "에너지 쓸 곳에 투자", "좋은 감정 기록해두기"],
    "매우 좋음": ["가장 중요한 일 시작하기", "좋은 에너지 나누기", "결실을 위한 구체적 한 걸음"],
}


def _element_relation(e1, e2):
    if e1 == e2:
        return "동일"
    if ELEMENT_SHENG.get(e1) == e2:
        return "상생"
    if ELEMENT_KE.get(e1) == e2:
        return "상극"
    return "중립"


def map_mood_to_saju(mood_level, eight_char):
    """
    기분(1~5) + 사주 -> 감정코칭 데이터

    Args:
        mood_level: 1(매우힘듦) ~ 5(매우좋음)
        eight_char: get_saju()['eight_char']

    Returns dict:
        mood_label, mood_emoji
        saju_reason   - "지금 이 감정이 사주에서 오는 이유"
        ending_point  - "이 시기가 끝나는 시점"
        action_hints  - 실용적 액션 카드 3개
        day_element, relation
    """
    mood = MOOD_MAP.get(mood_level, MOOD_MAP[3])
    day_el = eight_char["day_pillar"]["element"]["branch"]
    mood_el = mood["elements"][0]
    rel = _element_relation(day_el, mood_el)
    label = mood["label"]
    day_g = eight_char["day_pillar"]["glyph"]

    reason_map = {
        "상생": (
            f"오늘 일주({day_g})의 {day_el} 기운이 {mood_el}를 북돋우고 있어요. "
            "이 에너지 흐름이 지금의 감정을 만들고 있습니다."
        ),
        "상극": (
            f"오늘 일주({day_g})의 {day_el} 기운이 {mood_el}와 부딪히는 시기입니다. "
            "그 긴장감이 지금 감정으로 표현되는 거예요."
        ),
        "동일": (
            f"오늘은 {day_el}의 기운이 강하게 작용하는 날이에요. "
            "그 힘이 지금 느끼는 감정으로 드러나고 있습니다."
        ),
        "중립": (
            "오늘 일주의 기운이 내면의 감정과 조용히 공존하고 있어요. "
            "지금 느끼는 것을 그대로 인정해도 괜찮습니다."
        ),
    }

    ending_map = {
        "매우 힘듦": "지금이 가장 어두운 시간일 수 있어요. 대부분 3~7일 안에 전환점이 옵니다.",
        "힘듦":      "이 감정의 파도는 1~2주 안에 자연스럽게 가라앉을 가능성이 높아요.",
        "보통":      "에너지를 축적하는 시간입니다. 작은 안정을 찾는 게 맞는 때예요.",
        "좋음":      "이 좋은 기운이 2~3주 이어질 수 있어요. 중요한 일을 시작하기 좋은 시기입니다.",
        "매우 좋음": "지금의 상승 기운을 믿으세요. 행동으로 옮기면 결실이 보이는 때입니다.",
    }

    return {
        "mood_level":   mood_level,
        "mood_label":   label,
        "mood_emoji":   mood["emoji"],
        "saju_reason":  reason_map.get(rel, reason_map["중립"]),
        "ending_point": ending_map.get(label, ""),
        "action_hints": ACTION_MAP.get((day_el, label), DEFAULT_ACTIONS.get(label, [])),
        "day_element":  day_el,
        "relation":     rel,
    }


# ─────────────────────────────────────────────
# 7. 오행 분포 계산 (만세력 기반)
# ─────────────────────────────────────────────

def get_five_element_distribution(eight_char: dict) -> dict:
    """
    사주 팔자에서 오행(五行) 분포를 집계한다.

    Args:
        eight_char: get_saju()['eight_char'] 반환값

    Returns dict:
        counts   - {'목':N, '화':N, '토':N, '금':N, '수':N}
        dominant - 가장 강한 오행
        lacking  - 가장 부족한 오행 (없으면 None)
        balance  - 'balanced' | 'moderate' | 'imbalanced'
        details  - 각 기둥별 오행 정보
    """
    pillars = ['year_pillar', 'month_pillar', 'day_pillar', 'hour_pillar']
    counts = {'목': 0, '화': 0, '토': 0, '금': 0, '수': 0}
    details = []

    for name in pillars:
        p = eight_char.get(name)
        if not p:
            continue
        el = p['element']
        stem_el   = el['stem']
        branch_el = el['branch']
        if stem_el in counts:
            counts[stem_el] += 1
        if branch_el in counts:
            counts[branch_el] += 1
        details.append({
            'pillar':    name,
            'glyph':     p['glyph'],
            'stem_el':   stem_el,
            'branch_el': branch_el,
        })

    total = sum(counts.values())
    if total == 0:
        dominant = lacking = None
        balance = 'unknown'
    else:
        dominant = max(counts, key=counts.get)
        min_val  = min(counts.values())
        lacking  = max(counts, key=lambda k: -counts[k]) if min_val == 0 else None
        max_val  = max(counts.values())
        ratio    = max_val / total
        if ratio <= 0.30:
            balance = 'balanced'
        elif ratio <= 0.45:
            balance = 'moderate'
        else:
            balance = 'imbalanced'

    return {
        'counts':   counts,
        'dominant': dominant,
        'lacking':  lacking,
        'balance':  balance,
        'details':  details,
    }


# ─────────────────────────────────────────────
# 8. 일주(日柱) 기반 성격 해석 딕셔너리
# 60갑자 전체 수록 — 공인 명리학 해석 기반
# ─────────────────────────────────────────────

ILJU_PERSONALITY: dict[str, dict] = {
    # ──────── 甲 (갑) ────────
    "甲子": {
        "summary": "물 위에 뿌리내린 나무. 유연하면서도 방향을 잃지 않습니다.",
        "strengths": ["창의성", "끈기", "직관력"],
        "challenges": ["우유부단함", "과도한 자의식"],
        "energy": "수(水)가 목(木)을 기르는 구조. 내면의 힘이 차오르는 일주입니다.",
    },
    "甲寅": {
        "summary": "숲 속의 큰 나무. 독립심과 개척 정신이 강합니다.",
        "strengths": ["리더십", "독립심", "결단력"],
        "challenges": ["완고함", "타협 부족"],
        "energy": "목(木)이 겹쳐 힘이 강하지만 유연성을 키워야 합니다.",
    },
    "甲辰": {
        "summary": "흙 위에 선 나무. 현실 감각과 이상을 함께 갖춥니다.",
        "strengths": ["현실성", "포용력", "지속력"],
        "challenges": ["우선순위 혼란", "분산"],
        "energy": "토(土)가 근을 지지. 안정된 성장을 추구하는 에너지.",
    },
    "甲午": {
        "summary": "불길 속의 나무. 열정과 카리스마가 넘칩니다.",
        "strengths": ["열정", "표현력", "카리스마"],
        "challenges": ["충동성", "감정 기복"],
        "energy": "목(木)이 화(火)를 돕는 구조. 에너지 소모가 빠릅니다.",
    },
    "甲申": {
        "summary": "금이 나무를 다듬는 형상. 섬세한 완성도를 추구합니다.",
        "strengths": ["분석력", "완성도 추구", "논리성"],
        "challenges": ["지나친 자기비판", "경직성"],
        "energy": "금(金)이 목(木)을 극하는 긴장 구조. 갈등을 통해 성장합니다.",
    },
    "甲戌": {
        "summary": "마른 땅의 나무. 강인하지만 따뜻함이 필요합니다.",
        "strengths": ["인내력", "신중함", "책임감"],
        "challenges": ["고독감", "융통성 부족"],
        "energy": "토(土)와 금(金)이 혼재. 내면의 고집을 의식적으로 풀어야 합니다.",
    },
    # ──────── 乙 (을) ────────
    "乙丑": {
        "summary": "겨울 흙 속의 풀. 환경에 유연하게 적응하는 생존력.",
        "strengths": ["적응력", "인내", "섬세함"],
        "challenges": ["우유부단", "자기 표현 부족"],
        "energy": "금(金)이 잠재된 토(土) 위의 목(木). 때를 기다리는 에너지.",
    },
    "乙卯": {
        "summary": "봄의 새싹. 순수하고 감수성이 풍부합니다.",
        "strengths": ["감수성", "창의력", "공감 능력"],
        "challenges": ["예민함", "경계 설정 어려움"],
        "energy": "목(木)이 강하게 겹침. 초반 기세가 강하나 지속성 관리 필요.",
    },
    "乙巳": {
        "summary": "불꽃 곁의 풀. 빠른 두뇌와 언변이 특기입니다.",
        "strengths": ["언변", "기민함", "사교성"],
        "challenges": ["산만함", "깊이 부족"],
        "energy": "화(火)가 목(木)을 태울 수 있음. 에너지 보충에 주의.",
    },
    "乙未": {
        "summary": "여름 끝의 풀. 지속력과 실용성을 갖춥니다.",
        "strengths": ["실용성", "지속력", "포용력"],
        "challenges": ["결단 지연", "우선순위 분산"],
        "energy": "화(火)와 토(土)가 혼재. 중심을 잡는 것이 과제입니다.",
    },
    "乙酉": {
        "summary": "금이 풀을 자르는 형상. 날카로운 판단력의 소유자.",
        "strengths": ["판단력", "정확성", "집중력"],
        "challenges": ["냉철함이 차갑게 느껴질 수 있음", "완벽주의"],
        "energy": "금(金)이 목(木)을 직접 극함. 갈등 에너지가 강합니다.",
    },
    "乙亥": {
        "summary": "물 위의 풀. 깊은 직관과 감성적 지혜를 가집니다.",
        "strengths": ["직관", "감성 지혜", "배려심"],
        "challenges": ["경계 없는 공감으로 소진", "현실 감각 부족"],
        "energy": "수(水)가 목(木)을 기름. 감수성이 강점이자 약점입니다.",
    },
    # ──────── 丙 (병) ────────
    "丙子": {
        "summary": "겨울 물 위의 태양. 어둠 속에서 빛나는 따뜻함.",
        "strengths": ["온기", "희망", "사회성"],
        "challenges": ["내면 외로움", "감정 기복"],
        "energy": "수(水)가 화(火)를 억누름. 감정과 이성 사이 균형이 관건.",
    },
    "丙寅": {
        "summary": "봄 숲의 태양. 활력이 넘치고 진취적입니다.",
        "strengths": ["활력", "진취성", "긍정"],
        "challenges": ["과잉 행동", "주의 분산"],
        "energy": "목(木)이 화(火)를 도움. 에너지가 강력히 상승합니다.",
    },
    "丙辰": {
        "summary": "흙 위에서 빛나는 태양. 현실적 온기를 나눕니다.",
        "strengths": ["포용력", "사회성", "추진력"],
        "challenges": ["과욕", "에너지 분산"],
        "energy": "화(火)가 토(土)를 만들어 안정. 내실 있는 성장 구조.",
    },
    "丙午": {
        "summary": "한낮의 태양. 강렬한 존재감과 카리스마.",
        "strengths": ["카리스마", "결단력", "열정"],
        "challenges": ["독선", "감정 과열"],
        "energy": "화(火)가 겹쳐 극강. 에너지 소모를 의식적으로 조절해야 합니다.",
    },
    "丙申": {
        "summary": "금빛 석양. 창의성과 분석력을 함께 갖춥니다.",
        "strengths": ["창의성", "분석력", "독창성"],
        "challenges": ["자존심 강함", "협력 어려움"],
        "energy": "화(火)가 금(金)을 녹이는 구조. 강렬한 에너지 변환기.",
    },
    "丙戌": {
        "summary": "가을 석양. 깊은 철학과 삶의 지혜.",
        "strengths": ["지혜", "책임감", "신뢰"],
        "challenges": ["완고함", "변화 거부"],
        "energy": "토(土)와 금(金) 속의 화(火). 내면의 불을 꺼트리지 않는 것이 과제.",
    },
    # ──────── 丁 (정) ────────
    "丁丑": {
        "summary": "겨울 흙 속의 촛불. 섬세하고 따뜻한 내면의 빛.",
        "strengths": ["섬세함", "헌신", "인내"],
        "challenges": ["자기 희생 과다", "표현 부족"],
        "energy": "금(金)과 수(水) 속의 작은 화(火). 자기 보호가 필요합니다.",
    },
    "丁卯": {
        "summary": "봄 나무 곁의 촛불. 예술적 감성과 표현력.",
        "strengths": ["예술성", "감성", "소통력"],
        "challenges": ["경제 관념 부족", "현실성"],
        "energy": "목(木)이 화(火)를 도움. 창의적 에너지가 꽃핍니다.",
    },
    "丁巳": {
        "summary": "불꽃 속의 촛불. 강렬한 직관과 신비로운 매력.",
        "strengths": ["직관력", "매력", "집중력"],
        "challenges": ["신비주의로 거리감", "감정 과열"],
        "energy": "화(火)가 겹침. 강렬하지만 과열 주의.",
    },
    "丁未": {
        "summary": "여름 끝의 촛불. 인내와 따뜻함으로 주변을 돌봅니다.",
        "strengths": ["돌봄", "인내", "공감"],
        "challenges": ["자기 감정 억압", "소진"],
        "energy": "화(火)와 토(土)가 연결. 안정적이나 에너지 재충전 필요.",
    },
    "丁酉": {
        "summary": "금빛 촛불. 명확한 판단과 심미적 감각.",
        "strengths": ["심미안", "명확성", "추진력"],
        "challenges": ["냉철한 인상", "감정 표현 어색함"],
        "energy": "화(火)가 금(金)을 다듬음. 정제된 에너지.",
    },
    "丁亥": {
        "summary": "물 위의 촛불. 위태롭지만 꺼지지 않는 강인함.",
        "strengths": ["강인함", "적응력", "깊이"],
        "challenges": ["불안감", "감정 기복"],
        "energy": "수(水)가 화(火)를 억누름. 내면의 불을 지키는 것이 과제.",
    },
    # ──────── 戊 (무) ────────
    "戊子": {
        "summary": "겨울 물 위의 산. 묵직하고 차분한 존재감.",
        "strengths": ["안정감", "인내", "포용"],
        "challenges": ["고집", "변화 거부"],
        "energy": "수(水)가 토(土) 안에 저장. 깊은 내면의 에너지.",
    },
    "戊寅": {
        "summary": "산속의 나무. 실용적이면서도 열정적입니다.",
        "strengths": ["실용성", "활력", "추진력"],
        "challenges": ["성급함", "계획 부족"],
        "energy": "목(木)이 토(土)를 뚫는 구조. 도전 에너지가 강합니다.",
    },
    "戊辰": {
        "summary": "거대한 산. 강인하고 신뢰할 수 있는 존재.",
        "strengths": ["신뢰성", "강인함", "지도력"],
        "challenges": ["융통성 부족", "독단"],
        "energy": "토(土)가 겹쳐 매우 강함. 유연함을 의식적으로 키워야 합니다.",
    },
    "戊午": {
        "summary": "불 위의 산. 뜨겁고 강렬한 에너지의 소유자.",
        "strengths": ["열정", "리더십", "결단"],
        "challenges": ["과열", "독선"],
        "energy": "화(火)와 토(土)의 강한 결합. 강력하지만 냉각이 필요합니다.",
    },
    "戊申": {
        "summary": "금이 담긴 산. 풍요롭고 세련된 판단력.",
        "strengths": ["판단력", "세련됨", "조직력"],
        "challenges": ["냉정함", "감정 표현 부족"],
        "energy": "토(土)에서 금(金)이 생성. 자원이 풍부한 구조.",
    },
    "戊戌": {
        "summary": "건조한 산. 강인하고 독립적입니다.",
        "strengths": ["독립성", "강인함", "지속력"],
        "challenges": ["고독", "의존 어려움"],
        "energy": "토(土)가 과도하게 쌓임. 수(水)의 기운을 보충해야 합니다.",
    },
    # ──────── 己 (기) ────────
    "己丑": {
        "summary": "겨울 논밭. 근면하고 꾸준히 가꿔나가는 성실함.",
        "strengths": ["성실함", "꾸준함", "실용성"],
        "challenges": ["느린 행동", "기회 놓침"],
        "energy": "토(土)가 겹쳐 안정. 점진적 성장 에너지.",
    },
    "己卯": {
        "summary": "봄 논밭. 부드럽지만 생명력 있는 에너지.",
        "strengths": ["유연성", "적응력", "생명력"],
        "challenges": ["경계 없는 친절", "자기 보호 약함"],
        "energy": "목(木)이 토(土)를 통과. 부드러운 돌파력.",
    },
    "己巳": {
        "summary": "불에 달군 흙. 정제된 지식과 지혜.",
        "strengths": ["학구열", "지혜", "논리"],
        "challenges": ["이론 치우침", "실행력 부족"],
        "energy": "화(火)가 토(土)를 생성. 지적 에너지가 강합니다.",
    },
    "己未": {
        "summary": "여름 논밭. 풍요롭고 인간적입니다.",
        "strengths": ["포용력", "사교성", "인간미"],
        "challenges": ["결단 어려움", "감정 과잉"],
        "energy": "토(土)가 강하게 쌓임. 중심 잡기가 과제.",
    },
    "己酉": {
        "summary": "논밭의 금. 섬세하고 심미적인 감각.",
        "strengths": ["심미안", "섬세함", "완성도"],
        "challenges": ["완벽주의로 인한 스트레스", "유연성 부족"],
        "energy": "토(土)에서 금(金)이 생성. 정제된 에너지 흐름.",
    },
    "己亥": {
        "summary": "물기 머금은 논밭. 감성적이고 포용력이 넓습니다.",
        "strengths": ["감성", "포용", "직관"],
        "challenges": ["감정에 휩쓸림", "현실 판단 흐림"],
        "energy": "수(水)가 토(土)를 적심. 감성과 실용 사이 균형이 관건.",
    },
    # ──────── 庚 (경) ────────
    "庚子": {
        "summary": "겨울 물 위의 검. 날카롭고 차갑지만 깊은 생각.",
        "strengths": ["논리력", "날카로움", "독립심"],
        "challenges": ["냉정함", "고독"],
        "energy": "금(金)이 수(水)를 생성. 지식과 직관이 결합하는 구조.",
    },
    "庚寅": {
        "summary": "숲 속의 도끼. 개척적이고 실행력이 뛰어납니다.",
        "strengths": ["개척력", "실행력", "용기"],
        "challenges": ["충동성", "섬세함 부족"],
        "energy": "금(金)이 목(木)을 베는 긴장 구조. 강한 도전 에너지.",
    },
    "庚辰": {
        "summary": "보석이 든 땅. 가치 있는 것을 발굴해내는 능력.",
        "strengths": ["발굴력", "통찰", "인내"],
        "challenges": ["숨은 것 집착", "표현 부족"],
        "energy": "토(土)가 금(金)을 생성. 내면의 자원이 풍부합니다.",
    },
    "庚午": {
        "summary": "불 속의 금속. 강인하게 단련된 성격.",
        "strengths": ["강인함", "의지력", "열정"],
        "challenges": ["과열 시 폭발", "유연성 부족"],
        "energy": "화(火)가 금(金)을 제련. 변화와 단련의 에너지.",
    },
    "庚申": {
        "summary": "정련된 강철. 완벽주의와 날카로운 판단력.",
        "strengths": ["완벽주의", "판단력", "자기관리"],
        "challenges": ["냉철함이 관계에 장벽", "융통성 부족"],
        "energy": "금(金)이 겹침. 강력한 집중력과 자기 통제.",
    },
    "庚戌": {
        "summary": "가을 산의 광석. 단단하고 믿음직합니다.",
        "strengths": ["신뢰성", "견고함", "책임감"],
        "challenges": ["완고함", "감정 억압"],
        "energy": "토(土)와 금(金)의 결합. 안정적이나 따뜻함 보충 필요.",
    },
    # ──────── 辛 (신) ────────
    "辛丑": {
        "summary": "겨울 땅의 보석. 섬세하고 가치 있는 것을 알아봅니다.",
        "strengths": ["심미안", "섬세함", "가치 판단"],
        "challenges": ["까다로움", "자기 표현 어려움"],
        "energy": "금(金)과 토(土)의 결합. 정밀하고 정제된 에너지.",
    },
    "辛卯": {
        "summary": "봄 정원의 보석. 아름다움과 예술성이 뛰어납니다.",
        "strengths": ["예술성", "창의력", "아름다움 추구"],
        "challenges": ["경계 설정 어려움", "현실성 부족"],
        "energy": "금(金)이 목(木)을 만남. 예술적 긴장이 창의력을 만듭니다.",
    },
    "辛巳": {
        "summary": "불로 정제된 보석. 탁월한 심미안과 완성도.",
        "strengths": ["완성도", "심미안", "집중력"],
        "challenges": ["완벽주의 스트레스", "타인 판단 엄격"],
        "energy": "화(火)가 금(金)을 단련. 정제의 에너지.",
    },
    "辛未": {
        "summary": "여름 흙 속의 보석. 숨겨진 가치를 드러냅니다.",
        "strengths": ["잠재력 발굴", "인내", "섬세함"],
        "challenges": ["자기 과소평가", "느린 자기 표현"],
        "energy": "토(土)가 금(金)을 생성. 때를 기다리는 성숙 에너지.",
    },
    "辛酉": {
        "summary": "순수한 보석. 날카롭고 투명한 판단력.",
        "strengths": ["명확성", "날카로움", "순수함"],
        "challenges": ["냉정함", "감정 격리"],
        "energy": "금(金)이 극강. 집중력이 최고이나 유연함 필요.",
    },
    "辛亥": {
        "summary": "물 속의 보석. 깊은 감수성과 직관.",
        "strengths": ["감수성", "직관", "공감"],
        "challenges": ["감정 과몰입", "실용성 부족"],
        "energy": "금(金)이 수(水)를 생성. 감성의 흐름이 강합니다.",
    },
    # ──────── 壬 (임) ────────
    "壬子": {
        "summary": "깊은 바다. 지적 깊이와 신비로운 매력.",
        "strengths": ["깊이", "직관", "지적 탐구"],
        "challenges": ["감정 통제 어려움", "현실 회피"],
        "energy": "수(水)가 겹침. 감성이 극강. 흐름을 조절하는 것이 관건.",
    },
    "壬寅": {
        "summary": "봄 강물. 활차고 방향 있는 에너지.",
        "strengths": ["진취성", "활력", "방향감"],
        "challenges": ["성급함", "과신"],
        "energy": "수(水)가 목(木)을 기름. 성장과 진취의 에너지.",
    },
    "壬辰": {
        "summary": "거대한 저수지. 방대한 에너지를 담고 있습니다.",
        "strengths": ["방대함", "포용력", "지속력"],
        "challenges": ["집중 어려움", "우우단"],
        "energy": "토(土) 속의 수(水). 방향을 정하면 강력합니다.",
    },
    "壬午": {
        "summary": "불 위의 강. 뜨거운 감성과 차가운 이성의 공존.",
        "strengths": ["열정", "이성", "카리스마"],
        "challenges": ["내적 갈등", "감정 기복"],
        "energy": "수(水)와 화(火)의 충돌. 내면의 긴장이 창의력 원천.",
    },
    "壬申": {
        "summary": "금이 만들어낸 강물. 지식과 지혜의 흐름.",
        "strengths": ["지성", "유연성", "통찰"],
        "challenges": ["산만함", "집중 부족"],
        "energy": "금(金)이 수(水)를 생성. 아이디어가 넘치는 구조.",
    },
    "壬戌": {
        "summary": "가을 강. 깊어지는 철학과 성찰.",
        "strengths": ["철학적 사유", "책임감", "성찰"],
        "challenges": ["과거 집착", "변화 두려움"],
        "energy": "토(土)와 금(金) 속의 수(水). 내면 탐구가 강해집니다.",
    },
    # ──────── 癸 (계) ────────
    "癸丑": {
        "summary": "겨울 눈 속의 빗물. 조용하고 섬세한 내면.",
        "strengths": ["섬세함", "내성적 깊이", "인내"],
        "challenges": ["자기 표현 어려움", "고독"],
        "energy": "수(水)와 토(土)의 긴장. 내면의 감수성이 깊습니다.",
    },
    "癸卯": {
        "summary": "봄비. 부드럽고 촉촉한 생명력.",
        "strengths": ["공감력", "배려", "감수성"],
        "challenges": ["자기 희생 과다", "경계 설정 부족"],
        "energy": "수(水)가 목(木)을 기름. 따뜻하고 조용한 성장 에너지.",
    },
    "癸巳": {
        "summary": "불 옆의 빗물. 섬세한 감성과 날카로운 직관.",
        "strengths": ["직관", "예리함", "감성"],
        "challenges": ["에너지 소진", "내적 갈등"],
        "energy": "수(水)와 화(火)의 긴장. 강렬한 감성과 이성의 교차.",
    },
    "癸未": {
        "summary": "여름 비. 주변을 적시는 따뜻한 배려.",
        "strengths": ["배려", "공감", "포용"],
        "challenges": ["자기 감정 돌봄 부족", "경계 없는 공감"],
        "energy": "수(水)와 토(土)의 만남. 조화와 균형의 에너지.",
    },
    "癸酉": {
        "summary": "가을비. 섬세하고 정밀한 판단력.",
        "strengths": ["정밀함", "심미안", "관찰력"],
        "challenges": ["까다로움", "완벽주의"],
        "energy": "금(金)이 수(水)를 생성. 감성이 정밀함을 만납니다.",
    },
    "癸亥": {
        "summary": "깊은 겨울 바다. 신비로운 내면과 무한한 감수성.",
        "strengths": ["심도", "직관", "신비감"],
        "challenges": ["현실 감각 부족", "감정 익사"],
        "energy": "수(水)가 극강. 감성의 바다 — 방향키가 필요합니다.",
    },
}


def get_ilju_personality(eight_char: dict) -> dict:
    """
    일주(日柱)를 기반으로 성격 해석을 반환한다.

    Args:
        eight_char: get_saju()['eight_char'] 반환값

    Returns dict:
        glyph         - 일주 한자 (예: '甲子')
        reading       - 한국어 읽기 (예: '갑자')
        personality   - ILJU_PERSONALITY 딕셔너리 항목 (None if unknown)
        found         - bool, 딕셔너리에 항목이 있는지 여부
    """
    day_pillar = eight_char.get('day_pillar', {})
    glyph   = day_pillar.get('glyph', '')
    reading = day_pillar.get('reading', '')
    pers = ILJU_PERSONALITY.get(glyph)
    return {
        'glyph':       glyph,
        'reading':     reading,
        'personality': pers,
        'found':       pers is not None,
    }


if __name__ == "__main__":
    # ⚠ 개발/디버깅 전용 CLI 블록 — 프로덕션 API에서 호출되지 않음
    # 하드코딩된 샘플 날짜(1990-01-15) 사용 — 실제 사용자 PII 없음
    import json
    print("=== 1990-01-15 10:30 사주 ===")  # 샘플 데이터
    r = get_saju(1990, 1, 15, hour=10, minute=30)
    print("팔자:", r["eight_char"]["eight_glyphs"], " 방법:", r["method"])
    for k in ["year_pillar", "month_pillar", "day_pillar", "hour_pillar"]:
        p = r["eight_char"][k]
        print(f"  {k}: {p['glyph']} ({p['reading']}) 오행={p['element']['branch']}")
    print()

    print("=== 시(時) 미입력 ===")
    r2 = get_saju(1990, 1, 15)
    print(r2["note"])
    print("기본:", r2["eight_char"]["eight_glyphs"])
    print("자시:", r2["hour_variants"][0]["eight_char"]["eight_glyphs"])
    print("오시:", r2["hour_variants"][6]["eight_char"]["eight_glyphs"])
    print()

    print("=== 감정 체크인 (기분=2/5) ===")
    m = map_mood_to_saju(2, r["eight_char"])
    print(json.dumps(m, ensure_ascii=False, indent=2))
    print()

    print("=== 오행 분포 ===")
    dist = get_five_element_distribution(r["eight_char"])
    print("분포:", dist["counts"])
    print("강한 오행:", dist["dominant"])
    print("부족 오행:", dist["lacking"])
    print("균형도:", dist["balance"])
    print()

    print("=== 일주 성격 해석 ===")
    ilju = get_ilju_personality(r["eight_char"])
    print(f"일주: {ilju['glyph']} ({ilju['reading']})")
    if ilju["found"]:
        p = ilju["personality"]
        print("요약:", p["summary"])
        print("강점:", ", ".join(p["strengths"]))
        print("과제:", ", ".join(p["challenges"]))
        print("에너지:", p["energy"])
    else:
        print("(해석 데이터 없음)")
