#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hlzd-logistics-planner lib 测试。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import (  # noqa: E402
    CONTAINERS, list_containers, utilization_estimate, recommend_container,
)


def test_all_6_standard_containers_present():
    codes = {c.code for c in list_containers()}
    assert {"20GP", "40GP", "40HQ", "45HQ", "20OT", "40FR"} <= codes


def test_utilization_within_capacity():
    r = utilization_estimate(30.0, "40GP")
    assert r["container"] == "40GP"
    assert 0.4 < r["utilization"] < 0.5
    assert not r["recommend_more_boxes"]


def test_utilization_overflow_flags_more_boxes():
    r = utilization_estimate(200.0, "20GP")
    assert r["utilization"] == 1.0
    assert r["recommend_more_boxes"]


def test_unknown_container_raises():
    try:
        utilization_estimate(10.0, "99XX")
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown container")


def test_recommend_prefers_higher_utilization():
    recs = recommend_container(60.0, 20000)
    # 60 m3 → 20GP 需 2 箱 (util=0.909), 40GP 1 箱 (util=0.889), 40HQ 1 箱 (0.789)
    # 贪心按 (-util, boxes) → 20GP 第一
    assert recs[0]["container"] == "20GP"
    assert recs[0]["boxes"] == 2


def test_recommend_respects_weight_constraint():
    # 60 m3 但 60,000 kg → 40GP max payload 26,500 → 至少 3 箱
    recs = recommend_container(60.0, 60000)
    for r in recs:
        if r["container"] == "40GP":
            assert r["boxes"] >= 3
