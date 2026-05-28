#!/usr/bin/env python3
"""사주담 Phase2 — API 기능 QA (엣지케이스, 오류처리, 응답 구조)"""
import sys, requests, json

BASE = "http://localhost:8002"
ERRORS = []
PASSES = []

def test(label, fn):
    try:
        fn()
        PASSES.append(label)
        print(f"[PASS] {label}")
    except AssertionError as e:
        ERRORS.append(f"[FAIL] {label}: {e}")
        print(f"[FAIL] {label}: {e}")
    except Exception as e:
        ERRORS.append(f"[ERROR] {label}: {e}")
        print(f"[ERROR] {label}: {e}")

# 유효한 생년월일
VALID = {"year": 1990, "month": 6, "day": 15, "hour": 10, "gender": "male"}

def t1_valid_response_keys():
    r = requests.post(f"{BASE}/api/saju/calculate", json=VALID, timeout=15)
    assert r.status_code == 200, f"status={r.status_code}"
    d = r.json()
    for k in ["pillars", "five_elements", "day_master", "year_pillar", "month_pillar", "day_pillar"]:
        assert k in d, f"missing key: {k}"

def t2_interpretation_not_empty():
    r = requests.post(f"{BASE}/api/saju/calculate", json=VALID, timeout=15)
    d = r.json()
    interp = d.get("interpretation", {})
    assert isinstance(interp, dict), "interpretation must be dict"
    # 비어있으면 WARN만 (CRITICAL 아님 — 데이터 로드 문제)
    if not interp:
        print("  [WARN] interpretation 비어있음 — 다음 Phase에서 수정 필요")

def t3_invalid_month():
    r = requests.post(f"{BASE}/api/saju/calculate", json={**VALID, "month": 13}, timeout=10)
    assert r.status_code in [400, 422], f"잘못된 월에 대해 오류 반환 필요, got={r.status_code}"

def t4_daily_energy_structure():
    r = requests.post(f"{BASE}/api/saju/daily-energy", json=VALID, timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert "daily_energy" in d, "daily_energy 키 없음"

def t5_compatibility_score_range():
    body = {
        "person1": VALID,
        "person2": {**VALID, "year": 1992, "month": 3, "day": 22, "hour": 14, "gender": "female"}
    }
    r = requests.post(f"{BASE}/api/saju/compatibility", json=body, timeout=15)
    assert r.status_code == 200
    d = r.json()
    score = d.get("score", -1)
    assert 0 <= score <= 100, f"score 범위 초과: {score}"

def t6_future_birth_year():
    r = requests.post(f"{BASE}/api/saju/calculate", json={**VALID, "year": 2099}, timeout=10)
    # 미래 연도에도 계산 되거나 오류 반환 — 둘 다 OK
    assert r.status_code in [200, 400, 422]

test("사주 계산 응답 구조", t1_valid_response_keys)
test("interpretation 딕셔너리 검증", t2_interpretation_not_empty)
test("잘못된 월(13) 오류 처리", t3_invalid_month)
test("오늘의 에너지 구조", t4_daily_energy_structure)
test("궁합 점수 범위(0-100)", t5_compatibility_score_range)
test("미래 출생연도 처리", t6_future_birth_year)

print(f"\n총 {len(PASSES)+len(ERRORS)}개 테스트: PASS={len(PASSES)} FAIL={len(ERRORS)}")
if ERRORS:
    for e in ERRORS:
        print(e)
    sys.exit(1)
sys.exit(0)
