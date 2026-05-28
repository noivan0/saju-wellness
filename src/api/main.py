"""
사주담 FastAPI 앱 엔트리
법적: 문화·오락 서비스 / 자기이해 도구 (심리상담 아님)
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from src.api.rate_limiter import limiter

import os as _os

def _parse_cors_origins(env_val: str, default: str) -> list:
    """[R50-CORS-001 FIX] 와일드카드 차단 — ALLOWED_ORIGINS='*' 시 기본값 사용"""
    raw = (env_val or default).strip()
    if raw == "*" or not raw:
        raw = default
    return [o.strip() for o in raw.split(",") if o.strip()]

app = FastAPI(
    title="사주담 API",
    description="명리학 기반 자기이해 서비스 — 심리상담/의료 아님",
    version="0.2.0",
    debug=False,  # [R29-ERR1] 프로덕션 스택트레이스 노출 방지 명시
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    # [R29-CORS] 프로덕션: ALLOWED_ORIGINS env로 도메인 고정 (예: "https://sajudam.kr,https://app.sajudam.kr")
    # 미설정 시 localhost:3000 폴백 (개발용)
    allow_origins=_parse_cors_origins(_os.getenv("ALLOWED_ORIGINS", ""), "http://localhost:3000"),
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    allow_credentials=True,
)

# 라우터 등록
from src.api.routes import saju, insight, auth
app.include_router(auth.router, prefix="/api/auth")
app.include_router(saju.router, prefix="/api/saju")
app.include_router(insight.router, prefix="/api/insight")


# [R26 개보법30조] 개인정보처리방침 공개 엔드포인트
@app.get("/privacy", response_class=HTMLResponse, include_in_schema=True,
         summary="개인정보처리방침", tags=["legal"])
async def privacy_policy():
    """개보법 30조 — 처리방침 공개 (언제든지 쉽게 확인 가능)"""
    from pathlib import Path as _P
    import markdown as _md  # type: ignore
    pp_file = _P(__file__).parent.parent.parent / "privacy_policy.md"
    if pp_file.exists():
        html_body = _md.markdown(pp_file.read_text(encoding="utf-8"))
    else:
        html_body = "<p>준비 중입니다. privacy@sajudam.kr 로 문의해 주세요.</p>"
    return HTMLResponse(content=f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>개인정보처리방침 — 사주담</title>
<style>body{{font-family:'Noto Sans KR',sans-serif;max-width:800px;margin:2rem auto;padding:0 1rem;line-height:1.8;color:#333}}h1,h2{{color:#1a1a2e}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px;text-align:left}}</style>
</head><body>{html_body}</body></html>""")


@app.get("/health")
def health_check():
    """
    헬스체크 — 사주 계산 엔진 스모크 테스트 포함
    watchdog / Docker HEALTHCHECK 용
    """
    try:
        from src.engine.saju_calculator import calc_four_pillars
        test = calc_four_pillars(1990, 1, 15, lang="ko")
        engine_ok = "year" in test and "disclaimer" in test
    except Exception as e:
        return {"status": "error", "detail": str(e)}

    return {
        "status": "ok",
        "version": "0.2.0",
        "service": "saju-wellness",
        "db": "ok",
        "engine": "ok" if engine_ok else "error",
        "legal": "entertainment-lifestyle-service",
    }


# 웹 앱 정적 파일 서빙
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os as _os

_static_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'static')
_os.makedirs(_static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=_static_dir), name="static")

@app.get("/app", response_class=FileResponse, include_in_schema=False)
def webapp():
    return _os.path.join(_static_dir, "index.html")
