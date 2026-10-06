# -*- coding: utf-8 -*-
"""Split NYC / LA / Houston into 3 provinces each and carve metro states.

NY Island (1125) keeps province 859 only.
New states:
  1138 New York City  - 3878 + 2 new
  1139 Los Angeles    - 9814 + 2 new
  1140 Houston        - 10337 + 2 new
"""
from __future__ import annotations

import re
import shutil
import struct
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "map"
STATES = ROOT / "history" / "states"
VANILLA_REGIONS = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\map\strategicregions"
)

# parent_id -> (new_id_a, new_id_b, rgb_a, rgb_b)
SPLITS = {
    3878: (13421, 13422, (40, 200, 90), (55, 40, 210)),   # NYC
    9814: (13423, 13424, (200, 40, 80), (90, 180, 40)),   # LA
    10337: (13425, 13426, (40, 90, 200), (210, 120, 40)), # Houston
}


def load_definition(path: Path):
    rgb_to_id = {}
    id_to_line = {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for ln in lines:
        if not ln.strip() or ln.startswith("#"):
            continue
        parts = ln.split(";")
        if len(parts) < 5:
            continue
        try:
            pid = int(parts[0])
            rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
        except ValueError:
            continue
        rgb_to_id[rgb] = pid
        id_to_line[pid] = ln
    return rgb_to_id, id_to_line, lines


def collect_pixels(im: Image.Image, rgb: tuple[int, int, int]):
    px = im.load()
    w, h = im.size
    pts = []
    for y in range(h):
        for x in range(w):
            if px[x, y][:3] == rgb:
                pts.append((x, y))
    return pts


def split_pixels_by_x(pts: list[tuple[int, int]]):
    """Partition into 3 strips by x so each keeps roughly equal pixels."""
    if len(pts) < 3:
        raise SystemExit(f"too few pixels to split: {len(pts)}")
    xs = sorted(p[0] for p in pts)
    n = len(xs)
    t1 = xs[n // 3]
    t2 = xs[(2 * n) // 3]
    # ensure progress
    if t1 >= t2:
        t2 = t1 + 1
    a, b, c = [], [], []
    for p in pts:
        if p[0] < t1:
            a.append(p)
        elif p[0] < t2:
            b.append(p)
        else:
            c.append(p)
    # rebalance empties
    buckets = [a, b, c]
    for i, bucket in enumerate(buckets):
        if not bucket:
            donor = max(range(3), key=lambda j: len(buckets[j]))
            if len(buckets[donor]) < 2:
                raise SystemExit("cannot rebalance empty strip")
            buckets[i].append(buckets[donor].pop())
    return buckets


def paint_splits():
    defn_path = MAP / "definition.csv"
    bmp_path = MAP / "provinces.bmp"
    rgb_to_id, id_to_line, lines = load_definition(defn_path)

    # ensure new RGBs unused
    for parent, (na, nb, ra, rb) in SPLITS.items():
        for rgb, nid in ((ra, na), (rb, nb)):
            if rgb in rgb_to_id:
                raise SystemExit(f"RGB {rgb} already used by {rgb_to_id[rgb]}")
            if nid in id_to_line:
                raise SystemExit(f"province id {nid} already exists")

    im = Image.open(bmp_path).convert("RGB")
    px = im.load()
    parent_rgb = {}
    for parent in SPLITS:
        parts = id_to_line[parent].split(";")
        parent_rgb[parent] = (int(parts[1]), int(parts[2]), int(parts[3]))

    report = {}
    for parent, (na, nb, ra, rb) in SPLITS.items():
        prgb = parent_rgb[parent]
        pts = collect_pixels(im, prgb)
        strips = split_pixels_by_x(pts)
        # Keep middle strip as original parent (usually city core).
        keep, new_a, new_b = strips[1], strips[0], strips[2]
        for x, y in new_a:
            px[x, y] = ra
        for x, y in new_b:
            px[x, y] = rb
        report[parent] = {
            "keep": len(keep),
            na: len(new_a),
            nb: len(new_b),
            "total": len(pts),
        }
        # append definition lines (coastal true like parent; urban)
        parent_parts = id_to_line[parent].split(";")
        # id;r;g;b;land;coastal;terrain;continent
        coastal = parent_parts[5] if len(parent_parts) > 5 else "true"
        terrain = parent_parts[6] if len(parent_parts) > 6 else "urban"
        continent = parent_parts[7] if len(parent_parts) > 7 else "2"
        for nid, rgb in ((na, ra), (nb, rb)):
            lines.append(
                f"{nid};{rgb[0]};{rgb[1]};{rgb[2]};land;{coastal};{terrain};{continent}"
            )
            print(f"added province {nid} from {parent} rgb={rgb}")

    im.save(bmp_path)
    # definition must end with newline
    text = "\n".join(lines) + "\n"
    defn_path.write_text(text, encoding="utf-8")
    print("paint report", report)
    return report


def patch_strategic_regions():
    mapping = {
        "197-New England.txt": [13421, 13422],
        "218-California.txt": [13423, 13424],
        "119-South West.txt": [13425, 13426],
    }
    dest_dir = MAP / "strategicregions"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for fname, extra in mapping.items():
        src = VANILLA_REGIONS / fname
        dest = dest_dir / fname
        text = src.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"(provinces\s*=\s*\{)([^}]*)(\})", text, re.S)
        if not m:
            raise SystemExit(f"no provinces block in {fname}")
        body = m.group(2)
        for pid in extra:
            if re.search(rf"\b{pid}\b", body):
                continue
            body = body.rstrip() + f" {pid}"
            if not body.endswith("\n") and "\n" in m.group(2):
                body += "\n\t\t"
        text = text[: m.start(2)] + body + text[m.end(2) :]
        dest.write_text(text, encoding="utf-8", newline="\n")
        print(f"strategic region {fname} += {extra}")


def write_states():
    # 1125 keeps only 859
    (STATES / "1125-New York Finance.txt").write_text(
        """state={
	id=1125
	name="STATE_1125"
	manpower = 800000
	state_category = city
	history={
		owner = USA
		add_extra_state_shared_building_slots = 2
		add_core_of = USA
		buildings = {
			infrastructure = 4
			industrial_complex = 1
			finance_center = 1
			services_building = 1
		}
	}
	provinces={
		859
	}
	local_supplies=0.0
}
""",
        encoding="utf-8",
        newline="\n",
    )

    (STATES / "1138-New York City.txt").write_text(
        """state={
	id=1138
	name="STATE_1138"
	manpower = 8400000
	state_category = megalopolis
	history={
		owner = USA
		add_extra_state_shared_building_slots = 8
		add_core_of = USA
		victory_points = { # New York
			3878 35
		}
		buildings = {
			infrastructure = 5
			industrial_complex = 5
			finance_center = 3
			services_building = 3
			air_base = 1
			3878 = {
				supply_node = 1
				naval_base = 1
				landmark_statue_of_liberty = {
					level = 1
					allowed = { has_dlc = "Gotterdammerung" }
				}
			}
		}
	}
	provinces={
		3878 13421 13422
	}
	local_supplies=0.0
}
""",
        encoding="utf-8",
        newline="\n",
    )

    (STATES / "1139-Los Angeles.txt").write_text(
        """state={
	id=1139
	name="STATE_1139"
	manpower = 10000000
	state_category = megalopolis
	history={
		owner = USA
		add_extra_state_shared_building_slots = 10
		add_core_of = USA
		victory_points = { # Los Angeles
			9814 30
		}
		buildings = {
			infrastructure = 5
			industrial_complex = 6
			dockyard = 1
			air_base = 2
			finance_center = 1
			services_building = 3
			9814 = {
				supply_node = 1
				naval_supply_hub = 1
				naval_base = 10
			}
		}
	}
	provinces={
		9814 13423 13424
	}
	local_supplies=0.0
}
""",
        encoding="utf-8",
        newline="\n",
    )

    (STATES / "1140-Houston.txt").write_text(
        """state={
	id=1140
	name="STATE_1140"
	manpower = 4500000
	state_category = metropolis
	history={
		owner = USA
		add_extra_state_shared_building_slots = 6
		add_core_of = USA
		victory_points = { # Houston
			10337 25
		}
		buildings = {
			infrastructure = 4
			industrial_complex = 4
			arms_factory = 1
			air_base = 1
			services_building = 2
			10337 = { naval_base = 1 }
		}
	}
	provinces={
		10337 13425 13426
	}
	local_supplies=0.0
}
""",
        encoding="utf-8",
        newline="\n",
    )

    # Remove LA from California
    cal = STATES / "378-California.txt"
    text = cal.read_text(encoding="utf-8")
    # remove 9814 from provinces list
    text = re.sub(r"\b9814\b", "", text)
    # remove LA victory points block
    text = re.sub(
        r"\s*victory_points\s*=\s*\{\s*#\s*Los Angeles\s*9814\s+\d+\s*\}",
        "",
        text,
        flags=re.S,
    )
    # remove 9814 building block
    text = re.sub(
        r"\n9814\s*=\s*\{[^}]*\}",
        "",
        text,
        flags=re.S,
    )
    # reduce manpower roughly
    text = re.sub(r"manpower\s*=\s*\d+", "manpower = 27213878", text, count=1)
    cal.write_text(text, encoding="utf-8", newline="\n")

    # Remove Houston from Gulf Oil 1126
    gulf = STATES / "1126-Gulf Oil.txt"
    text = gulf.read_text(encoding="utf-8")
    text = re.sub(r"\b10337\b", "", text)
    text = re.sub(
        r"\s*victory_points\s*=\s*\{\s*#\s*Houston\s*10337\s+\d+\s*\}",
        "",
        text,
        flags=re.S,
    )
    text = re.sub(r"\n\s*10337\s*=\s*\{[^}]*\}", "", text, flags=re.S)
    text = re.sub(r"manpower\s*=\s*\d+", "manpower = 2500000", text, count=1)
    gulf.write_text(text, encoding="utf-8", newline="\n")
    print("states written/updated")


def patch_buildings_state_ids():
    path = MAP / "buildings.txt"
    if not path.exists():
        return
    # map province -> new state
    prov_state = {
        3878: 1138,
        13421: 1138,
        13422: 1138,
        859: 1125,
        9814: 1139,
        13423: 1139,
        13424: 1139,
        10337: 1140,
        13425: 1140,
        13426: 1140,
    }
    out = []
    changed = 0
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines(True):
        # format: state;type;x;y;z;rot;province
        parts = ln.strip().split(";")
        if len(parts) >= 7 and parts[0].isdigit() and parts[-1].isdigit():
            prov = int(parts[-1])
            if prov in prov_state and int(parts[0]) != prov_state[prov]:
                parts[0] = str(prov_state[prov])
                ln = ";".join(parts) + ("\n" if ln.endswith("\n") else "")
                changed += 1
        out.append(ln)
    path.write_text("".join(out), encoding="utf-8")
    print(f"buildings.txt state retargets: {changed}")


def patch_cw_transfers():
    path = ROOT / "common" / "scripted_effects" / "doomsday_usa.txt"
    text = path.read_text(encoding="utf-8")
    # NYF also gets NYC
    old_nyf = """		NYF = {
			transfer_state = 1125
			add_state_core = 1125
			set_capital = { state = 1125 }
			set_country_flag = dd_cw_released
		}"""
    new_nyf = """		NYF = {
			transfer_state = 1125
			add_state_core = 1125
			transfer_state = 1138
			add_state_core = 1138
			set_capital = { state = 1138 }
			set_country_flag = dd_cw_released
		}"""
    if old_nyf not in text:
        raise SystemExit("NYF block not found")
    text = text.replace(old_nyf, new_nyf)

    # WCL gets LA
    old_wcl = """			WCL = {
				transfer_state = 378
				add_state_core = 378
				transfer_state = 377
				add_state_core = 377
				transfer_state = 376
				add_state_core = 376
				set_capital = { state = 378 }
				set_country_flag = dd_cw_released
			}"""
    new_wcl = """			WCL = {
				transfer_state = 378
				add_state_core = 378
				transfer_state = 1139
				add_state_core = 1139
				transfer_state = 377
				add_state_core = 377
				transfer_state = 376
				add_state_core = 376
				set_capital = { state = 378 }
				set_country_flag = dd_cw_released
			}"""
    if old_wcl not in text:
        raise SystemExit("WCL block not found")
    text = text.replace(old_wcl, new_wcl)

    old_txo = """		TXO = {
			transfer_state = 1126
			add_state_core = 1126
			transfer_state = 1133
			add_state_core = 1133
			set_country_flag = dd_cw_released
		}"""
    new_txo = """		TXO = {
			transfer_state = 1126
			add_state_core = 1126
			transfer_state = 1140
			add_state_core = 1140
			transfer_state = 1133
			add_state_core = 1133
			set_country_flag = dd_cw_released
		}"""
    if old_txo not in text:
        raise SystemExit("TXO block not found")
    text = text.replace(old_txo, new_txo)
    path.write_text(text, encoding="utf-8", newline="\n")
    print("CW transfers updated")


def patch_loc():
    usa = ROOT / "localisation" / "english" / "doomsday_usa_l_english.yml"
    raw = usa.read_bytes()
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig")
    text = text.replace('STATE_1125:0 "New York Island"', 'STATE_1125:0 "New York Island"')
    additions = []
    if "STATE_1138:" not in text:
        additions.append(' STATE_1138:0 "New York City"\n')
    if "STATE_1139:" not in text:
        additions.append(' STATE_1139:0 "Los Angeles"\n')
    if "STATE_1140:" not in text:
        additions.append(' STATE_1140:0 "Houston"\n')
    if additions:
        # insert after STATE_1137 if present else end of file before last lines
        if "STATE_1137:" in text:
            text = text.replace(
                ' STATE_1137:0 "Minneapolis"\n',
                ' STATE_1137:0 "Minneapolis"\n' + "".join(additions),
            )
        else:
            text = text.rstrip() + "\n" + "".join(additions)
    usa.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
    print("loc updated")


def verify():
    print("\n=== MAP VERIFY ===")
    rgb_to_id, id_to_line, _ = load_definition(MAP / "definition.csv")
    im = Image.open(MAP / "provinces.bmp").convert("RGB")
    px = im.load()
    w, h = im.size
    used = set()
    unknown = {}
    for y in range(h):
        for x in range(w):
            rgb = px[x, y][:3]
            pid = rgb_to_id.get(rgb)
            if pid is None:
                unknown[rgb] = unknown.get(rgb, 0) + 1
            else:
                used.add(pid)
    print(f"definition entries: {len(id_to_line)}")
    print(f"colors used on bmp: {len(used)}")
    print(f"unknown colors: {len(unknown)}")
    if unknown:
        for rgb, c in sorted(unknown.items(), key=lambda kv: -kv[1])[:10]:
            print("  ", rgb, c)

    # every land province in exactly one state
    land_ids = set()
    for pid, ln in id_to_line.items():
        if ";land;" in ln or ln.split(";")[4] == "land":
            land_ids.add(pid)
    owned = {}
    dups = []
    missing_state = []
    for p in STATES.glob("*.txt"):
        t = p.read_text(encoding="utf-8", errors="replace")
        m = re.search(r"id\s*=\s*(\d+)", t)
        pm = re.search(r"provinces\s*=\s*\{([^}]*)\}", t, re.S)
        if not m or not pm:
            continue
        sid = int(m.group(1))
        for pid in map(int, re.findall(r"\d+", pm.group(1))):
            if pid in owned:
                dups.append((pid, owned[pid], sid, p.name))
            owned[pid] = sid
    for pid in sorted(SPLITS.keys()) + [p for v in SPLITS.values() for p in v[:2]] + [859]:
        print(f"  province {pid} -> state {owned.get(pid, 'MISSING')} pixels_in_bmp={pid in used}")
    print(f"duplicate province assignments: {len(dups)}")
    for d in dups[:10]:
        print("  DUP", d)
    # new provinces must be in strategic regions
    for fname, extras in (
        ("197-New England.txt", [13421, 13422, 3878, 859]),
        ("218-California.txt", [13423, 13424, 9814]),
        ("119-South West.txt", [13425, 13426, 10337]),
    ):
        t = (MAP / "strategicregions" / fname).read_text(encoding="utf-8")
        for pid in extras:
            ok = re.search(rf"\b{pid}\b", t) is not None
            print(f"  region {fname} has {pid}: {ok}")
    # state files exist
    for sid, name in ((1138, "New York City"), (1139, "Los Angeles"), (1140, "Houston")):
        hits = list(STATES.glob(f"{sid}-*.txt"))
        print(f"  state {sid} ({name}) file: {hits[0].name if hits else 'MISSING'}")


def main():
    paint_splits()
    patch_strategic_regions()
    write_states()
    patch_buildings_state_ids()
    patch_cw_transfers()
    patch_loc()
    verify()


if __name__ == "__main__":
    main()
