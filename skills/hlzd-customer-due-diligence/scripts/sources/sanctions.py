"""Sanctions data — OFAC / UN static subset (deterministic for v0.1)."""
from __future__ import annotations

from typing import List

# 静态 OFAC SDN 子集 — 与 lib.OFAC_SDN_STATIC_NAMES 保持一致
# 真实合规复核请用 OFAC / EU / UN 官方 API (每 24h 刷新)
OFAC_SDN_STATIC_NAMES: List[str] = [
    "Russian National Commercial Bank",
    "Bank Saderat Iran",
    "Hezbollah",
    "Hamas",
    "Islamic State of Iraq and the Levant",
    "Wagner Group",
    "Tornado Cash",
    "Lazarus Group",
    "Fancy Bear",
    "Cozy Bear",
    "Pyongyang University of Science and Technology",
    "Iran Aircraft Manufacturing Industrial Co",
    "Tanker Pacific",
    "Islamic Revolutionary Guard Corps",
    "Navalny Anticorruption Foundation",
    "Al-Shabaab",
    "Boko Haram",
    "Taliban",
    "Donetsk People's Republic",
    "Luhansk People's Republic",
]
