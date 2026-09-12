#!/usr/bin/env python3
"""Count land pixels per HOI4 state from provinces.bmp (area weight fallback).

This is the local stand-in for WorldPop zonal stats when the unconstrained
global raster is not in-tree. Pixel counts are deterministic and map-accurate.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_lib import DATA, ROOT, load_all_states  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import patch_doomsday_map as p  # noqa: E402


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    states = load_all_states()
    prov_to_state: dict[int, int] = {}
    for s in states:
        for pid in s["provinces"]:
            prov_to_state[pid] = s["id"]

    def_path = ROOT / "map" / "definition.csv"
    rgb_to_id, id_to_kind = p.load_definition_maps(def_path)
    bmp = ROOT / "map" / "provinces.bmp"
    print(f"loading {bmp} ...")
    im = Image.open(bmp)
    px = im.load()
    w, h = im.size
    counts: dict[int, int] = defaultdict(int)
    unknown = 0
    sea = 0
    for y in range(h):
        for x in range(w):
            rgb = px[x, y]
            if isinstance(rgb, int):
                continue
            pid = rgb_to_id.get(rgb[:3] if len(rgb) >= 3 else rgb)
            if pid is None:
                unknown += 1
                continue
            kind = id_to_kind.get(pid)
            if kind != "land":
                sea += 1
                continue
            sid = prov_to_state.get(pid)
            if sid is None:
                continue
            counts[sid] += 1
        if y % 200 == 0:
            print(f"  row {y}/{h}")

    payload = {
        "source": "map/provinces.bmp + map/definition.csv + history/states provinces={}",
        "width": w,
        "height": h,
        "unknown_rgb": unknown,
        "non_land_pixels": sea,
        "pixels_by_state": {str(k): int(v) for k, v in sorted(counts.items())},
    }
    out = DATA / "state_pixel_area.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    print(f"wrote {out} states_with_pixels={len(counts)}")


if __name__ == "__main__":
    main()
