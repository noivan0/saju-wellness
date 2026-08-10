"""
정밀 사주 풀이(DEEP READING) 프롬프트 빌더 검증
출처: 노이반 제공 전통 명리학 통합 해석 프롬프트 (2026-08-10)

검증 대상: app/prompts/saju_deep_reading_prompt.py
- 만세력 데이터 없이는 "판독 불가" 문구 강제 여부
- 모드별(QUICK/STANDARD/DEEP) 프롬프트 단계 포함 여부 차등
- 신살 하나만으로 사고/질병 단정하는 문구가 시스템 프롬프트에 없는지 (금지 규칙 검증)
- 3대 고전(자평진전/적천수/궁통보감) 병기 형식 포함 여부
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.prompts.saju_deep_reading_prompt import (
    DeepReadingContext,
    build_deep_reading_prompt,
    MODE_QUICK,
    MODE_STANDARD,
    MODE_DEEP,
    VALID_MODES,
    _PANDOK_BULGA,
)


class TestModeResolution:
    def test_valid_modes_tuple(self):
        assert VALID_MODES == ("QUICK", "STANDARD", "DEEP")

    def test_invalid_mode_falls_back_to_standard(self):
        ctx = DeepReadingContext(mode="INVALID")
        result = build_deep_reading_prompt(ctx)
        assert result["mode"] == MODE_STANDARD

    def test_quick_mode_preserved(self):
        ctx = DeepReadingContext(mode=MODE_QUICK)
        result = build_deep_reading_prompt(ctx)
        assert result["mode"] == MODE_QUICK

    def test_deep_mode_preserved(self):
        ctx = DeepReadingContext(mode=MODE_DEEP)
        result = build_deep_reading_prompt(ctx)
        assert result["mode"] == MODE_DEEP


class TestMissingDataForcesPandokBulga:
    """만세력/대운/세운/신살 데이터가 없으면 '판독 불가'를 강제해야 한다."""

    def test_no_pillars_shows_pandok_bulga(self):
        ctx = DeepReadingContext()  # 년/월/일주 전부 빈 문자열
        result = build_deep_reading_prompt(ctx)
        assert _PANDOK_BULGA in result["user"]
        assert "년주 미제공" in result["user"]
        assert "월주 미제공" in result["user"]
        assert "일주 미제공" in result["user"]

    def test_no_hour_pillar_shows_restriction_note(self):
        ctx = DeepReadingContext(year_pillar="甲子", month_pillar="乙丑",
                                  day_pillar="丙寅", hour_pillar="")
        result = build_deep_reading_prompt(ctx)
        assert "시주 미입력" in result["user"]
        assert "자녀·말년·세부성향·시간대 해석 제한" in result["user"]

    def test_no_daewoon_shows_pandok_bulga(self):
        ctx = DeepReadingContext(daewoon_list=[])
        result = build_deep_reading_prompt(ctx)
        assert "대운 데이터 없음" in result["user"]
        assert "대운 시작 나이·순서 추정 금지" in result["user"]

    def test_daewoon_error_dict_treated_as_missing(self):
        ctx = DeepReadingContext(daewoon_list=[{"error": "lunar-python 미설치"}])
        result = build_deep_reading_prompt(ctx)
        assert "대운 데이터 없음" in result["user"]

    def test_no_sewoon_shows_pandok_bulga(self):
        ctx = DeepReadingContext(sewoon_list=[])
        result = build_deep_reading_prompt(ctx)
        assert "세운표 없음" in result["user"]
        assert "연도별 간지·형충합·신살 임의 생성 금지" in result["user"]

    def test_no_sinsal_shows_pandok_bulga(self):
        ctx = DeepReadingContext(sinsal=None)
        result = build_deep_reading_prompt(ctx)
        assert "신살 데이터 없음" in result["user"]
        assert "정밀 계산한 것처럼 서술 금지" in result["user"]

    def test_no_as_of_date_shows_pandok_bulga(self):
        ctx = DeepReadingContext(as_of_date="")
        result = build_deep_reading_prompt(ctx)
        assert "기준일 미제공" in result["user"]
        assert "현재/향후 N년 특정 금지" in result["user"]


class TestPresentDataInjectedVerbatim:
    """제공된 데이터는 재계산 없이 그대로 프롬프트에 주입되어야 한다."""

    def test_pillars_injected(self):
        ctx = DeepReadingContext(
            year_pillar="庚午", month_pillar="庚辰",
            day_pillar="乙巳", hour_pillar="癸未", hour_confirmed="확정",
        )
        result = build_deep_reading_prompt(ctx)
        assert "庚午" in result["user"]
        assert "庚辰" in result["user"]
        assert "乙巳" in result["user"]
        assert "癸未" in result["user"]
        assert "확정" in result["user"]

    def test_daewoon_list_injected(self):
        ctx = DeepReadingContext(daewoon_list=[
            {"order": 1, "age": 8, "glyph": "辛巳", "start_year": 1998, "end_year": 2007},
        ])
        result = build_deep_reading_prompt(ctx)
        assert "辛巳" in result["user"]
        assert "8세 시작" in result["user"]
        assert "재계산 금지" in result["user"]

    def test_sewoon_list_injected(self):
        ctx = DeepReadingContext(sewoon_list=[
            {"year": 2026, "glyph": "丙午", "reading": "병오"},
        ])
        result = build_deep_reading_prompt(ctx)
        assert "2026" in result["user"]
        assert "丙午" in result["user"]

    def test_sinsal_injected_with_disclaimer(self):
        ctx = DeepReadingContext(sinsal={
            "도화살": {"present": True, "basis": "년지 기준", "note": "매력 경향"},
            "미구현": ["귀문관살"],
            "disclaimer": "신살은 보조 지표입니다.",
        })
        result = build_deep_reading_prompt(ctx)
        assert "도화살" in result["user"]
        assert "성립" in result["user"]
        assert "귀문관살" in result["user"]
        assert "미구현" in result["user"]


class TestSinsalNeverOverridesCoreLogic:
    """신살은 격국·용신·조후보다 우선하지 않는다는 규칙이 시스템 프롬프트에 명시돼야 한다."""

    def test_system_prompt_declares_sinsal_as_secondary(self):
        ctx = DeepReadingContext(mode=MODE_STANDARD)
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "신살은 격국·용신·조후보다 우선하지 않는" in system or \
               "신살/귀문/도화/역마/괴강/백호/십이운성 = 보조 해석만" in system

    def test_system_prompt_forbids_single_sinsal_conclusion(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "신살 하나만으로" in system
        assert "단정" in system

    def test_system_prompt_forbids_absolute_expressions(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        for banned in ["\"반드시\"", "\"무조건\"", "\"100%\"", "\"운명적으로\""]:
            assert banned in system

    def test_system_prompt_forbids_fatal_predictions(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "사망, 중병, 사고, 파산, 범죄, 이혼" in system
        assert "확정 예언 금지" in system or "확정적 예언 금지" in system


class TestThreeClassicsIntegration:
    """3대 고전(자평진전/적천수/궁통보감) 관점 분리 + 충돌 병기 형식 검증."""

    def test_three_classics_named(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "자평진전" in system
        assert "적천수" in system
        assert "궁통보감" in system

    def test_conflict_disclosure_format_present(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "자평진전 관점:" in system
        assert "적천수 관점:" in system
        assert "궁통보감 관점:" in system
        assert "충돌 지점:" in system
        assert "최종 종합 판단:" in system

    def test_yongsin_three_way_split_present(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "격국용신" in system
        assert "억부" in system
        assert "조후용신" in system
        assert "[사용자용 종합 판단]" in system


class TestFixedDisclaimerLines:
    """출력 첫 줄/마지막 줄 고정 문구 검증."""

    def test_opening_disclaimer_present(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "[해석 안내]" in system
        assert "검증된 예측·의학적 진단·법률·투자 조언이 아닙니다" in system

    def test_closing_disclaimer_present(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "사실 정보와 전문 조언을 함께 검토해야 합니다" in system

    def test_source_attribution_present(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "노이반" in system
        assert "2026-08-10" in system


class TestModeStepDifferentiation:
    """QUICK/STANDARD/DEEP 모드별 단계 포함 여부 차등 검증."""

    def test_quick_mode_mentions_abbreviated_steps(self):
        ctx = DeepReadingContext(mode=MODE_QUICK)
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "3·4·5단계 상세 표는 생략" in system

    def test_standard_mode_mentions_5year_sewoon(self):
        ctx = DeepReadingContext(mode=MODE_STANDARD)
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "향후 5년 세운표" in system

    def test_deep_mode_mentions_20year_sewoon(self):
        ctx = DeepReadingContext(mode=MODE_DEEP)
        result = build_deep_reading_prompt(ctx)
        system = result["system"]
        assert "향후 20년" in system
        assert "고전 간 충돌 분석" in system

    def test_response_instruction_reflects_selected_mode(self):
        for mode in VALID_MODES:
            ctx = DeepReadingContext(mode=mode)
            result = build_deep_reading_prompt(ctx)
            assert f"선택된 MODE({mode})" in result["user"]


class TestUserContextOptionalFields:
    def test_missing_context_shows_default(self):
        ctx = DeepReadingContext()
        result = build_deep_reading_prompt(ctx)
        assert "미입력" in result["user"]

    def test_provided_context_injected(self):
        ctx = DeepReadingContext(
            current_status="대학원생", interest_area="이직",
            current_concern="진로 고민", focus_area="직업운",
            avoid_style="단정적 표현 지양",
        )
        result = build_deep_reading_prompt(ctx)
        user = result["user"]
        assert "대학원생" in user
        assert "이직" in user
        assert "진로 고민" in user
        assert "직업운" in user
        assert "단정적 표현 지양" in user

    def test_gender_translation(self):
        ctx_m = DeepReadingContext(gender="male")
        ctx_f = DeepReadingContext(gender="female")
        r_m = build_deep_reading_prompt(ctx_m)
        r_f = build_deep_reading_prompt(ctx_f)
        assert "남성" in r_m["user"]
        assert "여성" in r_f["user"]
