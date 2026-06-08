# saju-wellness Sprint 2 계획

작성자: nova-autoplan
작성일: 2026-06-04
상위 태스크: t_5f33dbff

---

## 현황 (Sprint 1 이후)

| 항목 | 현재 상태 | 목표 |
|------|-----------|------|
| 테스트 커버리지 | 46.4% (실측) | 70%+ |
| HIGH 보안 이슈 | 0개 (FIXED) | 유지 |
| 배포 환경 | 미완료 (노이반 .env 대기) | 배포 완료 |
| AI 인사이트 | 기본 구현 완료 | 품질 강화 |

---

## Sprint 2 목표

1. **테스트 커버리지 46.4% → 70%+**
   - engine/ 모듈 (saju_calculator, swiss_ephemeris 등) 테스트 추가
   - services/ 모듈 (ai_insight, llm_interpreter) 단위 테스트
   - routes/ (insight, ivr, auth) 커버리지 확장

2. **AI_SEMAPHORE 멀티워커 경쟁 조건 검증**
   - Python 3.12 lazy-init 패턴 실증
   - 동시 10요청 부하 테스트

3. **/api/insight/daily 율 제한 인증 사용자 분리**
   - 비인증: 10/minute 유지
   - 인증 사용자: 50/minute (별도 키)

4. **JWT Redis 블랙리스트 실증**
   - REDIS_URL 환경변수 테스트
   - 멀티워커 공유 검증

5. **배포 환경 준비**
   - Dockerfile 검증
   - noivan.env 8개 변수 목록 확정

---

## 태스크 분배

| 에이전트 | 담당 |
|---------|------|
| nova-dev | 구현 + 테스트 추가 (커버리지 개선) |
| nova-qa | 전체 테스트 스위트 실행 + 커버리지 검증 |
| nova-review | 코드 리뷰 + HIGH 이슈 점검 |

---

## 알려진 블로커

- 실서버 배포: noivan.env 8개 미수신 (배포 태스크는 블로킹 유지)
- Redis: REDIS_URL 없으면 메모리 폴백 (Sprint 2에서 실증만)
