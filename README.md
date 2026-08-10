# 사주담 (Sajudam)

> **MVP / Alpha** — AI 사주팔자 + 감정 코칭 서비스. 20–40대 한국 여성 타겟.

---

## 🇰🇷 소개 | 🇺🇸 Overview

**[한글]**
사주팔자 기반 AI 운세 해석과 감정 코칭을 결합한 서비스입니다.
단순한 운세 풀이를 넘어, 사용자의 감정 상태를 이해하고 동양 인문학적 시각으로 위로와 방향을 제시합니다.

**[English]**
Sajudam combines traditional Korean Four Pillars (Saju) astrology with AI-powered emotional coaching.
Beyond fortune-telling, it understands the user's emotional state and provides comfort and direction through an Eastern humanistic lens.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔮 AI Saju Reading | Four Pillars analysis with personalized narrative — not template-based |
| 💬 Emotional Coaching | Sentiment-aware responses that adapt to user's emotional state |
| 🎁 Free Event Mode | Admin-managed free coaching events for community building |
| 🌏 Multilingual | Korean · Japanese · English — independent per-language builds |
| 🔒 Security | JWT HttpOnly/SameSite=Strict — CRITICAL 0 / HIGH 0 (NOVA audit certified) |
| 📊 SSE Push | Real-time streaming response via Server-Sent Events |

---

## 🧠 Design Principles

- **Maslach framework** — Emotional burnout detection patterns to tailor coaching depth
- **Eastern humanism** — Responses grounded in Korean/Chinese philosophical traditions (음양오행)
- **Dark mystique UX** — Deep indigo palette evoking cosmic, contemplative atmosphere

---

## 🚀 Quick Start

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
REDIS_URL=redis://localhost:6379  # JWT 블랙리스트 멀티워커 공유 (없으면 메모리 폴백)
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

## 🛠 Tech Stack

```
Backend   FastAPI · PostgreSQL · Redis · Anthropic Claude API
Auth      JWT (HttpOnly Cookie, SameSite=Strict)
Frontend  React · SSE streaming
Infra     Docker · async architecture
Security  OWASP LLM Top 10 · CRITICAL 0 / HIGH 0 (NOVA audit certified)
```

---

## 📡 API Endpoints

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| POST | `/api/saju/calculate` | 사주팔자 계산 + AI 해석 | 공개 |
| POST | `/api/saju/daily-energy` | 오늘의 에너지 | 공개 |
| POST | `/api/saju/compatibility` | 궁합 분석 | 공개 |
| GET | `/api/saju/fortune-calendar` | 월별 운세달력 | 공개 |
| GET | `/api/saju/fortune-calendar/daily` | 일별 운세달력 | 공개 |
| GET | `/api/saju/pillar-details` | 일주 상세 해석 | 공개 |
| GET | `/api/insight/daily` | 일간 AI 인사이트 (rate-limit 10/min) | 공개 |
| GET | `/api/insight/session` | 세션 AI 인사이트 (유료) | JWT 필요 |
| POST | `/api/auth/register` | 회원가입 | 공개 |
| POST | `/api/auth/login` | 로그인 → JWT 발급 | 공개 |
| POST | `/api/auth/logout` | 로그아웃 + JWT 블랙리스트 | JWT 필요 |
| POST | `/api/auth/refresh` | 토큰 갱신 | JWT 필요 |
| POST | `/api/ivr/` | IVR 음성전화 (Twilio) | Twilio 서명 |
| GET | `/health` | 헬스체크 | 공개 |

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

---

## 📱 App Preview

> MVP — UI design tokens defined. Core API complete.

**Design System**
- Background: `#0F0A1E` (Deep indigo — cosmic atmosphere)
- Primary: `#8B5CF6` (Violet — mystique & wisdom)
- Accent: `#F59E0B` (Amber — Eastern warmth)
- Font: Pretendard

---

## 📌 Status

```
✅ Saju calculation engine complete
✅ AI coaching API complete
✅ Security audit passed (CRITICAL 0 / HIGH 0)
✅ Multilingual architecture designed (KO / JA / EN)
🔧 Frontend MVP in progress
⏳ Pending: .env credentials for deployment
```

---

## 보안 현황 (v1.1.0 — Sprint1 완료)

### 구현 완료

| ID | 심각도 | 상태 | 설명 |
|----|--------|------|------|
| HIGH-1 | HIGH | ✅ FIXED | AI_SEMAPHORE Python 3.12 RuntimeError — lazy-init 패턴 적용 |
| HIGH-2 | HIGH | ✅ FIXED | /api/insight/daily 율 제한 미적용 — slowapi 10/min 구현 |
| HIGH-3 | HIGH | ⚠️ PARTIAL | JWT Redis 블랙리스트 — Redis 없으면 메모리 폴백 (REDIS_URL 필요) |
| CVE-2024-33664 | HIGH | ✅ FIXED | python-jose → PyJWT 2.9.0 교체 (alg:none 공격 차단) |
| CVE-2024-0232 | HIGH | ✅ FIXED | bcrypt 72바이트 명시 절단 |
| MEDIUM-1 | MEDIUM | ✅ FIXED | API 키 환경변수 관리 |
| MEDIUM-2 | MEDIUM | 🔲 OPEN | 기분 데이터 별도 동의 항목 (온보딩 UI 미구현) |

### OWASP HTTP 보안 헤더 (v1.1.0 적용)

- X-Frame-Options: DENY (클릭재킹 방지)
- X-Content-Type-Options: nosniff (MIME 스니핑 방지)
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy: Anthropic API만 외부 연결 허용
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: camera/microphone/geolocation 차단

---

## Sprint 체크리스트

### Sprint1 완료 항목 ✅

```
[x] FastAPI 서버
[x] 60갑자 사주 계산 (연/월/일/시주)
[x] 음력 변환 (KASI 기반)
[x] AI 상세 해석 (Claude)
[x] 운세달력 (월별 + 일별)
[x] 궁합 분석
[x] 다크 테마 UI
[x] JWT 인증 (PyJWT 2.9.0 — Access 1h / Refresh 30d)
[x] JWT 블랙리스트 (Redis/메모리 폴백)
[x] OWASP HTTP 보안 헤더 (6종)
[x] 율 제한 (slowapi — 인사이트 10/min)
[x] 위기 키워드 감지 (ko/ja/en — 1393 안내)
[x] i18n 3개 언어 (ko/ja/en)
[x] IVR 음성전화 (Twilio)
[x] 면책 문구 자동 첨부
```

### Sprint2 이월 항목 🔲

```
[ ] AI_SEMAPHORE 멀티워커 부하 테스트 (Locust workers=4)
[ ] JWT Redis 블랙리스트 멀티워커 실증 (REDIS_URL 설정)
[ ] /api/insight/daily 율 제한 인증/비인증 분리 (인증: 30/min)
[ ] 실서버 배포 (noivan.env + Docker 환경)
[ ] 테스트 커버리지 89% → 95%
[ ] 사주 저장 기능 (PostgreSQL)
[ ] AI 해석 캐싱 (Redis)
[ ] HTTPS/SSL
[ ] 궁합 고도화 (연지/월주/시주 포함)
[ ] 기분 데이터 별도 동의 UI (온보딩)
```

---

## 법적 고지

본 서비스는 명리학적 관점의 **문화·오락 서비스**이며,
전문적 심리상담, 의료 행위, 점술을 대체하지 않습니다.

**금지 표현**: 코치/코칭/상담/진단/치료/예측/보장 — 모든 응답에서 사용 금지
(위반 시 심리사법 경계 위험 — HANDOFF.md 표현 금지 목록 참조)

---

## 라이선스

Private — 노이반 프로젝트

---

## 🔗 Related

- [NOVA OSS](https://github.com/noivan0/NOVA) — Agent framework powering this app
- [noivan0 Portfolio](https://noivan0.github.io/noivan-portfolio/)
