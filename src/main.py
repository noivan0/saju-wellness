"""
사주담 FastAPI 메인 앱
법적 포지션: 문화·오락 서비스 (심리상담/의료 아님)
"""
from __future__ import annotations
import sys
import os

# 프로젝트 루트를 sys.path에 추가 (saju_engine.py 임포트 지원)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.api.rate_limiter import limiter

from src.api.routes.saju import router as saju_router  # 확장판 (pillar-details/fortune-calendar/compatibility 포함)
from src.routes.saju import router as saju_base_router  # GET /api/saju + POST /api/saju/analyze
from src.routes.fortune import router as fortune_router
from src.api.routes.ivr import router as ivr_router  # Twilio IVR 음성 전화

app = FastAPI(
    title="사주담 API",
    description=(
        "명리학 기반 자기이해 서비스 — 심리상담/의료 아님.\n\n"
        "## 법적 고지\n"
        "- 본 서비스는 명리학·동양철학 기반 문화·오락 서비스입니다.\n"
        "- 심리상담, 의료 진단, 과학적 예측을 제공하지 않습니다.\n"
        "- 위기 상황(자해·자살 관련)은 자살예방상담전화 **1393** (24시간)으로 안내됩니다."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── [P1-SECURITY] HTTP 보안 헤더 미들웨어 ────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    OWASP 권장 HTTP 보안 헤더 — [R13/R14-SECURITY]
    X-Frame-Options: 클릭재킹 방지
    X-Content-Type-Options: MIME 스니핑 방지
    Referrer-Policy: 레퍼러 정보 최소화
    CSP connect-src: Anthropic API만 허용
    Cache-Control: API 응답 캐시 금지
    HSTS: SSL 배포 후 자동 활성화
    """
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # [R14] CSP — 폰트/연결 허용
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "connect-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "frame-ancestors 'none'"
        )
        # [R14] API 응답 캐시 금지 (개인 사주 정보 캐시 방지)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        # [R14] HSTS — HTTPS 환경에서만 활성화
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response

app.add_middleware(SecurityHeadersMiddleware)

# slowapi rate limiter 연결 (확장판 라우터에서 사용)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — Flutter 앱 + 웹 프리뷰 허용
# 프로덕션: ALLOWED_ORIGINS 환경변수로 도메인 명시 (쉼표 구분)
# 미설정 시 와일드카드 금지 — 배포 환경에서 반드시 도메인 명시 필요
import os as _os
_origins_env = _os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080")
# [R50-CORS-001 FIX] 와일드카드 차단 — "*" 입력 시 기본값 사용 (CVSS 7.4 방어)
_allowed_origins = [o.strip() for o in _origins_env.split(",") if o.strip()] if _origins_env != "*" else ["http://localhost:3000", "http://localhost:8080"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# 라우터 등록
app.include_router(saju_base_router, prefix="/api/saju")   # GET /api/saju, POST /api/saju/analyze
app.include_router(saju_router,      prefix="/api/saju")   # 확장판 (calculate/compatibility/fortune-calendar)
app.include_router(fortune_router,   prefix="/api/fortune")
app.include_router(ivr_router)   # IVR: /api/ivr/incoming, /gather, /menu, /outbound, /status


@app.get("/health", tags=["시스템"])
def health():
    return {
        "status": "ok",
        "service": "사주담",
        "version": "1.0.0",
        "legal": "entertainment-lifestyle-service",
        "crisis_line": "1393 (자살예방상담전화, 24시간)",
    }


@app.get("/", tags=["시스템"])
def root():
    return {
        "message": "사주담 API 서버입니다.",
        "docs": "/docs",
        "endpoints": {
            "사주 계산": "GET /api/saju",
            "사주 AI 해석": "POST /api/saju/analyze",
            "일간 운세": "GET /api/fortune/daily",
        },
    }
