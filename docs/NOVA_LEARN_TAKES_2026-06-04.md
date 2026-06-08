# saju-wellness nova-learn 학습 통합 문서

작성: nova-document (kanban t_ea8ce867)
작성일: 2026-06-04
기반: nova-learn 학습 결과 (t_911d66b0) + 이전 문서 (t_2294fea0)
Diataxis 분류: Reference (구조적 사실 기록)

---

## 1. nova-learn Takes 요약 (2026-05-27 기준)

nova_brain.db에 기록된 takes 10건의 핵심 패턴:

### 1.1 GOLD 패턴 (weight >= 0.95)

| ID | 패턴 | 근거 |
|----|------|------|
| saju-001 | Python 3.12 asyncio.Semaphore: 모듈 레벨 생성 금지 → lazy-init | RuntimeError 실증 (ai_insight.py L14) |
| saju-002 | '감정코칭'/'코치' 표현: 심리코칭법 선제 위험 → '가이드'/'인사이트' 대체 | 법적 감사 CRITICAL 판정 |
| saju-003 | 배포 전 Docker 환경 확인 필수 | 스프린트1 마지막 blocked 원인 |

### 1.2 SILVER 패턴 (weight >= 0.80)

| ID | 패턴 | 근거 |
|----|------|------|
| saju-004 | 기분 데이터 = 개보법 §23 민감정보 → 별도 동의 버튼 필수 | 헤르2 법적 감사 |
| saju-005 | JWT 블랙리스트: threading.Lock은 단일 워커에서만 안전 → Redis 폴백 설계 | 멀티워커 실증 미완 |
| saju-006 | 위기 키워드(CRISIS_KEYWORDS) DRY 원칙: 3곳 분산 → 단일 상수 | 코드 리뷰 반복 지적 |
| saju-007 | NOVA 체인 엔진: 폴링 크론 22개 → 이벤트 드리븐 1개 | 효율성 10x 실증 |

### 1.3 미검증 영역 (스프린트2 이월)

| 항목 | 상태 | 필요 조건 |
|------|------|-----------|
| AI_SEMAPHORE 멀티워커 | 미검증 | uvicorn --workers N 환경 |
| JWT Redis 실증 | 미검증 | 실서버 REDIS_URL |
| 배포 환경 | 미검증 | noivan.env 5개 + Docker 환경 |
| 커버리지 95% | 89% | 10개 테스트 케이스 추가 필요 |

---

## 2. NOVA 체인 v1.1 운영 기록

### 체인 실행 시퀀스

```
nova-qa (QA 감사)
  ↓ [보안 이슈 감지]
nova-dev (구현 — HIGH 3건)
  ↓ [코드 생성]
nova-review (코드 리뷰)
  ↓ [CRITICAL=0 확인]
nova-evaluator (최종 평가)
  ↓ [PASS 판정]
nova-retro (회고 + SOUL.md 갱신)
  ↓ [패턴 추출]
nova-learn (지식 통합 — takes 10건)
  ↓ [nova_brain.db 기록]
nova-document (이 문서)
```

### 성과 지표

| 지표 | 값 |
|------|-----|
| 자율 체인 완주 | 최초 실증 (2026-05-27) |
| 총 태스크 수 | 13개 |
| 자율 완료 | 11개 (84.6%) |
| 사람 개입 | 0회 (배포 제외) |
| nova_brain.db takes | 10건 기록 |

---

## 3. 스프린트1 → 스프린트2 이관 정보

### 이관 파일

| 파일 | 위치 | 용도 |
|------|------|------|
| SPRINT1_REPORT.md | docs/ | 스프린트1 전체 결과 보고서 |
| HANDOFF.md | / | 법적 감사 결과 + 표현 금지 목록 |
| CHANGELOG.md | / | v1.1.0 변경 이력 |
| evolution.md | / | NOVA 진화 기록 (이번 문서에서 갱신) |

### 스프린트2 DAG (t_b7bd3e05에서 생성)

```
t_02524df8 (nova-dev, HIGH 3건)  ─┐
t_b4a524a8 (nova-dev, MEDIUM 3건) ─┤→ t_aeecb5f3 (nova-qa, QA)
t_f501065f (nova-dev, 커버리지)   ─┘
t_34f2d564 (nova-strategy, 배포 환경)  [독립 병렬]
```

### 필요 환경변수 (노이반 수신 대기)

```
SAJU_DB_PASSWORD
MENTAL_DB_PASSWORD
SENIOR_DB_PASSWORD
SECRET_KEY
REFRESH_SECRET_KEY
```

---

## 4. 법적 포지셔닝 요약

(HANDOFF.md 전문 참조)

| 항목 | 결정 |
|------|------|
| 서비스 분류 | 문화·오락 (명리학 자기이해 도구) |
| 금지 표현 | 코치/코칭/심리상담/진단/치료 |
| 권장 표현 | 가이드/인사이트/해석/탐색 |
| 면책 문구 | 3개 언어 (ko/ja/en) 자동 첨부 |
| 위기 감지 | 1393 자살예방상담전화 자동 안내 |
| 기분 데이터 | 개보법 §23 → 별도 동의 필수 |

---

*nova-document 작성 완료 — Diataxis Reference 형식*
*다음 단계: 스프린트2 dev 태스크 완료 후 nova-document 재실행 예정*
