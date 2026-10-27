"""Put every Cold War equipment tech on its year row, and complete only what each tag fields.

1936-1944 equipment stays researched for every country (those techs are hidden).
Later equipment is researched when that country's 2026 forces use it, plus the
small-arms and vehicle steps of its tier. Rocket trucks, silo cruise missiles,
and the light-tank line are hardcoded tier tables: a missing battalion does
not withhold them. No 2026 order of battle fields a light tank, so reading
the divisions never granted M41 (the 1960 row) to anyone, including the US.
Earlier steps of a researched line are included, because each tech requires the
one before it.

Industry, electronics, support, and ship-module lines are filled up to a year
cap for the country's tier. Weapons past that stay researchable. Civilian
nuclear reactors are granted only to countries that operate them.
"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from start_audit import TIER_1, TIER_2, TIER_3  # noqa: E402

TECH = ROOT / "common" / "technologies"
EQ = ROOT / "common" / "units" / "equipment"
HIST = ROOT / "history" / "countries"
UNITS = ROOT / "history" / "units"
GUI = ROOT / "interface" / "countrytechtreeview.gui"
LOC = ROOT / "localisation" / "english" / "doomsday_tech_l_english.yml"
GEN = ROOT / "tools" / "gen_modern_tech.py"

TECH_FILE = {
    "dd_infantry.txt": ["infantry_folder"],
    "dd_support.txt": ["support_folder"],
    "dd_armor.txt": ["armour_folder", "nsb_armour_folder"],
    "dd_artillery.txt": ["artillery_folder"],
    "dd_air.txt": ["air_techs_folder", "bba_air_techs_folder"],
    "dd_naval.txt": ["naval_folder", "mtgnavalfolder"],
    "dd_naval_parts.txt": ["mtgnavalsupportfolder", "naval_folder"],
    "dd_electronics.txt": ["electronics_folder"],
    "dd_industry.txt": ["industry_folder"],
}

# Established arsenals vs first-generation programs.
NUCLEAR_FULL = {"USA", "SOV", "CHI", "ENG", "FRA", "RAJ"}
NUCLEAR_SMALL = {"ISR", "PAK", "DPK"}

# Operating power reactors in 2026. Fleet is a real reactor fleet, not one plant.
NUCLEAR_FLEET = NUCLEAR_FULL | {"JAP", "KOR", "CAN", "GER", "SWE", "UKR", "UAE"}
NUCLEAR_POWER = NUCLEAR_FLEET | {
    "FIN", "CZE", "SWI", "BEL", "SPR", "HUN", "ROM", "BUL", "ARG", "BRA", "MEX",
    "SAF", "PAK", "ARM", "BLR", "HOL", "FOR", "SVK", "SLO",
}

# How far each tier has already walked the non-weapon lines. 1955 is the hidden floor.
YEAR_CAP = {0: 1955, 1: 1980, 2: 2005, 3: 2015}
BONUS_PREFIX = {
    "mat", "fuel", "bld", "ext", "slot", "tol", "syn", "con",
    "cpu", "cry", "ew", "rdr", "rad", "nrg",
    "eng", "rec", "hos", "log", "mp", "sig", "mnt", "sup", "nv", "fcs",
    "prot", "ewc",
    "torp", "son", "neng", "nav", "ciws", "vls", "dc", "ngun",
}
# Not started, even when the year cap would reach them.
BONUS_BLOCK = {
    "dd_rad_4", "dd_tol_8", "dd_cpu_8", "dd_cyb_3", "dd_dew_1", "dd_dew_2",
}

# Ends of the 1944 ship-module chains. Parents are filled in with them.
FLEET_TIPS = (
    "advanced_light_battery",
    "advanced_heavy_battery",
    "advanced_dp_light_battery",
    "modern_ship_torpedo_launcher",
    "damage_control_3",
    "fire_control_methods_3",
    "advanced_naval_mines",
    "modern_depth_charges",
    "modern_sonar",
    "advanced_ship_hull_light",
    "antiair5",
)

LAND = {
    0: ["dd_inf_1", "dd_truck_1", "dd_at_1", "dd_mor_1", "dd_supkit_1"],
    1: ["dd_inf_2", "dd_truck_2", "dd_at_2", "dd_mor_1", "dd_supkit_1", "dd_mbt_2", "dd_tow_1", "dd_shorad_1"],
    2: ["dd_inf_4", "dd_truck_2", "dd_at_3", "dd_mor_2", "dd_supkit_2", "dd_mbt_3", "dd_mech_3", "dd_tow_2", "dd_shorad_2", "dd_fcs_2"],
    3: ["dd_inf_6", "dd_truck_3", "dd_at_4", "dd_mor_3", "dd_supkit_3", "dd_mbt_4", "dd_mech_5", "dd_tow_3", "dd_shorad_3", "dd_fcs_3"],
}

# Rocket trucks and silo cruise. Not read from orders of battle.
# dd_rkt_5 (PrSM, 2023) and later stay off the 1 January list.
# dd_wpn_5 is the 2009 cruise missile. Its parents are fighter-attack steps
# and are not granted with it.
ROCKET_BY_TIER = {
    0: [],
    1: ["dd_rkt_1"],
    2: ["dd_rkt_1", "dd_rkt_2", "dd_rkt_3"],
    3: ["dd_rkt_1", "dd_rkt_2", "dd_rkt_3", "dd_rkt_4", "dd_wpn_5"],
}
ROCKET_COUNTRY = {
    "PER": ["dd_rkt_2", "dd_rkt_3", "dd_wpn_5"],
    "KOR": ["dd_wpn_5"],
    "ISR": ["dd_wpn_5"],
    "DPK": ["dd_rkt_2", "dd_rkt_3", "dd_wpn_5"],
    "PAK": ["dd_rkt_2", "dd_rkt_3", "dd_wpn_5"],
    "RAJ": ["dd_wpn_5"],
}

# Light tanks are not in any 2026 division, so the order-of-battle scan never
# grants them. Years follow YEAR_CAP. dd_lt_1 is the M41 (1955, the 1960 row).
# dd_lt_5 is 2016, past the tier-3 cap, so it stays researchable.
LIGHT_BY_TIER = {
    0: ["dd_lt_1"],
    1: ["dd_lt_1", "dd_lt_2"],
    2: ["dd_lt_1", "dd_lt_2", "dd_lt_3", "dd_lt_4"],
    3: ["dd_lt_1", "dd_lt_2", "dd_lt_3", "dd_lt_4"],
}

BLOCK_RE = re.compile(r"\n\t([A-Za-z0-9_]+) = \{")


def split_blocks(text: str) -> dict[str, str]:
    marks = list(BLOCK_RE.finditer(text))
    out = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else text.rfind("\n}")
        out[m.group(1)] = text[m.start() : end]
    return out


def parse_dd() -> dict[str, dict]:
    techs = {}
    for fname, folders in TECH_FILE.items():
        text = (TECH / fname).read_text(encoding="utf-8")
        for tid, body in split_blocks(text).items():
            if not tid.startswith("dd_"):
                continue
            year = re.search(r"start_year = (\d+)", body)
            leads = re.findall(r"leads_to_tech = ([A-Za-z0-9_]+)", body)
            unlocked = []
            for kind in ("enable_equipments", "enable_equipment_modules"):
                for block in re.findall(kind + r" = \{\s*([^}]*)\}", body):
                    unlocked += re.findall(r"[A-Za-z][A-Za-z0-9_]*", block)
            pos = re.findall(
                r"folder = \{\s*name = ([A-Za-z0-9_]+)\s*position = \{ x = (-?\d+) y = (-?\d+) \}",
                body,
            )
            techs[tid] = {
                "file": fname,
                "folders": folders,
                "year": int(year.group(1)) if year else 1955,
                "leads": leads,
                "eq": unlocked,
                "pos": pos,
                "body": body,
            }
    return techs


def all_enabled() -> set[str]:
    found = set()
    for path in TECH.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for body in split_blocks(text).values():
            for kind in ("enable_equipments", "enable_equipment_modules"):
                for block in re.findall(kind + r" = \{\s*([^}]*)\}", body):
                    found.update(re.findall(r"[A-Za-z][A-Za-z0-9_]*", block))
    return found


def buildable_orphans(enabled: set[str]) -> list[tuple[str, int]]:
    out = []
    for path in EQ.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        dup_at = text.find("duplicate_archetypes")
        for tid, body in split_blocks(text).items():
            at = text.find(body)
            if dup_at >= 0 and at > dup_at:
                continue
            if "is_archetype = yes" in body or "build_cost_ic" not in body:
                continue
            if "is_buildable = no" in body:
                continue
            if tid in enabled:
                continue
            year_m = re.search(r"\byear = (\d+)", body)
            year = int(year_m.group(1)) if year_m else 0
            if year < 1948:
                continue
            out.append((tid, year))
    return out


def attach_target(eid: str) -> str | None:
    e = eid.lower()
    if "heli" in e and "pad" not in e:
        return "dd_hel_1"
    if "ssbn" in e or "missile_sub" in e:
        return "dd_ssbn_1"
    if "nuclear_sub" in e or e.endswith("nuclear_submarine"):
        return "dd_ssn_1"
    if "carrier" in e:
        return "dd_cv_1"
    if "cruiser" in e or "battleship" in e or "ship_hull_heavy" in e:
        return "dd_cg_1"
    if "guided_missile" in e:
        return "dd_wpn_5"
    if "ballistic" in e or "nuclear_missile" in e:
        return "dd_rkt_1"
    if e.startswith("ship_hull_light") or "destroyer" in e:
        return "dd_esc_1"
    if "submarine" in e or e.startswith("ship_hull_sub"):
        return "dd_ssn_1"
    return None


def pixel(year: int) -> int:
    band = (year - 1955) // 5
    if band < 0:
        band = 0
    return 90 + band * 100


def tier_of(tag: str) -> int:
    if tag in TIER_3:
        return 3
    if tag in TIER_2:
        return 2
    if tag in TIER_1:
        return 1
    return 0


def closure(seeds: list[str], parents: dict[str, list[str]], techs: dict) -> list[str]:
    seen: set[str] = set()
    stack = [s for s in seeds if s in techs]
    while stack:
        cur = stack.pop()
        if cur in seen:
            continue
        seen.add(cur)
        stack.extend(parents.get(cur, []))
    return sorted(seen)


def spawned_regiments(text: str) -> set[str]:
    if "units =" not in text:
        return set()
    head, units = text.split("units =", 1)
    units = units.split("air_wings =", 1)[0].split("fleet =", 1)[0]
    names = re.findall(r'division_template = "([^"]+)"', units)
    kinds: set[str] = set()
    for name in names:
        m = re.search(
            rf'name = "{re.escape(name)}"\s*\r?\n\s*regiments = \{{(.*?)\r?\n\t\}}',
            head,
            re.S,
        )
        if not m:
            continue
        kinds.update(re.findall(r"^\s*([a-z_]+) =", m.group(1), re.M))
    return kinds


def unit_text(tag: str) -> str:
    parts = []
    for path in sorted(UNITS.glob(f"{tag}_*.txt")):
        parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def prefix_of(tid: str) -> str:
    parts = tid.split("_")
    if len(parts) < 3 or parts[0] != "dd":
        return ""
    return parts[1]


def bonus_seeds(tag: str, techs: dict) -> list[str]:
    cap = YEAR_CAP[tier_of(tag)]
    seeds = []
    for tid, data in techs.items():
        pre = prefix_of(tid)
        if pre not in BONUS_PREFIX or tid in BONUS_BLOCK:
            continue
        # ERA and ground jammers are already fielded by any real army, ahead of that tier's year cap.
        if tid in {"dd_prot_1", "dd_prot_2", "dd_ewc_1", "dd_ewc_2"} and tier_of(tag) >= 1:
            seeds.append(tid)
            continue
        if tid in {"dd_nrg_1", "dd_nrg_2"}:
            if tag not in NUCLEAR_POWER:
                continue
            if tid == "dd_nrg_2" and tag not in NUCLEAR_FLEET:
                continue
            seeds.append(tid)
            continue
        if data["year"] <= cap:
            seeds.append(tid)
    return seeds


def rocket_seeds(tag: str) -> list[str]:
    ids = list(ROCKET_BY_TIER[tier_of(tag)])
    ids += ROCKET_COUNTRY.get(tag, [])
    seen = set()
    out = []
    for tid in ids:
        if tid in seen or tid in {"dd_rkt_5", "dd_rkt_6", "dd_rkt_7"}:
            continue
        seen.add(tid)
        out.append(tid)
    return out


def kit_for(tag: str, techs: dict, eq_to_tech: dict[str, str], parents: dict[str, list[str]]) -> list[str]:
    tier = tier_of(tag)
    seeds = [t for t in LAND[tier] if t in techs]
    seeds += [t for t in LIGHT_BY_TIER[tier] if t in techs]
    seeds += [t for t in rocket_seeds(tag) if t in techs]
    seeds += bonus_seeds(tag, techs)
    text = unit_text(tag)
    kinds = spawned_regiments(text)
    if tier == 0 and kinds & {"modern_armor", "light_armor", "medium_armor", "heavy_armor"}:
        seeds.append("dd_mbt_1")
    if "mechanized" in kinds and tier < 2:
        seeds.append("dd_mech_1")
    if kinds & {"artillery", "rocket_artillery"} and tier == 0:
        seeds.append("dd_tow_1")
    if "anti_air" in kinds and tier < 2:
        seeds.append("dd_shorad_1")
    for tok in re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\b", text):
        if tok in eq_to_tech:
            seeds.append(eq_to_tech[tok])
    cap = 2005 if tag in NUCLEAR_FULL else 1965 if tag in NUCLEAR_SMALL else None
    if cap is not None:
        seeds += [t for t, d in techs.items() if t.startswith("dd_nuke") and d["year"] <= cap]
    got = closure(seeds, parents, techs)
    # Gas and grid sit downstream of the reactor techs. A country can have the
    # later steps without having operated a reactor fleet.
    if tag not in NUCLEAR_POWER:
        got = [t for t in got if t not in {"dd_nrg_1", "dd_nrg_2"}]
    elif tag not in NUCLEAR_FLEET:
        got = [t for t in got if t != "dd_nrg_2"]
    return got


def vanilla_parents() -> dict[str, list[str]]:
    parents: dict[str, list[str]] = defaultdict(list)
    for path in TECH.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="replace")
        blocks = split_blocks(text)
        for tid, body in blocks.items():
            for child in re.findall(r"leads_to_tech = ([A-Za-z0-9_]+)", body):
                parents[child].append(tid)
    return parents


def fleet_techs(parents: dict[str, list[str]], present: set[str]) -> list[str]:
    seen: set[str] = set()
    stack = [t for t in FLEET_TIPS if t in present]
    while stack:
        cur = stack.pop()
        if cur in seen or cur.startswith("sp_"):
            continue
        seen.add(cur)
        stack.extend(parents.get(cur, []))
    return sorted(seen)


def rewrite_history() -> None:
    techs = parse_dd()
    parents: dict[str, list[str]] = defaultdict(list)
    eq_to_tech: dict[str, str] = {}
    for tid, d in techs.items():
        for child in d["leads"]:
            parents[child].append(tid)
        for eid in d["eq"]:
            eq_to_tech.setdefault(eid, tid)
    equipment_techs = {t for t, d in techs.items() if d["eq"]}
    nuke_techs = {t for t in techs if t.startswith("dd_nuke")}
    bonus_techs = {t for t in techs if prefix_of(t) in BONUS_PREFIX}
    present = set()
    for path in TECH.glob("*.txt"):
        present.update(split_blocks(path.read_text(encoding="utf-8", errors="replace")))
    fleet = fleet_techs(vanilla_parents(), present)
    report = []
    for path in sorted(HIST.glob("*.txt")):
        tag = path.name.split(" - ", 1)[0].strip()
        text = path.read_text(encoding="utf-8")
        m = re.search(r"set_technology = \{.*?\n\}", text, re.S)
        if not m:
            continue
        block = m.group(0)
        allowed = set(kit_for(tag, techs, eq_to_tech, parents))
        nl = "\r\n" if "\r\n" in text else "\n"
        kept = []
        have = set()
        for line in block.splitlines(keepends=True):
            mm = re.match(r"\t([A-Za-z0-9_]+) = 1\s*$", line.strip("\r\n"))
            if mm and (mm.group(1) in equipment_techs or mm.group(1) in nuke_techs or mm.group(1) in bonus_techs):
                if mm.group(1) in allowed:
                    kept.append(line if line.endswith("\n") else line + nl)
                    have.add(mm.group(1))
                continue
            if mm:
                have.add(mm.group(1))
            line = line.replace(
                "Cold War floor: Cuba/Eritrea/NK/Taliban-style inventories.",
                "Later equipment is completed only when this country fields it.",
            )
            line = line.replace(
                "WWI/WWII weapon IDs stay researched (hidden from the tree) so vanilla focuses resolve.",
                "1936-1944 equipment stays researched so older gear still builds.",
            )
            kept.append(line if line.endswith("\n") else line + nl)
        grant = equipment_techs | nuke_techs | bonus_techs
        missing = [t for t in sorted(allowed) if t not in have and t in grant]
        for tech_id in fleet:
            if tech_id not in have:
                missing.append(tech_id)
                have.add(tech_id)
        if tag in NUCLEAR_POWER:
            for tech_id in ("atomic_research", "nuclear_reactor"):
                if tech_id in present and tech_id not in have:
                    missing.append(tech_id)
                    have.add(tech_id)
        close = kept.pop()
        for t in missing:
            kept.append(f"\t{t} = 1{nl}")
        kept.append(close if close.strip() == "}" else "}" + nl)
        text = text[: m.start()] + "".join(kept) + text[m.end() :]
        path.write_bytes(text.encode("utf-8"))
        report.append((tag, tier_of(tag), len(allowed & equipment_techs)))
    show = ["USA", "SOV", "CHI", "ENG", "FRA", "GER", "JAP", "ISR", "RAJ", "PER", "DPK", "PAK", "SOM", "AFG", "SAU", "KOR", "TWN"]
    by_tag = {t: (tier, n) for t, tier, n in report}
    print("countries", len(report))
    for tag in show:
        if tag in by_tag:
            print(f"  {tag} tier {by_tag[tag][0]} equipment techs {by_tag[tag][1]}")


def main() -> None:
    techs = parse_dd()
    enabled = all_enabled()
    orphans = buildable_orphans(enabled)
    grouped: dict[str, list[str]] = defaultdict(list)
    skipped = []
    for eid, year in orphans:
        dest = attach_target(eid)
        if dest and dest in techs:
            grouped[dest].append(eid)
        else:
            skipped.append((eid, year))
    for fname in TECH_FILE:
        path = TECH / fname
        text = path.read_text(encoding="utf-8")
        blocks = split_blocks(text)
        changed = False
        for tid, eids in grouped.items():
            if tid not in blocks or blocks[tid] not in text:
                continue
            if techs[tid]["file"] != fname:
                continue
            body = blocks[tid]
            new = body
            for eid in eids:
                if eid in new:
                    continue
                m = re.search(r"(enable_equipments = \{\n)([\s\S]*?)(\t\t\})", new)
                if m:
                    new = new[: m.end(1)] + m.group(2) + f"\t\t\t{eid}\n" + new[m.end(2) :]
                else:
                    new = new.replace(
                        " = {\n",
                        " = {\n\t\tenable_equipments = {\n\t\t\t" + eid + "\n\t\t}\n",
                        1,
                    )
            if new != body:
                text = text.replace(body, new, 1)
                changed = True
        if changed:
            path.write_text(text, encoding="utf-8", newline="\n")
    print("attached", {k: v for k, v in grouped.items()})
    print("left free (no matching line)", skipped)

    techs = parse_dd()
    parents: dict[str, list[str]] = defaultdict(list)
    for tid, d in techs.items():
        for child in d["leads"]:
            parents[child].append(tid)

    gui = GUI.read_text(encoding="utf-8")
    folder_grids: dict[str, dict[str, tuple[int, int]]] = defaultdict(dict)
    folder_spans: dict[str, tuple[int, int]] = {}
    for folder in {f for fs in TECH_FILE.values() for f in fs}:
        key = f'name = "{folder}"'
        idx = gui.find(key)
        if idx < 0:
            print("missing folder window", folder)
            continue
        end = gui.find("# DD_TECH_GRID_END", idx)
        start = gui.find("# DD_TECH_GRID_START", idx)
        if end < 0 or start < 0 or start > end:
            print("missing grid marker", folder)
            continue
        folder_spans[folder] = (start, end)
        chunk = gui[start:end]
        for m in re.finditer(
            r'name = "(dd_[A-Za-z0-9_]+)_tree" position = \{ x = (-?\d+) y = (-?\d+) \}',
            chunk,
        ):
            folder_grids[folder][m.group(1)] = (int(m.group(2)), int(m.group(3)))

    def nearest_x(tid: str, folder: str) -> int:
        seen = set()
        queue = [(tid, 0)]
        best = None
        while queue:
            cur, dist = queue.pop(0)
            if cur in seen or cur not in techs:
                continue
            seen.add(cur)
            if cur in folder_grids[folder] and cur != tid:
                best = folder_grids[folder][cur][0]
                break
            if dist > 12:
                continue
            for nxt in list(techs[cur]["leads"]) + parents.get(cur, []):
                queue.append((nxt, dist + 1))
        return 200 if best is None else best

    inserts: dict[str, list[str]] = defaultdict(list)
    file_repl: dict[str, list[tuple[str, str]]] = defaultdict(list)
    placed = 0
    for tid, d in techs.items():
        own_x = {name: int(x) for name, x, _y in d["pos"]}
        needs_folder = not d["pos"]
        for folder in d["folders"]:
            if tid in folder_grids[folder] and not needs_folder and all(int(y) == 0 for _n, _x, y in d["pos"]):
                continue
            col = folder_grids[folder][tid][0] if tid in folder_grids[folder] else nearest_x(tid, folder)
            extra = own_x.get(folder, 0) * 70
            if tid in folder_grids[folder]:
                gx = folder_grids[folder][tid][0]
            else:
                gx = col + extra
            gy = pixel(d["year"])
            if tid not in folder_grids[folder]:
                inserts[folder].append(
                    f'\t\t\tgridboxtype = {{ name = "{tid}_tree" position = {{ x = {gx} y = {gy} }} '
                    f'slotsize = {{ width = 70 height = 100 }} format = "UP" }}'
                )
                placed += 1
            elif folder_grids[folder][tid][1] != gy:
                old = (
                    f'name = "{tid}_tree" position = {{ x = {folder_grids[folder][tid][0]} '
                    f'y = {folder_grids[folder][tid][1]} }}'
                )
                new = f'name = "{tid}_tree" position = {{ x = {gx} y = {gy} }}'
                gui = gui.replace(old, new, 1)
        if needs_folder or any(int(y) != 0 for _n, _x, y in d["pos"]):
            body = d["body"]
            new = re.sub(
                r"\tfolder = \{\s*name = [A-Za-z0-9_]+\s*position = \{ x = -?\d+ y = -?\d+ \}\s*\}",
                "",
                body,
            )
            new = re.sub(r"\n{3,}", "\n\n", new)
            folder_txt = "".join(
                f"\t\tfolder = {{\n\t\t\tname = {folder}\n\t\t\tposition = {{ x = 0 y = 0 }}\n\t\t}}\n"
                for folder in d["folders"]
            )
            if "\t\tcategories = {" in new:
                new = new.replace("\t\tcategories = {", folder_txt + "\t\tcategories = {", 1)
            else:
                new = new.rstrip() + "\n" + folder_txt
            if new != body:
                file_repl[d["file"]].append((body, new))

    # Insert grids from the bottom of the file so earlier spans stay valid.
    for folder, lines in inserts.items():
        if folder not in folder_spans or not lines:
            continue
        _start, end = folder_spans[folder]
        # Re-find because earlier replacements may have shifted the file.
        key = f'name = "{folder}"'
        idx = gui.find(key)
        end = gui.find("# DD_TECH_GRID_END", idx)
        blob = "\n".join(lines) + "\n\t\t\t"
        gui = gui[:end] + blob + gui[end:]
    GUI.write_text(gui, encoding="utf-8", newline="\n")
    print("new grids", placed)

    for fname, pairs in file_repl.items():
        path = TECH / fname
        text = path.read_text(encoding="utf-8")
        for old, new in pairs:
            if old not in text:
                print("missed tech body", fname)
                continue
            text = text.replace(old, new, 1)
        path.write_text(text, encoding="utf-8", newline="\n")

    # Drop equipment techs from the universal floor so a later regen does not grant them again.
    gen = GEN.read_text(encoding="utf-8")
    techs = parse_dd()
    equipment_ids = {t for t, d in techs.items() if d["eq"]}
    def drop_floor(m: re.Match) -> str:
        text = m.group(0)
        text = re.sub(
            r'"(dd_[a-z0-9_]+)"',
            lambda mm: "" if mm.group(1) in equipment_ids else mm.group(0),
            text,
        )
        text = text.replace(", ,", ",").replace(",,", ",")
        lines = [ln for ln in text.splitlines() if ln.strip() not in {"", ","}]
        return "\n".join(lines)
    gen2, n = re.subn(r"FLOOR_IDS = \{.*?\n\}", drop_floor, gen, count=1, flags=re.S)
    if n:
        needle = "            path.write_text(new, encoding=\"utf-8\")\n"
        hook = (
            needle
            + "    from apply_research_audit import rewrite_history\n"
            + "    rewrite_history()\n"
        )
        if "rewrite_history()" not in gen2 and needle in gen2:
            gen2 = gen2.replace(needle, hook, 1)
        GEN.write_text(gen2, encoding="utf-8", newline="\n")
        print("floor ids kept", gen2.count("dd_"), "rewrite hooked", "rewrite_history()" in gen2)

    rename_equipment(techs)
    rewrite_history()


def rename_equipment(techs: dict) -> None:
    raw = LOC.read_bytes()
    text = raw.decode("utf-8-sig")
    names = dict(re.findall(r'^ (dd_[A-Za-z0-9_]+):0 "([^"]*)"', text, re.M))
    descs = dict(re.findall(r'^ (dd_[A-Za-z0-9_]+)_desc:0 "([^"]*)"', text, re.M))
    used: dict[str, str] = {}
    renamed = 0

    def technical(desc: str, ids: list[str]) -> str:
        parts = [p.strip() for p in desc.split(".")]
        kept = []
        for part in parts:
            if not part or part in ids:
                continue
            kept.append(part)
        return ". ".join(kept).strip()

    def set_key(key: str, value: str) -> None:
        nonlocal text, renamed
        pat = re.compile(rf'^ ({re.escape(key)}):0 "([^"]*)"', re.M)
        m = pat.search(text)
        if not m or m.group(2) == value:
            return
        text = pat.sub(f' {key}:0 "{value}"', text, count=1)
        renamed += 1

    for tid in sorted(techs):
        eqs = techs[tid]["eq"]
        if not eqs or tid not in names:
            continue
        plain = names[tid]
        desc = technical(descs.get(tid, plain), eqs)
        if not desc:
            desc = plain
        primary = eqs[0]
        if plain in used and used[plain] != primary:
            plain_for = None
        else:
            used[plain] = primary
            plain_for = primary
        for eid in eqs:
            if eid == plain_for:
                set_key(eid, plain)
                set_key(eid + "_short", plain)
            set_key(eid + "_desc", desc)
    out = b"\xef\xbb\xbf" + text.encode("utf-8")
    LOC.write_bytes(out)
    print("loc strings retitled", renamed)


if __name__ == "__main__":
    main()
