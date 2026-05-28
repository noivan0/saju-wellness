# 사주담 (Saju Wellness) — Multi-stage Dockerfile
# Base: python:3.11-slim
# 법적: 문화·오락 서비스 (심리상담 아님)

# ─────────────────────────────────────────────
# Stage 1: builder (의존성 설치)
# ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# 시스템 의존성 (psycopg2 빌드용)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 의존성 먼저 복사 (레이어 캐시 최적화)
COPY requirements.txt .

# 가상환경에 설치
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────
# Stage 2: runtime
# ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# 메타데이터
LABEL maintainer="saju-wellness"
LABEL description="사주담 API — 명리학 기반 자기이해 서비스 (문화·오락)"
LABEL legal="entertainment-lifestyle-service"

WORKDIR /app

# 런타임 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 가상환경 복사
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 소스 복사
COPY src/ ./src/
COPY saju_engine.py ./
COPY prompts/ ./prompts/

# 비-루트 사용자 (보안)
RUN groupadd -r saju && useradd -r -g saju saju
RUN chown -R saju:saju /app
USER saju

# 환경변수 기본값
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEFAULT_LANG=ko
ENV SERVICE_TYPE=entertainment-lifestyle
ENV DISCLAIMER_ENABLED=true
ENV CRISIS_LINE_KR=1393

# 포트
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 시작 커맨드
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
