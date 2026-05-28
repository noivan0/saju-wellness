#!/usr/bin/env python3
"""사주담 Phase3 — UI QA (HTML 구조, CSS 토큰, 접근성)"""
import sys, requests, re

BASE = "http://localhost:8002"
ERRORS = []

r = requests.get(f"{BASE}/app", timeout=10)
if r.status_code != 200:
    print(f"[FAIL] UI 로드 실패: {r.status_code}")
    sys.exit(1)

html = r.text

def check(label, condition, detail=""):
    if not condition:
        ERRORS.append(f"[FAIL] {label}{': '+detail if detail else ''}")
        print(f"[FAIL] {label}")
    else:
        print(f"[OK] {label}")

# 기본 구조
check("DOCTYPE 선언", "<!DOCTYPE html>" in html.lower() or "<!doctype html>" in html.lower())
check("meta viewport", 'viewport' in html)
check("meta charset", 'charset' in html.lower())
check("title 태그", '<title>' in html.lower())

# 핵심 기능 요소
check("생년월일 입력 폼", 'type="number"' in html or 'input' in html.lower())
check("계산 버튼", 'button' in html.lower())
check("API 통신 fetch", 'fetch(' in html)
check("결과 표시 영역", 'result' in html.lower() or 'display' in html.lower())

# WCAG AA — 색상 토큰
check("보라 기조색 사용", '#7C3AED' in html or '#8B5CF6' in html or '#6D28D9' in html or 'indigo' in html.lower() or '--color-primary' in html)

# 오행 색상 (사주담 핵심)
check("오행 색상 정의", any(c in html for c in ['--wood', '--fire', '--earth', '--metal', '--water', 'five_elem', '오행']))

# JS 에러 방어
check("이벤트 리스너 방식", 'addEventListener' in html)
check("onclick 인라인 없음", 'onclick=' not in html)

# 반응형
check("미디어 쿼리 있음", '@media' in html)

# 한국어 UI
check("한국어 콘텐츠", any(k in html for k in ['출생', '사주', '오행', '일주', '에너지']))

if ERRORS:
    print(f"\n[FAIL] UI QA: {len(ERRORS)}개 문제")
    for e in ERRORS:
        print(e)
    sys.exit(1)
else:
    print(f"\n[PASS] Phase3 사주담 UI QA 완료")
    sys.exit(0)
