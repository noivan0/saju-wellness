"""
i18n 유틸리티 — 한국어/일본어/영어 다국어 지원
사용법:
    from app.i18n.i18n_utils import get_i18n, t
    labels = get_i18n("ko")
    msg = t("disclaimer", lang="ja")
"""
from __future__ import annotations
import json
import os
from functools import lru_cache
from typing import Optional

_I18N_DIR = os.path.dirname(os.path.abspath(__file__))
SUPPORTED_LANGS = ("ko", "ja", "en")
DEFAULT_LANG = "ko"


@lru_cache(maxsize=8)
def _load_i18n(lang: str) -> dict:
    """JSON 파일 캐시 로드"""
    path = os.path.join(_I18N_DIR, f"{lang}.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        if lang != DEFAULT_LANG:
            return _load_i18n(DEFAULT_LANG)
        return {}


def get_i18n(lang: str = DEFAULT_LANG) -> dict:
    """
    지정 언어의 레이블 딕셔너리 반환
    미지원 언어는 DEFAULT_LANG(ko) 폴백
    """
    normalized = lang.lower().strip()
    if normalized not in SUPPORTED_LANGS:
        normalized = DEFAULT_LANG
    data = _load_i18n(normalized)
    return data.get("labels", {})


def t(key: str, lang: str = DEFAULT_LANG, default: Optional[str] = None) -> str:
    """
    단일 번역 키 조회
    중첩 키: "element.목", "zodiac.rat" 형식 지원
    """
    labels = get_i18n(lang)
    parts = key.split(".")
    current = labels
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = None
        if current is None:
            break
    if current is None:
        # 폴백: ko 언어에서 재시도
        if lang != DEFAULT_LANG:
            return t(key, DEFAULT_LANG, default)
        return default if default is not None else key
    return str(current)


def resolve_lang(
    query_lang: Optional[str] = None,
    accept_language: Optional[str] = None,
) -> str:
    """
    언어 코드 해석 우선순위:
    1. ?lang= 쿼리 파라미터
    2. Accept-Language 헤더
    3. 기본값 ko

    Accept-Language 예: "ja,ko;q=0.9,en;q=0.8"
    """
    # 1. 쿼리 파라미터 우선
    if query_lang:
        candidate = query_lang.lower().strip()[:2]
        if candidate in SUPPORTED_LANGS:
            return candidate

    # 2. Accept-Language 헤더 파싱
    if accept_language:
        for segment in accept_language.split(","):
            code = segment.strip().split(";")[0].strip()[:2].lower()
            if code in SUPPORTED_LANGS:
                return code

    return DEFAULT_LANG
