# 사주 웰니스 — 기술설계서 (TECH_STACK.md)

버전: 1.0.0  
작성일: 2026-05-22  
대상: 개발팀 (풀스택)

---

## 1. 기술 스택 개요

```
[클라이언트]           [백엔드]                [인프라]
Flutter (iOS/Android)  FastAPI (Python 3.11)   AWS ECS Fargate
                           |                   PostgreSQL (RDS)
                       Claude API              Redis (ElastiCache)
                       saju_engine.py          S3 (공유 카드 이미지)
                                               CloudFront (CDN)
```

선택 근거 요약:
- Flutter: 한국·일본·영어 3개 언어 앱을 단일 코드베이스로 동시 배포
- FastAPI: 비동기 처리, Claude API 스트리밍 응답 지원, Python 생태계 (lunar-python)
- PostgreSQL: 사주 데이터 JSONB 저장, 시계열 감정 데이터 쿼리
- Redis: 사주 계산 결과 캐싱 (동일 생년월일 반복 계산 방지), 일간 운세 캐싱
- Claude API: 한·일·영 자연스러운 표현 품질, 다국어 프롬프트 일관성

---

## 2. 백엔드

### 2.1 FastAPI 구조

```
backend/
├── main.py                    # FastAPI 앱 진입점, 미들웨어 설정
├── api/
│   ├── v1/
│   │   ├── saju.py           # 사주 계산 엔드포인트
│   │   ├── daily.py          # 일간 운세
│   │   ├── emotional.py      # 정서 지원 채팅
│   │   ├── compatibility.py  # 궁합 분석
│   │   ├── community.py      # 커뮤니티
│   │   └── auth.py           # 인증 (JWT)
├── core/
│   ├── saju_engine.py        # 사주팔자 계산 엔진
│   ├── ai_interpreter.py     # Claude API 래퍼 + 프롬프트
│   ├── cache.py              # Redis 캐시 레이어
│   └── safety_filter.py     # 위기 키워드 감지
├── models/
│   ├── user.py               # SQLAlchemy 모델
│   ├── saju.py
│   └── community.py
├── schemas/
│   ├── saju.py               # Pydantic 요청/응답 스키마
│   └── emotional.py
├── tests/
│   ├── test_saju_engine.py   # 사주 계산 단위 테스트
│   └── test_safety_filter.py # 위기 감지 테스트
└── requirements.txt
```

### 2.2 핵심 의존성

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy==2.0.29
asyncpg==0.29.0          # PostgreSQL 비동기 드라이버
redis[asyncio]==5.0.3
anthropic==0.25.1        # Claude API
lunar-python==1.3.12     # 사주 계산 (절기 기준)
pytz==2024.1             # 시간대 처리
pydantic==2.7.1
python-jose==3.3.0       # JWT
passlib==1.7.4           # 패스워드 해싱
pillow==10.3.0           # 공유 카드 이미지 생성
```

### 2.3 API 엔드포인트 설계

**인증**
```
POST /api/v1/auth/register    # 회원가입 (이메일 + 생년월일시)
POST /api/v1/auth/login       # 로그인 → JWT 반환
POST /api/v1/auth/refresh     # 토큰 갱신
DELETE /api/v1/auth/me        # 계정 탈퇴 + 데이터 삭제
```

**사주 분석**
```
GET  /api/v1/saju/me          # 내 사주팔자 조회 (캐시 우선)
POST /api/v1/saju/calculate   # 생년월일시로 사주 계산 (비회원용)
GET  /api/v1/saju/daun        # 대운 10년 흐름
GET  /api/v1/saju/seun/{year} # 세운 분석
GET  /api/v1/saju/card        # 공유 카드 이미지 생성 (S3 업로드 후 URL 반환)
```

**일간 운세**
```
GET  /api/v1/daily/today          # 오늘 일간 운세 (캐시 TTL 자정)
GET  /api/v1/daily/history?days=30 # 과거 운세 히스토리 (프리미엄)
```

**정서 지원**
```
POST /api/v1/emotional/checkin    # 감정 체크인 저장
POST /api/v1/emotional/chat       # AI 정서 지원 메시지 생성
GET  /api/v1/emotional/history    # 감정 이력 + 캘린더 (프리미엄)
GET  /api/v1/emotional/trend      # 감정 트렌드 통계
```

**궁합**
```
POST /api/v1/compatibility        # 두 생년월일 → 궁합 분석
GET  /api/v1/compatibility/card   # 궁합 공유 카드 이미지
```

**커뮤니티**
```
GET  /api/v1/community/feed       # 오행 그룹 피드
POST /api/v1/community/posts      # 게시글 작성
POST /api/v1/community/reports    # 신고
```

### 2.4 Claude API 연동

스트리밍 응답 사용 (사용자가 답변 생성을 실시간으로 보도록):

```python
async def generate_interpretation(
    eight_char: EightChar,
    context: dict,
    lang: str = "ko"
) -> AsyncIterator[str]:
    
    system_prompt = SYSTEM_PROMPTS[lang]
    user_prompt   = _build_user_prompt(eight_char, context, lang)
    
    # 면책 문구 자동 주입
    disclaimer = DISCLAIMERS[lang]
    
    async with anthropic_client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=600,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    ) as stream:
        async for text in stream.text_stream:
            yield text
    
    yield f"\n\n{disclaimer}"
```

토큰 최적화:
- 사주 기본 정보는 캐싱된 구조체 재사용
- 해석 결과도 동일 입력(사주 + 날짜 + 감정레벨)이면 Redis 캐싱
- 프리미엄 심층 분석은 max_tokens=1200, 일반은 600

위기 키워드 감지는 Claude 호출 전에 선처리:

```python
CRISIS_KEYWORDS = ["죽고싶", "자해", "극단", "죽을것같", "사라지고싶",
                   "die", "kill myself", "suicide", "자살"]

def check_crisis(text: str) -> bool:
    return any(kw in text.lower() for kw in CRISIS_KEYWORDS)

CRISIS_RESPONSE = {
    "ko": "힘드셨군요. 지금 많이 힘드시다면 자살예방상담전화 1393에 연락해보세요. 24시간 연결됩니다.",
    "ja": "つらかったですね。今とても苦しいなら、よりそいホットライン 0120-279-338 に電話してみてください。24時間つながります。",
    "en": "I hear you. If you're in crisis, please reach out to the 988 Suicide & Crisis Lifeline by calling or texting 988. Available 24/7."
}
```

### 2.5 공유 카드 이미지 생성

사주 에너지 카드와 궁합 카드를 서버에서 이미지로 생성해 S3에 업로드.

```python
from PIL import Image, ImageDraw, ImageFont
import boto3

def generate_saju_card(eight_char: EightChar, user_name: str, lang: str) -> str:
    # 1200x630 px (OG 이미지 표준)
    img = Image.new("RGB", (1200, 630), color="#1a1a2e")
    draw = ImageDraw.Draw(img)
    
    # 오행 색상 배경 그라데이션
    element = STEM_ELEMENT[eight_char.day.stem_idx]
    ELEMENT_COLORS = {
        "목": "#4CAF50", "화": "#F44336",
        "토": "#FF9800", "금": "#9E9E9E", "수": "#2196F3"
    }
    
    # 8글자 사주 배치
    # ... 폰트·레이아웃 렌더링
    
    # S3 업로드
    s3 = boto3.client("s3")
    key = f"cards/{eight_char.eight_glyphs}_{lang}.png"
    s3.upload_fileobj(img_bytes, "saju-wellness-cards", key)
    
    return f"https://cdn.saju-wellness.com/{key}"
```

---

## 3. 사주 계산 엔진

### 3.1 외부 라이브러리 의존성

`lunar-python` (PyPI): 음력 변환 + 절기 기준 사주팔자 계산. 핵심 의존성.

```bash
pip install lunar-python
```

`lunar-python`이 설치 안 된 경우 fallback 알고리즘이 작동하지만, 절기 경계일(매월 4~8일)에 오차가 생길 수 있다. 프로덕션에서는 반드시 `lunar-python` 설치.

### 3.2 시간대 처리

출생지 시간대를 기준으로 계산:

```python
def normalize_birth_datetime(year, month, day, hour, minute, tz_str: str):
    import pytz
    tz = pytz.timezone(tz_str)
    local_dt = tz.localize(datetime.datetime(year, month, day, hour, minute))
    # 사주는 현지 시간 기준 (KST 아니어도 현지 시각 그대로 사용)
    return local_dt.year, local_dt.month, local_dt.day, local_dt.hour, local_dt.minute
```

일본 사용자: JST (UTC+9) = KST와 동일 → 차이 없음  
미국 서부 사용자: PST (UTC-8) → 현지 시각 기준으로 계산

### 3.3 시각 모름 처리

사용자가 출생 시각을 모르는 경우, 시주 없이 연·월·일 3기둥만 계산:

```python
def calculate_without_hour(year, month, day) -> dict:
    ec = calculate_four_pillars(year, month, day, 12, 0)  # 정오로 임시 계산
    result = ec.to_dict()
    result["hour_pillar"] = None
    result["note"] = "출생 시각을 입력하면 더 정확한 분석이 가능합니다."
    return result
```

---

## 4. 프론트엔드 (Flutter)

### 4.1 선택 이유

React Native 대신 Flutter를 선택한 이유:
- 한자 렌더링 (갑을병정...) 크로스플랫폼 안정성이 Flutter 우위
- 오행 시각화 (차트, 그라데이션, 애니메이션) 커스텀 렌더링 유연성
- 단일 코드베이스로 iOS + Android 동시 빌드
- 다국어 폰트 처리 (한국어 Noto Sans KR, 일본어 Noto Sans JP) 간편

### 4.2 주요 패키지

```yaml
# pubspec.yaml
dependencies:
  flutter_localizations: sdk: flutter   # 다국어
  intl: ^0.19.0                          # 날짜/숫자 포맷
  fl_chart: ^0.68.0                      # 오행 레이더 차트
  flutter_riverpod: ^2.5.1              # 상태관리
  dio: ^5.4.3                           # HTTP 클라이언트 (스트리밍 지원)
  shared_preferences: ^2.2.3           # 로컬 설정 저장
  flutter_secure_storage: ^9.0.0       # JWT 토큰 안전 저장
  in_app_purchase: ^3.2.0              # 인앱 결제 (iOS/Android)
  share_plus: ^9.0.0                   # 카드 이미지 공유
  lottie: ^3.1.0                       # 온보딩 애니메이션
  cached_network_image: ^3.3.1        # 카드 이미지 캐싱
  firebase_messaging: ^14.9.2         # 푸시 알림
```

### 4.3 다국어 구조

```
lib/
└── l10n/
    ├── app_ko.arb    # 한국어 (기본)
    ├── app_ja.arb    # 일본어
    └── app_en.arb    # 영어
```

앱 실행 시 기기 언어 자동 감지. 사용자가 설정에서 변경 가능.

```dart
// main.dart
MaterialApp(
  localizationsDelegates: [
    AppLocalizations.delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ],
  supportedLocales: [
    Locale('ko'),  // 한국어
    Locale('ja'),  // 일본어
    Locale('en'),  // 영어
  ],
)
```

### 4.4 인앱 결제

iOS App Store + Google Play 인앱 구독:

```dart
// 구독 상품 ID (앱스토어에 등록)
const String kSubBasicId   = 'com.sajuwellness.sub.basic.monthly';   // 3,900원
const String kSubPremiumId = 'com.sajuwellness.sub.premium.monthly'; // 9,900원

// 결제 검증: 클라이언트 → 백엔드 영수증 검증 필수
// iOS: App Store Server API
// Android: Google Play Developer API
// 클라이언트 단독 검증 금지 (보안 취약)
```

### 4.5 푸시 알림

Firebase Cloud Messaging (FCM) 사용:

```dart
// 알림 스케줄: 매일 아침 8시 (사용자 시간대)
// 서버에서 FCM 토큰 저장 → 배치 발송
// 내용: 개인화된 오늘의 에너지 한 줄 (사주 오행별 다른 문구)
```

알림 개인화 예시:
- 갑목(甲木) 일주: "오늘 목기운이 맑아요. 새로운 시작에 좋은 하루입니다 🌱"
- 신금(辛金) 일주: "오늘은 금기운이 깨끗합니다. 결단이 필요한 일을 처리하기 좋아요 💎"

---

## 5. 데이터베이스

### 5.1 PostgreSQL (AWS RDS)

인스턴스: db.t3.medium (MVP), db.r6g.large (스케일링)  
버전: PostgreSQL 16  
멀티 AZ: 프로덕션에서 활성화

주요 테이블 (ALGORITHM.md 스키마 참조 + 추가):

```sql
-- 구독 정보
CREATE TABLE subscriptions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID REFERENCES users(id) ON DELETE CASCADE,
    plan         VARCHAR(20) NOT NULL CHECK (plan IN ('free', 'basic', 'premium')),
    status       VARCHAR(20) NOT NULL DEFAULT 'active',
    expires_at   TIMESTAMP,
    receipt_data TEXT,           -- 앱스토어 영수증 원본
    created_at   TIMESTAMP DEFAULT NOW(),
    UNIQUE (user_id)
);

-- 커뮤니티 게시글
CREATE TABLE community_posts (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID REFERENCES users(id) ON DELETE SET NULL,
    anon_name    VARCHAR(50) NOT NULL,   -- "갑목의 나무" 자동 생성
    element_tag  VARCHAR(10),            -- 목/화/토/금/수
    situation_tag VARCHAR(30),
    content      TEXT NOT NULL CHECK (length(content) <= 500),
    is_deleted   BOOLEAN DEFAULT FALSE,
    created_at   TIMESTAMP DEFAULT NOW()
);
```

개인정보 보호:
- `birth_year`, `birth_month`, `birth_day`, `birth_hour`: 앱 레벨 암호화 (AES-256) 후 저장
- 계정 탈퇴 시: 개인 식별 데이터 즉시 삭제, 익명화된 통계 데이터만 보존

### 5.2 Redis (ElastiCache)

인스턴스: cache.t3.micro (MVP)  
용도: 사주 계산 캐시 + 일간 운세 캐시 + 세션

TTL 설계:
```
사주 기본 분석:   영구 (생년월일 변하지 않음)
세운 분석:        365일
일간 운세:        자정 + 1시간 (KST 기준)
AI 해석:          당일 자정
궁합 분석:        7일
세션 토큰:        7일 (갱신 시 연장)
```

---

## 6. 인프라

### 6.1 AWS 아키텍처

```
[Route 53] → [CloudFront] → [ALB] → [ECS Fargate]
                                          |
                                     [FastAPI 컨테이너]
                                          |
                              [RDS PostgreSQL] [ElastiCache Redis]
                                          |
                                       [S3] (공유 카드 이미지)
```

리전: ap-northeast-2 (서울) — MVP  
추가 리전 (Phase C): ap-northeast-1 (도쿄)

ECS Fargate 태스크 스펙:
- CPU: 0.5 vCPU (MVP), 1 vCPU (성장기)
- Memory: 1GB
- 최소 태스크: 2 (가용성)
- 최대 태스크: 20 (Auto Scaling)

Auto Scaling 기준:
- CPU 60% 이상 → 스케일 아웃
- 연초 시즌(1월 1~15일): 수동으로 최소 5로 올리기

### 6.2 CI/CD

GitHub Actions:

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: pytest tests/ -v --cov=core

  deploy:
    needs: test
    steps:
      - name: Build Docker image
      - name: Push to ECR
      - name: Deploy to ECS (Blue/Green)
```

배포 전략: Blue/Green (ECS CodeDeploy 연동). 무중단 배포.

### 6.3 모니터링

- APM + 로그: Datadog (백엔드 + 프론트엔드 크래시 리포트)
- 에러 추적: Sentry (Python + Flutter)
- 비즈니스 지표: 내부 대시보드 (Metabase + PostgreSQL 직접 쿼리)
- 알림: Slack → 에러율 1% 이상, API 지연 2초 이상, Claude API 실패

---

## 7. 보안

### 7.1 인증

JWT (Access Token: 1h, Refresh Token: 30d)  
토큰 저장: Flutter `flutter_secure_storage` (iOS Keychain, Android Keystore)  
백엔드 검증: `python-jose` + `passlib`

소셜 로그인 (Phase B):
- 카카오 로그인 (한국 사용자 주)
- Apple Login (App Store 정책상 iOS 필수)
- Google OAuth (Android)

### 7.2 데이터 보호

생년월일시 암호화:
- 알고리즘: AES-256-GCM
- 키 관리: AWS KMS
- 저장: 암호화된 값만 DB에 저장, 조회 시 복호화

API 보안:
- 모든 엔드포인트 HTTPS (TLS 1.3)
- Rate limiting: IP당 100 req/min, 인증 사용자 300 req/min
- 입력 검증: Pydantic 스키마 강제 (SQL injection, XSS 방어)

### 7.3 개인정보 처리방침

GDPR (EU) / 개인정보보호법 (한국) / 개인情報保護法 (일본) 준수:
- 수집 항목: 이메일, 생년월일시 (최소 수집 원칙)
- 보관 기간: 계정 활성 기간 + 탈퇴 후 30일 (법적 의무 보관 제외)
- 수출: 한국 사용자 데이터는 ap-northeast-2(서울) 리전에서만 처리
- 삭제 요청: 30일 이내 처리 보장

---

## 8. 성능 목표

| 지표 | 목표 | 측정 방법 |
|------|------|----------|
| API 응답 (사주 계산) | < 200ms (캐시 히트) / < 800ms (계산) | Datadog APM |
| AI 스트리밍 첫 토큰 | < 1.5초 | 클라이언트 측정 |
| 앱 시작 시간 | < 2초 (iOS), < 3초 (Android) | Firebase Performance |
| 일간 운세 캐시 히트율 | > 95% | Redis 모니터링 |
| 가용성 | 99.5% (MVP) / 99.9% (성장기) | AWS CloudWatch |

---

## 9. 개발 환경 설정

### 9.1 로컬 개발

```bash
# 백엔드
cd backend/
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # Claude API 키, DB URL 등 설정

# DB + Redis 로컬 실행
docker-compose up -d postgres redis

# 서버 실행
uvicorn main:app --reload --port 8000
```

```bash
# 프론트엔드
cd frontend/
flutter pub get
flutter run -d ios     # iOS 시뮬레이터
flutter run -d android # Android 에뮬레이터
```

### 9.2 환경변수

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/saju_wellness
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
S3_BUCKET_CARDS=saju-wellness-cards
JWT_SECRET_KEY=...       # 256비트 이상 랜덤 키
ENCRYPTION_KEY=...       # AES-256 생년월일 암호화 키 (AWS KMS 관리)
```

---

## 10. MVP 출시 체크리스트

법적:
- [ ] 점술업 신고 여부 법무 검토 완료
- [ ] 심리사법 저촉 검토 완료 (AI 발화 패턴 포함)
- [ ] 개인정보처리방침 법률 검토
- [ ] 이용약관 법률 검토

기술:
- [ ] saju_engine.py 절기 경계일 테스트 통과
- [ ] 위기 키워드 감지 테스트 (자해/자살 키워드 100% 차단 확인)
- [ ] 인앱 결제 샌드박스 테스트 (iOS + Android)
- [ ] 푸시 알림 테스트 (iOS APNs + Android FCM)
- [ ] HTTPS 강제, 인증 토큰 검증 통과
- [ ] 생년월일 암호화 검증

앱스토어:
- [ ] iOS 앱스토어: 라이프스타일 카테고리, 스크린샷 준비
- [ ] 스크린샷·설명문 "치료/상담/진단" 미포함 확인
- [ ] 개인정보처리방침 URL 앱스토어 등록

---

작성: nova-strategy  
구현 참고: saju_engine.py, ai_interpreter.py (이미 프로토타입 구현됨)
