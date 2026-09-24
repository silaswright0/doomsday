#!/usr/bin/env python3
"""Port DLC gameplay systems from base HOI4 into the Doomsday mod (ungated).

Copies script folders that are NOT under replace_path (or that we want local
overrides for), strips has_dlc gates so systems work without owned DLC packs,
and pulls selected on_actions files (gameplay DLC hooks only — not 00_on_actions).

Does NOT touch:
- Doomsday intel decisions/effects
- Doomsday cash arms market
- AAT international market CIC payment (engine)
- National focuses / country focus on_actions scrubbing beyond focus no-ops
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

BASE = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV")
MOD = Path(__file__).resolve().parents[1]

# Folders to copy wholesale into the mod (override/add).
COPY_TREES = [
    "common/raids",
    "common/intelligence_agencies",
    "common/intelligence_agency_upgrades",
    "common/operations",
    "common/operation_phases",
    "common/operation_tokens",
    "common/special_projects",
    "common/scientist_traits",
    "common/timed_activities",
    "common/equipment_groups",
]

# Gameplay on_actions from DLC expansions (skip vanilla 00_ and focus-heavy early trees
# that mostly gate country content — still include LAR/NSB/BBA/AAT/Gotter/TAOG).
ON_ACTIONS = [
    "05_lar_on_actions.txt",
    "07_nsb_on_actions.txt",
    "08_bba_on_actions.txt",
    "09_aat_on_actions.txt",
    "12_wuw_on_actions.txt",  # Götterdämmerung / special projects / raids
    "16_taog_on_actions.txt",  # Thunder at Our Gates raids
]

# Also pull raid-related GFX interface if missing? Skip — base loads GFX.

HAS_DLC = re.compile(
    r"(?P<indent>^[ \t]*)has_dlc\s*=\s*\"[^\"]+\"\s*$",
    re.M,
)
# NOT = { has_dlc = "X" } blocks — turn into never so DLC-alt branches don't fight
NOT_HAS_DLC_BLOCK = re.compile(
    r"NOT\s*=\s*\{\s*has_dlc\s*=\s*\"[^\"]+\"\s*\}",
    re.M,
)


def ungate_text(text: str) -> str:
    """Replace has_dlc checks so content is always available."""
    # Positive gates → always
    text = HAS_DLC.sub(r"\g<indent>always = yes", text)
    # Negative DLC gates (content for non-owners) → never, prefer DLC branch
    text = NOT_HAS_DLC_BLOCK.sub("always = no", text)
    return text


def copy_tree(rel: str) -> int:
    src = BASE / rel
    dst = MOD / rel
    if not src.exists():
        print(f"  MISS {rel}")
        return 0
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    n = 0
    for f in dst.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".txt", ".md", ".lua"}:
            raw = f.read_text(encoding="utf-8", errors="ignore")
            new = ungate_text(raw)
            if new != raw:
                f.write_text(new, encoding="utf-8", newline="\n")
                n += 1
    print(f"  OK {rel} ({n} files ungated)")
    return n


def copy_on_actions() -> None:
    out = MOD / "common" / "on_actions"
    out.mkdir(parents=True, exist_ok=True)
    for name in ON_ACTIONS:
        src = BASE / "common" / "on_actions" / name
        if not src.exists():
            print(f"  MISS on_actions/{name}")
            continue
        dst = out / f"zz_dlc_{name}"  # load after doomsday_* ; keep distinct
        raw = src.read_text(encoding="utf-8", errors="ignore")
        dst.write_text(ungate_text(raw), encoding="utf-8", newline="\n")
        print(f"  OK on_actions/{dst.name}")


def patch_special_projects_extra() -> None:
    """Ensure flame tank SP and similar stay available even if nested gates remain."""
    land = MOD / "common" / "special_projects" / "projects" / "land_projects.txt"
    if not land.exists():
        return
    text = land.read_text(encoding="utf-8", errors="ignore")
    # Belt-and-suspenders: any leftover has_dlc
    text2 = ungate_text(text)
    if text2 != text:
        land.write_text(text2, encoding="utf-8", newline="\n")


def main() -> None:
    print("=== Copy + ungate DLC gameplay trees ===")
    for rel in COPY_TREES:
        copy_tree(rel)
    print("=== DLC on_actions ===")
    copy_on_actions()
    patch_special_projects_extra()
    print("done")


if __name__ == "__main__":
    main()
