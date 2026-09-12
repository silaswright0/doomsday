#!/usr/bin/env python3
"""Patch history/states in place from tools/doomsday_states.csv.

Updates manpower, category, extra slots, state-level factories/infra/parks/
finance/services, and resources. Leaves owners, cores, VPs, air bases,
rocket sites, and province buildings untouched.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_lib import (  # noqa: E402
    STATES_CSV,
    STATES_DIR,
    extract_block,
)

RESOURCE_KEYS = (
    "oil",
    "aluminium",
    "rubber",
    "tungsten",
    "steel",
    "chromium",
    "coal",
    "rare_earths",
    "lithium",
    "cobalt",
    "copper",
    "graphite",
)
STATE_BUILDINGS = (
    "infrastructure",
    "industrial_complex",
    "arms_factory",
    "dockyard",
    "renewable_park",
    "finance_center",
    "services_building",
)
NESTED_RE = re.compile(r"[ \t]*\d+\s*=\s*\{(?:[^{}]|\{[^{}]*\})*\}", re.S)


def load_plan() -> dict[int, dict]:
    plan = {}
    with STATES_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            plan[int(row["state_id"])] = row
    return plan


def split_buildings_inner(inner: str) -> tuple[str, list[str]]:
    nested: list[str] = []

    def keep(m: re.Match) -> str:
        chunk = m.group(0).rstrip()
        if not chunk[:1].isspace():
            chunk = "\t\t\t" + chunk.lstrip()
        nested.append(chunk)
        return f"\n__NESTED_{len(nested) - 1}__\n"

    stripped = NESTED_RE.sub(keep, inner)
    return stripped, nested


def set_state_key(stripped: str, key: str, value: int) -> str:
    pattern = re.compile(rf"^([ \t]*){key}\s*=\s*\d+[^\n]*$", re.M)
    if value <= 0 and key in {"dockyard", "renewable_park", "finance_center", "services_building"}:
        if pattern.search(stripped):
            stripped = pattern.sub("", stripped)
        return stripped
    line = f"\t\t\t{key} = {value}"
    if pattern.search(stripped):
        return pattern.sub(line, stripped, count=1)
    marker = re.search(r"__NESTED_\d+__", stripped)
    if marker:
        return stripped[: marker.start()] + line + "\n" + stripped[marker.start() :]
    return stripped.rstrip() + f"\n{line}\n"


def patch_resources(text: str, resources: dict[str, int]) -> str:
    body = "".join(f"\n\t\t{k}={v}" for k, v in resources.items() if v > 0)
    if not body:
        text = re.sub(r"\n[ \t]*resources\s*=\s*\{[^{}]*\}", "", text, count=1)
        return text
    block = "{\n" + body + "\n\t}"
    if re.search(r"\bresources\s*=", text):
        m = re.search(r"\bresources\s*=", text)
        old, end = extract_block(text, m.start())
        return text[: m.start()] + f"resources={block}" + text[end:]
    # insert after manpower or state_category
    m = re.search(r"state_category\s*=\s*\S+", text)
    if m:
        return text[: m.end()] + f"\n\n\tresources={block}\n" + text[m.end() :]
    m = re.search(r"manpower\s*=\s*\d+", text)
    if m:
        return text[: m.end()] + f"\n\n\tresources={block}\n" + text[m.end() :]
    return text


def patch_file(path: Path, row: dict) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    original = text
    manpower = max(1000, int(float(row["manpower"])))
    category = row["category"]
    slots = int(float(row.get("extra_slots") or 0))
    text = re.sub(r"\bmanpower\s*=\s*\d+", f"manpower = {manpower}", text, count=1)
    text = re.sub(r"\bstate_category\s*=\s*\"?\w+\"?", f"state_category = {category}", text, count=1)
    if re.search(r"add_extra_state_shared_building_slots", text):
        text = re.sub(
            r"add_extra_state_shared_building_slots\s*=\s*\d+",
            f"add_extra_state_shared_building_slots = {slots}",
            text,
            count=1,
        )
    elif slots:
        text = re.sub(
            r"(\bowner\s*=\s*[A-Z0-9]{3})",
            rf"\1\n\t\tadd_extra_state_shared_building_slots = {slots}",
            text,
            count=1,
        )

    bm = re.search(r"\bbuildings\s*=", text)
    if bm:
        block, end = extract_block(text, bm.start())
        inner = block[1:-1]
        stripped, nested = split_buildings_inner(inner)
        values = {
            "infrastructure": int(float(row.get("infra") or 1)),
            "industrial_complex": int(float(row.get("civs") or 0)),
            "arms_factory": int(float(row.get("mils") or 0)),
            "dockyard": int(float(row.get("docks") or 0)),
            "renewable_park": int(float(row.get("renewable") or 0)),
            "finance_center": int(float(row.get("finance") or 0)),
            "services_building": int(float(row.get("services") or 0)),
        }
        for key in STATE_BUILDINGS:
            stripped = set_state_key(stripped, key, values[key])
        for i, chunk in enumerate(nested):
            stripped = stripped.replace(f"__NESTED_{i}__", chunk, 1)
        new_block = "{\n" + stripped.strip("\n") + "\n\t\t}"
        text = text[: bm.start()] + "buildings = " + new_block + text[end:]

    resources = {k: int(float(row.get(k) or 0)) for k in RESOURCE_KEYS}
    text = patch_resources(text, resources)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    plan = load_plan()
    changed = 0
    missing = 0
    for path in sorted(STATES_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"\bid\s*=\s*(\d+)", text)
        if not m:
            continue
        sid = int(m.group(1))
        row = plan.get(sid)
        if not row:
            missing += 1
            continue
        if patch_file(path, row):
            changed += 1
    print(f"patched {changed} states; missing_from_plan {missing}")


if __name__ == "__main__":
    main()
