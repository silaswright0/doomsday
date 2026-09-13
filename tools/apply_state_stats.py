#!/usr/bin/env python3
"""Patch history/states in place from tools/doomsday_states.csv.

Updates manpower, category, extra slots, state-level factories/infra/parks/
finance/services/refineries/silos/grid/air/AA/radar, resources, nested naval
levels (never deletes a port), and land supply hubs. Raises existing railway
levels; does not add or remove edges. Leaves owners, cores, and VPs untouched.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_lib import (  # noqa: E402
    COUNTRIES_CSV,
    ROOT,
    STATES_CSV,
    STATES_DIR,
    extract_block,
    iter_province_blocks,
    load_all_states,
    parse_victory_points,
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
    "synthetic_refinery",
    "fuel_silo",
    "energy_infrastructure",
    "air_base",
    "anti_air_building",
    "radar_station",
)
SUPPLY_CATS = {"megalopolis", "metropolis", "large_city", "city"}
RAIL_MIN = {
    "CHI": 2, "JAP": 2, "KOR": 2, "FOR": 2, "RAJ": 2, "PAK": 2,
    "USA": 2, "CAN": 2, "GER": 2, "FRA": 2, "ENG": 2, "ITA": 2,
    "POL": 2, "TUR": 2, "VIN": 2, "THA": 2, "SIA": 2, "MAL": 2,
    "SOV": 2, "UKR": 2,
}
RAIL_TRUNK = {"CHI", "JAP", "KOR", "USA", "GER", "RAJ", "SOV"}
FLAT_KEY_RE = {
    "naval_base": re.compile(r"^[ \t]*naval_base\s*=\s*\d+[ \t]*$", re.M),
    "naval_supply_hub": re.compile(r"^[ \t]*naval_supply_hub\s*=\s*\d+[ \t]*$", re.M),
    "supply_node": re.compile(r"^[ \t]*supply_node\s*=\s*\d+[ \t]*$", re.M),
}


def load_plan() -> dict[int, dict]:
    plan = {}
    with STATES_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            plan[int(row["state_id"])] = row
    return plan


def load_capitals() -> dict[str, int]:
    out: dict[str, int] = {}
    with COUNTRIES_CSV.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            cap = str(row.get("capital") or "").strip()
            tag = (row.get("tag") or "").strip()
            if tag and cap.isdigit():
                out[tag] = int(cap)
    return out


def split_buildings_inner(inner: str) -> tuple[str, list[tuple[int, str]]]:
    nested: list[tuple[int, str]] = []
    parts: list[str] = []
    last = 0
    for pid, start, end, chunk in iter_province_blocks(inner):
        parts.append(inner[last:start])
        nested.append((pid, chunk))
        last = end
    parts.append(inner[last:])
    stripped = "".join(parts)
    for i in range(len(nested)):
        stripped += f"\n__NESTED_{i}__\n"
    return stripped, nested


def set_state_key(stripped: str, key: str, value: int) -> str:
    pattern = re.compile(rf"^([ \t]*){key}\s*=\s*\d+[^\n]*$", re.M)
    if value <= 0 and key in {
        "dockyard",
        "renewable_park",
        "finance_center",
        "services_building",
        "synthetic_refinery",
        "fuel_silo",
        "energy_infrastructure",
        "air_base",
        "anti_air_building",
        "radar_station",
    }:
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


def set_flat_key(chunk: str, key: str, value: int | None) -> str:
    pattern = FLAT_KEY_RE[key]
    if value is None:
        return pattern.sub("", chunk)
    line = f"\t\t\t\t{key} = {value}"
    if pattern.search(chunk):
        return pattern.sub(line, chunk, count=1)
    brace = chunk.find("{")
    if brace < 0:
        return chunk
    return chunk[: brace + 1] + f"\n{line}" + chunk[brace + 1 :]


def strip_named_block(chunk: str, key: str) -> str:
    m = re.search(rf"{key}\s*=\s*{{", chunk)
    if not m:
        return chunk
    _block, end = extract_block(chunk, m.start())
    return chunk[: m.start()] + chunk[end:]


def primary_port(ports: dict[int, int], vps: dict[int, int]) -> int | None:
    if not ports:
        return None
    return min(ports, key=lambda pid: (-vps.get(pid, 0), -ports[pid], pid))


def rewrite_province_chunk(pid: int, chunk: str, naval_level: int | None, want_supply: bool) -> str:
    if naval_level is not None:
        chunk = set_flat_key(chunk, "naval_base", max(1, min(10, naval_level)))
        if naval_level >= 8:
            chunk = set_flat_key(chunk, "naval_supply_hub", 1)
        else:
            chunk = set_flat_key(chunk, "naval_supply_hub", None)
            chunk = strip_named_block(chunk, "naval_headquarters")
    if want_supply:
        chunk = set_flat_key(chunk, "supply_node", 1)
    return chunk


def compact_inner(inner: str) -> str:
    inner = re.sub(r"[ \t]+\n", "\n", inner)
    inner = re.sub(r"\n{3,}", "\n\n", inner)
    return inner.strip("\n")


def patch_resources(text: str, resources: dict[str, int]) -> str:
    body = "".join(f"\n\t\t{k}={v}" for k, v in resources.items() if v > 0)
    if not body:
        text = re.sub(r"\n[ \t]*resources\s*=\s*\{[^{}]*\}", "", text, count=1)
        return text
    block = "{\n" + body + "\n\t}"
    if re.search(r"\bresources\s*=", text):
        m = re.search(r"\bresources\s*=", text)
        _old, end = extract_block(text, m.start())
        return text[: m.start()] + f"resources={block}" + text[end:]
    m = re.search(r"state_category\s*=\s*\S+", text)
    if m:
        return text[: m.end()] + f"\n\n\tresources={block}\n" + text[m.end() :]
    m = re.search(r"manpower\s*=\s*\d+", text)
    if m:
        return text[: m.end()] + f"\n\n\tresources={block}\n" + text[m.end() :]
    return text


def state_provinces(text: str) -> list[int]:
    m = re.search(r"provinces\s*=\s*\{([^}]*)\}", text)
    if not m:
        return []
    return [int(x) for x in re.findall(r"\d+", m.group(1))]


def patch_file(path: Path, row: dict, is_capital: bool) -> bool:
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
            "synthetic_refinery": int(float(row.get("refinery") or 0)),
            "fuel_silo": int(float(row.get("fuel_silo") or 0)),
            "energy_infrastructure": int(float(row.get("energy_grid") or 0)),
            "air_base": int(float(row.get("air_base") or 0)),
            "anti_air_building": int(float(row.get("anti_air") or 0)),
            "radar_station": int(float(row.get("radar") or 0)),
        }
        for key in STATE_BUILDINGS:
            stripped = set_state_key(stripped, key, values[key])

        ports = {}
        for pid, chunk in nested:
            nb = re.search(r"\bnaval_base\s*=\s*(\d+)", chunk)
            if nb:
                ports[pid] = int(nb.group(1))
        vps = parse_victory_points(text)
        primary = primary_port(ports, vps)
        primary_level = int(float(row.get("naval_primary") or 0))
        if ports and primary_level <= 0:
            primary_level = 1

        impassable = bool(re.search(r"\bimpassable\s*=\s*yes", text))
        max_vp = max(vps.values(), default=0)
        want_hub = (not impassable or is_capital) and (
            is_capital
            or category in SUPPLY_CATS
            or max_vp >= 15
            or primary_level >= 8
        )
        hub_pid = None
        provs = state_provinces(text)
        if want_hub:
            in_state = [pid for pid in vps if pid in set(provs)]
            if in_state:
                hub_pid = min(in_state, key=lambda pid: (-vps[pid], pid))
            elif provs:
                hub_pid = provs[0]

        seen_hub = False
        n_orig = len(nested)
        for i, (pid, chunk) in enumerate(nested):
            naval = None
            if pid in ports:
                naval = primary_level if pid == primary else 1
            is_hub = want_hub and hub_pid == pid
            if is_hub:
                seen_hub = True
            nested[i] = (pid, rewrite_province_chunk(pid, chunk, naval, is_hub))
        extra_chunk = None
        if want_hub and hub_pid and not seen_hub:
            extra_chunk = f"\t\t\t{hub_pid} = {{\n\t\t\t\tsupply_node = 1\n\t\t\t}}"

        for i in range(n_orig):
            stripped = stripped.replace(f"__NESTED_{i}__", nested[i][1], 1)
        if extra_chunk:
            stripped = stripped.rstrip() + "\n" + extra_chunk + "\n"
        new_block = "{\n" + compact_inner(stripped) + "\n\t\t}"
        text = text[: bm.start()] + "buildings = " + new_block + text[end:]

    resources = {k: int(float(row.get(k) or 0)) for k in RESOURCE_KEYS}
    text = patch_resources(text, resources)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def upgrade_railways() -> None:
    path = ROOT / "map" / "railways.txt"
    prov_tag: dict[int, str] = {}
    for s in load_all_states():
        for pid in s["provinces"]:
            prov_tag[pid] = s["owner"]
    raised = 0
    new_lines: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split()
        if len(parts) < 3:
            new_lines.append(line)
            continue
        try:
            level = int(parts[0])
            n = int(parts[1])
            pids = [int(x) for x in parts[2:]]
        except ValueError:
            new_lines.append(line)
            continue
        tags = {prov_tag[pid] for pid in pids if pid in prov_tag}
        want = level
        for tag in tags:
            want = max(want, RAIL_MIN.get(tag, 0))
        if n >= 4 and (tags & RAIL_TRUNK):
            want = max(want, 3)
        want = min(max(want, level), 3)
        if want != level:
            raised += 1
        new_lines.append(" ".join([str(want), str(n), *map(str, pids)]))
    path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"railways raised {raised} edges (topology unchanged)")


def main() -> None:
    plan = load_plan()
    capitals = load_capitals()
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
        owner = re.search(r"owner\s*=\s*([A-Z0-9]{3})", text)
        is_capital = bool(owner and capitals.get(owner.group(1)) == sid)
        if patch_file(path, row, is_capital):
            changed += 1
    print(f"patched {changed} states; missing_from_plan {missing}")
    upgrade_railways()


if __name__ == "__main__":
    main()
