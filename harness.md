# 사주담 (Saju Wellness) — NOVA Harness

## 목표
전통 사주명리 기반 웰니스 앱. FastAPI 백엔드 + 바닐라 JS 웹 UI.
- AI 심층 해석 통합 (ANTHROPIC_API_KEY 연동)
- 사주 결과 공유 카드 생성
- 사용자 히스토리 (SQLite 영속화)

## Phase 정의

### Phase 1: 서버 헬스체크 (60s)
- 서버 3 포트(8002) 정상 응답 확인
- `/api/saju/calculate`, `/api/saju/daily-energy`, `/api/saju/compatibility` 응답 검증
- UI `/app` HTML 서빙 확인

### Phase 2: API QA (120s)
- 유효/무효 입력에 대한 응답 코드 검증
- interpretation 딕셔너리 비어있지 않음 확인
- 궁합 점수 0~100 범위 확인
- 엣지케이스 처리 검증

### Phase 3: UI QA (120s)
- HTML 구조 / WCAG 토큰 / 한국어 콘텐츠 검증
- 오행 색상 정의 확인
- 이벤트 리스너 방식 검증

### Phase 4: Codex 감사 (90s)
- 파일 구조 / 보안 패턴 검사
- 데이터 파일 존재 및 JSON 유효성
- interpretation 로드 경로 검증

## 성공 기준
- Phase 1-4 전체 exit code 0
- CRITICAL 버그 0개
- UI WCAG AA 색상 토큰 적용
- interpretation 실제 데이터 반환

## 알려진 이슈
- interpretation 빈 dict 버그: pillar_interpretations.json 경로 로드 실패 가능 (Phase 2에서 감지)
- ANTHROPIC_API_KEY 미설정: AI 해석 비활성 (허용)
- PostgreSQL 미연결: 히스토리 미영속화 (MVP 단계 허용)

## 진화 이력
- 2026-05-22: NOVA 통합. Phase 1-4 스크립트 생성. (헤르)
