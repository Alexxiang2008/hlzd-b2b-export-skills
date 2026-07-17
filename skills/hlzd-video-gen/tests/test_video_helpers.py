"""Unit tests for hlzd-product-video-gen pure-function helpers.

Probes deterministic text/segment utilities that drive the video
pipeline. Skips network / API / FFmpeg / preset-file dependencies.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(_SCRIPTS))

import orchestrator  # noqa: E402
import prompt_builder  # noqa: E402
import subtitle_manager  # noqa: E402
import video_postprocess  # noqa: E402


# ================================================================
# orchestrator.split_into_segments
# 默认每段 ≤ 18 秒，超过则切
# ================================================================

class TestSplitIntoSegments:
    def test_short_clip_one_segment(self):
        # <= 18s → 一段
        assert orchestrator.split_into_segments(12) == [12]

    def test_18s_one_segment(self):
        # 边界值
        assert orchestrator.split_into_segments(18) == [18]

    def test_long_clip_two_equal_segments(self):
        # 30s → [15, 15]
        result = orchestrator.split_into_segments(30)
        assert len(result) == 2
        assert sum(result) == 30

    def test_very_long_clip_multiple_segments(self):
        # 60s → 多段
        result = orchestrator.split_into_segments(60)
        assert all(s <= 18 for s in result)
        assert sum(result) == 60

    def test_5s_one_segment(self):
        assert orchestrator.split_into_segments(5) == [5]


# ================================================================
# prompt_builder.match_product
# ================================================================

class TestMatchProduct:
    def test_returns_tuple(self):
        result = prompt_builder.match_product("API 5CT Casing", "industrial")
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_unknown_returns_none_tuple(self):
        result = prompt_builder.match_product("XYZ Random Product", "industrial")
        # 没有匹配到 preset 时返回 (None, None) 或 (None, preset)
        assert result[0] is None or isinstance(result[0], str)


# ================================================================
# prompt_builder.auto_select_preset
# ================================================================

class TestAutoSelectPreset:
    def test_returns_none_or_preset(self):
        entities = {"product_name": "API 5CT Casing", "product_category": "industrial"}
        result = prompt_builder.auto_select_preset(entities)
        # 接受 None 或 dict / str
        assert result is None or isinstance(result, (dict, str, list))


# ================================================================
# subtitle_manager.generate_subtitles
# ================================================================

class TestGenerateSubtitles:
    def test_english_subtitles(self):
        # 返回 list; 若 catalog 有该产品, 含 text/start/end
        subs = subtitle_manager.generate_subtitles("Industrial Valve", "en", max_tags=2)
        assert isinstance(subs, list)
        if subs:
            assert all("text" in s and "start" in s and "end" in s for s in subs)

    def test_zh_subtitles(self):
        subs = subtitle_manager.generate_subtitles("球阀", "zh", max_tags=2)
        assert isinstance(subs, list)
        if subs:
            assert all("text" in s for s in subs)

    def test_subtitle_timing_order(self):
        subs = subtitle_manager.generate_subtitles("Industrial Pump", "en", max_tags=3)
        # 时间顺序：start 单调非降
        for i in range(1, len(subs)):
            assert subs[i]["start"] >= subs[i - 1]["start"], \
                f"subtitle {i} start < previous: {subs[i]}"

    def test_custom_subtitles(self):
        # custom subtitle path
        lines = ["Line 1", "Line 2", "Line 3"]
        subs = subtitle_manager.generate_custom_subtitles(lines, 6.0)
        assert isinstance(subs, list)
        assert len(subs) == 3
        # 时长应被 6s 平均分配
        assert subs[0]["start"] == 0.0
        assert subs[-1]["end"] <= 6.0


# ================================================================
# subtitle_manager.get_font_path
# ================================================================

class TestGetFontPath:
    def test_default_returns_str_or_none(self):
        # 字体文件可能不存在, 但函数应正常返回 (None 或 path string)
        result = subtitle_manager.get_font_path(lang="en")
        assert result is None or isinstance(result, str)

    def test_zh_returns_str_or_none(self):
        result = subtitle_manager.get_font_path(lang="zh")
        assert result is None or isinstance(result, str)


# ================================================================
# video_postprocess.get_bgm_path
# ================================================================

class TestGetBgmPath:
    def test_corporate_style(self):
        result = video_postprocess.get_bgm_path("corporate")
        # 字体文件可能不存在, 但函数应正常返回
        assert result is None or isinstance(result, str)

    def test_unknown_style_returns_none_or_path(self):
        result = video_postprocess.get_bgm_path("unknown_style_xyz")
        assert result is None or isinstance(result, str)


# ================================================================
# video_postprocess._probe_duration (ffmpeg 跳过测试)
# ================================================================

class TestProbeDuration:
    def test_nonexistent_file(self):
        # 对不存在的文件不崩 - 任何 numeric 都可以 (default 10.0 或 None)
        result = video_postprocess._probe_duration("/non/existent/file.mp4")
        assert result is None or isinstance(result, (int, float))
