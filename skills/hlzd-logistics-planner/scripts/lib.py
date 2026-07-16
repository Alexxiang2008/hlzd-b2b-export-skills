#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hlzd-logistics-planner — 标准集装箱尺寸库 + 体积利用率估算。

v0.1.0 仅交付纯函数（无 py3dbp 依赖）；v0.2 接入 py3dbp 真 3D 装箱。
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Container:
    code: str       # e.g. "20GP"
    name: str       # 20尺普通箱
    length_m: float
    width_m: float
    height_m: float
    max_payload_kg: float
    volume_m3: float


CONTAINERS: Dict[str, Container] = {
    "20GP": Container("20GP", "20尺普通箱", 5.90, 2.35, 2.39, 28200, 33.0),
    "40GP": Container("40GP", "40尺普通箱", 12.03, 2.35, 2.39, 26500, 67.5),
    "40HQ": Container("40HQ", "40尺高箱", 12.03, 2.35, 2.69, 26500, 76.0),
    "45HQ": Container("45HQ", "45尺高箱", 13.56, 2.35, 2.69, 27600, 86.0),
    "20OT": Container("20OT", "20尺开顶箱", 5.90, 2.35, 2.39, 28200, 33.0),
    "40FR": Container("40FR", "40尺框架箱", 12.03, 2.35, 2.39, 40000, 67.5),
}


def list_containers() -> List[Container]:
    return list(CONTAINERS.values())


def utilization_estimate(items_volume_m3: float, container_code: str) -> Dict[str, float]:
    """简单体积利用率估算（不考虑单品尺寸约束）。"""
    c = CONTAINERS.get(container_code)
    if not c:
        raise ValueError(f"unknown container: {container_code}")
    util = items_volume_m3 / c.volume_m3
    return {
        "container": container_code,
        "items_volume_m3": round(items_volume_m3, 3),
        "container_volume_m3": c.volume_m3,
        "utilization": round(min(util, 1.0), 4),
        "recommend_more_boxes": util > 1.0,
    }


def recommend_container(total_volume_m3: float, total_weight_kg: float) -> List[Dict]:
    """按体积+重量双约束推荐最佳箱型（贪心）。"""
    recs = []
    for c in CONTAINERS.values():
        n_by_vol = -(-int(total_volume_m3 * 1000) // int(c.volume_m3 * 1000))
        n_by_wt = -(-int(total_weight_kg) // int(c.max_payload_kg))
        n = max(n_by_vol, n_by_wt, 1)
        recs.append({"container": c.code, "boxes": n,
                     "utilization": round(total_volume_m3 / (c.volume_m3 * n), 4)})
    recs.sort(key=lambda r: (-r["utilization"], r["boxes"]))
    return recs
