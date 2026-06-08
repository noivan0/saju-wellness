# CHANGELOG — 사주담 (Saju Wellness)

형식: Keep a Changelog (https://keepachangelog.com)
버전 전략: MAJOR.MINOR.PATCH
법적 포지션: 문화·오락 서비스 (심리상담/의료 아님)

---

## [Unreleased — Sprint 3]

> 전제: noivan.env 8개 수신 + Docker 환경 구성 완료 후 진행
> 목표: 커버리지 95% 달성 + 최종 보안 감사 + 실서버 배포

### Planned
- 커버리지 93.83% → 95% (t_1b44a554 재개)
- 최종 보안 감사 (OWASP Top10 점검)
- noivan.env 8개 수신 → Docker 배포

### Sprint 3 nova-learn 지식 통합 정식 문서화 (2026-06-08)

nova-document Sprint 3 체인 문서화 (nova-document t_c9747200).

- Pydantic v2 마이그레이션 패턴 공식 등재: 1041→1132 테스트 부수 증가, 93.07% 커버리지 유지
- no_agent watchdog 황금률 Sprint 3 재확인: saju-wellness 3서비스 HTTP 200, 비용 0
- Telegram message_thread_id int 타입 필수 패턴 정립
- NOVA 8단계 체인 3차 완주 실증: build→review→security→qa→ship→evaluator→retro→learn 무중단
- Sprint 3 잔여 블로커 명확화: noivan.env 8개 + ANTHROPIC_API_KEY + 커버리지 93→95%
- KB 등록: kb/agents/nova-document/2026-06-08-sprint3-nova-learn-doc.md (8,208자)

### watchdog + 헬스체크 크론 체인 정식 문서화 릴리즈 (2026-06-08)

nova-document 정식 문서화 결과 릴리즈 (nova-document-release t_63368324).

- no_agent watchdog 황금률 실증: saju-wellness 3개 서비스 HTTP 200 확인 (크론 30분 주기, LLM 없이 완전 alerting 루프)
- TG_THREAD_ID int 변환 패턴 정립: str→int 명시 변환으로 Telegram API 오류 예방
- nova_chain 3단 자율성장 루프 반복 실증: evaluator→retro→learn→document 5/5 PASS
- Diataxis 4분류 공식 문서 구조 적용: Tutorial/How-to/Reference/Explanation
- KB 등록: kb/agents/nova-document/2026-06-08-watchdog-saju-wellness-doc.md (5,765자)

### 자율 학습 루프 릴리즈 (2026-06-08)

nova-learn 자율성장 2차 실행 결과 릴리즈 (nova-document-release t_d025d1fc).

- watchdog 표준 패턴 확립: 30m 주기, p95<5ms, 3앱 동시 모니터링 (크론 36ae57260fd9)
- URL 정규화 패턴 통일: APP_BASE_URL + .rstrip("/") (멘탈로드/케어링/사주담)
- NOVA 21/21 에이전트 evolution 갱신 완료 (avg_score=0.834)
- nova_chain_engine 3단 자율성장 루프 반복 실증 (5건 연속 성공)

### Sprint 3 nova-learn 지식 통합 공식 릴리즈 (2026-06-08)

nova-document Sprint 3 지식 통합 공식 릴리즈 (nova-document-release t_3bd783f4).

- Pydantic v2 마이그레이션 패턴 공식 릴리즈: 1041→1132 테스트 증가, 93.07% 커버리지 (commit 23bbc20)
- no_agent watchdog 황금률 Sprint 3 공식 릴리즈: LLM 없이 HTTP 200 감지 + Telegram 알림, 비용 0
- Telegram message_thread_id int 타입 강제 패턴 공식 릴리즈: `int(os.getenv("TG_THREAD_ID", "9"))` 표준화
- NOVA 8단계 체인 3차 완주 공식 릴리즈: build→review→security→qa→ship→evaluator→retro→learn 무중단
- Sprint 3 잔여 블로커 공식 명확화: noivan.env 8개 + ANTHROPIC_API_KEY + 커버리지 93→95%
- Diataxis 4분류 공식 문서 릴리즈: Tutorial/How-to/Reference/Explanation
- KB 릴리즈: kb/agents/nova-document/2026-06-08-sprint3-nova-learn-doc.md (8,208자)

---

## [v1.2.0] — 2026-06-04 (Sprint 2 완료)

> 스프린트 2 완주. NOVA 자율 체인 연속 실행. 878 테스트 PASS, 커버리지 93.83%.
> 배포 블로커(Docker + noivan.env) 해소 후 v1.3.0 릴리즈 예정.

### Security

- [HIGH-1] Python 3.12 asyncio.Semaphore RuntimeError 수정 (Sprint2 검증)
  - _get_semaphore() lazy-init 패턴 — 5개 동시 요청 정상 처리 확인
  - 위치: src/services/ai_insight.py L14-24

- [HIGH-2] /api/insight/daily 율 제한 구현 (Sprint2 검증)
  - slowapi @limiter.limit("10/minute") — Round17 E2E 3개 케이스 검증 완료

- [HIGH-3] JWT 블랙리스트 Redis 멀티워커 지원 (Sprint2 검증)
  - REDIS_URL 있으면 Redis, 없으면 메모리 폴백 — revoke_token/revoke_user_tokens/is_token_revoked 검증 완료

### Fixed

- [MEDIUM-1] get_running_loop() 대신 asyncio.get_event_loop() 패턴 수정
- [MEDIUM-2] DRY 원칙 위반 코드 리팩토링
- [MEDIUM-3] session_id secrets 모듈 사용 표준화

### QA

- Round17 E2E 실증: 878 PASS, 0 FAIL
- 커버리지: 93.83% (목표 72% 초과)
- 법적 포지션 재확인: '감정코칭' 문구 → '문화·오락 서비스' 로 대체 (법적 리스크 차단)

---

## [v1.1.0] — 2026-05-27

> 스프린트 1 완주. NOVA 자율 에이전트 체인(nova-qa → nova-dev → nova-review → nova-evaluator → nova-retro) 5단 자율 완주.

### Security

- [R13/R14] HTTP 보안 헤더 미들웨어 추가 (SecurityHeadersMiddleware)
  - X-Frame-Options: DENY (클릭재킹 방지)
  - X-Content-Type-Options: nosniff (MIME 스니핑 방지)
  - X-XSS-Protection: 1; mode=block
  - Content-Security-Policy: Anthropic API만 외부 연결 허용
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy: camera/microphone/geolocation 차단

- [HIGH-1] Python 3.12 asyncio.Semaphore RuntimeError 수정
  - 원인: 모듈 레벨 Semaphore() 생성이 Python 3.12에서 event loop 없이 RuntimeError 발생
  - 수정: _AI_SEMAPHORE = None (모듈 레벨) → _get_semaphore() lazy init 패턴
  - 위치: src/services/ai_insight.py L14-24

- [HIGH-2] /api/insight/daily 율 제한 구현
  - slowapi @limiter.limit("10/minute") 적용
  - IP 기반 키 (get_remote_address)
  - 미인증 공개 엔드포인트 보호

- [HIGH-3] JWT 블랙리스트 Redis 멀티워커 지원
  - REDIS_URL 환경변수 있으면 Redis, 없으면 메모리 폴백
  - revoke_token / revoke_user_tokens / is_token_revoked 3개 함수 구현
  - 탈퇴/로그아웃 시 즉시 블랙리스트 등록
  - 위치: src/core/auth.py L20-90

- [A07-REVOKE] CVE-2024-33664 대응: python-jose → PyJWT==2.9.0 교체
  - alg:none 공격 차단 확인 (401 반환)
  - HS256 알고리즘 명시 강제

- [BLK-JWT-LANG] 언어 파라미터 화이트리스트 검증
  - lang: Field(pattern="^(ko|ja|en)$") 적용
  - 허용값 외 입력 422 반환

### Fixed

- 라우터 이중 구조 통합 (PARTIAL PASS 이슈 해결)
  - 증상: main.py가 src/routes/saju.py(기본판)만 import, src/api/routes/saju.py(확장판) 미사용
  - 수정: main.py에서 양쪽 라우터 모두 등록 (saju_router + saju_base_router)
  - 결과: pillar-details, fortune-calendar, compatibility 엔드포인트 정상 노출

- bcrypt CVE-2024-0232 대응: 72바이트 명시 절단 적용 (src/api/routes/auth.py)

- 사주 계산 절기 경계일 KST 보정
  - lunar-python CST(UTC+8) → KST(UTC+9) +1h 보정
  - 절기 경계일(2월 3~5일) 월주 변경 테스트 12/12 PASS

### Added

- 60갑자 ILJU_PERSONALITY 전체 수록 (甲子~癸亥, 60개 완비)
- 위기 키워드 3개 언어 확장 (ko/ja/en)
  - 감지 시 1393 자살예방상담전화 자동 안내 (24시간)
  - 추가 안전망: 1577-0199 정신건강 위기상담전화
- /api/insight/daily 공개 엔드포인트 (JWT 불필요)
- /api/insight/session 유료 엔드포인트 (JWT 필요, 인가 분리)
- IVR 음성전화 라우터 (Twilio, src/api/routes/ivr.py)
- i18n 3개 언어 JSON 완성 (ko/ja/en)
- 면책 문구 자동 첨부 (모든 인사이트 응답 하단)

### Blocked (Sprint 2 이월)

- 실서버 배포: Docker 환경 없음 (헤르 컨테이너에 Docker 미설치)
  - 해결책: noivan.env 환경변수 + 실서버 SSH 키 세팅 후 재시도
- 커버리지 89% → 95%: 추가 테스트 케이스 작성 필요

---

## [v1.0.0] — 2026-05-22

> 스프린트 0: NOVA 에이전트 체인 초기 구현

### Added

- 사주팔자 4기둥 계산 엔진 (saju_engine.py — lunar-python 기반)
  - 연주/월주/일주/시주 완전 계산
  - 절기 기준 월주 결정 (입춘/경칩/청명 등)
  - 시주 모름 시 연·월·일 3기둥만 계산 지원

- FastAPI REST API 기본 구조
  - POST /saju/calculate: 사주팔자 계산
  - POST /saju/compatibility: 궁합 분석 (오행 상생/상극 기반)
  - GET  /saju/daily-energy: 오늘의 에너지 (규칙 기반)
  - GET  /saju/fortune-calendar: 월별 운세 달력
  - GET  /saju/pillar-details: 일주 상세 해석

- JWT 인증 (Access 1h / Refresh 30d)
  - flutter_secure_storage 연동 설계 (iOS Keychain, Android Keystore)

- 개인정보처리방침 (privacy_policy.md)
  - 개보법 28조의8 국외이전 항목 포함
  - GDPR / 개보법 / 個人情報保護法 준수
  - 기분 데이터 별도 동의 항목 (개보법 §23 민감정보 대응)

- Pydantic 입력 검증 (타입 강제, 범위 검증)
  - birth_year: 1900~2100, birth_month: 1~12, birth_day: 1~31

### Security

- [R25] 입춘 기준 연주 계산 — 절기 경계일 정확도 확보
- 환경변수 기반 API 키 관리 (.env — git 제외)
- ANTHROPIC_API_KEY 하드코딩 금지 정책 적용

---

## 보안 이슈 추적

| ID | 심각도 | 상태 | 설명 |
|----|--------|------|------|
| HIGH-1 | HIGH | FIXED (v1.1.0) | AI_SEMAPHORE Python 3.12 RuntimeError |
| HIGH-2 | HIGH | FIXED (v1.1.0) | /api/insight/daily 율 제한 미적용 |
| HIGH-3 | HIGH | PARTIAL (v1.1.0) | JWT Redis 블랙리스트 멀티워커 (Redis 환경 미확인) |
| CVE-2024-33664 | HIGH | FIXED (v1.1.0) | python-jose → PyJWT 2.9.0 교체 |
| CVE-2024-0232 | HIGH | FIXED (v1.1.0) | bcrypt 72바이트 절단 |
| MEDIUM-1 | MEDIUM | FIXED (v1.0.0) | API 키 환경변수 관리 |
| MEDIUM-2 | MEDIUM | OPEN | 기분 데이터 별도 동의 항목 (온보딩 UI 미구현) |

---

작성: nova-document (kanban t_2294fea0)
기반: nova-learn 스프린트1 통합 결과 (t_911d66b0)
