# 사주담 (Saju-Wellness) — AI 명리학 사주 서비스

> 사주팔자(四柱八字) 계산 + Claude AI 상세 해석 + 운세달력 + 궁합 분석

---

## 화면 구성

| 탭 | 설명 |
|----|------|
| 나의 사주 | 생년월일시 입력 → 년주/월주/일주/시주 + AI 상세 해석 |
| 오늘의 에너지 | 일주 × 오늘 일진 교차 분석 + AI 에너지 해석 |
| 궁합 | 두 사람의 오행 관계 분석 |
| 상성보기 | API 기반 궁합 상세 분석 + AI 해석 |
| 운세달력 | 월별 운세 + 일자별 달력 클릭 상세보기 |

---

## 기술 스택

- **백엔드**: Python + FastAPI
- **사주 엔진**: `saju_engine.py` (60갑자, 절기 기반)
- **음력 변환**: `korean-lunar-calendar` (KASI 기반)
- **AI 해석**: Claude API (`src/services/ai_interpreter.py`)
- **프론트엔드**: Vanilla JS (다크 테마 SPA)

---

## 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

```env
# 필수
SECRET_KEY=your_random_secret

# AI 해석 (없으면 기본 해석만 제공)
ANTHROPIC_API_KEY=your_claude_api_key
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 또는 사내 게이트웨이

# 선택
KASI_API_KEY=    # 음력 변환 API 폴백용
ALLOWED_ORIGINS=http://localhost:3000
```

### 3. 서버 실행

```bash
# 개발
uvicorn src.api.main:app --host 0.0.0.0 --port 8002 --reload

# 프로덕션
uvicorn src.api.main:app --host 0.0.0.0 --port 8002
```

브라우저에서 `http://localhost:8002/app` 접속

---

## 주요 API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/api/saju/calculate` | 사주팔자 계산 + AI 해석 |
| POST | `/api/saju/daily-energy` | 오늘의 에너지 |
| POST | `/api/saju/compatibility` | 궁합 분석 |
| GET | `/api/saju/fortune-calendar` | 월별 운세달력 |
| GET | `/api/saju/fortune-calendar/daily` | 일별 운세달력 |
| GET | `/api/saju/pillar-details` | 일주 상세 해석 |
| GET | `/health` | 헬스체크 |

### 사주 계산 예시

```bash
curl -X POST http://localhost:8002/api/saju/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "birth_year": 1990,
    "birth_month": 5,
    "birth_day": 15,
    "birth_hour": 10,
    "gender": "male",
    "lang": "ko"
  }'
```

응답에 `interpretation.ai` 필드로 AI 상세 해석이 포함됩니다.

---

## 사주 엔진 정확도

| 항목 | 방법 | 정확도 |
|------|------|--------|
| 음력 변환 | KASI 기반 (korean-lunar-calendar) | ✅ 최고 |
| 연주 | 입춘 기준 정확 계산 | ✅ |
| 일주 | JDN(율리우스 통일적일) 기반 | ✅ |
| 시주 | 오자환원법 (2시간 배당) | ✅ |
| 월주 | 절기 기준 | ✅ |

### 12지시 2시간 배당 (KST 기준)
```
子자시 23:00~01:00  |  午오시 11:00~13:00
丑축시 01:00~03:00  |  未미시 13:00~15:00
寅인시 03:00~05:00  |  申신시 15:00~17:00
卯묘시 05:00~07:00  |  酉유시 17:00~19:00
辰진시 07:00~09:00  |  戌술시 19:00~21:00
巳사시 09:00~11:00  |  亥해시 21:00~23:00
```

---

## Docker로 실행

```bash
docker build -t saju-wellness .
docker run -p 8002:8002 --env-file .env saju-wellness
```

---

## 추가로 구현 필요한 부분

### 🔴 필수

1. **ANTHROPIC_API_KEY 설정**
   - 없으면 AI 상세 해석이 비어있음 (기본 해석만 제공)
   - `interpretation.ai` 필드가 `{}` 로 반환됨
   - Claude API 키: https://console.anthropic.com/

2. **회원 인증 시스템**
   - 현재: 비로그인 체험용 (rate limit 10회/분)
   - 필요: JWT 로그인 → 개인 사주 저장/조회 기능

3. **사주 저장 기능**
   - 현재: DB 없이 계산만 반환
   - 필요: PostgreSQL로 사주 기록 저장, 연도별 운세 히스토리

### 🟡 권장

4. **AI 해석 캐싱**
   - 동일한 사주는 Redis 캐시 활용 (응답 속도 개선)

5. **궁합 고도화**
   - 현재: 일간 오행 1:1 비교
   - 필요: 연지, 월주, 시주까지 포함한 종합 궁합

6. **다국어 완성**
   - 현재: ko/ja/en 구조 있음
   - 일본어 해석 데이터 추가 필요

7. **모바일 앱 버전**
   - 현재: 모바일 반응형 웹
   - 권장: React Native 또는 Flutter 앱

---

## 프로덕션 체크리스트

```
[x] FastAPI 서버
[x] 60갑자 사주 계산 (연/월/일/시주)
[x] 음력 변환 (KASI 기반)
[x] AI 상세 해석 (Claude)
[x] 운세달력 (월별 + 일별)
[x] 궁합 분석
[x] 다크 테마 UI
[ ] 회원 인증 & 사주 저장
[ ] AI 해석 캐싱 (Redis)
[ ] HTTPS/SSL
[ ] 궁합 고도화
```

---

## 법적 고지

본 서비스는 명리학적 관점의 **문화·오락 서비스**이며,  
전문적 심리상담, 의료 행위, 점술을 대체하지 않습니다.

---

## 라이선스

Private — 노이반 프로젝트
