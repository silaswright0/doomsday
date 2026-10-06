# -*- coding: utf-8 -*-
"""Fix HOI4 map crash after NYC/LA/Houston/RI splits: retag buildings, add ports."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from PIL import Image  # noqa: E402
import patch_doomsday_map as p  # noqa: E402

# Provinces carved into new metro/RI states (retag buildings whose pixel lands here).
MOVED = {
    859,
    3878,
    3906,
    9814,
    10337,
    11830,
    13421,
    13422,
    13423,
    13424,
    13425,
    13426,
}

# Log: "coastal but has no port building in the nudger. This will likely crash"
CRASH_PORTS = {
    859,
    3878,
    3906,
    9814,
    11830,
    13421,
    13422,
    13423,
    13424,
    13426,
}

SITE_STATES = {1125, 1126, 1136, 1138, 1139, 1140}


def load_prov_to_state() -> dict[int, int]:
    out: dict[int, int] = {}
    for path in (ROOT / "history" / "states").glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"id\s*=\s*(\d+)", text)
        if not m:
            continue
        sid = int(m.group(1))
        pm = re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S)
        if not pm:
            continue
        for tok in re.findall(r"\d+", pm.group(1)):
            out[int(tok)] = sid
    return out


def collect_pixels(px, w: int, h: int, rgb_to_id: dict) -> dict[int, list[tuple[int, int]]]:
    pixels: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for y in range(h):
        for x in range(w):
            pid = rgb_to_id.get(px[x, y][:3])
            if pid is not None:
                pixels[pid].append((x, y))
    return pixels


def main() -> None:
    buildings = ROOT / "map" / "buildings.txt"
    prov_to_state = load_prov_to_state()
    state_provs: dict[int, list[int]] = defaultdict(list)
    for pid, sid in prov_to_state.items():
        state_provs[sid].append(pid)

    print("loading provinces.bmp...")
    im = Image.open(ROOT / "map" / "provinces.bmp")
    px = im.load()
    w, h = im.size
    rgb_to_id, id_to_kind = p.load_definition_maps(ROOT / "map" / "definition.csv")

    # Drop trailing blank / short rows (invalid arguments at EOF).
    p._strip_blank_building_lines(buildings)

    # Drop bogus RI naval spawns tagged to New England province 8518.
    lines = [
        ln
        for ln in buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
        if not (
            ln.startswith("1136;naval_base_spawn;")
            and ln.rstrip().endswith(";8518")
        )
    ]
    p.write_buildings_txt(buildings, lines)

    n = p.retag_buildings_by_province(
        buildings, px, h, w, h, rgb_to_id, id_to_kind, prov_to_state, MOVED
    )
    print(f"retagged building rows: {n}")

    print("indexing land pixels for metro provinces...")
    # Only scan bbox around US east/west coast metros for speed.
    want = set(MOVED)
    pixels: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for y in range(h):
        for x in range(w):
            pid = rgb_to_id.get(px[x, y][:3])
            if pid in want:
                pixels[pid].append((x, y))
    for pid in sorted(want):
        print(f"  province {pid}: {len(pixels.get(pid, []))} pixels -> state {prov_to_state.get(pid)}")

    # Place missing crash ports.
    have_ports: set[int] = set()
    kept: list[str] = []
    for line in buildings.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split(";")
        if len(parts) != 7:
            if line.strip():
                kept.append(line)
            continue
        if parts[1] == "naval_base_spawn":
            try:
                tag = int(parts[6])
            except ValueError:
                kept.append(line)
                continue
            pixel_pid = p._province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
            if tag in CRASH_PORTS and (pixel_pid != tag or id_to_kind.get(pixel_pid) != "land"):
                continue  # drop invalid crash-port rows
            if pixel_pid == tag and tag in CRASH_PORTS:
                have_ports.add(tag)
        kept.append(line)

    add: list[str] = []
    for pid in sorted(CRASH_PORTS):
        if pid in have_ports:
            continue
        sid = prov_to_state.get(pid)
        pts = pixels.get(pid, [])
        if sid is None or not pts:
            print(f"ERROR: cannot place port on {pid}")
            continue
        ix, iy = p._interior_pixel(pts, px, w, h, rgb_to_id, pid)
        sea = p._find_sea_touch(pts, px, w, h, rgb_to_id, id_to_kind)
        if sea is not None and rgb_to_id.get(px[sea[0], sea[1]][:3]) == pid:
            ix, iy = sea
        x, z = p._to_xz(ix, iy, h)
        if p._province_at(px, x, z, h, rgb_to_id, w, h) != pid:
            ix, iy = p._interior_pixel(pts, px, w, h, rgb_to_id, pid)
            x, z = p._to_xz(ix, iy, h)
        add.append(f"{sid};naval_base_spawn;{x};9.50;{z};0.00;{pid}")
        have_ports.add(pid)
        print(f"  +port state {sid} province {pid} @ {x},{z}")

    # Ensure air_base + rocket_site_spawn land inside each metro state.
    have_sites: dict[int, set[str]] = defaultdict(set)
    for line in kept + add:
        parts = line.split(";")
        if len(parts) < 5:
            continue
        try:
            sid = int(parts[0])
        except ValueError:
            continue
        if sid not in SITE_STATES:
            continue
        pixel_pid = p._province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
        if (
            pixel_pid is not None
            and id_to_kind.get(pixel_pid) == "land"
            and prov_to_state.get(pixel_pid) == sid
        ):
            have_sites[sid].add(parts[1])

    for sid in sorted(SITE_STATES):
        xz = None
        for pid in state_provs.get(sid, []):
            pts = pixels.get(pid) or []
            if not pts:
                # fall back: scan full map for this one province if not in MOVED
                continue
            ix, iy = p._interior_pixel(pts, px, w, h, rgb_to_id, pid)
            xz = p._to_xz(ix, iy, h)
            break
        if xz is None:
            # gather pixels for any state province
            for pid in state_provs.get(sid, []):
                if pid not in pixels:
                    # quick full scan for this province only — expensive but rare
                    for y in range(h):
                        for x in range(w):
                            if rgb_to_id.get(px[x, y][:3]) == pid:
                                pixels[pid].append((x, y))
                if pixels.get(pid):
                    ix, iy = p._interior_pixel(pixels[pid], px, w, h, rgb_to_id, pid)
                    xz = p._to_xz(ix, iy, h)
                    break
        if xz is None:
            print(f"warning: no land for state {sid} sites")
            continue
        x, z = xz
        land_pid = p._province_at(px, x, z, h, rgb_to_id, w, h) or 0
        for kind in ("air_base", "rocket_site_spawn"):
            if kind not in have_sites[sid]:
                add.append(f"{sid};{kind};{x};9.50;{z};0.00;{land_pid}")
                have_sites[sid].add(kind)
                print(f"  +{kind} state {sid}")

    # Snap existing site rows for SITE_STATES onto their own land.
    out: list[str] = []
    snapped = 0
    for line in kept:
        parts = line.split(";")
        if len(parts) != 7:
            out.append(line)
            continue
        try:
            sid = int(parts[0])
        except ValueError:
            out.append(line)
            continue
        if sid not in SITE_STATES or parts[1] in {"naval_base_spawn", "floating_harbor"}:
            out.append(line)
            continue
        pixel_pid = p._province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
        if (
            pixel_pid is not None
            and id_to_kind.get(pixel_pid) == "land"
            and prov_to_state.get(pixel_pid) == sid
        ):
            out.append(line)
            continue
        # move onto state land
        xz = None
        for pid in state_provs.get(sid, []):
            pts = pixels.get(pid, [])
            if pts:
                ix, iy = p._interior_pixel(pts, px, w, h, rgb_to_id, pid)
                xz = p._to_xz(ix, iy, h)
                break
        if xz is None:
            out.append(line)
            continue
        parts[2], parts[4] = xz
        out.append(";".join(parts))
        snapped += 1
    out.extend(add)
    p.write_buildings_txt(buildings, out)
    print(f"snapped site rows: {snapped}; added rows: {len(add)}")

    # Verify crash ports exist and sample correctly.
    missing = []
    for line in buildings.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split(";")
        if len(parts) != 7 or parts[1] != "naval_base_spawn":
            continue
        try:
            tag = int(parts[6])
        except ValueError:
            continue
        if tag not in CRASH_PORTS:
            continue
        pid = p._province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
        sid = int(parts[0])
        ok = pid == tag and prov_to_state.get(tag) == sid
        print(f"verify port {tag}: pixel={pid} state={sid} ok={ok}")
        if ok:
            have_ports.add(tag)
    missing = sorted(CRASH_PORTS - have_ports)
    if missing:
        raise SystemExit(f"still missing ports: {missing}")
    print("OK: crash coastal ports present")


if __name__ == "__main__":
    main()
