"""Split vanilla map lumps that MapChart shows as one state but 2026 owns separately.

1082 Balta (UKR) from 192 Odessa — 3575 3757 9714 inland; leftover 192 is the Odessa coast
1083 Ceuta (SPR) from 290 Rif (MOR) — province 9945, Strait tip plus vanilla port pixel
1097 Melilla (SPR) from 290 Rif (MOR) — province 12100, shrunk to the northern coastal tip
1084 Mayotte (FRA) from 708 Comoros — southeastern island blob of province 13072
1085 Gaza (HAM) from 454 Israel — province 4088
1086 West Bank (PAL) from 454 Israel — province 7107
1087 Northern Cyprus (NCY) from 183 Cyprus — province 11984
1088 Golan Heights (ISR) from 554 Damascus — province 1074, western strip only (east painted to 7184)
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
1101 South Ossetia (SOE) from 231 Georgia — province 9626
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
1112 Guantanamo Bay (USA) from 315 Cuba — 7590, south-coast inlet (not Maisí)
1113 Azov Zaporizhzhia (UKR occupied by SOV) from 200 — Melitopol land bridge
1114 Left-Bank Kherson (UKR occupied by SOV) from 196 — Kakhovka / east bank
1120 Tel Aviv (ISR) from 454 — 1065 1201 4206; leftover 454 is Jerusalem/Negev
1121 Jonglei (SIO) from 884 — 10859 12800 Nasir/Akobo; leftover 884 is Juba 2096 and 10877
196 Kherson keeps 3755 574 9573 11715; leftover 197 Mykolaiv keeps 409 3403 6597 11546 11683
1115 Kramatorsk (UKR) from 227 — west Donetsk still Ukrainian on 1 Jan 2026
1116 Mocha (YNR) from 293 — Tareq Saleh National Resistance west coast
1117 Trieste (ITA) from 736 Litorale — city stays 6626; Slovenia 599 gets the thin Koper coast
1118 Sahrawi Free Zone (WES) from 699 — 4920 northeast, 7979 north, 13416 inland waist, 13415 south coast; Morocco keeps the Dakhla triangle
Azawad pockets 13417 Tinzaouaten, 13418 Tessalit, 13419 Kidal stay in 782; 13420 Timbuktu stays in 898
1119 Aksai Chin (CHI) from 441 — province 5042 plus east half of 10821
Gibraltar 4135 shrinks to the sea tip; hinterland pixels become Spanish 7153
Kherson city is 3755 (UKR); occupied 721 stays on the left-bank estuary
Transnistria 834 keeps 741 754 9576 9423 (Moldova-border tile, not 9435) and is thinned on the bmp
"""
from __future__ import annotations

import re
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
CEUTA_SEA_RGB = (60, 0, 232)  # 5407 Strait
CEUTA_BBOX = (2710, 2730, 795, 815)
# Vanilla port 2722.60,1244.89 snaps to y=803. Keep that row plus sea-facing
# pixels so leftover 10113 stays inland and does not steal 9945's port.
CEUTA_KEEP_MAX_Y = 803
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
# Golan 1074: keep the Israel-facing west; leftover is Syrian 7184.
GOLAN_RGB = (5, 69, 45)
GOLAN_SYRIA_RGB = (89, 171, 91)  # 7184 Damascus leftover
GOLAN_BBOX = (3360, 3378, 841, 862)
GOLAN_KEEP_COLS = 6
GOLAN_MAX_PIXELS = 75
# Guantanamo 7590: keep the south-coast bay inlet (gap at x=1633).
# Leftover including Punta de Maisí is Cuban 1550.
GTMO_RGB = (91, 120, 146)
GTMO_CUBA_RGB = (7, 99, 15)  # 1550
GTMO_BBOX = (1620, 1650, 842, 860)
GTMO_BAY_MIN_Y = 855
GTMO_BAY_MAX_X = 1636
GTMO_BAY_X = 1633
GTMO_MAX_PIXELS = 20
# Trieste 6626 is the urban city. Paint the south-east finger onto 599 so
# Slovenia holds a thin Koper coast between Italy and Croatian Istria.
TRIESTE_RGB = (87, 15, 176)  # 6626
KOPER_RGB = (3, 6, 210)  # 599
TRIESTE_BBOX = (3014, 3026, 610, 626)
# Gibraltar 4135: Britain keeps the southern sea tip (vanilla port pixel);
# leftover Andalusian hinterland is Spanish 7153.
GIB_RGB = (47, 132, 78)  # 4135
GIB_HINTERLAND_RGB = (89, 135, 206)  # 7153
GIB_SEA_RGB = (60, 0, 232)  # 5407 Strait
GIB_BBOX = (2714, 2730, 785, 800)
GIB_PORT_PIXEL = (2722, 795)
GIB_KEEP_MIN_Y = 794
# Western Sahara Free Zone: paint the eastern halves of coastal 10875 and
# 5012 onto inland 7979. Western/Atlantic columns stay Moroccan 699.
# The Dakhla triangle west of the berm elbows is Moroccan; rebels get
# south of a jagged berm (MapChart wall), plus a thin southern strip.
WES_FREE_RGB = (93, 54, 66)  # 7979
WES_SOUTH_PROV = 13415
WES_SOUTH_RGB = (214, 72, 39)  # 13415 southern Free Zone + Dakhla-south coast
WES_ISTHMUS_PROV = 13416
WES_ISTHMUS_RGB = (186, 48, 91)  # 13416 inland lobe north of the 13415 waist
SAHARA_EAST_RGB = {
    (135, 162, 84): 10875,
    (51, 111, 203): 5012,
}
SAHARA_BBOX = (2540, 2672, 952, 1055)
# No 2-row sliver. Southern Dakhla below the jagged berm is 13415.
SAHARA_SOUTH_ROWS = 0
# Aksai Chin 5042 plus the eastern half of Pakistani 10821 (Shaksgam).
AKSAI_RGB = (51, 144, 68)  # 5042
SHAKSGAM_RGB = (135, 102, 224)  # 10821
AKSAI_BBOX = (3970, 4065, 775, 830)
# Kherson: keep 721 only where it touches the occupied left bank (568/737).
# The western estuary peninsula becomes city 3755.
KHERSON_CITY_RGB = (45, 174, 183)  # 3755
KHERSON_SOUTH_RGB = (3, 132, 55)  # 721
KHERSON_LEFT_RGB = (2, 183, 165)  # 568
KAKHOVKA_RGB = (3, 150, 150)  # 737
KHERSON_BBOX = (3295, 3336, 580, 612)
# Azawad city pockets: FAMa garrisons inside AZA-owned 782/898 desert.
# Real Tinzaouaten sits on Algerian 5095; keep the capital on Mali's NE tip.
AZA_TINZ_PROV = 13417
AZA_TESS_PROV = 13418
AZA_KIDAL_PROV = 13419
AZA_TIMB_PROV = 13420
AZA_TINZ_RGB = (201, 72, 44)
AZA_TESS_RGB = (88, 162, 201)
AZA_KIDAL_RGB = (174, 91, 38)
AZA_TIMB_RGB = (62, 128, 96)
AZA_PARENT_RGB = {
    2068: (9, 171, 155),
    10868: (135, 153, 89),
    7930: (93, 18, 31),
    10788: (135, 69, 4),
}
# Centers sit on vanilla type-9 city markers (names were west of the first disks).
AZA_POCKETS = (
    (AZA_TINZ_PROV, AZA_TINZ_RGB, 2864, 1101, 5, (2068,)),
    (AZA_TESS_PROV, AZA_TESS_RGB, 2828, 1080, 5, (10868,)),
    (AZA_KIDAL_PROV, AZA_KIDAL_RGB, 2835, 1108, 6, (2068,)),
    (AZA_TIMB_PROV, AZA_TIMB_RGB, 2774, 1129, 5, (7930, 10788)),
)
AZA_BBOX = (2710, 2880, 1028, 1172)


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


def _close_images(*images) -> None:
    for im in images:
        if im is None:
            continue
        try:
            im.close()
        except Exception:
            pass


def shrink_ceuta_pixels(bmp_path: Path) -> None:
    """Keep the Strait tip of 9945, including the vanilla naval_base pixel."""
    vanilla = Image.open(VANILLA_MAP / "provinces.bmp")
    im = Image.open(bmp_path)
    vpx = vanilla.load()
    px = im.load()
    w, h = im.size
    x0, x1, y0, y1 = CEUTA_BBOX
    try:
        # Restore vanilla 9945/10113 first so a prior 12-px shrink can grow.
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = vpx[x, y][:3]
                if rgb in {CEUTA_RGB, CEUTA_HINTERLAND_RGB}:
                    px[x, y] = rgb
        pts = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == CEUTA_RGB
        ]
        if not pts:
            return

        def touches_sea(x: int, y: int) -> bool:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][:3] == CEUTA_SEA_RGB:
                    return True
            return False

        keep = {(x, y) for x, y in pts if y <= CEUTA_KEEP_MAX_Y or touches_sea(x, y)}
        if not keep:
            return
        # Drop 1-pixel fingers (2724,806) that are not 4-connected to the tip.
        seed = min(keep, key=lambda p: (p[1], p[0]))
        conn: set[tuple[int, int]] = {seed}
        q = deque([seed])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in keep and n not in conn:
                    conn.add(n)
                    q.append(n)
        keep = conn
        for x, y in pts:
            if (x, y) not in keep:
                px[x, y] = CEUTA_HINTERLAND_RGB
        im.save(bmp_path)
    finally:
        _close_images(vanilla, im)


def shrink_melilla_pixels(bmp_path: Path) -> None:
    """Keep only the northern coastal tip of 12100 as Spanish Melilla."""
    im = Image.open(bmp_path)
    px = im.load()
    x0, x1, y0, y1 = MELILLA_BBOX
    try:
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
    finally:
        _close_images(im)


def shrink_golan_pixels(bmp_path: Path) -> None:
    """Keep the western Israel-facing strip of 1074; east is Syrian hinterland."""
    im = Image.open(bmp_path)
    px = im.load()
    x0, x1, y0, y1 = GOLAN_BBOX
    try:
        pts = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == GOLAN_RGB
        ]
        if len(pts) <= GOLAN_MAX_PIXELS:
            return
        min_x = min(x for x, _ in pts)
        keep = {(x, y) for x, y in pts if x <= min_x + GOLAN_KEEP_COLS - 1}
        if not keep:
            return
        for x, y in pts:
            if (x, y) not in keep:
                px[x, y] = GOLAN_SYRIA_RGB
        im.save(bmp_path)
    finally:
        _close_images(im)


def shrink_guantanamo_pixels(bmp_path: Path) -> None:
    """Keep the south-coast inlet of 7590; Maisí and the rest go to Cuban 1550."""
    vanilla = Image.open(VANILLA_MAP / "provinces.bmp")
    im = Image.open(bmp_path)
    vpx = vanilla.load()
    px = im.load()
    x0, x1, y0, y1 = GTMO_BBOX
    try:
        # Always restore vanilla 7590/1550 first so a prior Maisí shrink can move.
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = vpx[x, y][:3]
                if rgb in {GTMO_RGB, GTMO_CUBA_RGB}:
                    px[x, y] = rgb
        pts = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == GTMO_RGB
        ]
        bay = [
            (x, y)
            for x, y in pts
            if y >= GTMO_BAY_MIN_Y and x <= GTMO_BAY_MAX_X
        ]
        if len(bay) > GTMO_MAX_PIXELS:
            bay = sorted(bay, key=lambda p: (-p[1], abs(p[0] - GTMO_BAY_X)))[:GTMO_MAX_PIXELS]
        keep = set(bay)
        if not keep:
            return
        for x, y in pts:
            if (x, y) not in keep:
                px[x, y] = GTMO_CUBA_RGB
        im.save(bmp_path)
    finally:
        _close_images(vanilla, im)


def nudge_guantanamo_unitstacks(path: Path) -> None:
    """Put 7590 stacks on the south-coast inlet instead of the Maisí centroid."""
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    out = []
    changed = False
    for line in lines:
        if not line.startswith("7590;"):
            out.append(line)
            continue
        parts = line.split(";")
        if len(parts) >= 5:
            try:
                x = float(parts[2])
                z = float(parts[4])
            except ValueError:
                out.append(line)
                continue
            if x >= 1633.5 and z >= 1195:
                parts[2] = "1630.00"
                parts[4] = "1192.00"
                changed = True
            elif z >= 1194 and x < 1633:
                parts[4] = "1192.00"
                changed = True
            out.append(";".join(parts))
        else:
            out.append(line)
    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf-8")


def paint_koper_coast(bmp_path: Path) -> None:
    """Italy keeps Trieste city on 6626; Slovenia 599 gets the thin Koper coast."""
    vanilla = Image.open(VANILLA_MAP / "provinces.bmp")
    im = Image.open(bmp_path)
    vpx = vanilla.load()
    px = im.load()
    x0, x1, y0, y1 = TRIESTE_BBOX
    try:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = vpx[x, y][:3]
                if rgb in {TRIESTE_RGB, KOPER_RGB}:
                    px[x, y] = rgb
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if px[x, y][:3] != TRIESTE_RGB:
                    continue
                # South finger is the real Koper waterfront. East column plus
                # (3022,621) keeps 599 4-connected to that finger.
                if y >= 622 or x >= 3023 or (x >= 3022 and y >= 621):
                    px[x, y] = KOPER_RGB
        im.save(bmp_path)
    finally:
        _close_images(vanilla, im)


def shrink_gibraltar_pixels(bmp_path: Path) -> None:
    """Keep the southern sea tip of 4135, including the vanilla naval_base pixel."""
    vanilla = Image.open(VANILLA_MAP / "provinces.bmp")
    im = Image.open(bmp_path)
    vpx = vanilla.load()
    px = im.load()
    w, h = im.size
    x0, x1, y0, y1 = GIB_BBOX
    try:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = vpx[x, y][:3]
                if rgb in {GIB_RGB, GIB_HINTERLAND_RGB}:
                    px[x, y] = rgb
        pts = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == GIB_RGB
        ]
        if not pts:
            return

        def touches_sea(x: int, y: int) -> bool:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][:3] == GIB_SEA_RGB:
                    return True
            return False

        keep = {(x, y) for x, y in pts if y >= GIB_KEEP_MIN_Y or touches_sea(x, y)}
        keep.add(GIB_PORT_PIXEL)
        seed = GIB_PORT_PIXEL if GIB_PORT_PIXEL in keep else min(keep, key=lambda p: (-p[1], p[0]))
        conn: set[tuple[int, int]] = {seed}
        q = deque([seed])
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in keep and n not in conn:
                    conn.add(n)
                    q.append(n)
        keep = conn
        if GIB_PORT_PIXEL not in keep:
            keep.add(GIB_PORT_PIXEL)
        for x, y in pts:
            if (x, y) not in keep:
                px[x, y] = GIB_HINTERLAND_RGB
        im.save(bmp_path)
    finally:
        _close_images(vanilla, im)


def paint_sahara_free_zone(bmp_path: Path) -> None:
    """Polisario: eastern interior plus Dakhla south of the screenshot diagonal.
    Morocco keeps the coast north of that line and the berm triangle."""
    vanilla = Image.open(VANILLA_MAP / "provinces.bmp")
    im = Image.open(bmp_path)
    vpx = vanilla.load()
    px = im.load()
    w, h = im.size
    x0, x1, y0, y1 = SAHARA_BBOX
    keep_rgbs = set(SAHARA_EAST_RGB) | {WES_FREE_RGB}
    try:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = vpx[x, y][:3]
                if rgb in keep_rgbs:
                    px[x, y] = rgb

        sea_rgbs: set[tuple[int, int, int]] = set()
        definition = MOD_MAP / "definition.csv"
        if not definition.exists():
            definition = VANILLA_MAP / "definition.csv"
        for line in definition.read_text(encoding="utf-8", errors="ignore").splitlines():
            parts = line.split(";")
            if len(parts) >= 5 and parts[4] == "sea":
                try:
                    sea_rgbs.add((int(parts[1]), int(parts[2]), int(parts[3])))
                except ValueError:
                    continue

        def touches_sea(x: int, y: int) -> bool:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][:3] in sea_rgbs:
                    return True
            return False

        wes = {
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == WES_FREE_RGB
        }
        south_rgb = (135, 162, 84)  # 10875
        south_pts = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == south_rgb
        ]
        south_y = 0
        if south_pts:
            south_y = max(p[1] for p in south_pts) - SAHARA_SOUTH_ROWS + 1

        candidates: set[tuple[int, int]] = set()
        for src_rgb in SAHARA_EAST_RGB:
            pts = [
                (x, y)
                for y in range(y0, y1 + 1)
                for x in range(x0, x1 + 1)
                if px[x, y][:3] == src_rgb
            ]
            if not pts:
                continue
            xs = [p[0] for p in pts]
            keep_x = min(xs) + (max(xs) - min(xs) + 1) // 2
            for x, y in pts:
                in_south = src_rgb == south_rgb and y >= south_y
                if in_south or (x > keep_x and not touches_sea(x, y)):
                    candidates.add((x, y))

        q = deque(wes)
        reachable = set(wes)
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in candidates and n not in reachable:
                    reachable.add(n)
                    q.append(n)
        for x, y in reachable - wes:
            px[x, y] = WES_FREE_RGB

        wes_pts = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == WES_FREE_RGB
        ]
        sea_ys = [y for x, y in wes_pts if touches_sea(x, y)]
        if wes_pts and sea_ys:
            mid_y = sorted(p[1] for p in wes_pts)[len(wes_pts) // 2]
            split_y = min(mid_y, min(sea_ys))
            for x, y in wes_pts:
                if y >= split_y:
                    px[x, y] = WES_SOUTH_RGB
            # A y-cut can leave a western 7979 pocket; fold leftovers into 13415.
            north_pts = [
                (x, y)
                for y in range(y0, y1 + 1)
                for x in range(x0, x1 + 1)
                if px[x, y][:3] == WES_FREE_RGB
            ]
            south = {
                (x, y)
                for y in range(y0, y1 + 1)
                for x in range(x0, x1 + 1)
                if px[x, y][:3] == WES_SOUTH_RGB
            }
            north_set = set(north_pts)
            seen: set[tuple[int, int]] = set()
            comps: list[list[tuple[int, int]]] = []
            for start in north_pts:
                if start in seen:
                    continue
                q = deque([start])
                seen.add(start)
                cur = [start]
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (x + dx, y + dy)
                        if n in north_set and n not in seen:
                            seen.add(n)
                            q.append(n)
                            cur.append(n)
                comps.append(cur)
            comps.sort(key=len, reverse=True)
            for extra in comps[1:]:
                if any(
                    (x + dx, y + dy) in south
                    for x, y in extra
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                ):
                    for x, y in extra:
                        px[x, y] = WES_SOUTH_RGB
        mor_rgbs = {
            (135, 162, 84),  # 10875
            (51, 111, 203),  # 5012
            (93, 117, 41),   # 8038
            (93, 192, 181),  # 8111
        }
        for leftover_rgb in ((135, 162, 84), (51, 111, 203)):
            pts = [
                (x, y)
                for y in range(y0, y1 + 1)
                for x in range(x0, x1 + 1)
                if px[x, y][:3] == leftover_rgb
            ]
            leftover_set = set(pts)
            seen_m: set[tuple[int, int]] = set()
            mcomps: list[list[tuple[int, int]]] = []
            for start in pts:
                if start in seen_m:
                    continue
                q = deque([start])
                seen_m.add(start)
                cur = [start]
                while q:
                    x, y = q.popleft()
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        n = (x + dx, y + dy)
                        if n in leftover_set and n not in seen_m:
                            seen_m.add(n)
                            q.append(n)
                            cur.append(n)
                mcomps.append(cur)
            mcomps.sort(key=len, reverse=True)
            wes_rgbs = {WES_FREE_RGB, WES_SOUTH_RGB}
            for extra in mcomps[1:]:
                target = None
                wes_target = None
                for x, y in extra:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h:
                            nrgb = px[nx, ny][:3]
                            if nrgb in mor_rgbs and nrgb != leftover_rgb:
                                target = nrgb
                            elif nrgb in wes_rgbs:
                                wes_target = nrgb
                if target is None:
                    target = wes_target or (135, 162, 84)
                for x, y in extra:
                    px[x, y] = target
        _return_sahara_triangle_to_morocco(px, w, h, x0, x1, y0, y1, sea_rgbs)
        _split_wes_south_inland(px, x0, x1, y0, y1)
        _give_dakhla_south_to_wes(px, w, h, x0, x1, y0, y1, sea_rgbs)
        _split_13415_at_pinch(px, w, h, x0, x1, y0, y1)
        _carve_wes_pinch(px, w, h, x0, x1, y0, y1, sea_rgbs)
        im.save(bmp_path)
    finally:
        _close_images(vanilla, im)


def _return_sahara_triangle_to_morocco(px, w, h, x0, x1, y0, y1, sea_rgbs) -> None:
    """Paint the Dakhla-east triangle (west of the 5012 berm) onto 699.

    Line: 5012's eastern elbow, due south. Eastern Free Zone stays WES.
    """
    rgb_5012 = (51, 111, 203)
    dakhla = (135, 162, 84)
    mor_rgbs = {
        dakhla,
        rgb_5012,
        (93, 117, 41),   # 8038
        (93, 192, 181),  # 8111
    }
    wes_rgbs = {WES_FREE_RGB, WES_SOUTH_RGB}
    pts_5012: list[tuple[int, int]] = []
    pts_10875: list[tuple[int, int]] = []
    wes_pts: list[tuple[int, int]] = []
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            rgb = px[x, y][:3]
            if rgb == rgb_5012:
                pts_5012.append((x, y))
            elif rgb == dakhla:
                pts_10875.append((x, y))
            elif rgb in wes_rgbs:
                wes_pts.append((x, y))
    if not pts_5012 or not wes_pts:
        return
    x_line = max(p[0] for p in pts_5012)
    y_start = min(p[1] for p in pts_5012)
    for x, y in wes_pts:
        if y >= y_start and x <= x_line:
            target = dakhla if y >= min(p[1] for p in pts_10875) else rgb_5012
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (0, 2)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][:3] in mor_rgbs:
                    target = px[nx, ny][:3]
                    break
            px[x, y] = target
    for x, y in wes_pts:
        if px[x, y][:3] not in wes_rgbs:
            continue
        if any(
            0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][:3] in sea_rgbs
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        ):
            px[x, y] = dakhla


def _split_wes_south_inland(px, x0, x1, y0, y1) -> None:
    """Keep 13415 as the southern inland Free Zone after the triangle returns to 699."""
    pts = [
        (x, y)
        for y in range(y0, y1 + 1)
        for x in range(x0, x1 + 1)
        if px[x, y][:3] == WES_FREE_RGB
    ]
    if len(pts) < 40:
        return
    split_y = sorted(p[1] for p in pts)[len(pts) // 2]
    for x, y in pts:
        if y >= split_y:
            px[x, y] = WES_SOUTH_RGB


def _give_dakhla_south_to_wes(px, w, h, x0, x1, y0, y1, sea_rgbs) -> None:
    """WES gets 10875 south of a jagged berm, plus the southern border strip.

    The old straight diagonal looked like a ruler cut. MapChart's berm jogs
    and leaves Polisario a bit more of the Dakhla hinterland and the
    Mauritanian-border strip.
    """
    dakhla = (135, 162, 84)
    pts = [
        (x, y)
        for y in range(y0, y1 + 1)
        for x in range(x0, x1 + 1)
        if px[x, y][:3] == dakhla
    ]
    if len(pts) < 40:
        return

    def sea_west(x: int, y: int) -> bool:
        nx = x - 1
        return 0 <= nx < w and px[nx, y][:3] in sea_rgbs

    west_coast = [(x, y) for x, y in pts if sea_west(x, y)]
    if not west_coast:
        west_coast = pts
    x_w = min(p[0] for p in west_coast)
    west_ys = sorted(y for x, y in west_coast if x <= x_w + 4)
    # Further north than the old 0.72 cut so rebels take more hinterland.
    y_w = west_ys[int(len(west_ys) * 0.52)]
    x_e = max(p[0] for p in pts)
    east_ys = sorted(y for x, y in pts if x >= x_e - 1)
    y_e = east_ys[int(len(east_ys) * 0.18)]
    span = max(1, x_e - x_w)
    verts = [
        (x_w, y_w - 3),
        (x_w + int(span * 0.18), y_w + 4),
        (x_w + int(span * 0.34), y_w - 2),
        (x_w + int(span * 0.52), y_w + int((y_e - y_w) * 0.45) + 3),
        (x_w + int(span * 0.70), y_e + 5),
        (x_e, y_e - 1),
    ]

    def line_y(x: int) -> float:
        if x <= verts[0][0]:
            base = float(verts[0][1])
        elif x >= verts[-1][0]:
            base = float(verts[-1][1])
        else:
            base = float(verts[-1][1])
            for (xa, ya), (xb, yb) in zip(verts, verts[1:]):
                if xa <= x <= xb:
                    t = 0.0 if xb == xa else (x - xa) / (xb - xa)
                    base = ya + t * (yb - ya)
                    break
        jog = ((x * 19 + 11) % 7) - 3
        return base + jog

    max_y = max(p[1] for p in pts)
    for x, y in pts:
        south_strip = y >= max_y - 8
        if south_strip or y > line_y(x) + 0.5:
            px[x, y] = WES_SOUTH_RGB


def _wes_pinch_y(pts: list[tuple[int, int]]) -> int | None:
    by_y: dict[int, list[int]] = {}
    for x, y in pts:
        by_y.setdefault(y, []).append(x)
    mid = [
        (len(xs), y)
        for y, xs in by_y.items()
        if 1005 <= y <= 1035 and min(xs) < 2610
    ]
    if not mid:
        return None
    return min(mid)[1]


def _split_13415_at_pinch(px, w: int, h: int, x0: int, x1: int, y0: int, y1: int) -> None:
    """Cut 13415 at the waist: inland lobe → 13416, coastal south stays 13415."""
    south = [
        (x, y)
        for y in range(y0, y1 + 1)
        for x in range(x0, x1 + 1)
        if px[x, y][:3] == WES_SOUTH_RGB
    ]
    pinch_y = _wes_pinch_y(south)
    if pinch_y is None:
        return
    blob = set(south)
    cut = {(x, y) for x, y in south if y == pinch_y}
    walk = blob - cut
    seeds = [
        (x, y)
        for x, y in walk
        if any(
            0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][:3] == WES_FREE_RGB
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
    ]
    if not seeds:
        return
    seen: set[tuple[int, int]] = set(seeds)
    q: deque[tuple[int, int]] = deque(seeds)
    while q:
        x, y = q.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n in walk and n not in seen:
                seen.add(n)
                q.append(n)
    if len(seen) < 80 or len(seen) > len(walk) - 80:
        print(f"warning: 13415 pinch split skipped ({len(seen)}/{len(walk)})")
        return
    for x, y in seen:
        px[x, y] = WES_ISTHMUS_RGB
    for x, y in cut:
        north = sum(
            0 <= y + dy < h and px[x + dx, y + dy][:3] == WES_ISTHMUS_RGB
            for dx, dy in ((0, -1), (1, -1), (-1, -1), (1, 0), (-1, 0))
            if 0 <= x + dx < w
        )
        px[x, y] = WES_ISTHMUS_RGB if north >= 2 else WES_SOUTH_RGB


def _carve_wes_pinch(px, w: int, h: int, x0: int, x1: int, y0: int, y1: int, sea_rgbs) -> None:
    """Round the 13415/13416 waist into a wavy neck. No 90-degree berm corner."""
    morocco = {(135, 162, 84), (51, 111, 203)}
    inland = [
        (x, y)
        for y in range(y0, y1 + 1)
        for x in range(x0, x1 + 1)
        if px[x, y][:3] == WES_ISTHMUS_RGB
    ]
    south = [
        (x, y)
        for y in range(y0, y1 + 1)
        for x in range(x0, x1 + 1)
        if px[x, y][:3] == WES_SOUTH_RGB
    ]
    if not inland or not south:
        return
    west_i = min(p[0] for p in inland)
    south_i = max(p[1] for p in inland)
    north_s = min(p[1] for p in south)
    cx = west_i
    cy = min(south_i, north_s)

    def touches_sea(x: int, y: int) -> bool:
        return any(
            0 <= x + dx < w and 0 <= y + dy < h and px[x + dx, y + dy][:3] in sea_rgbs
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )

    def owner_at(x: int, y: int) -> tuple[int, int, int]:
        return WES_ISTHMUS_RGB if y <= cy else WES_SOUTH_RGB

    # Quarter-disk into the Morocco pocket west/north of the waist, a wavy
    # westward bulge along 13416's ruler-cut west wall, and a matching
    # south-lobe push so the neck is a curve instead of a shelf.
    west_by_y: dict[int, int] = {}
    for x, y in inland:
        prev = west_by_y.get(y)
        if prev is None or x < prev:
            west_by_y[y] = x
    south_west: dict[int, int] = {}
    for x, y in south:
        prev = south_west.get(y)
        if prev is None or x < prev:
            south_west[y] = x

    for y in range(max(y0, cy - 42), min(y1, cy + 16) + 1):
        t = (cy - y) / 42.0
        wall_x = west_by_y.get(y, cx)
        jog = ((y * 17 + 5) % 7) - 3
        if 0.0 <= t <= 1.0:
            bulge = 4.0 + 5.5 * (1.0 - t) * (1.0 - t) + jog * 0.7
        elif t < 0.0:
            bulge = 6.5 + ((y * 13) % 5) * 0.5
            wall_x = south_west.get(y, wall_x)
        else:
            bulge = 2.0 + jog * 0.4
        for x in range(x0, min(x1, wall_x) + 1):
            if px[x, y][:3] not in morocco or touches_sea(x, y):
                continue
            dx = wall_x - x
            dy = cy - y
            if dx < -1:
                continue
            ang = (dx * 11 + dy * 19 + y) % 11
            radius = 13.0 + (ang - 5) * 0.65
            in_fillet = dy >= 0 and dx >= 0 and (dx * dx + 0.72 * dy * dy) <= radius * radius
            in_wall = 0 <= dx <= bulge + 0.5
            if in_fillet or in_wall:
                px[x, y] = owner_at(x, y)

    wes = {WES_SOUTH_RGB, WES_ISTHMUS_RGB}
    for _ in range(3):
        grow: list[tuple[int, int, tuple[int, int, int]]] = []
        shrink: list[tuple[int, int]] = []
        for y in range(max(y0, cy - 38), min(y1, cy + 20) + 1):
            for x in range(x0, cx + 6):
                rgb = px[x, y][:3]
                nwes = [
                    px[x + dxx, y + dyy][:3]
                    for dxx, dyy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                    if 0 <= x + dxx < w and 0 <= y + dyy < h
                    if px[x + dxx, y + dyy][:3] in wes
                ]
                nmor = sum(
                    0 <= x + dxx < w
                    and 0 <= y + dyy < h
                    and px[x + dxx, y + dyy][:3] in morocco
                    for dxx, dyy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                )
                if rgb in morocco and not touches_sea(x, y) and len(nwes) >= 3:
                    grow.append((x, y, nwes[0]))
                elif rgb in wes and nmor >= 3 and len(nwes) <= 1 and x < cx + 2:
                    shrink.append((x, y))
        for x, y, rgb in grow:
            px[x, y] = rgb
        dakhla = (135, 162, 84)
        for x, y in shrink:
            px[x, y] = dakhla

    # Tiny Morocco pockets trapped in the neck look like blocky holes.
    mor_pts = [
        (x, y)
        for y in range(max(y0, cy - 8), min(y1, cy + 20) + 1)
        for x in range(x0, x1 + 1)
        if px[x, y][:3] in morocco
    ]
    leftover = set(mor_pts)
    seen_h: set[tuple[int, int]] = set()
    for start in mor_pts:
        if start in seen_h:
            continue
        q: deque[tuple[int, int]] = deque([start])
        seen_h.add(start)
        cur = [start]
        while q:
            x, y = q.popleft()
            for dxx, dyy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dxx, y + dyy)
                if n in leftover and n not in seen_h:
                    seen_h.add(n)
                    q.append(n)
                    cur.append(n)
        if len(cur) > 28:
            continue
        target = None
        for x, y in cur:
            for dxx, dyy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dxx, y + dyy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][:3] in wes:
                    target = px[nx, ny][:3]
                    break
            if target is not None:
                break
        if target is not None:
            for x, y in cur:
                px[x, y] = target


def paint_aksai_chin(bmp_path: Path) -> None:
    """Give China 5042 plus the eastern half of 10821 (Shaksgam / Karakoram)."""
    vanilla = Image.open(VANILLA_MAP / "provinces.bmp")
    im = Image.open(bmp_path)
    vpx = vanilla.load()
    px = im.load()
    x0, x1, y0, y1 = AKSAI_BBOX
    try:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = vpx[x, y][:3]
                if rgb in {AKSAI_RGB, SHAKSGAM_RGB}:
                    px[x, y] = rgb
        aksai = {
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == AKSAI_RGB
        }
        shak = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == SHAKSGAM_RGB
        ]
        if not aksai or not shak:
            return
        xs = [p[0] for p in shak]
        keep_x = min(xs) + (max(xs) - min(xs) + 1) // 2
        candidates = {(x, y) for x, y in shak if x > keep_x}
        q = deque(aksai)
        reachable = set(aksai)
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in candidates and n not in reachable:
                    reachable.add(n)
                    q.append(n)
        for x, y in reachable - aksai:
            px[x, y] = AKSAI_RGB
        im.save(bmp_path)
    finally:
        _close_images(vanilla, im)


def paint_kherson_front(bmp_path: Path) -> None:
    """City 3755 takes the western 721 peninsula; occupied 721 stays on the left bank."""
    vanilla = Image.open(VANILLA_MAP / "provinces.bmp")
    im = Image.open(bmp_path)
    vpx = vanilla.load()
    px = im.load()
    w, h = im.size
    x0, x1, y0, y1 = KHERSON_BBOX
    occupied = {KHERSON_LEFT_RGB, KAKHOVKA_RGB}
    try:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = vpx[x, y][:3]
                if rgb in {KHERSON_CITY_RGB, KHERSON_SOUTH_RGB, KHERSON_LEFT_RGB, KAKHOVKA_RGB}:
                    px[x, y] = rgb
        pts = [
            (x, y)
            for y in range(y0, y1 + 1)
            for x in range(x0, x1 + 1)
            if px[x, y][:3] == KHERSON_SOUTH_RGB
        ]
        if not pts:
            return

        def touches_occupied(x: int, y: int) -> bool:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and px[nx, ny][:3] in occupied:
                    return True
            return False

        seeds = [(x, y) for x, y in pts if touches_occupied(x, y)]
        keep: set[tuple[int, int]] = set(seeds)
        q = deque(seeds)
        ptset = set(pts)
        while q:
            x, y = q.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (x + dx, y + dy)
                if n in ptset and n not in keep:
                    keep.add(n)
                    q.append(n)
        for x, y in pts:
            if (x, y) not in keep:
                px[x, y] = KHERSON_CITY_RGB
        im.save(bmp_path)
    finally:
        _close_images(vanilla, im)


def paint_azawad_pockets(bmp_path: Path) -> None:
    """Carve FAMa city disks out of AZA desert so Mali starts in supply-cut pockets."""
    im = Image.open(bmp_path)
    px = im.load()
    w, h = im.size
    x0, x1, y0, y1 = AZA_BBOX
    x0, x1 = max(0, x0), min(w - 1, x1)
    y0, y1 = max(0, y0), min(h - 1, y1)
    try:
        for pid, rgb, cx, cy, rad, parents in AZA_POCKETS:
            parent_rgb = AZA_PARENT_RGB[parents[0]]
            allowed = {AZA_PARENT_RGB[p] for p in parents}
            allowed.add(rgb)
            for y in range(y0, y1 + 1):
                for x in range(x0, x1 + 1):
                    if px[x, y][:3] == rgb:
                        px[x, y] = parent_rgb
            r2 = rad * rad
            for y in range(cy - rad, cy + rad + 1):
                if y < y0 or y > y1:
                    continue
                for x in range(cx - rad, cx + rad + 1):
                    if x < x0 or x > x1:
                        continue
                    if (x - cx) ** 2 + (y - cy) ** 2 > r2:
                        continue
                    if px[x, y][:3] in allowed or px[x, y][:3] == parent_rgb:
                        px[x, y] = rgb
        im.save(bmp_path)
    finally:
        _close_images(im)


def ensure_azawad_definition(definition: Path) -> None:
    text = definition.read_text(encoding="utf-8", errors="ignore")
    extra = []
    for pid, rgb, *_rest in AZA_POCKETS:
        if f"{pid};" not in text:
            r, g, b = rgb
            extra.append(f"{pid};{r};{g};{b};land;false;desert;5")
    if extra:
        definition.write_text(text.rstrip() + "\n" + "\n".join(extra) + "\n", encoding="utf-8")


def patch_azawad_unitstacks(path: Path, bmp_path: Path) -> None:
    """Park every pocket stack on the painted disk so VP names sit in the circle."""
    im = Image.open(bmp_path)
    px = im.load()
    h = im.size[1]
    x0, x1, y0, y1 = AZA_BBOX
    blobs: dict[tuple[int, int, int], list[tuple[int, int]]] = {rgb: [] for _, rgb, *_ in AZA_POCKETS}
    try:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = px[x, y][:3]
                if rgb in blobs:
                    blobs[rgb].append((x, y))
    finally:
        im.close()
    rgb_to_pid = {rgb: pid for pid, rgb, *_ in AZA_POCKETS}
    parent_of = {pid: parents[0] for pid, _rgb, _cx, _cy, _r, parents in AZA_POCKETS}
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    skip = {str(pid) for pid, *_ in AZA_POCKETS}
    kept = [ln for ln in lines if ln.split(";", 1)[0] not in skip]
    extra = []
    for rgb, pts in blobs.items():
        if not pts:
            continue
        pid = rgb_to_pid[rgb]
        tx, tz = _to_xz(*_centroid(pts), h)
        src = [ln for ln in kept if ln.startswith(f"{parent_of[pid]};")]
        if not src:
            continue
        for line in src:
            parts = line.split(";")
            if len(parts) < 5:
                continue
            try:
                parts[0] = str(pid)
                parts[2] = tx
                parts[4] = tz
                extra.append(";".join(parts))
            except ValueError:
                pass
    path.write_text("\n".join(kept + extra) + "\n", encoding="utf-8")


def mark_koper_coastal(definition: Path) -> None:
    """599 is inland in vanilla; after the Koper paint it must be a coastal province."""
    lines = definition.read_text(encoding="utf-8", errors="ignore").splitlines()
    out = []
    changed = False
    for line in lines:
        if line.startswith("599;"):
            parts = line.split(";")
            if len(parts) >= 6 and parts[5].lower() != "true":
                parts[5] = "true"
                line = ";".join(parts)
                changed = True
        out.append(line)
    if changed:
        definition.write_text("\n".join(out) + "\n", encoding="utf-8")


def mark_wes_coastal(definition: Path) -> None:
    """7979 and 13416 inland; 13415 stays coastal for the Dakhla-south port."""
    flags = {
        "7979": "false",
        str(WES_ISTHMUS_PROV): "false",
        str(WES_SOUTH_PROV): "true",
    }
    lines = definition.read_text(encoding="utf-8", errors="ignore").splitlines()
    out = []
    changed = False
    for line in lines:
        pid = line.split(";", 1)[0]
        if pid in flags:
            parts = line.split(";")
            if len(parts) >= 6 and parts[5].lower() != flags[pid]:
                parts[5] = flags[pid]
                line = ";".join(parts)
                changed = True
        out.append(line)
    if changed:
        definition.write_text("\n".join(out) + "\n", encoding="utf-8")


def thin_transnistria_pixels(bmp_path: Path, definition: Path) -> None:
    """Keep a thin Moldova-facing Dniester strip; leftover pixels go to Ukraine."""
    rgb_to_id = _load_rgb_ids(definition)
    im = Image.open(bmp_path)
    px = im.load()
    w, h = im.size
    x0, x1, y0, y1 = PMR_BBOX
    pmr_pts: dict[int, list[tuple[int, int]]] = {pid: [] for pid in PMR_PROVS}
    try:
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
    finally:
        _close_images(im)


def split_mayotte_pixels(bmp_path: Path) -> None:
    im = Image.open(bmp_path)
    px = im.load()
    w, h = im.size
    try:
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
    finally:
        _close_images(im)


def drop_building_state(buildings: Path, state_id: int) -> None:
    """Remove every buildings.txt row for a retired or reused state id."""
    lines = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
    kept = [line for line in lines if not line.startswith(f"{state_id};")]
    if len(kept) != len(lines):
        write_buildings_txt(buildings, kept)


def drop_building_lines(buildings: Path, exact: set[str]) -> None:
    """Remove leftover invented rows (exact full-line match)."""
    if not exact:
        return
    lines = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
    kept = [line for line in lines if line not in exact]
    if len(kept) != len(lines):
        write_buildings_txt(buildings, kept)


def retag_building_lines(buildings: Path, specs: list[tuple[str, str, str]]) -> None:
    """Rewrite the state id on exact vanilla buildings.txt rows after a split.

    specs: (old_state, new_state, rest_of_line after the first semicolon).
    Idempotent if the row is already on new_state.
    """
    wanted = {(old, rest): new for old, new, rest in specs}
    already = {f"{new};{rest}" for old, new, rest in specs}
    lines = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: list[str] = []
    changed = False
    for line in lines:
        if line in already:
            out.append(line)
            continue
        parts = line.split(";", 1)
        key = (parts[0], parts[1]) if len(parts) == 2 else None
        if key in wanted:
            out.append(f"{wanted[key]};{parts[1]}")
            changed = True
        else:
            out.append(line)
    if changed:
        write_buildings_txt(buildings, out)


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
        write_buildings_txt(buildings, kept)


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
        write_buildings_txt(buildings, [ln for ln in text.splitlines() if ln.strip()] + cloned)


def append_building_lines(buildings: Path, lines: list[str]) -> None:
    text = buildings.read_text(encoding="utf-8", errors="ignore")
    have = set(text.splitlines())
    add = [ln for ln in lines if ln and ln not in have]
    if add:
        write_buildings_txt(buildings, [ln for ln in text.splitlines() if ln.strip()] + add)


def rewrite_state_buildings(buildings: Path, state_id: int, lines: list[str]) -> None:
    """Replace a state's buildings.txt rows. Use for tiny coastal enclaves."""
    drop_building_state(buildings, state_id)
    append_building_lines(buildings, lines)


def write_buildings_txt(buildings: Path, lines: list[str]) -> None:
    """Write buildings.txt the way vanilla does: Unix LF, no trailing newline.

    HOI4 splits on \\n and treats a final empty token as line N+1
    ('invalid arguments count'). Vanilla's file has no trailing newline.
    """
    buildings.write_bytes("\n".join(lines).encode("utf-8"))


SAM_SITE_MAP_SLOTS = 1
# Offset from AA pads so SAM meshes do not z-fight. Not a new spawn type.
SAM_SITE_OFFSETS = ((1.8, 1.6),)


def ensure_sam_site_map_positions(buildings: Path) -> tuple[int, int]:
    """One sam_site mesh slot per state (provincial, show_on_map = 1).

    Extra leftover state-building slots draw as extra rocket icons. Keep one
    preferred coordinate; HOI4 places constructed provincial SAM there.
    """
    lines = [ln for ln in buildings.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]
    aa_by_state: dict[int, list[list[str]]] = {}
    fallback_by_state: dict[int, list[list[str]]] = {}
    sam_count: dict[int, int] = {}
    kept: list[str] = []
    dropped = 0
    for ln in lines:
        parts = ln.split(";")
        if len(parts) != 7:
            kept.append(ln)
            continue
        sid = int(parts[0])
        btype = parts[1]
        if btype == "anti_air_building":
            aa_by_state.setdefault(sid, []).append(parts)
        elif btype == "sam_site":
            n = sam_count.get(sid, 0)
            if n >= SAM_SITE_MAP_SLOTS:
                dropped += 1
                continue
            sam_count[sid] = n + 1
        elif btype in ("industrial_complex", "rocket_site_spawn", "arms_factory"):
            fallback_by_state.setdefault(sid, []).append(parts)
        kept.append(ln)

    add: list[str] = []
    states = set(aa_by_state) | {sid for sid, n in sam_count.items() if n < SAM_SITE_MAP_SLOTS}
    states |= set(fallback_by_state)
    for sid in sorted(states):
        have = sam_count.get(sid, 0)
        if have >= SAM_SITE_MAP_SLOTS:
            continue
        sources = aa_by_state.get(sid) or fallback_by_state.get(sid) or []
        if not sources:
            continue
        for i in range(have, SAM_SITE_MAP_SLOTS):
            src = sources[min(i, len(sources) - 1)]
            dx, dz = SAM_SITE_OFFSETS[i % len(SAM_SITE_OFFSETS)]
            x = float(src[2]) + dx
            z = float(src[4]) + dz
            add.append(f"{sid};sam_site;{x:.2f};{src[3]};{z:.2f};{src[5]};{src[6]}")
    if add or dropped:
        write_buildings_txt(buildings, kept + add)
    return len(add), dropped


def _strip_blank_building_lines(buildings: Path) -> None:
    """Drop blanks and short rows. HOI4 errors on a trailing empty line (invalid arguments)."""
    kept: list[str] = []
    for ln in buildings.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not ln.strip():
            continue
        parts = ln.split(";")
        if len(parts) != 7:
            print(f"warning: dropping buildings.txt row with {len(parts)} fields: {ln[:80]}")
            continue
        kept.append(";".join(parts))
    write_buildings_txt(buildings, kept)


REQUIRED_STATE_SITES = ("air_base", "rocket_site_spawn")
# rocket_site_spawn is also the mega_gun_emplacement site ("no gun emplacement").
NEW_STATE_IDS = range(1082, 1122)
SPLIT_PARENT_IDS = {
    109, 118, 183, 192, 196, 197, 200, 227, 230, 231, 290, 293, 308, 315, 441, 448, 449, 454, 553, 554,
    559, 676, 680, 686, 692, 694, 699, 708, 719, 736, 787, 834, 844, 884, 890, 1005,
}


def parse_state_provinces(states_dir: Path) -> dict[int, list[int]]:
    out: dict[int, list[int]] = {}
    for path in states_dir.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        mid = re.search(r"id\s*=\s*(\d+)", text)
        mprov = re.search(r"provinces\s*=\s*\{([^}]+)\}", text)
        if not mid or not mprov:
            continue
        out[int(mid.group(1))] = [int(x) for x in re.findall(r"\d+", mprov.group(1))]
    return out


def load_definition_maps(path: Path) -> tuple[dict[tuple[int, int, int], int], dict[int, str]]:
    rgb_to_id: dict[tuple[int, int, int], int] = {}
    id_to_kind: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        p = line.split(";")
        if len(p) < 5:
            continue
        try:
            pid = int(p[0])
            rgb = (int(p[1]), int(p[2]), int(p[3]))
        except ValueError:
            continue
        rgb_to_id[rgb] = pid
        id_to_kind[pid] = p[4]
    return rgb_to_id, id_to_kind


def load_coastal_land(path: Path) -> set[int]:
    out: set[int] = set()
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        p = line.split(";")
        if len(p) < 6:
            continue
        try:
            pid = int(p[0])
        except ValueError:
            continue
        if p[4] == "land" and p[5].lower() == "true":
            out.add(pid)
    return out


def index_province_pixels(
    im: Image.Image,
    rgb_to_id: dict[tuple[int, int, int], int],
    wanted: set[int],
) -> dict[int, list[tuple[int, int]]]:
    px = im.load()
    w, h = im.size
    out: dict[int, list[tuple[int, int]]] = {pid: [] for pid in wanted}
    for y in range(h):
        for x in range(w):
            pid = rgb_to_id.get(px[x, y][:3])
            if pid in out:
                out[pid].append((x, y))
    return out


def _centroid(pts: list[tuple[int, int]]) -> tuple[int, int]:
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    return min(pts, key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2)


def _interior_pixel(
    pts: list[tuple[int, int]],
    px,
    w: int,
    h: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    pid: int,
) -> tuple[int, int]:
    """Prefer a pixel whose 4-neighbors are the same province so HOI4 rounding stays inside."""
    for x, y in pts:
        ok = True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not (0 <= nx < w and 0 <= ny < h):
                ok = False
                break
            if rgb_to_id.get(px[nx, ny][:3]) != pid:
                ok = False
                break
        if ok:
            return x, y
    return _centroid(pts)


def _hoi4_pixel(x: str | float, z: str | float, height: int) -> tuple[int, int] | None:
    """Bitmap pixel HOI4 samples for a buildings.txt x,z.

    Confirmed against 1.19.2 716 errors: pixel_x = trunc(x),
    pixel_y = (height - 1) - trunc(z). height-z (no -1) was one pixel south
    and made every split-state port look valid to us and ignored by HOI4.
    """
    try:
        ix = int(float(x))
        iy = (height - 1) - int(float(z))
    except ValueError:
        return None
    return ix, iy


def _to_xz(bmp_x: int, bmp_y: int, height: int) -> tuple[str, str]:
    return f"{bmp_x:.2f}", f"{height - 1 - bmp_y:.2f}"


def _province_at(
    px,
    x: str,
    z: str,
    height: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    w: int,
    h: int,
) -> int | None:
    pix = _hoi4_pixel(x, z, height)
    if pix is None:
        return None
    ix, iy = pix
    if ix < 0 or iy < 0 or ix >= w or iy >= h:
        return None
    return rgb_to_id.get(px[ix, iy][:3])


def _land_province_near(
    px,
    x: str,
    z: str,
    height: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    id_to_kind: dict[int, str],
    w: int,
    h: int,
) -> int | None:
    """Land province under a building, or the nearest land if the pixel is sea."""
    pix = _hoi4_pixel(x, z, height)
    if pix is None:
        return None
    ix, iy = pix

    def pid_at(ax: int, ay: int) -> int | None:
        if 0 <= ax < w and 0 <= ay < h:
            return rgb_to_id.get(px[ax, ay][:3])
        return None

    pid = pid_at(ix, iy)
    if pid is not None and id_to_kind.get(pid) == "land":
        return pid
    for radius in range(1, 17):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if max(abs(dx), abs(dy)) != radius:
                    continue
                nid = pid_at(ix + dx, iy + dy)
                if nid is not None and id_to_kind.get(nid) == "land":
                    return nid
    return None


def _find_sea_touch(
    pts: list[tuple[int, int]],
    px,
    w: int,
    h: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    id_to_kind: dict[int, str],
) -> tuple[int, int] | None:
    """Land pixel that touches sea. 4-connected first, then diagonal."""
    rings = (
        ((1, 0), (-1, 0), (0, 1), (0, -1)),
        ((1, 1), (1, -1), (-1, 1), (-1, -1)),
    )
    for deltas in rings:
        for x, y in pts:
            for dx, dy in deltas:
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h:
                    nid = rgb_to_id.get(px[nx, ny][:3])
                    if nid is not None and id_to_kind.get(nid) == "sea":
                        return x, y
    return None


def _verified_state_xz(
    sid: int,
    pixels: dict[int, list[tuple[int, int]]],
    state_provs: dict[int, list[int]],
    px,
    w: int,
    h: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    id_to_kind: dict[int, str],
    prov_to_state: dict[int, int],
) -> tuple[str, str] | None:
    """x,z that round-trip onto this state's own land (centroid can sit in a strait)."""
    land_pts: list[tuple[int, int]] = []
    for pid in state_provs.get(sid, []):
        land_pts.extend(pixels.get(pid, []))
    if not land_pts:
        return None

    def ok(bmp_x: int, bmp_y: int) -> tuple[str, str] | None:
        x, z = _to_xz(bmp_x, bmp_y, h)
        pid = _province_at(px, x, z, h, rgb_to_id, w, h)
        if pid is not None and id_to_kind.get(pid) == "land" and prov_to_state.get(pid) == sid:
            return x, z
        return None

    for pid in state_provs.get(sid, []):
        pts = pixels.get(pid, [])
        if not pts:
            continue
        got = ok(*_interior_pixel(pts, px, w, h, rgb_to_id, pid))
        if got:
            return got

    got = ok(*_centroid(land_pts))
    if got:
        return got
    step = max(1, len(land_pts) // 40)
    for bmp_x, bmp_y in land_pts[::step]:
        got = ok(bmp_x, bmp_y)
        if got:
            return got
    for bmp_x, bmp_y in land_pts:
        got = ok(bmp_x, bmp_y)
        if got:
            return got
    return None


def retag_buildings_by_province(
    buildings: Path,
    px,
    height: int,
    w: int,
    h: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    id_to_kind: dict[int, str],
    prov_to_state: dict[int, int],
    moved_provs: set[int],
) -> int:
    """Retag only rows on provinces we split. Leave every vanilla row untouched.

    HOI4 checks the *pixel* against the row's state. Rewriting all vanilla tags
    (Aquitaine/Pyrenees, etc.) moved thousands of factories and crashed in
    maparrow.shader while building harbor arrows.
    """
    lines = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: list[str] = []
    changed = 0
    for line in lines:
        parts = line.split(";")
        if len(parts) < 5:
            out.append(line)
            continue
        tagged = None
        if len(parts) >= 7:
            try:
                tagged = int(parts[6])
            except ValueError:
                tagged = None
        pixel_pid = _province_at(px, parts[2], parts[4], height, rgb_to_id, w, h)
        use_pid = None
        if (
            pixel_pid is not None
            and pixel_pid in moved_provs
            and id_to_kind.get(pixel_pid) == "land"
        ):
            use_pid = pixel_pid
        elif tagged in moved_provs and id_to_kind.get(tagged) == "land":
            use_pid = tagged
        if use_pid is None:
            out.append(line)
            continue
        new_state = prov_to_state.get(use_pid)
        if new_state is None:
            out.append(line)
            continue
        while len(parts) < 7:
            parts.append("0")
        if parts[0] != str(new_state) or parts[6] != str(use_pid):
            parts[0] = str(new_state)
            parts[6] = str(use_pid)
            out.append(";".join(parts))
            changed += 1
        else:
            out.append(line)
    if changed:
        write_buildings_txt(buildings, out)
    return changed


def ensure_on_land_sites(
    buildings: Path,
    state_provs: dict[int, list[int]],
    pixels: dict[int, list[tuple[int, int]]],
    px,
    w: int,
    h: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    id_to_kind: dict[int, str],
    state_ids: list[int],
    prov_to_state: dict[int, int],
    coastal_land: set[int],
) -> int:
    """Add air/rocket/port rows for split states only. Never rewrite vanilla harbors.

    Filling every definition.csv coastal tile with a nudger port (lakes, inland
    seas) spawned harbor arrows that crash in maparrow.shader.
    """
    lines = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
    have: dict[int, set[str]] = {}
    ports_on: set[int] = set()
    for line in lines:
        parts = line.split(";")
        if len(parts) < 5:
            continue
        try:
            sid = int(parts[0])
        except ValueError:
            continue
        pixel_pid = _province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
        on_own_land = (
            pixel_pid is not None
            and id_to_kind.get(pixel_pid) == "land"
            and prov_to_state.get(pixel_pid) == sid
        )
        if on_own_land:
            have.setdefault(sid, set()).add(parts[1])
        if parts[1] != "naval_base_spawn" or len(parts) < 7:
            continue
        try:
            tagged = int(parts[6])
        except ValueError:
            continue
        if tagged > 0 and id_to_kind.get(tagged) == "land" and on_own_land:
            ports_on.add(tagged)

    add: list[str] = []
    for sid in state_ids:
        xz = _verified_state_xz(
            sid, pixels, state_provs, px, w, h, rgb_to_id, id_to_kind, prov_to_state
        )
        if xz is None:
            print(f"warning: no land pixel for state {sid}")
            continue
        x, z = xz
        land_pid = _province_at(px, x, z, h, rgb_to_id, w, h) or 0
        existing = have.setdefault(sid, set())
        for kind in REQUIRED_STATE_SITES:
            if kind not in existing:
                add.append(f"{sid};{kind};{x};9.50;{z};0.00;{land_pid}")
                existing.add(kind)
        for pid in state_provs.get(sid, []):
            if pid not in coastal_land or pid in ports_on:
                continue
            # Only new split states plus Koper. Parent leftovers already have
            # vanilla (often sea-tagged) harbors; duplicating them crashed
            # maparrow.shader.
            if sid not in NEW_STATE_IDS and pid != 599:
                continue
            pts = pixels.get(pid, [])
            if not pts:
                print(f"warning: cannot place nudger port on coastal province {pid}")
                continue
            sea = _interior_pixel(pts, px, w, h, rgb_to_id, pid)
            if _find_sea_touch(pts, px, w, h, rgb_to_id, id_to_kind):
                sea = _find_sea_touch(pts, px, w, h, rgb_to_id, id_to_kind) or sea
            px_, pz = _to_xz(sea[0], sea[1], h)
            add.append(f"{sid};naval_base_spawn;{px_};9.50;{pz};0.00;{pid}")
            ports_on.add(pid)
    if add:
        append_building_lines(buildings, add)
    return len(add)


def snap_state_sites_to_land(
    buildings: Path,
    state_ids: set[int],
    state_provs: dict[int, list[int]],
    pixels: dict[int, list[tuple[int, int]]],
    px,
    w: int,
    h: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    id_to_kind: dict[int, str],
    prov_to_state: dict[int, int],
) -> int:
    """Move leftover air/rocket rows off water after island splits. Leave harbors."""
    water_ok = {"naval_base_spawn", "floating_harbor"}
    lines = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: list[str] = []
    changed = 0
    xz_cache: dict[int, tuple[str, str] | None] = {}
    for line in lines:
        parts = line.split(";")
        if len(parts) < 5:
            out.append(line)
            continue
        try:
            sid = int(parts[0])
        except ValueError:
            out.append(line)
            continue
        if sid not in state_ids or parts[1] in water_ok:
            out.append(line)
            continue
        pid = _province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
        if pid is not None and id_to_kind.get(pid) == "land" and prov_to_state.get(pid) == sid:
            out.append(line)
            continue
        if sid not in xz_cache:
            xz_cache[sid] = _verified_state_xz(
                sid, pixels, state_provs, px, w, h, rgb_to_id, id_to_kind, prov_to_state
            )
        xz = xz_cache[sid]
        if xz is None:
            out.append(line)
            continue
        parts[2], parts[4] = xz
        out.append(";".join(parts))
        changed += 1
    if changed:
        write_buildings_txt(buildings, out)
    return changed


NEW_STATE_SET = set(NEW_STATE_IDS)
PARENT_STATE_SET = set(SPLIT_PARENT_IDS)
REQUIRED_PORTS = (
    379, 599, 721, 3755, 4135, 4155, 7123, 7590, WES_SOUTH_PROV, 9945, 10752, 10891, 13084, MAYOTTE_PROV,
)


def reconcile_split_buildings(
    buildings: Path,
    px,
    w: int,
    h: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    id_to_kind: dict[int, str],
    prov_to_state: dict[int, int],
    state_provs: dict[int, list[int]],
    pixels: dict[int, list[tuple[int, int]]],
    moved_provs: set[int],
) -> int:
    """Make each row's state match the land pixel HOI4 will sample, then snap.

    New-state rows keep their state id and move onto that state's land. Vanilla
    rows that now sit on a split-out province are retagged to the child.
    """
    water_ok = {"naval_base_spawn", "floating_harbor"}
    lines = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
    out: list[str] = []
    changed = 0
    xz_cache: dict[int, tuple[str, str] | None] = {}

    def xz_for(sid: int) -> tuple[str, str] | None:
        if sid not in xz_cache:
            xz_cache[sid] = _verified_state_xz(
                sid, pixels, state_provs, px, w, h, rgb_to_id, id_to_kind, prov_to_state
            )
        return xz_cache[sid]

    for line in lines:
        parts = line.split(";")
        if len(parts) < 5:
            if line.strip():
                out.append(line)
            continue
        while len(parts) < 7:
            parts.append("0")
        parts = parts[:7]
        try:
            row_sid = int(parts[0])
        except ValueError:
            out.append(";".join(parts))
            continue
        pixel_pid = _province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
        pixel_kind = id_to_kind.get(pixel_pid) if pixel_pid is not None else None
        # Vanilla sea harbors must stay in the water. Snapping them onto land
        # crashed maparrow.shader; a land port on the wrong state is ignored
        # (716) and then coastal-without-port crashes.
        if parts[1] in water_ok and pixel_kind != "land":
            out.append(";".join(parts))
            continue
        if pixel_kind != "land":
            pixel_pid = _land_province_near(
                px, parts[2], parts[4], h, rgb_to_id, id_to_kind, w, h
            )
        actual = prov_to_state.get(pixel_pid) if pixel_pid is not None else None
        if actual == row_sid:
            out.append(";".join(parts))
            continue
        split_related = (
            row_sid in NEW_STATE_SET
            or row_sid in PARENT_STATE_SET
            or (actual in NEW_STATE_SET if actual is not None else False)
            or (pixel_pid in moved_provs if pixel_pid is not None else False)
        )
        if not split_related:
            out.append(";".join(parts))
            continue
        if row_sid in NEW_STATE_SET:
            xz = None
            if parts[1] in water_ok:
                for pid in state_provs.get(row_sid, []):
                    pts = pixels.get(pid, [])
                    if not pts:
                        continue
                    sea = _find_sea_touch(pts, px, w, h, rgb_to_id, id_to_kind)
                    if sea is None:
                        sea = _interior_pixel(pts, px, w, h, rgb_to_id, pid)
                    cand = _to_xz(sea[0], sea[1], h)
                    if _province_at(px, cand[0], cand[1], h, rgb_to_id, w, h) == pid:
                        xz = cand
                        parts[6] = str(pid)
                        break
            if xz is None:
                xz = xz_for(row_sid)
            if xz is None:
                out.append(";".join(parts))
                continue
            parts[2], parts[4] = xz
            npid = _province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
            if npid is not None and prov_to_state.get(npid) == row_sid:
                parts[6] = str(npid)
            changed += 1
            out.append(";".join(parts))
            continue
        if actual in NEW_STATE_SET and pixel_pid is not None:
            parts[0] = str(actual)
            parts[6] = str(pixel_pid)
            # Keep vanilla harbor coords: HOI4 already samples this land pixel.
            # Snapping them was moving ports onto the neighbor tile.
            if parts[1] not in water_ok:
                pts = pixels.get(pixel_pid, [])
                if pts:
                    ix, iy = _interior_pixel(pts, px, w, h, rgb_to_id, pixel_pid)
                    parts[2], parts[4] = _to_xz(ix, iy, h)
            changed += 1
        elif actual is None:
            xz = xz_for(row_sid)
            if xz is not None:
                parts[2], parts[4] = xz
                changed += 1
        out.append(";".join(parts))
    write_buildings_txt(buildings, out)
    return changed


def place_required_ports(
    buildings: Path,
    px,
    w: int,
    h: int,
    rgb_to_id: dict[tuple[int, int, int], int],
    id_to_kind: dict[int, str],
    prov_to_state: dict[int, int],
    pixels: dict[int, list[tuple[int, int]]],
    coastal_land: set[int],
) -> int:
    """Force land-tagged ports whose coords round-trip onto the crash provinces."""
    lines = [
        ln
        for ln in buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
        if ln.strip()
    ]
    have: set[int] = set()
    kept: list[str] = []
    for line in lines:
        parts = line.split(";")
        if len(parts) != 7:
            kept.append(line)
            continue
        if parts[1] == "naval_base_spawn":
            try:
                tag = int(parts[6])
            except ValueError:
                kept.append(line)
                continue
            pid = _province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
            if tag in REQUIRED_PORTS and (pid != tag or id_to_kind.get(pid) != "land"):
                continue
            if pid == tag and tag in coastal_land:
                have.add(tag)
        kept.append(line)
    add: list[str] = []
    for pid in REQUIRED_PORTS:
        if pid in have or pid not in coastal_land:
            continue
        sid = prov_to_state.get(pid)
        pts = pixels.get(pid, [])
        if sid is None or not pts:
            print(f"warning: cannot place required port {pid}")
            continue
        ix, iy = _interior_pixel(pts, px, w, h, rgb_to_id, pid)
        sea = _find_sea_touch(pts, px, w, h, rgb_to_id, id_to_kind)
        if sea is not None and rgb_to_id.get(px[sea[0], sea[1]][:3]) == pid:
            ix, iy = sea
        x, z = _to_xz(ix, iy, h)
        if _province_at(px, x, z, h, rgb_to_id, w, h) != pid:
            ix, iy = _interior_pixel(pts, px, w, h, rgb_to_id, pid)
            x, z = _to_xz(ix, iy, h)
        add.append(f"{sid};naval_base_spawn;{x};9.50;{z};0.00;{pid}")
        have.add(pid)
    if add:
        kept.extend(add)
    write_buildings_txt(buildings, kept)
    missing = [pid for pid in REQUIRED_PORTS if pid in coastal_land and pid not in have]
    if missing:
        raise SystemExit(f"required coastal ports missing (will crash HOI4): {missing}")
    return len(add)


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


def ensure_wes_south_definition(definition: Path) -> None:
    text = definition.read_text(encoding="utf-8", errors="ignore")
    extra = []
    if f"{WES_SOUTH_PROV};" not in text:
        r, g, b = WES_SOUTH_RGB
        extra.append(f"{WES_SOUTH_PROV};{r};{g};{b};land;true;desert;5")
    if f"{WES_ISTHMUS_PROV};" not in text:
        r, g, b = WES_ISTHMUS_RGB
        extra.append(f"{WES_ISTHMUS_PROV};{r};{g};{b};land;false;desert;5")
    if extra:
        definition.write_text(text.rstrip() + "\n" + "\n".join(extra) + "\n", encoding="utf-8")


def patch_wes_south_unitstacks(path: Path, bmp_path: Path) -> None:
    """Park 7979 stacks on the north blob; clone them onto 13415 in the south."""
    im = Image.open(bmp_path)
    px = im.load()
    h = im.size[1]
    x0, x1, y0, y1 = SAHARA_BBOX
    north, south = [], []
    try:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = px[x, y][:3]
                if rgb == WES_FREE_RGB:
                    north.append((x, y))
                elif rgb == WES_SOUTH_RGB:
                    south.append((x, y))
    finally:
        im.close()
    if not north or not south:
        return
    nx, nz = _to_xz(int(sum(p[0] for p in north) / len(north)), int(sum(p[1] for p in north) / len(north)), h)
    sx, sz = _to_xz(int(sum(p[0] for p in south) / len(south)), int(sum(p[1] for p in south) / len(south)), h)
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    kept = []
    src = []
    for line in lines:
        if line.startswith(f"{WES_SOUTH_PROV};"):
            continue
        if line.startswith("7979;"):
            src.append(line)
        kept.append(line)
    xs, zs = [], []
    for line in src:
        parts = line.split(";")
        if len(parts) >= 5:
            try:
                xs.append(float(parts[2]))
                zs.append(float(parts[4]))
            except ValueError:
                pass
    if not xs:
        return
    avg_x = sum(xs) / len(xs)
    avg_z = sum(zs) / len(zs)
    ndx = float(nx) - avg_x
    ndz = float(nz) - avg_z
    sdx = float(sx) - avg_x
    sdz = float(sz) - avg_z
    out = []
    extra = []
    for line in kept:
        if line.startswith("7979;"):
            parts = line.split(";")
            if len(parts) >= 5:
                try:
                    parts[2] = f"{float(parts[2]) + ndx:.2f}"
                    parts[4] = f"{float(parts[4]) + ndz:.2f}"
                    south_parts = parts[:]
                    south_parts[0] = str(WES_SOUTH_PROV)
                    south_parts[2] = f"{float(line.split(';')[2]) + sdx:.2f}"
                    south_parts[4] = f"{float(line.split(';')[4]) + sdz:.2f}"
                    extra.append(";".join(south_parts))
                    line = ";".join(parts)
                except ValueError:
                    pass
        out.append(line)
    path.write_text("\n".join(out + extra) + "\n", encoding="utf-8")


def patch_wes_isthmus_unitstacks(path: Path, bmp_path: Path) -> None:
    """Park 13415/13416 stacks on their own blobs. Leaves 7979 alone."""
    im = Image.open(bmp_path)
    px = im.load()
    h = im.size[1]
    x0, x1, y0, y1 = SAHARA_BBOX
    blobs = {WES_SOUTH_RGB: [], WES_ISTHMUS_RGB: []}
    try:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                rgb = px[x, y][:3]
                if rgb in blobs:
                    blobs[rgb].append((x, y))
    finally:
        im.close()
    if not blobs[WES_SOUTH_RGB] or not blobs[WES_ISTHMUS_RGB]:
        return
    cents = {}
    for rgb, pts in blobs.items():
        pid = WES_SOUTH_PROV if rgb == WES_SOUTH_RGB else WES_ISTHMUS_PROV
        cents[pid] = _to_xz(
            int(sum(p[0] for p in pts) / len(pts)),
            int(sum(p[1] for p in pts) / len(pts)),
            h,
        )
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    src = [ln for ln in lines if ln.startswith(f"{WES_SOUTH_PROV};")]
    if not src:
        src = [ln for ln in lines if ln.startswith("7979;")]
    if not src:
        return
    kept = [
        ln
        for ln in lines
        if not ln.startswith(f"{WES_SOUTH_PROV};") and not ln.startswith(f"{WES_ISTHMUS_PROV};")
    ]
    xs, zs = [], []
    for line in src:
        parts = line.split(";")
        if len(parts) >= 5:
            try:
                xs.append(float(parts[2]))
                zs.append(float(parts[4]))
            except ValueError:
                pass
    if not xs:
        return
    avg_x = sum(xs) / len(xs)
    avg_z = sum(zs) / len(zs)
    extra = []
    for pid, (tx, tz) in cents.items():
        dx = float(tx) - avg_x
        dz = float(tz) - avg_z
        for line in src:
            parts = line.split(";")
            if len(parts) < 5:
                continue
            try:
                parts[0] = str(pid)
                parts[2] = f"{float(parts[2]) + dx:.2f}"
                parts[4] = f"{float(parts[4]) + dz:.2f}"
                extra.append(";".join(parts))
            except ValueError:
                pass
    path.write_text("\n".join(kept + extra) + "\n", encoding="utf-8")


def patch_split_railways() -> None:
    """Reroute vanilla rails whose hops we broke by thinning or shrinking.

    HOI4 access-violates while building the railway graph if two consecutive
    provinces no longer share a pixel edge (LastRead map/railways.txt).
    """
    src = VANILLA_MAP / "railways.txt"
    dest = MOD_MAP / "railways.txt"
    text = src.read_text(encoding="utf-8")
    repls = (
        ("1 5 6626 11735 11564 13252 3601", "1 6 6626 599 11735 11564 13252 3601"),
        ("2 6 476 9423 9576 754 741 11670", "2 7 476 6455 9423 9576 754 741 11670"),
        ("1 6 754 3757 3575 6597 409 3452", "1 7 754 9714 3757 3575 6597 409 3452"),
        ("1 2 1111 12100", "1 3 1111 7215 12100"),
    )
    for old, new in repls:
        if new not in text:
            text = text.replace(old, new)
    dest.write_bytes(text.encode("utf-8"))


def patch_strategic_region() -> None:
    patches = (
        (Path("strategicregions") / "102-East African Coast.txt", "13072 ", f"13072 {MAYOTTE_PROV} "),
        (Path("strategicregions") / "182-North West Africa.txt", "7979 ", f"7979 {WES_SOUTH_PROV} "),
        (Path("strategicregions") / "182-North West Africa.txt", f"{WES_SOUTH_PROV} ", f"{WES_SOUTH_PROV} {WES_ISTHMUS_PROV} "),
        (Path("strategicregions") / "127-Saharadesert.txt", "2068 ", f"2068 {AZA_TINZ_PROV} {AZA_TESS_PROV} {AZA_KIDAL_PROV} "),
        (Path("strategicregions") / "140-Sub-Sarhan Africa.txt", "7930 ", f"7930 {AZA_TIMB_PROV} "),
    )
    for rel, needle, repl in patches:
        dest = MOD_MAP / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        src = VANILLA_MAP / rel
        if not dest.exists():
            shutil.copy2(src, dest)
        text = dest.read_text(encoding="utf-8", errors="ignore")
        token = repl.strip().split()[-1]
        if token in text:
            continue
        dest.write_text(text.replace(needle, repl), encoding="utf-8")


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
    shrink_gibraltar_pixels(bmp)
    shrink_melilla_pixels(bmp)
    shrink_golan_pixels(bmp)
    shrink_guantanamo_pixels(bmp)
    nudge_guantanamo_unitstacks(unitstacks)
    thin_transnistria_pixels(bmp, definition)
    paint_koper_coast(bmp)
    paint_sahara_free_zone(bmp)
    paint_aksai_chin(bmp)
    paint_kherson_front(bmp)
    paint_azawad_pockets(bmp)
    ensure_wes_south_definition(definition)
    ensure_azawad_definition(definition)
    mark_koper_coastal(definition)
    mark_wes_coastal(definition)
    patch_wes_south_unitstacks(unitstacks, bmp)
    patch_wes_isthmus_unitstacks(unitstacks, bmp)
    patch_azawad_unitstacks(unitstacks, bmp)

    patch_strategic_region()
    patch_split_railways()

    # Always start from vanilla buildings.txt so retags are not deleted on
    # the next run. Retag only split/moved provinces, then add missing
    # air/rocket/port sites on those states' own land.
    shutil.copy2(VANILLA_MAP / "buildings.txt", buildings)

    rgb_to_id, id_to_kind = load_definition_maps(definition)
    state_provs = parse_state_provinces(ROOT / "history" / "states")
    prov_to_state = {pid: sid for sid, pids in state_provs.items() for pid in pids}

    im = Image.open(bmp)
    try:
        w, h = im.size
        px = im.load()
        moved_provs = set()
        for sid in NEW_STATE_IDS:
            moved_provs.update(state_provs.get(sid, []))
        moved_provs.update({1041, 9423, 2063, 599, 6626, 4135, 7153, 7979, 10875, 5012, 4920, WES_SOUTH_PROV, WES_ISTHMUS_PROV, 5042, 10821, 721, 3755, 409, 574, 3403, 6597, 9573, 11546, 11683, 11715, 1065, 1201, 4206, 3575, 3738, 3757, 9698, 9714, 11670, 11703})
        n_retag = retag_buildings_by_province(
            buildings, px, h, w, h, rgb_to_id, id_to_kind, prov_to_state, moved_provs
        )
        # Vanilla 736 harbor sat in Croatian Istria water after Pola split.
        before = buildings.read_text(encoding="utf-8", errors="ignore").splitlines()
        kept = [ln for ln in before if not ln.startswith("736;floating_harbor;")]
        if len(kept) != len(before):
            write_buildings_txt(buildings, kept)

        wanted: set[int] = set()
        ensure_ids = sorted(set(NEW_STATE_IDS) | SPLIT_PARENT_IDS)
        for sid in ensure_ids:
            wanted.update(state_provs.get(sid, []))
        coastal_land = load_coastal_land(definition)
        wanted.update(coastal_land)
        wanted.update(REQUIRED_PORTS)
        pixels = index_province_pixels(im, rgb_to_id, wanted)
        n_add = ensure_on_land_sites(
            buildings,
            state_provs,
            pixels,
            px,
            w,
            h,
            rgb_to_id,
            id_to_kind,
            ensure_ids,
            prov_to_state,
            coastal_land,
        )
        n_snap = snap_state_sites_to_land(
            buildings,
            set(ensure_ids),
            state_provs,
            pixels,
            px,
            w,
            h,
            rgb_to_id,
            id_to_kind,
            prov_to_state,
        )
        n_fix = reconcile_split_buildings(
            buildings,
            px,
            w,
            h,
            rgb_to_id,
            id_to_kind,
            prov_to_state,
            state_provs,
            pixels,
            moved_provs,
        )
        n_req = place_required_ports(
            buildings,
            px,
            w,
            h,
            rgb_to_id,
            id_to_kind,
            prov_to_state,
            pixels,
            coastal_land,
        )
        print(
            f"buildings: retagged {n_retag} rows, added {n_add} on-land sites, "
            f"snapped {n_snap} off water, reconciled {n_fix}, required ports {n_req}"
        )
        _strip_blank_building_lines(buildings)
        have_port: set[int] = set()
        mismatches: list[str] = []
        bad_fields = 0
        required_ok: dict[int, bool] = {pid: False for pid in REQUIRED_PORTS}
        for i, line in enumerate(
            buildings.read_text(encoding="utf-8", errors="ignore").splitlines(), 1
        ):
            parts = line.split(";")
            if not line.strip():
                continue
            if len(parts) != 7:
                bad_fields += 1
                print(f"warning: buildings.txt line {i} has {len(parts)} fields")
                continue
            try:
                sid = int(parts[0])
                tagged = int(parts[6])
            except ValueError:
                continue
            pid = _province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
            if parts[1] == "naval_base_spawn" and tagged in coastal_land:
                have_port.add(tagged)
            if pid is not None and tagged in REQUIRED_PORTS and pid == tagged:
                actual = prov_to_state.get(pid)
                if actual == sid and id_to_kind.get(pid) == "land":
                    required_ok[tagged] = True
            if pid is None or id_to_kind.get(pid) != "land":
                continue
            actual = prov_to_state.get(pid)
            if actual is None or actual == sid:
                continue
            if sid in NEW_STATE_SET or sid in PARENT_STATE_SET or actual in NEW_STATE_SET:
                mismatches.append(
                    f"L{i} {parts[1]} row={sid} pixel={actual} tag={tagged} pid={pid}"
                )
        if mismatches:
            print(f"warning: {len(mismatches)} remaining split-state 716 mismatches:")
            for msg in mismatches[:25]:
                print(" ", msg)
        if bad_fields:
            print(f"warning: {bad_fields} buildings.txt lines with !=7 fields")
        missing_ok = [pid for pid, ok in required_ok.items() if pid in coastal_land and not ok]
        if missing_ok:
            raise SystemExit(
                f"required coastal ports do not round-trip onto their land (will crash HOI4): {missing_ok}"
            )
        missing_ports = [
            pid
            for sid in ensure_ids
            for pid in state_provs.get(sid, [])
            if pid in coastal_land and pid not in have_port
        ]
        if missing_ports:
            print(f"warning: split-state coastal provinces missing nudger ports: {missing_ports}")
        required = [pid for pid in REQUIRED_PORTS if pid in coastal_land and pid not in have_port]
        if required:
            raise SystemExit(f"required coastal ports missing (will crash HOI4): {required}")
    finally:
        _close_images(im)


if __name__ == "__main__":
    ensure_map_splits()
    print("map splits ready")
