---
name: 사주담 (Saju Wellness)
version: 1.0.0
date: 2026-05-22
---

## 브랜드 포지셔닝
"오늘의 나를 이해하는 가장 오래된 방법" — 동양 명리학 × 현대 자기이해

## 색상 시스템 (오행 기반)
```
wood  (木/갑을): #22c55e  (초록 — 성장, 생명력)
fire  (火/병정): #ef4444  (빨강 — 열정, 에너지)  
earth (土/무기): #eab308  (황금 — 안정, 신뢰)
metal (金/경신): #f8fafc  (흰/은 — 순수, 결단)  배경 강조: #64748b
water (水/임계): #1e3a5f  (남색 — 지혜, 깊이)

primary:       #1e3a5f  (딥 네이비 — 밤하늘, 동양적)
primary-light: #2d5a8e
gold:          #c9a227  (금색 강조 — 사주패 테두리)
gold-light:    #e8c547
surface:       #0d1b2a  (다크 배경 — 밤 별자리)
surface-card:  rgba(255,255,255,.07)
surface-card-hover: rgba(255,255,255,.12)
text-primary:  #f8f9fa
text-secondary:#94a3b8
text-muted:    #64748b
border:        rgba(201,162,39,.25)  (금색 테두리)
```

## 타이포그래피
```
font-family: 'Noto Serif KR', 'Noto Serif SC', serif  (제목 — 고전적)
font-body:   'Pretendard', 'Noto Sans KR', sans-serif  (본문)
heading-xl:  2rem / 700 / letter-spacing: -0.02em
heading-lg:  1.5rem / 600
heading-md:  1.125rem / 600
body:        1rem / 400 / line-height 1.7
han-char:    1.5rem / 700 (甲乙丙丁... 한자)
```

## 컴포넌트 스펙
```
border-radius-card: 20px
border-radius-btn:  12px
shadow-card: 0 4px 24px rgba(0,0,0,.4), inset 0 1px 0 rgba(201,162,39,.2)
shadow-gold: 0 0 20px rgba(201,162,39,.3)
backdrop: blur(12px)
transition: 300ms cubic-bezier(.4,0,.2,1)
```

## 사주 기둥(四柱) 카드 스펙
```
각 기둥: 너비 80px / 높이 120px
한자: 1.75rem / gold 색상
간지: 0.75rem / text-secondary
오행 뱃지: 원형 8px / 해당 오행 색상
```

## 애니메이션
```
별자리 배경: CSS keyframe, 별 반짝임 (opacity 0.3→1 무한)
카드 등장: slideUp 400ms + fadeIn
궁합 결과: 게이지 fill 애니메이션 1.5s
```

## UX 원칙
1. 한자 표시 필수 (甲 乙 丙 丁 戊 己 庚 辛 壬 癸 / 子丑寅卯辰巳午未申酉戌亥)
2. 오행 색상으로 즉각적 시각 피드백
3. 신비로운 분위기 (다크 테마 필수)
4. 공유하기 쉬운 카드 형태

## 레퍼런스 앱
- Co-Star: 다크 테마, 별자리, 미니멀
- The Pattern: 감성적 카피, 깊이
- 천기누설: 한국적 UI, 한자 활용 (단 UI는 구식)
