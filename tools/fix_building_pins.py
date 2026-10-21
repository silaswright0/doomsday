"""Place missing building meshes and supply-hub slots found by check_buildings.py.

Adds rows to the mod's map/buildings.txt on land the state still owns, and
lists history supply hubs in map/supply_nodes.txt. Existing rows are left
alone. Safe to run again: a building that already round-trips is skipped.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_buildings as cb  # noqa: E402
import patch_doomsday_map as pd  # noqa: E402

ROOT = cb.ROOT


def missing_meshes(states: dict, prov_to_state: dict, pins: cb.MapPins) -> list[tuple[int, str, int]]:
    needed: list[tuple[int, str, int]] = []
    for sid, state in sorted(states.items()):
        for history_key, map_types in cb.SLOTTED.items():
            level = state["levels"].get(history_key, 0)
            if level <= 0:
                continue
            found: list[int | None] = []
            for map_type in map_types:
                found.extend(pins.rows.get((sid, map_type), []))
            if cb.on_state(found, prov_to_state, sid):
                continue
            needed.append((sid, map_types[0], level))
        for history_key, map_types in cb.SINGLE_PIN.items():
            level = state["levels"].get(history_key, 0)
            if level <= 0:
                continue
            found = []
            for map_type in map_types:
                found.extend(pins.rows.get((sid, map_type), []))
            if cb.on_state(found, prov_to_state, sid):
                continue
            needed.append((sid, map_types[0], 1))
    return needed


def missing_hubs(states: dict, listed: set[int]) -> list[int]:
    hubs: list[int] = []
    seen: set[int] = set()
    for state in states.values():
        owned = set(state["provinces"])
        for pid, levels in state["province_buildings"].items():
            if levels.get("supply_node", 0) <= 0 or pid not in owned or pid in listed or pid in seen:
                continue
            seen.add(pid)
            hubs.append(pid)
    return hubs


def safe_sites(
    sid: int,
    provinces: list[int],
    pixels: dict[int, list[tuple[int, int]]],
    image_px,
    w: int,
    h: int,
    rgb_to_id: dict,
    id_to_kind: dict,
    prov_to_state: dict[int, int],
) -> list[tuple[int, int, bool]]:
    """Bmp pixels that trunc-sample back onto this state's land. Coastal first."""
    sites: list[tuple[int, int, bool]] = []
    for pid in provinces:
        for x, y in pixels.get(pid, []):
            xz = pd._to_xz(x, y, h)
            got = pd._province_at(image_px, xz[0], xz[1], h, rgb_to_id, w, h)
            if got is None or id_to_kind.get(got) != "land" or prov_to_state.get(got) != sid:
                continue
            coastal = False
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    nid = rgb_to_id.get(image_px[nx, ny][:3])
                    if nid is not None and id_to_kind.get(nid) == "sea":
                        coastal = True
                        break
            sites.append((x, y, coastal))
    return sites


def take_sites(sites: list[tuple[int, int, bool]], count: int, coastal: bool, cursor: int) -> tuple[list[tuple[int, int]], int]:
    pool = [s for s in sites if s[2]] if coastal else sites
    if coastal and not pool:
        pool = sites
    if not pool:
        return [], cursor
    picked: list[tuple[int, int]] = []
    for _ in range(count):
        x, y, _sea = pool[cursor % len(pool)]
        cursor += max(1, len(pool) // max(count, 1))
        picked.append((x, y))
    return picked, cursor


def main() -> int:
    states: dict[int, dict] = {}
    for path in sorted((ROOT / "history" / "states").glob("*.txt")):
        parsed = cb.parse_state(path)
        if parsed is not None:
            states[parsed["id"]] = parsed
    prov_to_state: dict[int, int] = {}
    for sid, state in states.items():
        for pid in state["provinces"]:
            prov_to_state.setdefault(pid, sid)

    print("loading map ...")
    image = Image.open(cb.map_file("provinces.bmp"))
    rgb_to_id, id_to_kind = cb.load_definition(cb.map_file("definition.csv"))
    pins = cb.MapPins(image, rgb_to_id, id_to_kind)
    buildings_path = ROOT / "map" / "buildings.txt"
    for line in buildings_path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split(";")
        if len(parts) < 5:
            continue
        try:
            sid = int(parts[0])
        except ValueError:
            continue
        tagged = None
        if len(parts) >= 7:
            try:
                tagged = int(parts[6])
            except ValueError:
                tagged = None
        pins.add_row(sid, parts[1], parts[2], parts[4], tagged)

    needed = missing_meshes(states, prov_to_state, pins)
    wanted: set[int] = set()
    for sid, _kind, _level in needed:
        wanted.update(states[sid]["provinces"])
    print(f"indexing land for {len(wanted)} provinces ...")
    pixels = pd.index_province_pixels(image, rgb_to_id, wanted) if wanted else {}
    image_px = image.load()
    w, h = image.size

    rows: list[str] = []
    by_state: dict[int, list[tuple[int, int, bool]]] = {}
    cursors: dict[int, int] = {}
    for sid, kind, level in needed:
        if sid not in by_state:
            by_state[sid] = safe_sites(
                sid,
                states[sid]["provinces"],
                pixels,
                image_px,
                w,
                h,
                rgb_to_id,
                id_to_kind,
                prov_to_state,
            )
            cursors[sid] = 0
        sites, cursors[sid] = take_sites(by_state[sid], level, kind == "dockyard", cursors[sid])
        if not sites:
            print(f"warning: state {sid} has no land pixel for {kind}")
            continue
        for x, y in sites:
            bx, bz = pd._to_xz(x, y, h)
            rows.append(f"{sid};{kind};{bx};9.50;{bz};0.00;0")
    if rows:
        pd.append_building_lines(buildings_path, rows)
    print(f"added {len(rows)} building rows across {len(needed)} missing levels")

    supply_dest = ROOT / "map" / "supply_nodes.txt"
    if not supply_dest.exists():
        shutil.copyfile(cb.VANILLA_MAP / "supply_nodes.txt", supply_dest)
    listed = cb.load_supply_nodes(supply_dest)
    hubs = missing_hubs(states, listed)
    if hubs:
        text = supply_dest.read_text(encoding="utf-8", errors="replace")
        if text and not text.endswith("\n"):
            text += "\n"
        text += "".join(f"1 {pid}\n" for pid in hubs)
        supply_dest.write_text(text, encoding="utf-8", newline="\n")
    print(f"added {len(hubs)} supply hub provinces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
