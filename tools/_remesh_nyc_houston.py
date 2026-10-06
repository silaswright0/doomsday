# -*- coding: utf-8 -*-
"""Remesh NYC + Houston metro provinces.

NYC (left→right was 13421 | 3878 | 13422):
  merge two left, split that blob top/bottom by y.
  13421 = north half, 3878 = south half, 13422 = right unchanged.

Houston (left→right was 13425 | 10337 | 13426):
  merge two rightmost, split that blob top/bottom by y.
  13425 = left unchanged, 10337 = north half, 13426 = south half.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "map"


def load_def(path: Path):
    rgb_to_id = {}
    id_to_rgb = {}
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = ln.split(";")
        if len(parts) < 4:
            continue
        try:
            pid = int(parts[0])
            rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
        except ValueError:
            continue
        rgb_to_id[rgb] = pid
        id_to_rgb[pid] = rgb
    return rgb_to_id, id_to_rgb


def collect(px, w, h, rgb_to_id, pids: set[int]):
    pts: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for y in range(h):
        for x in range(w):
            pid = rgb_to_id.get(px[x, y][:3])
            if pid in pids:
                pts[pid].append((x, y))
    return pts


def split_by_y(pts: list[tuple[int, int]]):
    if len(pts) < 2:
        raise SystemExit(f"too few pixels to split: {len(pts)}")
    ys = sorted(p[1] for p in pts)
    mid = ys[len(ys) // 2]
    top, bot = [], []
    for p in pts:
        # smaller y = north (top of provinces.bmp)
        if p[1] < mid:
            top.append(p)
        else:
            bot.append(p)
    if not top or not bot:
        # fallback equal count split
        ordered = sorted(pts, key=lambda p: (p[1], p[0]))
        half = len(ordered) // 2
        top, bot = ordered[:half], ordered[half:]
    if not top or not bot:
        raise SystemExit("y-split produced empty half")
    return top, bot


def paint(px, pts, rgb):
    for x, y in pts:
        px[x, y] = rgb


def main() -> None:
    defn = MAP / "definition.csv"
    bmp = MAP / "provinces.bmp"
    rgb_to_id, id_to_rgb = load_def(defn)
    im = Image.open(bmp).convert("RGB")
    px = im.load()
    w, h = im.size

    # --- NYC ---
    nyc_ids = {13421, 3878, 13422}
    pts = collect(px, w, h, rgb_to_id, nyc_ids)
    for pid in nyc_ids:
        print(f"NYC {pid} before: {len(pts[pid])}")
    merged = pts[13421] + pts[3878]
    top, bot = split_by_y(merged)
    paint(px, top, id_to_rgb[13421])
    paint(px, bot, id_to_rgb[3878])
    # 13422 untouched
    print(f"NYC after: 13421(north)={len(top)} 3878(south)={len(bot)} 13422(right)={len(pts[13422])}")

    # --- Houston ---
    hou_ids = {13425, 10337, 13426}
    pts = collect(px, w, h, rgb_to_id, hou_ids)
    for pid in hou_ids:
        print(f"HOU {pid} before: {len(pts[pid])}")
    merged = pts[10337] + pts[13426]
    top, bot = split_by_y(merged)
    paint(px, top, id_to_rgb[10337])
    paint(px, bot, id_to_rgb[13426])
    # 13425 untouched
    print(f"HOU after: 13425(left)={len(pts[13425])} 10337(north)={len(top)} 13426(south)={len(bot)}")

    im.save(bmp)
    print("saved", bmp)


if __name__ == "__main__":
    main()
