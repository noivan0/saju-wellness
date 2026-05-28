#!/usr/bin/env python3
"""MVP 기능 통합 테스트"""
import sys
sys.path.insert(0, '/root/.hermes/projects/saju-wellness')

from src.routes.saju import get_saju_endpoint, analyze_saju
from src.routes.fortune import get_daily_fortune
from src.models.user import SajuAnalyzeRequest

print("=== 1. GET /api/saju (1990-01-15 10:30 남성) ===")
result = get_saju_endpoint(year=1990, month=1, day=15, hour=10, minute=30, gender='male', lang='ko')
print("팔자:", result['eight_char']['eight_glyphs'])
print("일주:", result['eight_char']['day_pillar']['glyph'], result['eight_char']['day_pillar']['reading'])
print("오행점수:", result['element_scores'])
print("성격유형:", result['personality_type']['type'], result['personality_type']['traits'])
print("계산방법:", result['method'])
print()

print("=== 2. POST /api/saju/analyze (기분=2) ===")
req = SajuAnalyzeRequest(year=1990, month=1, day=15, hour=10, minute=30, gender='male', lang='ko', mood_level=2)
r2 = analyze_saju(req)
print("팔자:", r2['saju']['eight_char']['eight_glyphs'])
mc = r2.get('mood_coaching')
if mc:
    print("기분:", mc['mood_label'], mc['mood_emoji'])
    print("사주이유:", mc['saju_reason'])
    print("행동힌트:", mc['action_hints'])
print("AI인사이트:", r2['insight'].get('type', 'n/a'))
print()

print("=== 3. GET /api/fortune/daily ===")
f = get_daily_fortune(year=1990, month=1, day=15, hour=10, lang='ko')
print("오늘일진:", f['daily_pillar']['glyph'])
print("나의일주오행:", f['my_day_element'])
print("에너지관계:", f['element_relation'])
print("에너지흐름:", f['energy_flow'])
print("액션카드:", f['action_cards'])
print()

print("=== 4. 시(時) 미입력 ===")
r3 = get_saju_endpoint(year=1985, month=7, day=23, hour=None, minute=0, gender='female', lang='ko')
print("시간불명:", r3['hour_unknown'])
print("기본팔자:", r3['eight_char']['eight_glyphs'])
print("자시:", r3['hour_variants'][0]['eight_char']['eight_glyphs'])
print()

print("ALL TESTS PASSED")
