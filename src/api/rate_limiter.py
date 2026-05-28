"""
slowapi Limiter 공유 모듈
main.py와 routes 파일 양쪽에서 동일 인스턴스를 사용해야
rate limit 데코레이터가 올바르게 동작한다.

테스트 환경: RATELIMIT_ENABLED=False 로 비활성화.
"""
import os
from slowapi import Limiter
from slowapi.util import get_remote_address

_enabled = os.getenv("RATELIMIT_ENABLED", "True").lower() not in ("false", "0", "no")

limiter = Limiter(key_func=get_remote_address, enabled=_enabled)
