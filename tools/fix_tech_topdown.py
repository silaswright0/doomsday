#!/usr/bin/env python3
"""Fix doomsday tech trees to top-down timeline layout.

HOI4 gridbox format="LEFT" maps folder x→vertical and y→horizontal.
Our generator stored column in x and year in y, so trees ran left-to-right
against vertical year labels. format="UP" maps x→horizontal, y→vertical.

Branch roots get a gridbox at the absolute pixel. Children use the parent's
gridbox via path, with folder positions relative to the root (0, dy).
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TECH_DIR = ROOT / "common" / "technologies"
GUI = ROOT / "interface" / "countrytechtreeview.gui"

FOLDERS = {
    "infantry": ["infantry_folder"],
    "support": ["support_folder"],
    "armor": ["armour_folder", "nsb_armour_folder"],
    "artillery": ["artillery_folder"],
    "air": ["air_techs_folder", "bba_air_techs_folder"],
    "naval": ["naval_folder", "mtgnavalfolder"],
    "naval_parts": ["mtgnavalsupportfolder", "naval_folder"],
    "electronics": ["electronics_folder"],
    "industry": ["industry_folder"],
}

# Pixels: columns across, years down. Slot height matches year-label step.
# Equipment icons are ~110–120px wide; keep clear padding between columns.
COL_PX = 175
YEAR_ORIGIN = 90
YEAR_STEP = 100  # px per 5-year band
SLOT = 70
# Left pad — shift right (never left) so trees stay centered with wider columns.
COL_ORIGIN = 240
YEAR_LABEL_X = 40

# Per-tree overrides: (col_origin, col_px).
# Wider col_px keeps column 0 fixed and nudges later columns right.
# Higher col_origin shifts the whole tree right (ship hulls).
LAYOUT: dict[str, tuple[int, int]] = {
    "infantry": (240, 205),   # small arms
    "armor": (240, 205),      # tanks
    "artillery": (240, 205),
    "air": (240, 205),        # aircraft
    "naval": (450, 360),      # ship hulls — 360px between columns
}

# Extra gap inserted starting at this column index (that column and all to its right).
# tree_id -> (from_col_index, extra_px)
COL_GAP_BEFORE: dict[str, tuple[int, int]] = {
    "armor": (2, 120),  # Airborne light (dd_lt_2) and everything right of it
}


def tree_layout(tid: str) -> tuple[int, int]:
    return LAYOUT.get(tid, (COL_ORIGIN, COL_PX))


def col_x(tid: str, col: int) -> int:
    origin, step = tree_layout(tid)
    px = origin + col * step
    gap = COL_GAP_BEFORE.get(tid)
    if gap is not None:
        from_col, extra = gap
        if col >= from_col:
            px += extra
    return px


def year_index(year: int) -> int:
    return max(0, (int(year) - 1955) // 5)


def parse_tech_file(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    techs: dict[str, dict] = {}
    for m in re.finditer(r"\n\t([a-z0-9_]+) = \{", text):
        name = m.group(1)
        start = m.end() - 1
        depth = 0
        i = start
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    body = text[start + 1 : i]
                    year_m = re.search(r"start_year = (\d+)", body)
                    leads = re.findall(r"leads_to_tech = ([a-z0-9_]+)", body)
                    folder_m = re.search(
                        r"folder = \{\s*name = (\w+)\s*position = \{ x = (-?\d+) y = (-?\d+) \}",
                        body,
                    )
                    techs[name] = {
                        "year": int(year_m.group(1)) if year_m else 1955,
                        "leads": leads,
                        "has_folder": folder_m is not None,
                        "body_start": start,
                        "body_end": i,
                        "body": body,
                    }
                    break
            i += 1
    return techs


def column_roots(techs: dict[str, dict]) -> dict[str, str]:
    """Map each visible tech → its branch-root id (first visible ancestor with folder)."""
    parents: dict[str, str] = {}
    for tid, t in techs.items():
        for child in t["leads"]:
            parents.setdefault(child, tid)

    def root_of(tid: str) -> str:
        seen = set()
        cur = tid
        while cur in parents and cur not in seen:
            seen.add(cur)
            p = parents[cur]
            if not techs.get(p, {}).get("has_folder"):
                # parent is floor/hidden — cur is the visible root
                return cur
            cur = p
        return cur

    return {tid: root_of(tid) for tid, t in techs.items() if t["has_folder"]}


def assign_columns(techs: dict[str, dict], roots: dict[str, str]) -> dict[str, int]:
    """Stable column index per branch root, ordered by min year then name."""
    root_ids = sorted(
        set(roots.values()),
        key=lambda r: (techs[r]["year"], r),
    )
    return {r: i for i, r in enumerate(root_ids)}


def rewrite_tech_folders(path: Path, techs: dict[str, dict], roots: dict[str, str], col_of: dict[str, int]) -> None:
    text = path.read_text(encoding="utf-8")
    pieces: list[str] = []
    cursor = 0
    # Process in file order using original spans.
    ordered = sorted(
        ((tid, t) for tid, t in techs.items() if t["has_folder"]),
        key=lambda kv: kv[1]["body_start"],
    )
    for tid, t in ordered:
        root = roots[tid]
        dy = year_index(t["year"]) - year_index(techs[root]["year"])
        new_body = re.sub(
            r"(folder = \{\s*name = \w+\s*)position = \{ x = -?\d+ y = -?\d+ \}",
            rf"\1position = {{ x = 0 y = {dy} }}",
            t["body"],
        )
        abs_start = t["body_start"]
        abs_end = t["body_end"]
        pieces.append(text[cursor : abs_start + 1])
        pieces.append(new_body)
        pieces.append("}")
        cursor = abs_end + 1
    pieces.append(text[cursor:])
    path.write_text("".join(pieces), encoding="utf-8")


def year_labels(folder: str) -> list[str]:
    lines = []
    for y in range(1955, 2040, 5):
        py = YEAR_ORIGIN + year_index(y) * YEAR_STEP
        lines.append(
            f'\t\t\tinstantTextBoxType = {{ name = "dd_yr_{folder}_{y}" '
            f"position = {{ x = {YEAR_LABEL_X} y = {py} }} textureFile = \"\" font = \"hoi_22tech\" "
            f'borderSize = {{ x = 0 y = 0 }} text = "{y}" maxWidth = 48 maxHeight = 24 '
            f'format = left Orientation = "UPPER_LEFT" }}'
        )
    return lines


def rebuild_gui(all_trees: dict[str, dict[str, dict]]) -> None:
    """all_trees: tree_id -> techs dict"""
    text = GUI.read_text(encoding="utf-8")
    text = re.sub(
        r"\n\t\t\t# DD_TECH_GRID_START.*?# DD_TECH_GRID_END\n",
        "\n",
        text,
        flags=re.S,
    )

    by_folder: dict[str, list[str]] = defaultdict(list)
    for tid, techs in all_trees.items():
        roots = column_roots(techs)
        col_of = assign_columns(techs, roots)
        origin, step = tree_layout(tid)
        # One gridbox per branch root only.
        for root, col in sorted(col_of.items(), key=lambda kv: kv[1]):
            t = techs[root]
            px = col_x(tid, col)
            py = YEAR_ORIGIN + year_index(t["year"]) * YEAR_STEP
            box = (
                f'\t\t\tgridboxtype = {{ name = "{root}_tree" '
                f"position = {{ x = {px} y = {py} }} "
                f'slotsize = {{ width = {SLOT} height = {YEAR_STEP} }} format = "UP" }}'
            )
            for folder in FOLDERS[tid]:
                by_folder[folder].append(box)
        last_col = max(col_of.values()) if col_of else 0
        print(f"  {tid} col0={origin} step={step} cols={len(col_of)} last_x={col_x(tid, last_col)}")

    for folder, boxes in by_folder.items():
        marker = f'name = "{folder}"'
        idx = text.find(marker)
        if idx < 0:
            print("missing folder", folder)
            continue
        insert_at = text.find("gridboxtype", idx)
        if insert_at < 0:
            insert_at = text.find("gridboxType", idx)
        if insert_at < 0:
            print("no gridbox in", folder)
            continue
        # Widen canvas for tall timeline
        # (stripes size patched below globally)
        block = (
            "\n\t\t\t# DD_TECH_GRID_START\n"
            + "\n".join(year_labels(folder) + boxes)
            + "\n\t\t\t# DD_TECH_GRID_END\n\t\t\t"
        )
        text = text[:insert_at] + block + text[insert_at:]

    # Tall enough for 1955→2035; wide enough for denser / right-shifted trees
    for old, new in (
        ("width = 1600 height = 2000", "width = 2800 height = 2000"),
        ("width = 1800 height = 2000", "width = 2800 height = 2000"),
        ("width = 2000 height = 2000", "width = 2800 height = 2000"),
        ("width = 2200 height = 2000", "width = 2800 height = 2000"),
        ("width = 2400 height = 2000", "width = 2800 height = 2000"),
        ("width = 2600 height = 2000", "width = 3000 height = 2000"),
        ("width = 1800 height = 2100", "width = 2800 height = 2000"),
        ("width = 2000 height = 2100", "width = 2800 height = 2000"),
        ("width = 2240 height = 2100", "width = 2800 height = 2000"),
        ("width = 2500 height = 2100", "width = 3000 height = 2000"),
        ("width=1600 height=2000", "width=2800 height=2000"),
        ("width=1800 height=2100", "width=2800 height=2000"),
        ("width=2400 height=2000", "width=2800 height=2000"),
    ):
        text = text.replace(old, new)

    GUI.write_text(text, encoding="utf-8")
    print("wrote", GUI)


def main() -> None:
    all_trees: dict[str, dict[str, dict]] = {}
    for tid in FOLDERS:
        path = TECH_DIR / f"dd_{tid}.txt"
        if not path.exists():
            print("skip missing", path.name)
            continue
        techs = parse_tech_file(path)
        roots = column_roots(techs)
        col_of = assign_columns(techs, roots)
        print(f"{tid}: {len(techs)} techs, {len(col_of)} columns")
        rewrite_tech_folders(path, techs, roots, col_of)
        # re-parse after rewrite
        all_trees[tid] = parse_tech_file(path)

    rebuild_gui(all_trees)

    # Spot-check infantry mech chain
    inf = all_trees["infantry"]
    roots = column_roots(inf)
    for tid in ["dd_mech_2", "dd_mech_3", "dd_mech_4", "dd_mech_5"]:
        t = inf[tid]
        m = re.search(r"position = \{ x = (-?\d+) y = (-?\d+) \}", t["body"])
        print(f"  {tid} root={roots[tid]} folder=({m.group(1)},{m.group(2)}) year={t['year']}")


if __name__ == "__main__":
    main()
