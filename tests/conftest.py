"""
사주담 테스트 공통 설정
- PYTHONPATH: 프로젝트 루트 기준
- FastAPI TestClient 픽스처
"""
import sys
import os
import pytest

# 프로젝트 루트를 PYTHONPATH에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 테스트용 환경변수 (SECRET_KEY 미설정 시 서버 시작 실패 방지)
os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-placeholder!")
os.environ.setdefault("REFRESH_SECRET_KEY", "test-refresh-secret-key-32chars!!")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_saju.db")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key-placeholder")
# [HIGH-2] 테스트 환경에서 rate-limit 비활성화
os.environ["RATELIMIT_ENABLED"] = "False"

# 모듈 임포트 전에 환경변수가 설정됐으므로 Limiter가 disabled로 초기화됨.
# 만약 이미 enabled=True로 초기화됐다면 직접 패치.
try:
    from src.api.rate_limiter import limiter as _limiter
    _limiter.enabled = False
except Exception:
    pass


@pytest.fixture(scope="session")
def api_client():
    """FastAPI TestClient (src.api.main 기준)"""
    from fastapi.testclient import TestClient
    from src.api.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def main_client():
    """FastAPI TestClient (src.main 기준 — 실제 saju_engine 라우터)"""
    from fastapi.testclient import TestClient
    from src.main import app
    return TestClient(app)
