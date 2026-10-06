# -*- coding: utf-8 -*-
from pathlib import Path
import re
from collections import defaultdict

text = Path(
    r"c:\Users\siwri\Documents\Paradox Interactive\Hearts of Iron IV\mod\doomsday\common\national_focus\usa.txt"
).read_text(encoding="utf-8")
blocks = re.findall(r"focus\s*=\s*\{(.*?)(?=\n\tfocus\s*=|\n\}\s*\Z)", text, re.S)
rows = []
for b in blocks:
    ids = re.search(r"id\s*=\s*(\S+)", b)
    xs = re.search(r"\nx\s*=\s*(-?\d+)", b)
    ys = re.search(r"\ny\s*=\s*(-?\d+)", b)
    if ids and xs and ys:
        rows.append((int(ys.group(1)), int(xs.group(1)), ids.group(1)))
rows.sort()
print("y range", rows[0][0], rows[-1][0], "count", len(rows))
byy = defaultdict(list)
for y, x, i in rows:
    byy[y].append((x, i))
for y in sorted(byy):
    items = sorted(byy[y])
    names = ", ".join(f"{x}:{i[4:]}" for x, i in items[:10])
    if len(items) > 10:
        names += " ..."
    print(f"y={y:3d} n={len(items):2d} x=[{items[0][0]}..{items[-1][0]}]  {names}")

# classify
print("\n--- likely post-election / late (y>=36) ---")
for y, x, i in rows:
    if y >= 36:
        print(f"  y={y} x={x} {i}")
print("\n--- likely CW (intro/cw in id or y>=48) ---")
for y, x, i in rows:
    if "cw_" in i or "intro_" in i or y >= 48:
        print(f"  y={y} x={x} {i}")
