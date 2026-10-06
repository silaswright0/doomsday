# -*- coding: utf-8 -*-
"""Tighten USA focus layout: pull post-election up; compact CW on the left."""
from __future__ import annotations

import re
from pathlib import Path

PATH = Path(
    r"c:\Users\siwri\Documents\Paradox Interactive\Hearts of Iron IV\mod\doomsday\common\national_focus\usa.txt"
)

POST_ELECTION_DY = -10
CW_DY = -11
CW_ROOT_OLD = [-28, -24, -20, -16, -12, -8, -4]
CW_ROOT_NEW = [-20, -17, -14, -11, -8, -5, -2]


def is_cw_focus(fid: str) -> bool:
    return (
        fid.startswith("USA_cw_")
        or fid.startswith("USA_intro_")
        or fid == "USA_recover"
    )


def remap_cw_x(x: int) -> int:
    for old, new in zip(CW_ROOT_OLD, CW_ROOT_NEW):
        if old <= x <= old + 2:
            return new + (x - old)
    return x + 8


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = re.sub(
        r"continuous_focus_position\s*=\s*\{\s*x\s*=\s*-?\d+\s*y\s*=\s*-?\d+\s*\}",
        "continuous_focus_position = { x = 20 y = 50 }",
        text,
        count=1,
    )

    # Walk focuses: for each id, the following x=/y= within ~12 lines belong to it.
    lines = text.splitlines(keepends=True)
    i = 0
    changed = 0
    while i < len(lines):
        m = re.match(r"\t\tid = (USA_\S+)\s*$", lines[i])
        if not m:
            i += 1
            continue
        fid = m.group(1)
        # look ahead for x and y
        x_idx = y_idx = None
        x_val = y_val = None
        for j in range(i + 1, min(i + 15, len(lines))):
            xm = re.match(r"\t\tx = (-?\d+)\s*$", lines[j])
            ym = re.match(r"\t\ty = (-?\d+)\s*$", lines[j])
            if xm and x_idx is None:
                x_idx, x_val = j, int(xm.group(1))
            if ym and y_idx is None:
                y_idx, y_val = j, int(ym.group(1))
            if x_idx is not None and y_idx is not None:
                break
            if lines[j].startswith("\tfocus") or lines[j].startswith("\tid"):
                break
        if x_idx is None or y_idx is None:
            i += 1
            continue

        nx, ny = x_val, y_val
        if is_cw_focus(fid):
            nx = remap_cw_x(x_val)
            ny = y_val + CW_DY
        elif y_val >= 32:
            ny = y_val + POST_ELECTION_DY

        if nx != x_val:
            lines[x_idx] = re.sub(r"-?\d+", str(nx), lines[x_idx], count=1)
            changed += 1
        if ny != y_val:
            lines[y_idx] = re.sub(r"-?\d+", str(ny), lines[y_idx], count=1)
            changed += 1
        i += 1

    PATH.write_text("".join(lines), encoding="utf-8", newline="\n")
    print(f"coordinate edits: {changed}")

    # summary
    text2 = "".join(lines)
    rows = []
    for m in re.finditer(r"id = (USA_\S+)", text2):
        chunk = text2[m.start() : m.start() + 200]
        xm = re.search(r"x = (-?\d+)", chunk)
        ym = re.search(r"y = (-?\d+)", chunk)
        if xm and ym:
            rows.append((int(ym.group(1)), int(xm.group(1)), m.group(1)))
    rows.sort()
    print("y range", rows[0][0], "->", rows[-1][0])
    print("elections:")
    for y, x, fid in rows:
        if "election_" in fid:
            print(f"  y={y} x={x} {fid}")
    print("CW roots/intros/recover:")
    for y, x, fid in rows:
        if is_cw_focus(fid) and (
            "root" in fid or "intro" in fid or fid == "USA_recover" or "late" in fid
        ):
            print(f"  y={y} x={x} {fid}")


if __name__ == "__main__":
    main()
