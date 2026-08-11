---
name: 사주담 (Saju Wellness) — UI 전면 재설계 v2
version: 2.0.0
date: 2026-08-11
status: approved-by-default (노이반 응답대기 초과, 헤르 최선판단 진행 — 스타일1 에디토리얼 미스틱 채택)
concept: "에디토리얼 미스틱 (Editorial Mystic)"
references:
  - Co-Star (costarastrology.com): 오프블랙+웜아이보리, 세리프 헤드라인 타이포그래피 권위감
  - 2026 디자인 트렌드: 퓨어블랙 대신 오프블랙(할레이션 방지), 그레인 텍스처, Bento Grid, OKLCH
  - 기존 사주담 브랜드 자산: 오행 색상, 한자(干支) 표기, 딥네이비+금색 정체성 → 절제된 재해석
kb: "[[kb/design/design-reference-db.md]] Astrology/Wellness Mystic 섹션"
---

## 재설계 핵심 원칙

1. **캔디톤 saturated 색상 전면 폐기** — 기존 wood #22c55e/fire #ef4444 같은 "부트스트랩st"
   원색은 전부 muted/editorial 톤으로 재조정. 채도를 낮추고 톤온톤 구성.
2. **타이포그래피가 주인공** — Co-Star처럼 사진/일러스트 없이 굵은 세리프 헤드라인과
   여백으로 "권위 있는 해석자"라는 브랜드 포지셔닝을 시각적으로 증명.
3. **오프블랙 배경** — 퓨어블랙(#000) 대신 #0A0908(웜 오프블랙)으로 할레이션 방지,
   눈피로 감소(2026 트렌드).
4. **한자/간지는 유지하되 격상** — 甲乙丙丁 같은 한자 표기는 사주담의 핵심 차별점이므로
   삭제하지 않고, 더 큰 세리프 타이포로 "아트웍처럼" 격상.
5. **딥리딩(3대 고전) 신기능이 UI의 히어로** — 기존 UI엔 없던 deep-reading 탭을
   최상단 primary CTA로 배치. QUICK/STANDARD/DEEP 모드 선택 + 예상 소요시간 명시.
6. **Bento Grid 레이아웃** — 탭 전환 방식(기존) 대신 카드형 그리드로 여러 기능을
   한눈에 노출, 클릭 시 확장.

## 색상 시스템 (v2 — muted editorial)

```
--bg:            #0A0908   (오프블랙, 웜톤)
--bg-elevated:   #14120F   (카드 배경)
--bg-elevated-2: #1C1916   (호버 상태)
--ink:           #F5F0E6   (웜 아이보리 — 메인 텍스트, Co-Star 참조)
--ink-muted:     #A39C8E   (보조 텍스트)
--ink-faint:     #6B655A   (placeholder/disabled)
--border:        rgba(245,240,230,.08)
--border-strong: rgba(201,162,39,.28)  (금색 — 유지, 강조 요소만)
--gold:          #B8934A   (기존 #c9a227보다 채도 낮춤, 앤틱골드)
--gold-bright:   #D4AF6A   (호버/액티브)

/* 오행 — 채도 대폭 하향, 톤온톤 */
--wood:  #7A9B6E   (세이지 그린, 기존 #4ade80 대비 muted)
--fire:  #B8695A   (테라코타, 기존 #f87171 대비 muted)
--earth: #C4A35A   (머스타드 골드, 기존 #fbbf24 대비 muted)
--metal: #9C9890   (웜 그레이, 기존 #94a3b8 대비 warm-shift)
--water: #5E7A8C   (스레이트 블루, 기존 #60a5fa 대비 muted)
```

## 타이포그래피

```
--font-serif: 'Noto Serif KR', 'Source Serif Pro', serif   (헤드라인 — 권위감)
--font-sans:  'Pretendard', 'Inter', sans-serif             (본문/UI)
--font-han:   'Noto Serif KR', serif                        (한자 — 격상, 기존보다 큰 스케일)

h1 (히어로 헤드라인): 2.75rem / 700 / letter-spacing -0.03em / line-height 1.1
h2 (섹션): 1.5rem / 700 / serif
body: 1rem / 400 / line-height 1.7 / sans
han-hero (사주 기둥 한자): 2.5rem / 700 / serif / gold  (기존 1.875rem에서 확대)
label: 0.8125rem / 500 / uppercase / letter-spacing 0.04em / ink-muted
```

## 레이아웃 — Bento Grid

```
그리드: 2열 기본(모바일), 최대 480px 컨테이너 유지
카드 라운딩: 4px (기존 20px에서 대폭 축소 — 에디토리얼 성격, 브루탈리즘 절제 버전)
카드 보더: 1px solid var(--border), 강조카드만 border-strong
그레인 텍스처: body::before에 SVG noise 오버레이 opacity .025 (2026 트렌드)
간격 시스템: 4/8/12/16/24/32/48px 스케일 고정
```

## 신규 정보구조 (기존 5탭 → 재편)

1. **히어로 섹션**: "오늘의 나를 이해하는 가장 오래된 방법" 세리프 헤드라인 +
   생년월일 입력 폼 (기존 유지, 톤만 재설계)
2. **정밀 사주 풀이 (deep-reading)** — 신규 히어로 카드, 최상단 배치
   - 3대 고전(자평진전/적천수/궁통보감) 뱃지 노출
   - QUICK(~1분)/STANDARD(~3분)/DEEP(~5분) 모드 선택 세그먼트 컨트롤
   - 로딩 중 진행 상태 텍스트 (30초~5분 소요 고려, 스켈레톤 UI + 경과시간 표시)
3. **오늘의 에너지** (기존 daily-energy 유지, Bento 카드로 재배치)
4. **궁합 분석** — 기존 "궁합"(로컬)과 "상성보기"(API) 2개 중복 탭을 1개로 통합,
   내부적으로 API(compatibility) 사용 + 오행 상생상극 시각화 유지
5. **운세달력** (기존 fortune-calendar 유지, Bento 카드)
6. 접근성: 모든 인터랙티브 요소에 aria-label 추가, 색상 대비 WCAG AA 확보

## 배포 전 필수 검증 (DoD)
- [ ] 신규 deep-reading UI가 실제로 /api/saju/deep-reading 호출하고 응답 렌더링
- [ ] 기존 5개 API(calculate/ai-interpret/daily-energy/compatibility/fortune-calendar) 회귀 없음
- [ ] 궁합 통합 탭에서 중복 로직 제거 확인
- [ ] 색상 대비 WCAG AA (아이보리/오프블랙 대비 확인)
- [ ] 모바일 뷰포트(360px~480px) 실제 렌더링 확인
- [ ] Codex 독립 감사 APPROVED
