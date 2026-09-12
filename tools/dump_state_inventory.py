#!/usr/bin/env python3
"""Dump state inventory without depending on ingest network calls."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_lib import DATA, load_all_states  # noqa: E402


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    states = load_all_states()
    inv = [
        {
            "id": s["id"],
            "file": s["file"],
            "pretty": s["pretty"],
            "owner": s["owner"],
            "category": s["category"],
            "manpower_old": s["manpower"],
            "province_count": s["province_count"],
            "coastal": s["coastal"],
            "impassable": s["impassable"],
        }
        for s in states
    ]
    (DATA / "state_inventory.json").write_text(
        json.dumps({"count": len(inv), "states": inv}, indent=2), encoding="utf-8"
    )
    print("states", len(inv))
    by = {}
    for s in inv:
        by.setdefault(s["owner"], []).append(s)
    for tag in ("USA", "CHI", "RAJ", "SOV", "ENG", "GER", "JAP", "KOR", "BRA"):
        print(tag, len(by.get(tag, [])))
        for s in by.get(tag, [])[:12]:
            print(f"  {s['id']:4d} {s['pretty']}")


if __name__ == "__main__":
    main()
