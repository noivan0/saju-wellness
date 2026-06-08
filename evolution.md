# saju-wellness evolution log

NOVA v3.0 — 자율 진화 기록

---

## 스프린트1 완주 (2026-05-27)

nova-learn 학습 통합 완료 (takes 10건 기록).

### 핵심 학습 사항

**자율 성장 루프 최초 실증:**
- 체인: nova-qa → nova-dev → nova-review → nova-evaluator → nova-retro → nova-learn → nova-document
- 이벤트 드리븐 방식 (폴링 크론 22개 → 체인 엔진 1개 통합)
- NOVA v1.1 첫 완전 자율 실행

**보안 수정 완료:**
- HIGH-1: Python 3.12 asyncio.Semaphore lazy-init (ai_insight.py L14)
- HIGH-2: /api/insight/daily slowapi 율 제한 적용
- HIGH-3: JWT 블랙리스트 Redis 멀티워커 지원 (메모리 폴백 포함)
- 6종 HTTP 보안 헤더 미들웨어
- CVE-2024-33664 (PyJWT 2.9.0) / CVE-2024-0232 (bcrypt 72바이트) 패치

**법적 리스크 학습:**
- '감정코칭'/'코치' 표현 → 심리코칭법 위험 → 전면 금지
- 기분 데이터 = 개보법 §23 민감정보 → 별도 동의 필수
- 국외이전(Anthropic API): 개보법 28조의8 동의 항목 필수

**배포 차단 원인 확인:**
- 헤르 컨테이너에 Docker 미설치 → 서버 직접 배포 불가
- 해결 경로: noivan.env 8개 수신 + 호스트 SSH 또는 Docker 환경

### 스프린트1 수치

| 항목 | 결과 |
|------|------|
| 총 태스크 | 13개 |
| 완료 | 11개 (84.6%) |
| Blocked | 1개 (배포) |
| CRITICAL | 0건 |
| HIGH (수정됨) | 3건 |
| 테스트 커버리지 | 89% |
| nova_brain.db takes | 10건 |

---

## 스프린트2 계획 수립 (2026-05-27)

nova-autoplan이 인계받아 5개 태스크 DAG 생성:
- t_02524df8: HIGH 3건 수정 (nova-dev)
- t_b4a524a8: MEDIUM 3건 수정 (nova-dev)
- t_f501065f: 커버리지 89→95% (nova-dev)
- t_aeecb5f3: QA 감사 (nova-qa, dev 완료 후 자동 실행)
- t_34f2d564: 배포 환경 준비 (nova-strategy)

스프린트2 남은 이슈:
1. AI_SEMAPHORE 멀티워커 실증 (uvicorn --workers N 환경에서 미검증)
2. JWT Redis 블랙리스트 멀티워커 실증 필요
3. /api/insight/daily 인증 사용자 분리 (30/min 상향)
4. noivan.env 5개 환경변수 수신 대기

---

## 스프린트2 완주 (2026-06-04)

QA Round17 E2E 실증 완료. 878 PASS, 0 FAIL.

### 검증 결과

| 항목 | 결과 |
|------|------|
| 총 테스트 | 878건 |
| PASS | 878건 (0 FAIL) |
| 커버리지 | 93.83% (목표 72% 초과) |
| HIGH 수정 검증 | 3/3 전항목 ✅ |
| MEDIUM 수정 검증 | 3/3 전항목 ✅ |
| nova_brain.db takes | 10건 누적 (이번 5건) |

### 이번 실행 takes

- nova-learn 자율 성장 엔진: 21개 에이전트 evolution.md 갱신
- nova-qa takes=20, patterns=5
- nova-dev takes=20, patterns=5
- nova-evaluator takes=20, patterns=5
- nova-document takes=6, patterns=5

### 잔여 블로커

1. noivan.env 8개 수신 대기 (배포 전제조건)
2. Docker 환경 미구성 (호스트 배포 불가)
3. 커버리지 93.83% → 95% 1.17%p 추가 필요 (Sprint3)

---

## 자율 학습 루프 (2026-06-08)

nova-learn 자율성장 2차 실행. 3개 앱(멘탈로드/케어링/사주담) watchdog + 헬스체크 크론 체인 PASS.

### 핵심 학습 취득 (nova-learn takes 2026-06-08)

| Take | 내용 | Weight |
|------|------|--------|
| watchdog-pattern-001 | 크론 watchdog 표준: 30m 주기, no_agent=False(LLM판단), p95<5ms | 0.88 |
| watchdog-pattern-002 | URL 정규화: APP_BASE_URL + .rstrip("/") — 3앱 동일 패턴 통일 | 0.90 |
| chain-pattern-001 | NOVA 5단계 체인 PASS 패턴: SHIP→CHECKPOINT→CANARY→HEALTH→EVALUATOR | 0.85 |
| chain-loop-001 | nova_chain_engine 3단 자율성장 루프 반복 실증 (5건 이상 연속 성공) | 0.90 |
| system-001 | NOVA 21/21 에이전트 evolution 갱신 완료 (avg_score=0.834, 비활성=0) | 0.88 |

### 잔여 학습 과제 (Lacked 패턴)

- 에이전트 균등 활성화 미달 → 다음 스프린트 P1
- saju_health_check 상세 지표 미구현 (DB 레이턴시, 외부 API 응답시간)

---

## 문서화 이력

| 날짜 | 문서 | 작성자 |
|------|------|--------|
| 2026-05-27 | docs/SPRINT1_REPORT.md | nova-document (t_2294fea0) |
| 2026-05-27 | CHANGELOG.md (v1.1.0 섹션) | nova-document |
| 2026-05-27 | HANDOFF.md (법적 감사 결과) | 헤르2 법적 감사 |
| 2026-06-04 | evolution.md 갱신 | nova-document (t_ea8ce867) |
| 2026-06-04 | evolution.md Sprint2 섹션 추가 | nova-document (t_40e1a6fe) |
| 2026-06-04 | kb/agents/nova-document/2026-06-04-nova-learn-knowledge-integration.md | nova-document (t_40e1a6fe) |
| 2026-06-04 | CHANGELOG.md (v1.2.0 Sprint2 섹션) | nova-document (t_40e1a6fe) |
| 2026-06-08 | evolution.md 자율학습 루프 섹션 추가 | nova-document-release (t_d025d1fc) |

---

## Phase 상태

- Phase 0: 환경 설정 ✅ (변수 정의 완료, 수신 대기)
- Phase 1: 구현 ✅ (스프린트1+2 완주)
- Phase 2: QA ✅ (커버리지 93.83%, CRITICAL 0, HIGH 0, MEDIUM 0)
- Phase 3: 보안 ✅ (CRITICAL 0, HIGH 3 수정 검증, MEDIUM 3 수정 검증)
- Phase 4: 배포 🔲 (noivan.env 8개 + Docker 환경 필요)
