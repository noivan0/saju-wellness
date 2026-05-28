#!/usr/bin/env python3
"""사주담 Phase1 — 서버 헬스체크 + API 응답 검증"""
import sys, requests, time

BASE = "http://localhost:8002"
ERRORS = []

def check(label, url, method="GET", body=None, expected_keys=None):
    try:
        if method == "POST":
            r = requests.post(url, json=body, timeout=10)
        else:
            r = requests.get(url, timeout=10)
        if r.status_code >= 400:
            ERRORS.append(f"[FAIL] {label}: HTTP {r.status_code}")
            return None
        data = r.json()
        if expected_keys:
            for k in expected_keys:
                if k not in data:
                    ERRORS.append(f"[FAIL] {label}: missing key '{k}' in response")
        print(f"[OK] {label}: {r.status_code}")
        return data
    except Exception as e:
        ERRORS.append(f"[ERROR] {label}: {e}")
        return None

# 1. 서버 가동 확인
check("루트 엔드포인트", f"{BASE}/")

# 2. 사주 계산 API
birth = {"year": 1990, "month": 6, "day": 15, "hour": 10, "gender": "male"}
result = check("사주 계산", f"{BASE}/api/saju/calculate", "POST", birth,
               ["pillars", "five_elements", "day_master"])
if result:
    # interpretation 비어있는지 확인
    interp = result.get("interpretation", {})
    if not interp:
        ERRORS.append("[WARN] interpretation 빈 dict 반환 — pillar_interpretations.json 로드 실패 가능")
    else:
        print(f"  interpretation keys: {list(interp.keys())[:3]}")

# 3. 오늘의 에너지
check("오늘의 에너지", f"{BASE}/api/saju/daily-energy", "POST", birth, ["daily_energy"])

# 4. 궁합
compat = {
    "person1": {"year": 1990, "month": 6, "day": 15, "hour": 10, "gender": "male"},
    "person2": {"year": 1992, "month": 3, "day": 22, "hour": 14, "gender": "female"}
}
check("궁합 계산", f"{BASE}/api/saju/compatibility", "POST", compat, ["score"])

# 5. 정적 UI
r = requests.get(f"{BASE}/app", timeout=10)
if r.status_code != 200 or "<!DOCTYPE" not in r.text:
    ERRORS.append(f"[FAIL] UI 서빙: status={r.status_code}")
else:
    print("[OK] UI /app: HTML 정상")

if ERRORS:
    print("\n=== 오류 목록 ===")
    for e in ERRORS:
        print(e)
    sys.exit(1)
else:
    print("\n[PASS] Phase1 사주담 헬스체크 완료")
    sys.exit(0)
