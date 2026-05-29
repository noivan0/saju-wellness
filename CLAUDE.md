# saju-wellness 하네스 메타 포인터

## Active Harness
harness.md

## 트리거 조건
- 키워드: '앱 실행', '배포', 'saju-wellness 상태'
- 크론 트리거: nova auto 루프

## Phase 순서
0. 컨텍스트 확인 (_workspace/ 존재 시 재개, 없으면 신규)
1. 환경 설정 (환경변수 + .env 확인)
2. 테스트 실행 (pytest -q)
3. 품질 검사 (Codex 감사, 기준: 70점 이상)
4. 배포 준비 (노이반 .env 8개 수신 후)

## 실패 시
_workspace/에 진행 단계 저장 후 재시작 시 해당 Phase부터 재개
