"""Find state buildings whose map pin is missing or sits in another state.

Hearts of Iron draws airfields, rocket sites, radars, reactors, factories, and
ports from map/buildings.txt. The level lives in history/states. After a state
split those two can disagree: the level is on a state with no pin, or the pin
pixel now belongs to a neighbor, so the building is invisible or the game
reports that you do not control it.

The pixel test matches the game. Confirmed against the 1.19 error log:
pixel_x = trunc(x), pixel_y = (height - 1) - trunc(z).

Usage:
    python tools/check_buildings.py
Exit 1 when any building is broken. Notes are printed but do not fail the run.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VANILLA_MAP = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV") / "map"

# One pin. Level with no on-state land pixel means the building does not work.
SINGLE_PIN = {
    "air_base": ("air_base",),
    "rocket_site": ("rocket_site", "rocket_site_spawn"),
    "radar_station": ("radar_station",),
    "nuclear_reactor": ("nuclear_reactor", "nuclear_reactor_spawn"),
}
# Several mesh slots. Broken only when every slot is off this state's land.
SLOTTED = {
    "arms_factory": ("arms_factory",),
    "industrial_complex": ("industrial_complex",),
    "dockyard": ("dockyard",),
    "anti_air_building": ("anti_air_building",),
    "synthetic_refinery": ("synthetic_refinery",),
    "fuel_silo": ("fuel_silo",),
}
# A port pixel is often the sea tile beside the province. Accept land this close.
PORT_RADIUS = 2


def map_file(name: str) -> Path:
    mod = ROOT / "map" / name
    if mod.exists():
        return mod
    vanilla = VANILLA_MAP / name
    if vanilla.exists():
        return vanilla
    sys.exit(f"missing map file {name}")


def strip_comments(text: str) -> str:
    return re.sub(r"#.*", "", text)


def brace_block(text: str, key: str) -> str | None:
    match = re.search(rf"\b{key}\s*=\s*\{{", text)
    if not match:
        return None
    start = match.end()
    depth = 1
    for i in range(start, len(text)):
        char = text[i]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start:i]
    return None


def parse_state(path: Path) -> dict | None:
    raw = path.read_text(encoding="utf-8", errors="replace")
    text = strip_comments(raw)
    mid = re.search(r"\bid\s*=\s*(\d+)", text)
    if not mid:
        return None
    sid = int(mid.group(1))
    prov_block = brace_block(text, "provinces")
    provs = [int(n) for n in re.findall(r"\d+", prov_block)] if prov_block else []
    buildings = brace_block(text, "buildings") or ""
    state_levels: dict[str, int] = {}
    province_buildings: dict[int, dict[str, int]] = {}
    # Province blocks are one level deep. Pull them out, then read state keys.
    rest = buildings
    for match in re.finditer(r"(\d+)\s*=\s*\{([^{}]*)\}", buildings):
        pid = int(match.group(1))
        levels: dict[str, int] = {}
        for key, value in re.findall(r"([A-Za-z_]\w*)\s*=\s*(-?\d+)", match.group(2)):
            levels[key] = int(value)
        province_buildings[pid] = levels
    rest = re.sub(r"\d+\s*=\s*\{[^{}]*\}", "", buildings)
    for key, value in re.findall(r"([A-Za-z_]\w*)\s*=\s*(-?\d+)", rest):
        state_levels[key] = int(value)
    return {
        "id": sid,
        "file": path.name,
        "provinces": provs,
        "levels": state_levels,
        "province_buildings": province_buildings,
        "buildings_open": re.search(r"\bbuildings\s*=\s*\{", text) is not None
        and brace_block(text, "buildings") is None,
    }


def load_definition(path: Path) -> tuple[dict[tuple[int, int, int], int], dict[int, str]]:
    rgb_to_id: dict[tuple[int, int, int], int] = {}
    id_to_kind: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split(";")
        if len(parts) < 5:
            continue
        try:
            pid = int(parts[0])
            rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
        except ValueError:
            continue
        rgb_to_id[rgb] = pid
        id_to_kind[pid] = parts[4]
    return rgb_to_id, id_to_kind


def load_supply_nodes(path: Path) -> set[int]:
    """Provinces that can hold a hub. The first field is not a state id."""
    provinces: set[int] = set()
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        nums = re.findall(r"\d+", line.split("#", 1)[0])
        if len(nums) >= 2:
            provinces.add(int(nums[1]))
        elif len(nums) == 1:
            provinces.add(int(nums[0]))
    return provinces


class MapPins:
    def __init__(self, image: Image.Image, rgb_to_id: dict, id_to_kind: dict) -> None:
        self.px = image.load()
        self.w, self.h = image.size
        self.rgb_to_id = rgb_to_id
        self.id_to_kind = id_to_kind
        # (state, map type) -> provinces under each row's pixel (None if off-map or unknown)
        self.rows: dict[tuple[int, str], list[int | None]] = defaultdict(list)
        self.ports: dict[int, list[int | None]] = defaultdict(list)

    def province_at(self, x: int, y: int) -> int | None:
        if x < 0 or y < 0 or x >= self.w or y >= self.h:
            return None
        return self.rgb_to_id.get(self.px[x, y][:3])

    def sample(self, x_text: str, z_text: str) -> tuple[int, int, int | None]:
        ix = int(float(x_text))
        iy = (self.h - 1) - int(float(z_text))
        return ix, iy, self.province_at(ix, iy)

    def nearest_land(self, ix: int, iy: int, radius: int) -> int | None:
        best: int | None = None
        best_d = radius * radius + 1
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                pid = self.province_at(ix + dx, iy + dy)
                if pid is None or self.id_to_kind.get(pid) != "land":
                    continue
                dist = dx * dx + dy * dy
                if dist < best_d:
                    best_d = dist
                    best = pid
        return best

    def add_row(self, state_id: int, kind: str, x_text: str, z_text: str, tagged: int | None) -> None:
        try:
            ix, iy, pid = self.sample(x_text, z_text)
        except ValueError:
            self.rows[(state_id, kind)].append(None)
            return
        self.rows[(state_id, kind)].append(pid)
        if kind == "naval_base_spawn":
            land = pid if self.id_to_kind.get(pid or -1) == "land" else None
            if land is None and tagged and self.id_to_kind.get(tagged) == "land":
                land = tagged
            if land is None:
                land = self.nearest_land(ix, iy, PORT_RADIUS)
            self.ports[state_id].append(land)


def on_state(pins: list[int | None], prov_to_state: dict[int, int], sid: int) -> list[int]:
    return [pid for pid in pins if pid is not None and prov_to_state.get(pid) == sid]


def foreign(pins: list[int | None], prov_to_state: dict[int, int], sid: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for pid in pins:
        if pid is None:
            continue
        owner = prov_to_state.get(pid)
        if owner is not None and owner != sid:
            out.append((pid, owner))
    return out


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []

    states: dict[int, dict] = {}
    for path in sorted((ROOT / "history" / "states").glob("*.txt")):
        parsed = parse_state(path)
        if parsed is None:
            errors.append(f"{path.name}: no state id")
            continue
        if parsed["id"] in states:
            errors.append(f"duplicate state id {parsed['id']}: {states[parsed['id']]['file']} and {path.name}")
        if parsed["buildings_open"]:
            errors.append(f"[file] {path.name}: buildings block is not closed")
        states[parsed["id"]] = parsed

    prov_to_state: dict[int, int] = {}
    for sid, state in states.items():
        for pid in state["provinces"]:
            prov_to_state.setdefault(pid, sid)

    print("loading provinces.bmp ...")
    image = Image.open(map_file("provinces.bmp"))
    rgb_to_id, id_to_kind = load_definition(map_file("definition.csv"))
    pins = MapPins(image, rgb_to_id, id_to_kind)
    buildings_path = map_file("buildings.txt")
    bad_fields = 0
    for line in buildings_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split(";")
        if len(parts) < 5:
            bad_fields += 1
            continue
        try:
            sid = int(parts[0])
        except ValueError:
            bad_fields += 1
            continue
        tagged = None
        if len(parts) >= 7:
            try:
                tagged = int(parts[6])
            except ValueError:
                tagged = None
        pins.add_row(sid, parts[1], parts[2], parts[4], tagged)
    if bad_fields:
        errors.append(f"[file] {buildings_path.name}: {bad_fields} rows with fewer than 5 fields")

    def check_kind(sid: int, state: dict, history_key: str, map_types: tuple[str, ...], single: bool) -> None:
        level = state["levels"].get(history_key, 0)
        if level <= 0:
            return
        found: list[int | None] = []
        for map_type in map_types:
            found.extend(pins.rows.get((sid, map_type), []))
        good = on_state(found, prov_to_state, sid)
        if good:
            return
        elsewhere = foreign(found, prov_to_state, sid)
        where = ""
        if elsewhere:
            shown = ", ".join(f"province {pid} in state {owner}" for pid, owner in elsewhere[:4])
            where = f"; pin is on {shown}"
        elif found:
            where = "; pin is not on land"
        label = "pin" if single else "mesh"
        kind = "no on-state pin" if single else "no on-state mesh"
        errors.append(f"[{label}] {state['file']} state {sid}: {history_key} {level} {kind}{where}")

    for sid, state in sorted(states.items()):
        provset = set(state["provinces"])
        for pid, levels in state["province_buildings"].items():
            if pid not in provset:
                owner = prov_to_state.get(pid)
                keys = ", ".join(f"{key}={value}" for key, value in levels.items()) or "empty"
                errors.append(
                    f"[province] {state['file']} state {sid}: province building {pid} ({keys}) is not in this state"
                    + (f" (it is in state {owner})" if owner else " (it is in no state)")
                )
                continue
            naval = levels.get("naval_base", 0)
            if naval > 0:
                spawned = [land for land in pins.ports.get(sid, []) if land == pid]
                if not spawned:
                    errors.append(
                        f"[port] {state['file']} state {sid}: naval_base {naval} on province {pid} has no port pin on that province"
                    )
        for history_key, map_types in SINGLE_PIN.items():
            check_kind(sid, state, history_key, map_types, True)
        for history_key, map_types in SLOTTED.items():
            check_kind(sid, state, history_key, map_types, False)

    supply_path = map_file("supply_nodes.txt")
    listed = load_supply_nodes(supply_path)
    for pid in sorted(listed):
        if pid not in prov_to_state:
            errors.append(f"[supply] {supply_path.name}: hub province {pid} is not in any state")
    for sid, state in sorted(states.items()):
        for pid, levels in state["province_buildings"].items():
            if levels.get("supply_node", 0) <= 0 or pid not in set(state["provinces"]):
                continue
            if pid not in listed:
                errors.append(
                    f"[supply] {state['file']} state {sid}: supply_node on province {pid} is not listed in {supply_path.name}"
                )

    print(f"states={len(states)} buildings={buildings_path.name} supply={supply_path.name}")
    tally: dict[str, int] = defaultdict(int)
    for line in errors:
        kind = line.split("]", 1)[0].lstrip("[") if line.startswith("[") else "other"
        tally[kind] += 1
    print("tally " + " ".join(f"{key}={tally[key]}" for key in sorted(tally)))
    print(f"errors={len(errors)} notes={len(notes)}")
    for line in errors:
        print("ERROR", line)
    for line in notes:
        print("NOTE", line)
    if errors:
        print("FAIL")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
