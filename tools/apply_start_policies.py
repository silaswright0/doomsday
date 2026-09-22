#!/usr/bin/env python3
"""Patch history/countries starting laws from the 2026 research table.

Does not regenerate OOBs, staff, or tech. Country-scoped. No random.
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from start_policies import POLICIES, ideas_for, validate  # noqa: E402

COUNTRIES_DIR = ROOT / "history" / "countries"
SIDECAR = ROOT / "tools" / "data" / "start_policies.csv"
TAG_MAP = ROOT / "tools" / "doomsday_tag_map.csv"

POLICY_IDS = set()
for prefix in (
    "dd_welfare_", "dd_education_", "dd_immigration_", "dd_taxes_",
    "dd_women_", "dd_minority_", "dd_investment_", "dd_security_",
    "dd_healthcare_", "dd_labor_", "dd_fertility_", "dd_aid_",
    "dd_religion_", "dd_media_", "dd_civil_military_",
):
    for n in range(1, 6):
        POLICY_IDS.add(f"{prefix}{n}")
POLICY_IDS.update({
    "volunteer_only", "limited_conscription", "extensive_conscription",
    "service_by_requirement", "scraping_the_barrel",
    "free_trade", "export_focus", "limited_exports", "closed_economy",
    "civilian_economy", "early_mobilization", "partial_economic_mobilisation",
    "war_economy", "tot_economic_mobilisation",
})


def on_map_tags() -> set[str]:
    out = set()
    with TAG_MAP.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("status") or "") == "on_map":
                out.add(row["tag"])
    return out


def patch_file(path: Path, ideas: list[str]) -> bool:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    kept = []
    removed = 0
    for line in lines:
        m = re.match(r"add_ideas\s*=\s*(\S+)", line.strip())
        if m and m.group(1) in POLICY_IDS:
            removed += 1
            continue
        kept.append(line)
    if not ideas:
        path.write_text("".join(kept), encoding="utf-8")
        return removed > 0
    insert = "".join(f"add_ideas = {idea}\n" for idea in ideas)
    out = []
    inserted = False
    for line in kept:
        if not inserted and re.match(r"set_politics\s*=", line.strip()):
            out.append(insert)
            inserted = True
        out.append(line)
    if not inserted:
        out.append(insert)
    new_text = "".join(out)
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    errs = validate()
    if errs:
        print("validation failed")
        for e in errs:
            print(" ", e)
        raise SystemExit(1)
    on = on_map_tags()
    missing = sorted(on - set(POLICIES))
    if missing:
        print("missing on-map tags", missing)
        raise SystemExit(1)
    changed = 0
    rows = []
    for path in sorted(COUNTRIES_DIR.glob("*.txt")):
        tag = path.name.split(" ")[0].strip()
        ideas = ideas_for(tag) if tag in on else []
        if patch_file(path, ideas):
            changed += 1
        rows.append((tag, " ".join(ideas)))
    SIDECAR.parent.mkdir(parents=True, exist_ok=True)
    with SIDECAR.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tag", "ideas"])
        w.writerows(rows)
    print("patched", changed, "history files;", len(on), "on-map researched")


if __name__ == "__main__":
    main()
