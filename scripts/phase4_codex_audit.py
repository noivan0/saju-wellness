#!/usr/bin/env python3
"""사주담 Phase4 — Codex 감사 (코드 품질, 보안, 구조)"""
import sys, os
from pathlib import Path

BASE = Path("/root/.hermes/projects/saju-wellness")
ERRORS = []
WARNINGS = []

def check_file(fpath, label, checks):
    """파일 존재 + 내용 패턴 검사"""
    p = BASE / fpath
    if not p.exists():
        ERRORS.append(f"[FAIL] {label}: 파일 없음 ({fpath})")
        return
    content = p.read_text(encoding='utf-8', errors='replace')
    for pat, msg, is_error in checks:
        found = pat in content
        if is_error and not found:
            ERRORS.append(f"[FAIL] {label}: {msg}")
        elif not is_error and found:
            ERRORS.append(f"[FAIL] {label}: {msg} (보안 위반)")
        elif not is_error and not found:
            pass  # OK — 위험 패턴 없음
        else:
            pass  # OK

# 1. FastAPI 구조 검사
check_file("src/api/main.py", "main.py", [
    ("StaticFiles", "StaticFiles 마운트 없음", True),
    ("app = FastAPI", "FastAPI 앱 정의 없음", True),
    ("exec(", "exec() 보안 위반", False),
    ("eval(", "eval() 보안 위반", False),
])

# 2. 사주 계산 엔진
check_file("src/engine/saju_calculator.py", "사주 계산 엔진", [
    ("def calculate", "calculate 함수 없음", True),
])

# 3. 데이터 파일
for fname in ["pillar_interpretations.json", "element_interpretations.json"]:
    p = BASE / "src/data" / fname
    if not p.exists():
        ERRORS.append(f"[FAIL] 데이터 파일 없음: {fname}")
    else:
        try:
            import json
            data = json.loads(p.read_text())
            if not data:
                WARNINGS.append(f"[WARN] {fname}: 빈 JSON")
            else:
                print(f"[OK] {fname}: {len(data)}개 항목")
        except Exception as e:
            ERRORS.append(f"[FAIL] {fname}: JSON 파싱 오류 — {e}")

# 4. UI 파일
ui = BASE / "static/index.html"
if not ui.exists():
    ERRORS.append("[FAIL] static/index.html 없음")
else:
    size = ui.stat().st_size
    if size < 5000:
        ERRORS.append(f"[FAIL] index.html 너무 작음: {size}bytes")
    else:
        print(f"[OK] index.html: {size:,}bytes")

# 5. interpretation 로드 경로 검증
routes_p = BASE / "src/api/routes/saju.py"
if routes_p.exists():
    content = routes_p.read_text()
    if "pillar_interpretations.json" not in content and "_load_pillar" not in content:
        WARNINGS.append("[WARN] saju.py: pillar_interpretations.json 로드 코드 없음")
    else:
        print("[OK] saju.py: 해석 데이터 로드 코드 있음")

# 보고
print(f"\n=== Phase4 감사 결과 ===")
print(f"ERRORS: {len(ERRORS)}, WARNINGS: {len(WARNINGS)}")
for w in WARNINGS:
    print(w)
for e in ERRORS:
    print(e)

sys.exit(1 if ERRORS else 0)
