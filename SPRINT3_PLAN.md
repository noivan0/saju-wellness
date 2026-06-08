# saju-wellness Sprint 3 계획

작성자: nova-autoplan
작성일: 2026-06-08
상위 태스크: t_24d4fe6a (nova-autoplan 체인)

---

## Sprint 2 결과 요약 (입력 기반)

| 항목 | Sprint 2 달성 | 목표 |
|------|--------------|------|
| 테스트 커버리지 | 93.83% (878 PASS, 0 FAIL) | 70%+ |
| HIGH 보안 이슈 | Semaphore lazy-init 5개 (nova-dev 수정 완료) | 0 |
| MEDIUM 이슈 | 3건 (get_running_loop/DRY/session) 수정 | 0 |
| 배포 환경 | 여전히 noivan.env 대기 | 배포 완료 |
| JWT Redis 실증 | REDIS_URL 없이 메모리 폴백 (허용) | 실증 |

**Sprint 2 판정: PASS (커버리지 목표 대폭 초과, 보안 이슈 수정 완료)**

---

## Sprint 3 목표

### 1. 커버리지 93.83% → 95%+ (소폭 추가)
- 미커버 경로: ai_interpreter.py 라인 279-313 (외부 API 의존)
- 테스트 추가 대상: 엣지케이스 / 오류 경로 / 경계값
- 전략: Mock 기반 외부 의존성 격리 후 커버

### 2. Pydantic v2 migration + async 패턴 검증 (nova-qa t_b92b3625)
- v1 deprecated API 제거
- async route 패턴 정합성 확인
- 회귀 없음 검증

### 3. 역방향↩ 태스크 해소
- t_77a49f77 (nova-dev): DoD 미달 재구현 → 완료 후 nova-review로 전달
- t_74a1665e (nova-review): 검토 후 nova-qa로 전달
- t_f70b89d6 (nova-investigate): nova-ship 실패 원인 조사

### 4. 배포 (여전히 blocking)
- noivan.env 8개 변수 수신 대기
- Dockerfile 검증은 완료 상태 유지
- 실서버 배포: 노이반 환경변수 제공 후 즉시 실행

---

## Sprint 3 태스크 분배

| 에이전트 | 담당 | 태스크 상태 |
|---------|------|------------|
| nova-dev | 커버리지 95% + 역방향 DoD 재달성 | running (t_77a49f77) |
| nova-qa | Pydantic v2 migration 검증 | running (t_b92b3625) |
| nova-review | DoD 통과 후 리뷰 | running (t_74a1665e) |
| nova-ship | 배포 (noivan.env 수신 시) | blocked (t_1d6697f6) |
| nova-strategy | 배포 환경 준비 | blocked (t_34f2d564) |
| nova-investigate | nova-ship 실패 조사 | todo (t_f70b89d6) |

---

## 알려진 블로커

1. **실서버 배포**: noivan.env 8개 미수신 — Sprint 3에서도 유지
2. **Redis JWT 블랙리스트**: REDIS_URL 환경변수 없으면 메모리 폴백 (허용)
3. **역방향 체인**: nova-dev t_77a49f77 DoD 재달성 필요

---

## DoD 기준 (Sprint 3)

- 테스트 커버리지 ≥ 95%
- CRITICAL = 0, HIGH = 0
- Pydantic v2 마이그레이션 완료
- 역방향↩ 태스크 전체 해소

---

## 체인 순서

```
nova-dev (t_77a49f77 역방향 해소)
  ↓
nova-review (DoD 통과 후)
  ↓
nova-qa (커버리지 + Pydantic 검증)
  ↓
nova-document (Sprint 3 보고서)
  ↓
nova-document-release (릴리즈)
  ↓
nova-autoplan (Sprint 4 계획 or 배포 트리거)
```
