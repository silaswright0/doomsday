"""Split vanilla map lumps that MapChart shows as one state but 2026 owns separately.

1082 Balta (UKR) from 834 Tiraspol (MOL)
1083 Ceuta (SPR) from 290 Rif (MOR) — province 9945, shrunk to the northern tip
1097 Melilla (SPR) from 290 Rif (MOR) — province 12100, shrunk to the northern coastal tip
1084 Mayotte (FRA) from 708 Comoros — southeastern island blob of province 13072
1085 Gaza (HAM) from 454 Israel — province 4088
1086 West Bank (PAL) from 454 Israel — province 7107
1087 Northern Cyprus (NCY) from 183 Cyprus — province 11984
1088 Golan Heights (ISR) from 554 Damascus — province 1074
1089 South Lebanon (HEZ) from 553 Lebanon — province 11919
1090 US Virgin Islands (USA) from 686 Puerto Rico — 4155
1091 Martinique (FRA) from 694 — 177
1092 Saint Martin (FRA) from 694 — 13084
1093 Dominica (DMA) from 308 — 7123
1094 Saint Lucia (STL) from 692 — 13009
1095 Saint Vincent (SVG) from 692 — 379
1096 Grenada (GND) from 692 — 11106
1098 Srem (SER) from 109 Croatia — province 11580 (Novi Sad–Belgrade rail)
1099 Iraqi Kurdistan (KUR) from 676 Mosul — Erbil, Duhok, Sulaymaniyah
1100 Rojava (ROJ) from 680 Deir-az-Zur — Qamishli, Kobani, east Jazira
1101 South Ossetia (SOS) from 231 Georgia — province 9626
1102 Marib (YEM) from 293 North Yemen — 4924
1103 Suwayda (DRZ) from 554 Damascus — 4486
1104 Peace Spring (SNA) from 1100 Rojava — 1578 1634
1105 Puntland (PNT) from 559 Somalia — 1966 10891 4909
1106 Jilib (SHB) from 844 Jubaland — 11014
1107 Goma (M23) from 890 Costermansville — 1181
1108 Nakhchivan (AZR) from 230 Armenia — 6997
1109 Panjshir (NRF) from 1005 Qataghan — 10781
1110 Lesotho (LES) from 719 Natal — 4556
1111 Eswatini (SWZ) from 719 Natal — 7900
Transnistria 834 keeps 741 754 9576 9423 (Moldova-border tile, not 9435) and is thinned on the bmp
"""
from __future__ import annotations

import shutil
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VANILLA_MAP = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV") / "map"
MOD_MAP = ROOT / "map"

MAYOTTE_PROV = 13414
MAYOTTE_RGB = (12, 244, 198)
COMOROS_RGB = (255, 61, 130)
# Vanilla 9945 is a 95-pixel lump. Keep the northern Strait tip as Ceuta;
# leftover pixels go to Rif 10113 (Morocco).
CEUTA_RGB = (131, 12, 29)
CEUTA_HINTERLAND_RGB = (131, 192, 59)  # 10113
CEUTA_MAX_PIXELS = 18
MELILLA_RGB = (173, 210, 62)
MELILLA_HINTERLAND_RGB = (89, 204, 61)  # 7215 Rif leftover
MELILLA_MAX_PIXELS = 18
# Transnistria strip: keep Moldova-facing pixels of 741/754/9576/9423.
PMR_PROVS = {741, 754, 9576, 9423}
MOL_PROVS = {414, 565, 3407, 3577, 3707, 3724, 6600, 9683, 11686, 11705}
PMR_HINTERLAND_RGB = {
    741: (129, 165, 54),   # 9714 Odessa
    754: (129, 165, 54),   # 9714 Odessa
    9576: (45, 177, 148),  # 3757 Balta
    9423: (128, 30, 54),   # 9435 Vinnytsia
}
PMR_MAX_PIXELS = 200
PMR_BBOX = (3238, 3282, 548, 605)
MELILLA_BBOX = (2750, 2774, 806, 828)


def _copy_if_needed(name: str) -> Path:
    dest = MOD_MAP / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = VANILLA_MAP / name
    if not dest.exists():
        shutil.copy2(src, dest)
    return dest


def _definition_has_mayotte(path: Path) -> bool:
    return path.exists() and f"{MAYOTTE_PROV};" in path.read_text(encoding="utf-8", errors="ignore")


def _load_rgb_ids(definition: Path) -> dict[tuple[int, int, int], int]:
    out: dict[tuple[int, int, int], int] = {}
    for line in definition.read_text(encoding="utf-8", errors="ignore").splitlines():
        p = line.split(";")
        if len(p) < 4:
            continue
        try:
            out[(int(p[1]), int(p[2]), int(p[3]))] = int(p[0])
        except ValueError:
            continue
    return out


def shrink_ceuta_pixels(bmp_path: Path) -> None:
    """Keep only the northern tip of 9945 as Spanish Ceuta."""
    im = Image.open(bmp_path)
    px = im.load()
    w, h = im.size
    pts = [(x, y) for y in range(h) for x in range(w) if px[x, y][:3] == CEUTA_RGB]
    if len(pts) <= CEUTA_MAX_PIXELS:
        return
    min_y = min(y for _, y in pts)
    # Northern 3 rows (~12 px) are the Strait peninsula. Rest is Moroccan hinterland.
    keep = {(x, y) for x, y in pts if y <= min_y + 2}
    if not keep:
        return
    for x, y in pts:
        if (x, y) not in keep:
            px[x, y] = CEUTA_HINTERLAND_RGB
    im.save(bmp_path)


def shrink_melilla_pixels(bmp_path: Path) -> None:
    """Keep only the northern coastal tip of 12100 as Spanish Melilla."""
    im = Image.open(bmp_path)
    px = im.load()
    x0, x1, y0, y1 = MELILLA_BBOX
    pts = [
        (x, y)
        for y in range(y0, y1 + 1)
        for x in range(x0, x1 + 1)
        if px[x, y][:3] == MELILLA_RGB
    ]
    if len(pts) <= MELILLA_MAX_PIXELS:
        return
    min_y = min(y for _, y in pts)
    keep = {(x, y) for x, y in pts if y <= min_y + 2}
    if len(keep) > MELILLA_MAX_PIXELS:
        # Same target size as Ceuta: northern rows, sea-facing first.
        ranked = sorted(keep, key=lambda p: (p[1], p[0]))
        keep = set(ranked[:MELILLA_MAX_PIXELS])
    if not keep:
        return
    for x, y in pts:
        if (x, y) not in keep:
            px[x, y] = MELILLA_HINTERLAND_RGB
    im.save(bmp_path)


def thin_transnistria_pixels(bmp_path: Path, definition: Path) -> None:
    """Keep a thin Moldova-facing Dniester strip; leftover pixels go to Ukraine."""
    rgb_to_id = _load_rgb_ids(definition)
    im = Image.open(bmp_path)
    px = im.load()
    w, h = im.size
    x0, x1, y0, y1 = PMR_BBOX
    pmr_pts: dict[int, list[tuple[int, int]]] = {pid: [] for pid in PMR_PROVS}
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            pid = rgb_to_id.get(px[x, y][:3])
            if pid in PMR_PROVS:
                pmr_pts[pid].append((x, y))
    total = sum(len(v) for v in pmr_pts.values())
    if total <= PMR_MAX_PIXELS:
        return
    pmr_set = {pt for pts in pmr_pts.values() for pt in pts}
    keep: set[tuple[int, int]] = set()
    for x, y in pmr_set:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                n = rgb_to_id.get(px[nx, ny][:3])
                if n in MOL_PROVS:
                    keep.add((x, y))
                    break
    # One-pixel grow so the four tiles stay a connected 2-wide ribbon.
    grown = set(keep)
    for x, y in keep:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in pmr_set:
                grown.add(n)
    keep = grown
    # Every PMR id must keep at least a handful of pixels.
    by_id = {pid: {pt for pt in pts if pt in keep} for pid, pts in pmr_pts.items()}
    for pid, pts in pmr_pts.items():
        if len(by_id[pid]) < 8:
            west = sorted(pts, key=lambda p: (p[0], p[1]))[:12]
            keep.update(west)
    for pid, pts in pmr_pts.items():
        hinter = PMR_HINTERLAND_RGB[pid]
        for x, y in pts:
            if (x, y) not in keep:
                px[x, y] = hinter
    im.save(bmp_path)


def split_mayotte_pixels(bmp_path: Path) -> None:
    im = Image.open(bmp_path)
    px = im.load()
    w, h = im.size
    pts = [(x, y) for y in range(h) for x in range(w) if px[x, y][:3] == COMOROS_RGB]
    if not pts:
        return
    remaining = set(pts)
    comps: list[list[tuple[int, int]]] = []
    while remaining:
        start = next(iter(remaining))
        q = deque([start])
        remaining.remove(start)
        comp = [start]
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                n = (x + dx, y + dy)
                if n in remaining:
                    remaining.remove(n)
                    q.append(n)
                    comp.append(n)
        comps.append(comp)
    # Southeastern island on MapChart / vanilla bmp is Mayotte.
    mayotte = max(comps, key=lambda c: (sum(p[0] for p in c) / len(c), sum(p[1] for p in c) / len(c)))
    for x, y in mayotte:
        px[x, y] = MAYOTTE_RGB
    im.save(bmp_path)


def drop_building_state(buildings: Path, state_id: int) -> None:
    """Remove every buildings.txt row for a retired or reused state id."""
    lines = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
    kept = [line for line in lines if not line.startswith(f"{state_id};")]
    if len(kept) != len(lines):
        buildings.write_text("\n".join(kept) + "\n", encoding="utf-8")


def drop_building_province(buildings: Path, state_id: int, province: int) -> None:
    """Remove spawn rows for a province that left this state (coastal hang if stale)."""
    text = buildings.read_text(encoding="utf-8", errors="ignore")
    kept = []
    changed = False
    for line in text.splitlines():
        parts = line.split(";")
        if parts and parts[0] == str(state_id) and parts[-1] == str(province):
            changed = True
            continue
        kept.append(line)
    if changed:
        buildings.write_text("\n".join(kept) + "\n", encoding="utf-8")


def clone_building_state(buildings: Path, src_id: int, dst_id: int, extra: list[str] | None = None) -> None:
    text = buildings.read_text(encoding="utf-8", errors="ignore")
    if f"\n{dst_id};" in text or text.startswith(f"{dst_id};"):
        return
    cloned = []
    for line in text.splitlines():
        if line.startswith(f"{src_id};"):
            cloned.append(f"{dst_id};" + line.split(";", 1)[1])
    if extra:
        cloned.extend(extra)
    if cloned:
        buildings.write_text(text + "\n" + "\n".join(cloned) + "\n", encoding="utf-8")


def patch_unitstacks(path: Path) -> None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if text.startswith(f"{MAYOTTE_PROV};") or f"\n{MAYOTTE_PROV};" in text:
        return
    extra = []
    for line in text.splitlines():
        if line.startswith("13072;"):
            parts = line.split(";")
            # 13072;type;x;y;z;rot;scale  — Mayotte is SE of the combined blob.
            if len(parts) >= 5:
                try:
                    parts[2] = f"{float(parts[2]) + 16:.2f}"
                    parts[4] = f"{float(parts[4]) - 9:.2f}"
                except ValueError:
                    pass
            parts[0] = str(MAYOTTE_PROV)
            extra.append(";".join(parts))
    if extra:
        path.write_text(text + "\n" + "\n".join(extra) + "\n", encoding="utf-8")


def patch_strategic_region() -> None:
    rel = Path("strategicregions") / "102-East African Coast.txt"
    dest = MOD_MAP / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    src = VANILLA_MAP / rel
    if not dest.exists():
        shutil.copy2(src, dest)
    text = dest.read_text(encoding="utf-8", errors="ignore")
    if str(MAYOTTE_PROV) in text:
        return
    dest.write_text(text.replace("13072 ", f"13072 {MAYOTTE_PROV} "), encoding="utf-8")


def ensure_map_splits() -> None:
    MOD_MAP.mkdir(parents=True, exist_ok=True)
    definition = _copy_if_needed("definition.csv")
    buildings = _copy_if_needed("buildings.txt")
    unitstacks = _copy_if_needed("unitstacks.txt")
    bmp = _copy_if_needed("provinces.bmp")

    if not _definition_has_mayotte(definition):
        split_mayotte_pixels(bmp)
        definition.write_text(
            definition.read_text(encoding="utf-8", errors="ignore").rstrip()
            + f"\n{MAYOTTE_PROV};{MAYOTTE_RGB[0]};{MAYOTTE_RGB[1]};{MAYOTTE_RGB[2]};land;true;plains;5\n",
            encoding="utf-8",
        )
        patch_unitstacks(unitstacks)

    shrink_ceuta_pixels(bmp)
    shrink_melilla_pixels(bmp)
    thin_transnistria_pixels(bmp, definition)

    patch_strategic_region()

    # Coastal spawn sets so CreateMapModes does not hang on the new states.
    clone_building_state(
        buildings,
        834,
        1082,
    )
    clone_building_state(
        buildings,
        118,
        1083,
        extra=[
            "1083;naval_base_spawn;2717.00;9.80;1242.00;-1.85;9945",
            "1083;floating_harbor;2695.00;9.50;1225.00;-3.87;9945",
        ],
    )
    drop_building_province(buildings, 1083, 12100)
    clone_building_state(
        buildings,
        118,
        1097,
        extra=[
            "1097;naval_base_spawn;2759.00;11.45;1230.00;-3.93;12100",
            "1097;floating_harbor;2768.00;9.50;1233.00;-3.93;12100",
        ],
    )
    clone_building_state(
        buildings,
        708,
        1084,
        extra=[
            f"1084;naval_base_spawn;3510.00;9.55;445.00;1.01;{MAYOTTE_PROV}",
            f"1084;floating_harbor;3516.00;9.50;440.00;-2.13;{MAYOTTE_PROV}",
        ],
    )
    clone_building_state(
        buildings,
        454,
        1085,
        extra=[
            "1085;naval_base_spawn;3338.00;9.50;1165.00;-2.36;4088",
            "1085;floating_harbor;3338.05;9.50;1172.95;0.79;4088",
        ],
    )
    clone_building_state(
        buildings,
        454,
        1086,
    )
    clone_building_state(
        buildings,
        183,
        1087,
        extra=[
            "1087;naval_base_spawn;3334.00;9.50;1234.00;-0.50;11984",
            "1087;floating_harbor;3334.00;9.50;1234.00;-0.50;11984",
        ],
    )
    clone_building_state(
        buildings,
        554,
        1088,
    )
    clone_building_state(
        buildings,
        553,
        1089,
        extra=[
            "1089;naval_base_spawn;3355.00;9.50;1197.00;-1.57;11919",
            "1089;floating_harbor;3353.00;9.50;1198.00;-1.57;11919",
        ],
    )
    clone_building_state(
        buildings,
        686,
        1090,
        extra=[
            "1090;naval_base_spawn;1794.00;9.50;1166.00;-1.50;4155",
            "1090;floating_harbor;1794.00;9.50;1166.00;-1.50;4155",
        ],
    )
    clone_building_state(
        buildings,
        694,
        1091,
        extra=[
            "1091;naval_base_spawn;1850.00;9.50;1104.00;-1.50;177",
            "1091;floating_harbor;1850.00;9.50;1104.00;-1.50;177",
        ],
    )
    clone_building_state(
        buildings,
        694,
        1092,
        extra=[
            "1092;naval_base_spawn;1818.00;9.50;1160.00;-1.50;13084",
            "1092;floating_harbor;1818.00;9.50;1160.00;-1.50;13084",
        ],
    )
    clone_building_state(
        buildings,
        308,
        1093,
        extra=[
            "1093;naval_base_spawn;1845.00;9.50;1116.00;-1.50;7123",
            "1093;floating_harbor;1845.00;9.50;1116.00;-1.50;7123",
        ],
    )
    clone_building_state(
        buildings,
        692,
        1094,
        extra=[
            "1094;naval_base_spawn;1851.00;9.50;1091.00;-1.50;13009",
            "1094;floating_harbor;1851.00;9.50;1091.00;-1.50;13009",
        ],
    )
    clone_building_state(
        buildings,
        692,
        1095,
        extra=[
            "1095;naval_base_spawn;1848.00;9.50;1079.00;-1.50;379",
            "1095;floating_harbor;1848.00;9.50;1079.00;-1.50;379",
        ],
    )
    clone_building_state(
        buildings,
        692,
        1096,
        extra=[
            "1096;naval_base_spawn;1840.00;9.50;1062.00;-1.50;11106",
            "1096;floating_harbor;1840.00;9.50;1062.00;-1.50;11106",
        ],
    )
    clone_building_state(
        buildings,
        109,
        1098,
    )
    clone_building_state(
        buildings,
        676,
        1099,
    )
    clone_building_state(
        buildings,
        680,
        1100,
    )
    clone_building_state(
        buildings,
        231,
        1101,
    )
    clone_building_state(buildings, 293, 1102)
    clone_building_state(buildings, 554, 1103)
    clone_building_state(buildings, 1100, 1104)
    clone_building_state(
        buildings,
        559,
        1105,
        extra=[
            "1105;naval_base_spawn;3585.48;9.50;841.83;0.22;1966",
            "1105;floating_harbor;3585.48;9.50;841.83;0.22;1966",
            "1105;naval_base_spawn;3605.86;9.50;800.63;-1.77;10891",
            "1105;floating_harbor;3605.86;9.50;800.63;-1.77;10891",
        ],
    )
    clone_building_state(buildings, 844, 1106)
    clone_building_state(buildings, 890, 1107)
    clone_building_state(buildings, 230, 1108)
    for stale_id in (1109, 1110, 1111, 1112, 1113, 1114, 1115, 1116):
        drop_building_state(buildings, stale_id)
    clone_building_state(buildings, 1005, 1109)
    clone_building_state(buildings, 719, 1110)
    clone_building_state(buildings, 719, 1111)


if __name__ == "__main__":
    ensure_map_splits()
    print("map splits ready")
