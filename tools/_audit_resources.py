#!/usr/bin/env python3
"""Dump country resource totals from doomsday_states.csv."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

KEYS = [
    "oil", "coal", "steel", "aluminium", "tungsten", "chromium",
    "copper", "graphite", "lithium", "cobalt", "rare_earths", "rubber",
]
WATCH = [
    "CHI", "USA", "GNA", "AST", "CAN", "NOR", "UAE", "INS", "PHI", "FRA",
    "GAB", "COG", "ZIM", "GYA", "JAM", "SER", "MLI", "SSD", "BRM", "ZAM",
    "SAF", "TUR", "KAZ", "CUB", "IVO", "NMB", "PNG", "PRU", "CHL", "ARG",
    "VIN", "SIE", "GHA", "MON", "LAO", "PAN", "AZR", "SOV", "RAJ", "ENG",
]


def main() -> None:
    tot: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    world: dict[str, int] = defaultdict(int)
    path = Path(__file__).resolve().parent / "doomsday_states.csv"
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            tag = row["owner_2026"]
            for k in KEYS:
                v = int(float(row.get(k) or 0))
                tot[tag][k] += v
                world[k] += v
    print("WORLD", dict(world))
    hdr = f"{'tag':6} " + " ".join(f"{k[:4]:>5}" for k in KEYS)
    print(hdr)
    for tag in WATCH:
        r = tot[tag]
        print(f"{tag:6} " + " ".join(f"{r[k]:5}" for k in KEYS))
    for k in ("aluminium", "chromium", "lithium", "cobalt", "copper", "rare_earths"):
        top = sorted(((tot[t][k], t) for t in tot), reverse=True)[:12]
        print(k, top)


if __name__ == "__main__":
    main()
