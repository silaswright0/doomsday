#!/usr/bin/env python3
"""Aggressively strip remaining has_dlc / dlc_allowed gates in ported + buildings files."""
from __future__ import annotations

import re
from pathlib import Path

MOD = Path(__file__).resolve().parents[1]

TARGETS = [
    MOD / "common" / "raids",
    MOD / "common" / "special_projects",
    MOD / "common" / "intelligence_agencies",
    MOD / "common" / "intelligence_agency_upgrades",
    MOD / "common" / "operations",
    MOD / "common" / "operation_phases",
    MOD / "common" / "operation_tokens",
    MOD / "common" / "scientist_traits",
    MOD / "common" / "timed_activities",
    MOD / "common" / "equipment_groups",
    MOD / "common" / "buildings" / "00_buildings.txt",
    MOD / "common" / "technologies" / "support.txt",
    MOD / "common" / "technologies" / "NSB_armor.txt",
    MOD / "common" / "technologies" / "special_projects_tech.txt",
    MOD / "common" / "technologies" / "bba_air_techs.txt",
    MOD / "common" / "technologies" / "MTG_naval.txt",
    MOD / "common" / "technologies" / "MTG_naval_Support.txt",
]

# Match zz_dlc on_actions too
ON_ACTIONS_GLOB = MOD / "common" / "on_actions"

# has_dlc = "Name" OR has_dlc = Name
HAS_DLC = re.compile(r'has_dlc\s*=\s*(?:"[^"]+"|[A-Za-z0-9_]+)')
# dlc_allowed = { has_dlc = ... }  → remove restriction by making empty always allow
# After HAS_DLC replace, becomes dlc_allowed = { always = yes }


def ungate(text: str) -> str:
    text = HAS_DLC.sub("always = yes", text)
    # NOT = { always = yes } from former NOT = { has_dlc } → always = no
    text = re.sub(r"NOT\s*=\s*\{\s*always\s*=\s*yes\s*\}", "always = no", text)
    return text


def main() -> None:
    files: list[Path] = []
    for t in TARGETS:
        if t.is_file():
            files.append(t)
        elif t.is_dir():
            files.extend(t.rglob("*.txt"))
    files.extend(ON_ACTIONS_GLOB.glob("zz_dlc_*.txt"))

    changed = 0
    leftover = 0
    for f in files:
        raw = f.read_text(encoding="utf-8", errors="ignore")
        new = ungate(raw)
        if new != raw:
            f.write_text(new, encoding="utf-8", newline="\n")
            changed += 1
        leftover += len(re.findall(r"has_dlc\s*=", new))
        leftover += len(re.findall(r"dlc_allowed\s*=\s*\{\s*always\s*=\s*yes\s*\}", new))  # ok form
    # recount real has_dlc
    real = 0
    for f in files:
        real += len(re.findall(r"has_dlc\s*=", f.read_text(encoding="utf-8", errors="ignore")))
    print(f"updated {changed} files; remaining has_dlc= {real}")


if __name__ == "__main__":
    main()
