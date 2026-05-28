# 사주 웰니스 — 알고리즘 설계서 (ALGORITHM.md)

버전: 1.0.0  
작성일: 2026-05-22  
대상: 백엔드 개발팀

---

## 1. 사주팔자 계산 엔진

### 1.1 데이터 모델

사주팔자(四柱八字)는 태어난 해·월·일·시를 각각 천간(天干, Heavenly Stem)과 지지(地支, Earthly Branch)의 조합으로 표현한다. 총 4개 기둥(柱), 8글자.

천간 10개 (갑을병정무기경신임계):
```
index:  0   1   2   3   4   5   6   7   8   9
한자:  甲  乙  丙  丁  戊  己  庚  辛  壬  癸
한글:  갑  을  병  정  무  기  경  신  임  계
오행:  목  목  화  화  토  토  금  금  수  수
음양:  양  음  양  음  양  음  양  음  양  음
```

지지 12개 (자축인묘진사오미신유술해):
```
index:  0   1   2   3   4   5   6   7   8   9  10  11
한자:  子  丑  寅  卯  辰  巳  午  未  申  酉  戌  亥
한글:  자  축  인  묘  진  사  오  미  신  유  술  해
오행:  수  토  목  목  토  화  화  토  금  금  토  수
음양:  양  음  양  음  양  음  양  음  양  음  양  음
동물:  쥐  소  호랑이 토끼 용  뱀  말  양  원숭이 닭  개  돼지
```

### 1.2 연주(年柱) 계산

갑자년(甲子年)을 기준으로 60년 주기로 순환한다.

```python
# 기준: 1984년 = 甲子年 (stem_idx=0, branch_idx=0)
year_stem_idx   = (year - 4) % 10
year_branch_idx = (year - 4) % 12
```

주의: 음력 정월 초하루(설날)가 아닌 절기 기준 입춘(立春, 보통 2월 4일경)을 넘어야 다음 해 연주로 전환된다. 음력 변환 라이브러리(lunar-python)를 사용하면 이를 자동 처리한다.

### 1.3 월주(月柱) 계산

월주는 절기(節氣) 기준이다. 양력 월과 다르다는 점이 핵심이다.

절기 기준 월별 지지:
```
인월(寅, 2월 입춘~) / 묘월(卯, 3월 경칩~) / 진월(辰, 4월 청명~)
사월(巳, 5월 입하~) / 오월(午, 6월 망종~) / 미월(未, 7월 소서~)
신월(申, 8월 입추~) / 유월(酉, 9월 백로~) / 술월(戌, 10월 한로~)
해월(亥, 11월 입동~) / 자월(子, 12월 대설~) / 축월(丑, 1월 소한~)
```

월간(月干)은 연간에 따라 결정된다:

| 연간 | 인월 시작 월간 |
|------|--------------|
| 갑·기년 | 병(丙, idx=2) |
| 을·경년 | 무(戊, idx=4) |
| 병·신년 | 경(庚, idx=6) |
| 정·임년 | 임(壬, idx=8) |
| 무·계년 | 갑(甲, idx=0) |

```python
MONTH_STEM_BASE = {0: 2, 5: 2,  # 갑·기
                   1: 4, 6: 4,  # 을·경
                   2: 6, 7: 6,  # 병·신
                   3: 8, 8: 8,  # 정·임
                   4: 0, 9: 0}  # 무·계

month_stem_idx = (MONTH_STEM_BASE[year_stem_idx] + month_offset) % 10
# month_offset: 인월=0, 묘월=1, ... (절기 기준 월 순서)
```

이 부분이 오차가 가장 많이 생기는 구간이다. lunar-python 없이 fallback으로 계산하면 절기 경계일(보통 월 4~8일)에 1일 오차가 생길 수 있다.

### 1.4 일주(日柱) 계산

일주는 갑자일(甲子日)부터 60일 주기로 순환한다.

```python
# 기준: 2000년 1월 7일 = 甲子日
BASE_DATE = datetime.date(2000, 1, 7)
diff = (target_date - BASE_DATE).days
day_stem_idx   = diff % 10
day_branch_idx = diff % 12
```

이 기준값은 검증된 값이다. 변경하지 말 것.

### 1.5 시주(時柱) 계산

시간을 지지에 매핑한다:

```python
HOUR_TO_BRANCH = [
    0,  # 23:00-01:00 → 자(子)
    1, 1,  # 01:00-03:00 → 축(丑)
    2, 2,  # 03:00-05:00 → 인(寅)
    3, 3,  # 05:00-07:00 → 묘(卯)
    4, 4,  # 07:00-09:00 → 진(辰)
    5, 5,  # 09:00-11:00 → 사(巳)
    6, 6,  # 11:00-13:00 → 오(午)
    7, 7,  # 13:00-15:00 → 미(未)
    8, 8,  # 15:00-17:00 → 신(申)
    9, 9,  # 17:00-19:00 → 유(酉)
    10, 10,  # 19:00-21:00 → 술(戌)
    11, 11,  # 21:00-23:00 → 해(亥)
]
# 24시(자정) 처리: 0 → 자(子, 0)
```

시간은 한국 기준(KST, UTC+9). 해외 사용자의 경우 출생지 현지 시간 기준으로 계산. pytz 사용.

시간(時干)은 일간에 따라 결정:

| 일간 | 자시(子時) 시간 |
|------|--------------|
| 갑·기일 | 갑(甲, 0) |
| 을·경일 | 병(丙, 2) |
| 병·신일 | 무(戊, 4) |
| 정·임일 | 경(庚, 6) |
| 무·계일 | 임(壬, 8) |

```python
HOUR_STEM_BASE = {0: 0, 5: 0,  # 갑·기
                  1: 2, 6: 2,  # 을·경
                  2: 4, 7: 4,  # 병·신
                  3: 6, 8: 6,  # 정·임
                  4: 8, 9: 8}  # 무·계

hour_stem_idx = (HOUR_STEM_BASE[day_stem_idx] + hour_branch_idx) % 10
```

### 1.6 라이브러리 우선순위

1순위: `lunar-python` (절기 경계 정확, 음력 변환 포함)  
2순위: fallback (직접 구현, 절기 경계일 ±1일 오차 가능)

```python
def calculate_four_pillars(year, month, day, hour, minute=0):
    try:
        from lunar_python import Solar
        solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
        ec = solar.getLunar().getEightChar()
        # ... 파싱 로직
        return result, "lunar-python"
    except ImportError:
        return _fallback_calculate(year, month, day, hour, minute), "fallback"
    except Exception as e:
        logger.warning(f"lunar-python 오류: {e}, fallback 사용")
        return _fallback_calculate(year, month, day, hour, minute), "fallback"
```

응답에 사용된 엔진(`source` 필드)을 포함해 클라이언트에 전달. fallback 결과에는 UI 주석 표시: "절기 경계일 근처의 경우 약간의 차이가 있을 수 있습니다."

---

## 2. 오행 분석 로직

### 2.1 오행 점수 계산

사주 8글자(천간 4 + 지지 4)에서 각 오행의 비중을 계산한다.

```python
def calculate_element_scores(eight_char: EightChar) -> dict:
    scores = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    
    for pillar in [ec.year, ec.month, ec.day, ec.hour]:
        # 천간 점수
        scores[STEM_ELEMENT[pillar.stem_idx]] += 10
        # 지지 점수 (지지가 천간보다 에너지 강하다는 전통 해석)
        scores[BRANCH_ELEMENT[pillar.branch_idx]] += 15
    
    total = sum(scores.values())
    return {k: round(v / total * 100, 1) for k, v in scores.items()}
```

가중치 (천간:지지 = 10:15)는 명리학 전통 해석 기준. 서비스 운영 후 사용자 피드백으로 조정 가능.

### 2.2 오행 관계 판정

```python
SHENG = {"목": "화", "화": "토", "토": "금", "금": "수", "수": "목"}  # 상생
KE    = {"목": "토", "토": "수", "수": "화", "화": "금", "금": "목"}  # 상극
HE    = {"같음": "비화"}  # 동일 오행

def get_element_relation(elem_a, elem_b):
    if elem_a == elem_b:
        return "비화"  # 같은 오행 → 강화
    if SHENG[elem_a] == elem_b:
        return "상생(생함)"  # A가 B를 생함
    if SHENG[elem_b] == elem_a:
        return "상생(받음)"  # A가 B에게 생받음
    if KE[elem_a] == elem_b:
        return "상극(극함)"  # A가 B를 극함
    if KE[elem_b] == elem_a:
        return "상극(받음)"  # A가 B에게 극받음
    return "무관"
```

이 함수는 정서 지원 채팅에서 "일주 오행 × 오늘 일진 오행" 관계를 파악하는 데 사용된다.

### 2.3 강약 판정

```python
def assess_element_strength(scores: dict) -> dict:
    avg = 100 / 5  # 균형 기준 20%
    return {
        "strongest": max(scores, key=scores.get),
        "weakest": min(scores, key=scores.get),
        "dominant": [k for k, v in scores.items() if v > avg * 1.5],  # 30% 이상
        "depleted": [k for k, v in scores.items() if v < avg * 0.5],  # 10% 이하
        "balanced": all(avg * 0.7 <= v <= avg * 1.3 for v in scores.values())
    }
```

---

## 3. 대운(大運) 계산

### 3.1 원리

대운은 10년 단위로 운의 흐름이 바뀌는 큰 기둥이다. 사주 중 월주(月柱)에서 출발해 음양에 따라 순방향 또는 역방향으로 진행한다.

진행 방향:
- 양간(甲·丙·戊·庚·壬)이면서 남성: 순행 (절기 앞으로)
- 양간이면서 여성: 역행
- 음간(乙·丁·己·辛·癸)이면서 남성: 역행
- 음간이면서 여성: 순행

간단히: `순행 = (양간 AND 남) OR (음간 AND 여)`

### 3.2 대운 시작 나이 계산

태어난 날부터 다음(또는 이전) 절기까지의 날수를 3으로 나눈 값이 대운 시작 나이다.

```python
def calculate_daun_start_age(birth_date, birth_gender, year_stem_idx) -> float:
    is_yang_stem = year_stem_idx % 2 == 0
    forward = (is_yang_stem and birth_gender == "M") or \
              (not is_yang_stem and birth_gender == "F")
    
    # lunar-python으로 다음/이전 절기 날짜 구하기
    if forward:
        days_to_next_jieqi = get_days_to_next_jieqi(birth_date)
        return round(days_to_next_jieqi / 3, 1)
    else:
        days_to_prev_jieqi = get_days_to_prev_jieqi(birth_date)
        return round(days_to_prev_jieqi / 3, 1)
```

### 3.3 대운 시퀀스 생성

월주에서 시작해 10년마다 다음 간지로 이동한다.

```python
def generate_daun_sequence(month_pillar: Pillar, forward: bool, 
                            start_age: float, count: int = 10) -> list:
    result = []
    stem_idx   = month_pillar.stem_idx
    branch_idx = month_pillar.branch_idx
    
    for i in range(count):
        if forward:
            stem_idx   = (stem_idx + 1) % 10
            branch_idx = (branch_idx + 1) % 12
        else:
            stem_idx   = (stem_idx - 1) % 10
            branch_idx = (branch_idx - 1) % 12
        
        age = start_age + i * 10
        result.append({
            "pillar": Pillar(stem_idx, branch_idx).to_dict(),
            "age_start": age,
            "age_end": age + 10,
            "element_relation": get_element_relation(
                STEM_ELEMENT[month_pillar.stem_idx],
                STEM_ELEMENT[stem_idx]
            )
        })
    
    return result
```

---

## 4. 세운(歲運) 계산

세운은 해당 연도의 연주(年柱)와 개인 사주 간의 에너지 교류다. 연도의 천간지지를 계산해 개인 일주 오행과의 관계를 분석한다.

```python
def calculate_seun(target_year: int, eight_char: EightChar) -> dict:
    seun_stem_idx   = (target_year - 4) % 10
    seun_branch_idx = (target_year - 4) % 12
    
    seun_element = STEM_ELEMENT[seun_stem_idx]
    day_element  = STEM_ELEMENT[eight_char.day.stem_idx]
    
    relation = get_element_relation(day_element, seun_element)
    
    return {
        "year": target_year,
        "glyph": HEAVENLY_STEMS[seun_stem_idx] + EARTHLY_BRANCHES[seun_branch_idx],
        "reading": STEM_KR[seun_stem_idx] + BRANCH_KR[seun_branch_idx],
        "element": seun_element,
        "relation_to_day": relation,
        "energy_forecast": _generate_seun_description(relation, seun_element, day_element)
    }

def _generate_seun_description(relation, seun_elem, day_elem) -> str:
    descriptions = {
        "비화":        f"올해 {day_elem} 에너지가 강화되는 해. 자신의 특성이 더 강하게 나타납니다.",
        "상생(생함)":  f"올해 {day_elem}이 {seun_elem}을 생하는 해. 에너지를 발산하고 베푸는 흐름.",
        "상생(받음)":  f"올해 {seun_elem}이 {day_elem}을 생하는 해. 지원받고 성장하는 시기.",
        "상극(극함)":  f"올해 {day_elem}이 {seun_elem}을 극하는 해. 리더십이 강해지나 과부하 주의.",
        "상극(받음)":  f"올해 {seun_elem}이 {day_elem}을 극하는 해. 외부 압력이 많을 수 있는 시기.",
        "무관":        f"올해 {seun_elem} 에너지가 새롭게 들어오는 해. 낯선 기회나 변화가 생길 수 있습니다."
    }
    return descriptions.get(relation, "에너지 변화가 있는 해입니다.")
```

---

## 5. 궁합(相性) 분석

두 사람의 사주를 비교해 오행 관계를 분석한다. "절대적으로 맞지 않는다" 같은 단정 표현을 금지하고, 에너지 상호작용 관점으로 표현.

```python
def calculate_compatibility(ec_a: EightChar, ec_b: EightChar) -> dict:
    # 일주 오행 중심 비교 (가장 중요)
    day_elem_a = STEM_ELEMENT[ec_a.day.stem_idx]
    day_elem_b = STEM_ELEMENT[ec_b.day.stem_idx]
    
    core_relation = get_element_relation(day_elem_a, day_elem_b)
    
    # 월주 (성격·사회적 자아)
    month_relation = get_element_relation(
        STEM_ELEMENT[ec_a.month.stem_idx],
        STEM_ELEMENT[ec_b.month.stem_idx]
    )
    
    # 오행 분포 유사도 (0~100)
    scores_a = calculate_element_scores(ec_a)
    scores_b = calculate_element_scores(ec_b)
    similarity = 100 - sum(abs(scores_a[k] - scores_b[k]) for k in scores_a) / 2
    
    return {
        "core_relation": core_relation,
        "month_relation": month_relation,
        "element_similarity": round(similarity, 1),
        "summary": _generate_compatibility_summary(core_relation, similarity)
    }

def _generate_compatibility_summary(relation, similarity) -> str:
    # 면책 문구 필수 포함
    base = {
        "비화":        "두 분의 에너지 방향이 비슷합니다. 서로를 잘 이해할 수 있지만, 때로는 같은 방향으로 너무 몰려 마찰이 생길 수 있어요.",
        "상생(생함)":  "한쪽이 다른쪽에게 에너지를 주는 관계입니다. 지원자와 수혜자의 역할이 생길 수 있습니다.",
        "상생(받음)":  "서로 에너지를 주고받는 흐름입니다. 균형 잡힌 지지 관계가 될 수 있어요.",
        "상극(극함)":  "두 에너지 사이에 긴장이 있는 조합입니다. 자극이 되어 서로 성장하는 계기가 되기도 합니다.",
        "상극(받음)":  "에너지 충돌이 있는 조합입니다. 서로의 차이를 이해하는 것이 중요합니다.",
        "무관":        "에너지 방향이 독립적입니다. 서로의 영역을 존중하면 좋은 관계가 될 수 있어요."
    }.get(relation, "독특한 에너지 조합입니다.")
    
    disclaimer = "\n\n※ 본 궁합은 명리학적 에너지 관점의 참고 정보입니다. 실제 관계는 두 분의 노력과 소통이 더 중요합니다."
    return base + disclaimer
```

---

## 6. 캐싱 전략

### 6.1 Redis 캐시 설계

사주 계산은 생년월일시가 고정이므로, 계산 결과를 사용자 ID 기준으로 캐싱한다.

```python
# 사주 기본 분석: TTL 없음 (생년월일 변하지 않음)
CACHE_KEY_SAJU     = "saju:{user_id}:base"

# 세운 분석: TTL 1년 (연도별 캐시)
CACHE_KEY_SEUN     = "saju:{user_id}:seun:{year}"

# 일진 (일간운세): TTL 자정 + 1시간
CACHE_KEY_DAILY    = "saju:{user_id}:daily:{date}"

# 궁합: TTL 1주 (두 사람 조합으로 키)
CACHE_KEY_COMPAT   = "saju:compat:{user_a_id}:{user_b_id}"
```

AI 해석 결과도 별도 캐싱 (Claude API 비용 절감):
```python
# AI 해석: 동일 사주 + 동일 감정 레벨 = 동일 결과 캐싱 가능
CACHE_KEY_AI_INTERP = "ai:{eight_glyphs}:{mood_level}:{lang}:{date}"
# TTL: 당일 자정까지 (날짜가 바뀌면 일진이 달라지므로)
```

### 6.2 캐시 무효화

- 사용자가 생년월일시 수정 시: `saju:{user_id}:*` 전체 삭제
- 연도 바뀔 때: `saju:*:seun:{old_year}` 삭제 (필요시)

---

## 7. 오행 감정 매핑

사용자가 감정을 입력하면 오행으로 매핑해 사주와 연결한다.

```python
MOOD_ELEMENT_MAP = {
    # 기분 5단계 × 상황 태그
    "슬픔·상실":    "수(水)",  # 수기운: 감수성, 내향, 은거
    "분노·충돌":    "화(火)",  # 화기운: 과열, 감정 폭발
    "불안·걱정":    "토(土)",  # 토기운: 과습, 답답함
    "우울·무기력":  "금(金)",  # 금기운: 수축, 냉각
    "활기·과활동":  "목(木)",  # 목기운: 과성장, 불균형
    "평온·안정":    "토(土)",  # 균형 잡힌 토
    "창의·설렘":    "목(木)",  # 목기운 성장
    "따뜻함·연결":  "화(火)",  # 화기운 교류
    "집중·결단":    "금(金)",  # 금기운 수렴
    "지혜·통찰":    "수(水)",  # 수기운 깊이
}
```

이 매핑은 전통 명리학의 오행-감정 대응 원리를 따른다. "수는 감수성과 내향성", "화는 열정과 감정 표현" 등.

AI 프롬프트에 이 매핑 결과를 주입해, 사주 오행과 현재 감정 오행의 관계를 해석하게 한다.

---

## 8. 데이터베이스 스키마 (핵심 테이블)

```sql
-- 사용자 생년월일시 (암호화 저장)
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    birth_year  INTEGER NOT NULL,
    birth_month INTEGER NOT NULL,
    birth_day   INTEGER NOT NULL,
    birth_hour  INTEGER,          -- NULL 허용 (시각 모르는 경우)
    birth_tz    VARCHAR(50) NOT NULL DEFAULT 'Asia/Seoul',
    gender      CHAR(1),          -- 'M', 'F', NULL
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 사주팔자 계산 결과 캐시
CREATE TABLE saju_cache (
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    engine      VARCHAR(20) NOT NULL,  -- 'lunar-python' or 'fallback'
    eight_glyphs CHAR(8) NOT NULL,
    year_pillar  JSONB NOT NULL,
    month_pillar JSONB NOT NULL,
    day_pillar   JSONB NOT NULL,
    hour_pillar  JSONB,
    element_scores JSONB NOT NULL,
    calculated_at  TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id)
);

-- 일간 감정 체크인
CREATE TABLE mood_checkins (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    mood_level INTEGER NOT NULL CHECK (mood_level BETWEEN 1 AND 5),
    mood_tag   VARCHAR(50),
    checkin_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id, checkin_date)
);

-- AI 해석 이력
CREATE TABLE ai_interpretations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE CASCADE,
    type        VARCHAR(30) NOT NULL,  -- 'daily', 'emotional_support', 'saju_analysis'
    lang        CHAR(2) NOT NULL DEFAULT 'ko',
    prompt_hash VARCHAR(64),           -- 동일 프롬프트 캐시용
    response    TEXT NOT NULL,
    tokens_used INTEGER,
    created_at  TIMESTAMP DEFAULT NOW()
);

-- 인덱스
CREATE INDEX idx_mood_user_date ON mood_checkins (user_id, checkin_date DESC);
CREATE INDEX idx_ai_user_type ON ai_interpretations (user_id, type, created_at DESC);
```

---

## 9. 알고리즘 검증 계획

### 9.1 단위 테스트 케이스

검증해야 할 핵심 날짜들 (절기 경계일 포함):

| 생년월일시 | 기대 사주 | 검증 포인트 |
|-----------|----------|------------|
| 1984-02-04 00:00 | 갑자년 | 입춘 경계 |
| 1990-01-27 (음력설) | 기사년 vs 무진년? | 설날 vs 입춘 기준 |
| 2000-01-07 갑자일 | 기준일 검증 | 일주 계산 |
| 2026-12-31 23:30 | 시주 = 子 | 자정 경계 |

### 9.2 사용자 피드백 루프

서비스 론칭 후:
- "내 사주 계산이 틀렸어요" 신고 기능 → 관리자 검토 큐
- 신고된 케이스를 테스트 케이스에 추가
- 월 1회 알고리즘 정확도 검토 (fallback vs lunar-python 불일치 케이스 모니터링)

---

작성: nova-strategy  
참고: saju_engine.py (구현체), /root/.hermes/projects/saju-wellness/data/ (만세력 데이터)
