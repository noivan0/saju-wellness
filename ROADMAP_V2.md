# ROADMAP_V2.md — 사주담 v2 로드맵 전략 문서

## 비전
동서양 점성술 통합 + 학문적 정확도 + 글로벌 3개 언어 → AI 웰니스 플랫폼

---

## Phase 1: 사주 + 서양 점성술 MVP (현재 — 2026 Q2)

### 완료 ✅
- 사주팔자 4주 계산 엔진 (saju_engine, 한국음력/절기 보정)
- 60갑자 일주 해석 데이터
- 오행 해석 JSON (5종)
- 월별 운세 달력
- 궁합 분석 (오행 상생/상극)
- FastAPI REST API + JWT 인증
- 레이트 리밋 (SlowAPI)
- Claude AI 해석 연동

### v2 신규 구현 ✅
- **서양 점성술 엔진** (ephem 기반 10행성/어센던트/어스펙트)
- **학문적 정확도 프롬프트** (명리학 정통 규칙 / 서양 점성술 규칙)
- **동서양 통합 해석** (일간 ↔ 태양궁 크로스 해석)
- **일관된 응답 포맷** (5섹션 고정: 성격/재운/애정/건강/올해)
- **헤르 API 연동** (claude-sonnet-4-6, HMG 내부 엔드포인트)
- **i18n 3개 언어** (ko/ja/en JSON 완성)

### API 엔드포인트 현황
```
POST /saju/calculate          # 사주팔자 계산
POST /saju/daily-energy       # 오늘의 에너지 (규칙 기반)
POST /saju/compatibility      # 궁합 분석
GET  /saju/fortune-calendar   # 월별 운세 달력
GET  /saju/pillar-details     # 일주 상세 해석

[v2 신규 예정]
POST /astrology/natal-chart   # 서양 점성술 출생 차트
POST /astrology/sun-sign      # 태양궁 계산 (간편)
POST /interpret/bazi          # 명리학 AI 해석 (학문적)
POST /interpret/astrology     # 서양 점성술 AI 해석
POST /interpret/integrated    # 동서양 통합 AI 해석
GET  /i18n/{lang}             # i18n 번역 파일
```

---

## Phase 2: 심화 분석 (2026 Q3 — 3개월)

### 기능
- **궁합 심화**: 일주×일주 상세 60갑자 매트릭스 궁합
- **연간 운세 리포트**: 대운(大運)/세운(歲運) 10년 흐름 시각화
- **서양 점성술 트랜짓**: 현재 행성 위치 × 출생차트 교차
- **PDF 리포트 생성**: 개인화 운세 보고서 (한/일/영)
- **푸시 알림**: 오늘의 에너지 daily 알림 (FCM)

### 기술
- PostgreSQL → Redis 캐싱 레이어 (사주/차트 계산 결과)
- celery + redis 비동기 AI 해석 큐
- PDF 생성: reportlab 또는 WeasyPrint

### KPI
- DAU 1,000 달성
- 리텐션 D7 > 25%
- 유료 전환율 > 3%

---

## Phase 3: 일본 시장 공식 런칭 (2026 Q4 — 6개월)

### 전략
- 일본 App Store 등재 (사주담 JP 버전)
- 일본 명리학 용어 완전 현지화 (四柱推命 표준)
- 일본 결제: PayPay / LINE Pay 연동
- 일본 점성술 커뮤니티 B2C 마케팅

### 기능
- 음력 기반 일본 전통 점술 연계 (六曜, 暦注)
- 일본 전용 콘텐츠: 성인식/결혼/취직 특화 리포트
- 일본어 AI 상담 품질 최적화

### KPI
- 일본 사용자 10,000명
- App Store 사주/점술 카테고리 Top 20
- 월 구독 ARR $50K

---

## Phase 4: AI 상담사 + B2B HR (2027 Q1 — 12개월)

### AI 상담사 1:1 세션
- 사주 기반 진로/관계/건강 상담 (30분 AI 세션)
- 구독 모델: ₩9,900/월 (5회 세션)
- 위기 감지 → 전문 상담사 연결 (CTA)

### B2B HR 솔루션
- 기업 팀 빌딩: 팀원 사주 에너지 상성 분석
- 채용 보조 도구: 지원자 에너지 유형 참고 자료
- 법적 포지셔닝: "문화 활동 / 참고 도구" (채용 결정 근거 아님)
- 파일럿: 중소기업 HR팀 5개사 무료 제공

### 수익 모델
```
개인 B2C:
  Free: 사주 계산 + 일간 에너지 (광고 지원)
  Premium: ₩4,900/월 — AI 해석 무제한 + 통합 분석
  Pro: ₩9,900/월 — AI 상담 세션 5회 + PDF 리포트

B2B HR:
  Starter: ₩99,000/월 (팀 20명)
  Business: ₩299,000/월 (팀 100명 + 전담 CS)
  Enterprise: 협의
```

### KPI (Phase 4 말)
- MRR $100K
- B2B 계약 20개사
- 총 사용자 100,000명 (한/일/글로벌)

---

## 기술 스택 진화 경로

```
현재 (v1):          → Phase 2:          → Phase 3:          → Phase 4:
FastAPI             FastAPI             FastAPI             FastAPI (MSA)
SQLite/PostgreSQL   PostgreSQL+Redis    PostgreSQL+Redis    PostgreSQL+Redis
Claude API          Claude API          Claude API (ja fine-tune)  Claude API
ephem               ephem               ephem               ephem + Swiss Ephemeris
i18n ko/ja/en       i18n ko/ja/en       i18n 완성            i18n + TTS
규칙 기반           Celery 비동기        PDF/Push            AI 세션 엔진
```

---

## 법적 리스크 관리

모든 단계에서 유지:
1. 모든 응답 끝 면책 문구 자동 첨부
2. "심리상담/의료 대체" 표현 전면 금지
3. 위기 키워드 선제 감지 → 1393/988/0570-783-556 즉시 안내
4. B2B HR: "채용 결정 근거 불가" 계약서 명시
5. 일본: 개인정보보호법(個人情報保護法) 준수

---

_최종 업데이트: 2026-05-22 | 작성: 헤르(Hermes Agent) nova-dev_
