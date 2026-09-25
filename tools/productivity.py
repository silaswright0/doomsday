#!/usr/bin/env python3
"""Productivity = real 2026 GDP / shared population-and-building formula.

Same weights as dd_apply_rates in common/scripted_effects/doomsday_economy.txt.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTRIES = ROOT / "tools" / "doomsday_countries.csv"
STATES = ROOT / "tools" / "doomsday_states.csv"

W_POP = 1.0
W_CIV = 8.0
W_MIL = 4.0
W_DOCK = 6.0
W_FIN = 12.0
W_SRV = 5.0


def pop_m(manpower: float) -> float:
    return round(manpower / 100_000.0) / 10.0


def points_by_tag() -> dict[str, float]:
    totals: dict[str, dict[str, float]] = defaultdict(
        lambda: {"pop": 0.0, "civ": 0.0, "mil": 0.0, "dock": 0.0, "fin": 0.0, "srv": 0.0}
    )
    with STATES.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tag = row["owner_2026"]
            b = totals[tag]
            b["pop"] += pop_m(float(row["manpower"] or 0))
            b["civ"] += float(row["civs"] or 0)
            b["mil"] += float(row["mils"] or 0)
            b["dock"] += float(row["docks"] or 0)
            b["fin"] += float(row["finance"] or 0)
            b["srv"] += float(row["services"] or 0)
    out = {}
    for tag, b in totals.items():
        out[tag] = (
            b["pop"] * W_POP
            + b["civ"] * W_CIV
            + b["mil"] * W_MIL
            + b["dock"] * W_DOCK
            + b["fin"] * W_FIN
            + b["srv"] * W_SRV
        )
    return out


def all_productivity() -> dict[str, float]:
    pts = points_by_tag()
    prod: dict[str, float] = {}
    with COUNTRIES.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tag = row["tag"]
            gdp = float(row.get("gdp_b") or 0)
            base = pts.get(tag, 0.0)
            if gdp > 0 and base > 0.001:
                prod[tag] = gdp / base
            else:
                prod[tag] = 1.0
    return prod
