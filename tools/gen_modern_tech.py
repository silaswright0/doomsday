"""Generate 1955-2036 research trees from the canvas draft.

Same research_cost and start kit for every tag. Vanilla IDs stay in files
(hidden, granted) so leftover focuses still resolve.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANVAS_CANDIDATES = [
    ROOT / "canvases" / "modern-tech-trees.canvas.tsx",
    Path.home()
    / ".cursor"
    / "projects"
    / "c-Users-siwri-Documents-Paradox-Interactive-Hearts-of-Iron-IV-mod-doomsday"
    / "canvases"
    / "modern-tech-trees.canvas.tsx",
    Path(r"C:\Users\siwri\.cursor\projects\c-Users-siwri-Documents-Paradox-Interactive-Hearts-of-Iron-IV-mod-doomsday\canvases\modern-tech-trees.canvas.tsx"),
]
CANVAS = next((p for p in CANVAS_CANDIDATES if p.exists()), CANVAS_CANDIDATES[0])

TECH_DIR = ROOT / "common" / "technologies"
EQ_DIR = ROOT / "common" / "units" / "equipment"
GUI = ROOT / "interface" / "countrytechtreeview.gui"
LOC = ROOT / "localisation" / "english" / "doomsday_tech_l_english.yml"
GFX = ROOT / "interface" / "doomsday_techicons.gfx"
HIST = ROOT / "history" / "countries"

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

CATEGORIES = {
    "infantry": "infantry_weapons",
    "support": "support_tech",
    "armor": "armor",
    "artillery": "artillery",
    "air": "air_equipment",
    "naval": "naval_equipment",
    "naval_parts": "naval_equipment",
    "electronics": "electronics",
    "industry": "industry",
}

VANILLA_FOLDER_FILES = [
    "infantry.txt",
    "support.txt",
    "armor.txt",
    "NSB_armor.txt",
    "artillery.txt",
    "air_techs.txt",
    "bba_air_techs.txt",
    "naval.txt",
    "MTG_naval.txt",
    "MTG_naval_Support.txt",
    "electronic_mechanical_engineering.txt",
    "industry.txt",
    "doomsday_techs.txt",
]

ICON_BY_TREE = {
    "infantry": "gfx/interface/technologies/improved_infantry_weapons.dds",
    "support": "gfx/interface/technologies/tech_support.dds",
    "armor": "gfx/interface/technologies/main_battle_tank.dds",
    "artillery": "gfx/interface/technologies/artillery.dds",
    "air": "gfx/interface/technologies/jet_fighter1.dds",
    "naval": "gfx/interface/technologies/basic_destroyer.dds",
    "naval_parts": "gfx/interface/technologies/basic_battery.dds",
    "electronics": "gfx/interface/technologies/radio.dds",
    "industry": "gfx/interface/technologies/basic_machine_tools.dds",
}

# Design: Cold War floor granted and hidden. Not granted: 4th-gen air, NGSW,
# PrSM, area SAM, DEW, Link-16, cyber command, AI factories.
FLOOR_IDS = {
    "dd_truck_1", "dd_mech_1", "dd_sup_1", "dd_inf_1", "dd_at_1",
    "dd_nv_1", "dd_sf_1",
    "dd_supkit_1", "dd_eng_1", "dd_rec_1", "dd_hos_1", "dd_log_1",
    "dd_mp_1", "dd_sig_1", "dd_mnt_1",
    "dd_lt_1", "dd_mbt_1", "dd_mbt_2", "dd_td_1", "dd_fcs_1",
    "dd_tow_1", "dd_mor_1", "dd_atg_1", "dd_shorad_1",
    "dd_ftr_1", "dd_ftr_2", "dd_ftr_3", "dd_cas_1", "dd_str_1", "dd_hel_1",
    "dd_wpn_1",
    "dd_esc_1", "dd_ssn_1", "dd_amph_1",
    "dd_ngun_1", "dd_torp_1", "dd_son_1", "dd_neng_1", "dd_nav_1", "dd_dc_1",
    "dd_vls_1",
    "dd_rad_1", "dd_rdr_1", "dd_cpu_1", "dd_cry_1", "dd_ew_1", "dd_nuke_1",
    "dd_tol_1", "dd_tol_2", "dd_fuel_1", "dd_mat_1", "dd_bld_1", "dd_ext_1",
    "dd_slot_1", "dd_slot_2",
    "dd_manpad_1", "dd_uav_3",
}

MUST_NOT_START = {
    "dd_inf_7", "dd_inf_8", "dd_ftr_6", "dd_cv_4", "dd_cv_5", "dd_cvf_5",
    "dd_sam_3", "dd_dew_1", "dd_dew_2", "dd_rkt_5", "dd_rad_4", "dd_cyb_3", "dd_tol_8",
    "dd_cpu_8", "dd_uav_5",
}

NODE_RE = re.compile(
    r"\{ id: \"([^\"]+)\", name: \"([^\"]+)\", year: (\d+), col: \"([^\"]+)\", "
    r"research: ([0-9.]+), ic: (null|[0-9.]+), kind: \"([^\"]+)\", "
    r"analogues: \"([^\"]*)\", unlocks: \"([^\"]*)\" \}"
)
TREE_RE = re.compile(
    r"\{\s*id: \"(infantry|support|armor|artillery|air|naval|naval_parts|"
    r"electronics|industry)\",\s*label: \"([^\"]+)\",\s*columns: \[",
    re.S,
)
COL_RE = re.compile(r'\{ id: "([^"]+)", name: "([^"]+)" \}')


def year_y(year: int) -> int:
    return max(0, (int(year) - 1955) // 5) * 2


def parse_canvas() -> dict[str, dict]:
    text = CANVAS.read_text(encoding="utf-8")
    trees: dict[str, dict] = {}
    starts = list(TREE_RE.finditer(text))
    for i, m in enumerate(starts):
        tid, label = m.group(1), m.group(2)
        end = starts[i + 1].start() if i + 1 < len(starts) else text.find("];", m.end())
        chunk = text[m.start() : end]
        col_block = chunk.split("nodes:", 1)[0]
        columns = COL_RE.findall(col_block)
        nodes = []
        for n in NODE_RE.finditer(chunk):
            ic = n.group(6)
            nodes.append(
                {
                    "id": n.group(1),
                    "name": n.group(2),
                    "year": int(n.group(3)),
                    "col": n.group(4),
                    "research": float(n.group(5)),
                    "ic": None if ic == "null" else float(ic),
                    "kind": n.group(7),
                    "analogues": n.group(8),
                    "unlocks": n.group(9),
                }
            )
        trees[tid] = {"id": tid, "label": label, "columns": columns, "nodes": nodes}
    # Air CV-fighter IDs collide with naval carrier hull IDs in the canvas.
    for n in trees["air"]["nodes"]:
        if n["id"] in {"dd_cv_2", "dd_cv_4", "dd_cv_5"}:
            n["id"] = n["id"].replace("dd_cv_", "dd_cvf_")
    ind = trees["industry"]
    cols = list(ind["columns"])
    if not any(cid == "slot" for cid, _ in cols):
        bld_i = next(i for i, (cid, _) in enumerate(cols) if cid == "bld")
        cols.insert(bld_i + 1, ("slot", "Building slots"))
        ind["columns"] = cols
    ind["nodes"].extend(
        [
            {
                "id": "dd_slot_1",
                "name": "Industrial estates",
                "year": 1965,
                "col": "slot",
                "research": 2,
                "ic": None,
                "kind": "bonus",
                "analogues": "greenfield parks, Soviet microdistricts",
                "unlocks": "+30% max factories",
            },
            {
                "id": "dd_slot_2",
                "name": "Suburban industrial parks",
                "year": 1995,
                "col": "slot",
                "research": 2,
                "ic": None,
                "kind": "bonus",
                "analogues": "export zones, science parks",
                "unlocks": "+35% max factories",
            },
            {
                "id": "dd_slot_3",
                "name": "Mega-site permitting",
                "year": 2020,
                "col": "slot",
                "research": 2.5,
                "ic": None,
                "kind": "bonus",
                "analogues": "CHIPS Act campuses, special economic zones",
                "unlocks": "+35% max factories",
            },
        ]
    )
    return trees


def eq_tokens(unlocks: str) -> list[str]:
    out = []
    for part in re.split(r"\s*\+\s*", unlocks):
        part = part.strip()
        if re.fullmatch(r"[a-z][a-z0-9_]+", part) and "_" in part:
            if re.search(
                r"equipment|chassis|airframe|hull|battery|torpedo|sonar|engine|"
                r"vls|radar|hangar|helipad|emals|dew|asroc|module",
                part,
            ):
                out.append(part)
    return out


GENERATED_EQ_FILES = {
    "doomsday_cw_land.txt",
    "doomsday_cw_air.txt",
    "doomsday_cw_hulls.txt",
    "doomsday_cw_chassis.txt",
    "doomsday_ship_modules.txt",
}


def existing_equipment() -> set[str]:
    found: set[str] = set()
    for path in EQ_DIR.rglob("*.txt"):
        if path.parent.name in {"upgrades"}:
            continue
        if path.name in GENERATED_EQ_FILES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r"^\t([A-Za-z0-9_]+) = \{", text, re.M):
            found.add(m.group(1))
    return found


def bonus_modifiers(tree: str, node: dict, col_index: int) -> str:
    nid = node["id"]
    col = node["col"]
    idx = int(re.sub(r"\D+", "", nid.split("_")[-1] or "1") or 1)
    mag = 0.05 * idx
    lines: list[str] = []

    def add(block: str) -> None:
        lines.append(block)

    if nid == "dd_slot_1":
        return "\t\tglobal_building_slots_factor = 0.30\n"
    if nid == "dd_slot_2":
        return "\t\tglobal_building_slots_factor = 0.35\n"
    if nid == "dd_slot_3":
        return "\t\tglobal_building_slots_factor = 0.35\n"

    if tree == "infantry":
        if col == "sup":
            v = 0.08 if idx >= 4 else 0.05
            stat = "breakthrough" if idx == 3 else "soft_attack"
            add(f"\t\tcategory_light_infantry = {{ {stat} = {v} }}\n")
        elif col == "nv":
            add(f"\t\tland_night_attack = {round(0.10 + 0.05 * (idx - 1), 2)}\n")
        elif col == "sf":
            add("\t\tspecial_forces_cap = 0.05\n")
            add("\t\tmarine = { max_organisation = 5 }\n")
        elif col == "inf" and node["kind"] == "bonus":
            if "b2" in nid:
                add("\t\tcategory_light_infantry = { defense = 0.08 }\n")
            else:
                add("\t\tcategory_light_infantry = { soft_attack = 0.05 }\n")
        elif col == "at":
            add(f"\t\tcategory_light_infantry = {{ hard_attack = {0.08 + 0.04 * (idx - 1)} ap_attack = {0.08 + 0.04 * (idx - 1)} }}\n")
    elif tree == "support":
        if col == "eng":
            add("\t\tengineer = { entrenchment = 0.25 river = { attack = 0.10 } }\n")
        elif col == "rec":
            add("\t\trecon = { recon = 1 }\n")
        elif col == "hos":
            add(f"\t\tcasualty_trickleback = {0.10 + 0.05 * (idx - 1)}\n")
            add("\t\texperience_loss_factor = -0.05\n")
        elif col == "log":
            add(f"\t\tsupply_consumption_factor = {-0.10 - 0.05 * (idx - 1)}\n")
        elif col == "mp":
            add("\t\tmilitary_police = { suppression_factor = 0.15 }\n")
        elif col == "sig":
            add(f"\t\tland_reinforce_rate = {0.02 * idx}\n")
        elif col == "mnt":
            add(f"\t\treliability_factor = {0.05 * idx}\n")
        elif col == "ew":
            add("\t\tenemy_army_bonus_air_superiority_factor = -0.05\n")
        elif col == "kit":
            pass
    elif tree == "armor":
        if col == "prot":
            add("\t\tarmor = { armor_value = 0.10 hardness = 0.04 }\n")
        elif col == "fcs":
            add("\t\tarmor = { hard_attack = 0.08 reliability = 0.05 }\n")
    elif tree == "artillery":
        if col == "rkt" and node["kind"] == "bonus":
            add("\t\trocket_artillery = { soft_attack = 0.20 }\n")
        elif col == "at":
            add("\t\tanti_tank = { hard_attack = 0.10 ap_attack = 0.10 }\n")
    elif tree == "air":
        if col == "wpn" and node["kind"] == "bonus":
            add(f"\t\tfighter = {{ air_attack = {0.10 + 0.05 * min(idx, 4)} }}\n")
        elif col == "cas" and node["kind"] == "bonus":
            add("\t\tcas = { air_ground_attack = 0.20 }\n")
    elif tree == "naval_parts":
        if col == "dc":
            add(f"\t\tnaval_morale_factor = {0.03 * idx}\n")
            add("\t\tnavy_max_range_factor = 0.04\n")
    elif tree == "electronics":
        if col == "radio":
            add(f"\t\tland_reinforce_rate = {0.02 + 0.01 * idx}\n")
        elif col == "cpu":
            add("\t\tresearch_speed_factor = 0.03\n")
        elif col == "crypto":
            add("\t\tencryption = 1\n")
        elif col == "cyber":
            add("\t\tdecryption = 1\n")
        elif col == "ew":
            add("\t\tair_superiority_efficiency = 0.05\n")
        elif col == "space":
            add("\t\trecon_factor = 0.05\n")
        elif col == "nuke":
            add("\t\tnuclear_production_factor = 0.10\n")
        elif col == "radar":
            add("\t\tspotting_chance = 0.05\n")
            add("\t\trecon_factor = 0.03\n")
    elif tree == "industry":
        if col == "tools":
            add("\t\tproduction_factory_max_efficiency_factor = 0.10\n")
        elif col == "conc":
            add("\t\tindustrial_capacity_factory = 0.05\n")
            add("\t\tindustrial_capacity_dockyard = 0.05\n")
        elif col == "disp":
            add("\t\tindustry_air_damage_factor = -0.10\n")
            add("\t\tindustry_repair_factor = 0.10\n")
        elif col == "fuel":
            add("\t\tfuel_gain_factor = 0.10\n")
        elif col == "synth":
            add("\t\tproduction_oil_factor = 0.10\n")
        elif col == "mat":
            add("\t\tlocal_resources_factor = 0.08\n")
        elif col == "bld":
            add("\t\tproduction_speed_buildings_factor = 0.10\n")
        elif col == "ext":
            add("\t\tlocal_resources_factor = 0.10\n")
        elif col == "nrg":
            add("\t\tproduction_speed_infrastructure_factor = 0.05\n")

    if nid.startswith("dd_rdr_"):
        lvl = min(idx, 6)
        add(
            "\t\tenable_building = {\n"
            "\t\t\tbuilding = radar_station\n"
            f"\t\t\tlevel = {lvl}\n"
            "\t\t}\n"
        )
    if nid in {"dd_nrg_1", "dd_nrg_2", "dd_nuke_6", "dd_nrg_5"}:
        add(
            "\t\tenable_building = {\n"
            "\t\t\tbuilding = nuclear_reactor\n"
            "\t\t\tlevel = 1\n"
            "\t\t}\n"
        )
    if nid.startswith("dd_syn_"):
        add(
            "\t\tenable_building = {\n"
            "\t\t\tbuilding = synthetic_refinery\n"
            f"\t\t\tlevel = {min(idx, 3)}\n"
            "\t\t}\n"
        )
    if nid == "dd_spc_1":
        add(
            "\t\tenable_building = {\n"
            "\t\t\tbuilding = rocket_site\n"
            "\t\t\tlevel = 2\n"
            "\t\t}\n"
        )
    return "".join(lines)


def subunit_enables(nid: str) -> str:
    mapping = {
        "dd_manpad_1": "manpads",
        "dd_shorad_1": "shorad",
        "dd_sam_1": "mobile_sam",
        "dd_eng_1": "engineer",
        "dd_rec_1": "recon",
        "dd_hos_1": "field_hospital",
        "dd_log_1": "logistics_company",
        "dd_mp_1": "military_police",
        "dd_sig_1": "signal_company",
        "dd_mnt_1": "maintenance_company",
        "dd_sf_1": "paratrooper",
    }
    sub = mapping.get(nid)
    if not sub:
        return ""
    return f"\t\tenable_subunits = {{\n\t\t\t{sub}\n\t\t}}\n"


def xor_block(nid: str) -> str:
    if nid == "dd_con_1":
        return "\t\tXOR = {\n\t\t\tdd_dis_1\n\t\t}\n"
    if nid == "dd_dis_1":
        return "\t\tXOR = {\n\t\t\tdd_con_1\n\t\t}\n"
    return ""


def paths_for(tree: dict) -> dict[str, list[str]]:
    by_col: dict[str, list[dict]] = defaultdict(list)
    for n in tree["nodes"]:
        by_col[n["col"]].append(n)
    out: dict[str, list[str]] = defaultdict(list)
    for col, nodes in by_col.items():
        nodes.sort(key=lambda n: (n["year"], 0 if n["kind"] != "sub" else 1, n["id"]))
        mains = [n for n in nodes if n["kind"] != "sub"]
        for a, b in zip(mains, mains[1:]):
            out[a["id"]].append(b["id"])
        for n in nodes:
            if n["kind"] != "sub":
                continue
            prev = [m for m in mains if m["year"] <= n["year"]]
            src = prev[-1]["id"] if prev else mains[0]["id"]
            out[src].append(n["id"])
    return out


def tech_block(tree_id: str, tree: dict, node: dict, col_x: dict[str, int], leads: list[str]) -> str:
    nid = node["id"]
    hidden = nid in FLOOR_IDS
    folders = []
    if not hidden:
        px = col_x[node["col"]]
        py = year_y(node["year"])
        for folder in FOLDERS[tree_id]:
            folders.append(
                f"\t\tfolder = {{\n\t\t\tname = {folder}\n"
                f"\t\t\tposition = {{ x = {px} y = {py} }}\n\t\t}}"
            )
    eq = eq_tokens(node["unlocks"])
    # BBA: canvas fighter IDs are airframe variants, keep names.
    enable_eq = ""
    if eq and node["kind"] in {"kit", "sub"}:
        inner = "\n".join(f"\t\t\t{e}" for e in eq)
        enable_eq = f"\t\tenable_equipments = {{\n{inner}\n\t\t}}\n"
    enable_mod = ""
    if tree_id == "naval_parts" and eq:
        inner = "\n".join(f"\t\t\t{e}" for e in eq)
        enable_mod = f"\t\tenable_equipment_modules = {{\n{inner}\n\t\t}}\n"
        if enable_eq:
            enable_eq = ""
    path = "".join(
        f"\t\tpath = {{\n\t\t\tleads_to_tech = {t}\n\t\t\tresearch_cost_coeff = 1\n\t\t}}\n"
        for t in leads
    )
    bonus = bonus_modifiers(tree_id, node, col_x[node["col"]])
    folder_txt = "".join(f"{f}\n" for f in folders)
    cat = CATEGORIES[tree_id]
    return f"""
	{nid} = {{
{enable_eq}{enable_mod}{subunit_enables(nid)}{bonus}{xor_block(nid)}{path}		research_cost = {node['research']}
		start_year = {node['year']}
{folder_txt}		categories = {{
			{cat}
		}}
		ai_will_do = {{
			factor = 1
		}}
	}}
"""


def write_techs(trees: dict[str, dict]) -> None:
    for tid, tree in trees.items():
        col_x = {cid: i * 2 for i, (cid, _) in enumerate(tree["columns"])}
        leads = paths_for(tree)
        macros = ["\t@1955 = 0"]
        for y in range(1960, 2040, 5):
            macros.append(f"\t@{y} = {year_y(y)}")
        body = [
            f"# Generated Cold War / 2026 {tree['label']} tree. Identical costs for every tag.\n",
            "technologies = {\n\n",
            "\n".join(macros),
            "\n",
        ]
        for node in tree["nodes"]:
            body.append(tech_block(tid, tree, node, col_x, leads.get(node["id"], [])))
        body.append("}\n")
        (TECH_DIR / f"dd_{tid}.txt").write_text("".join(body), encoding="utf-8")


def land_variant(name: str, arch: str, parent: str | None, year: int, ic: float, stats: dict, extra: str = "") -> str:
    par = f"\n\t\tparent = {parent}" if parent else ""
    stat_lines = "".join(f"\n\t\t{k} = {v}" for k, v in stats.items())
    return f"""
	{name} = {{
		year = {year}
		archetype = {arch}{par}
		priority = 50
		visual_level = 1
		build_cost_ic = {ic}{stat_lines}
{extra}	}}
"""


def cw_air_resources(year: int) -> str:
    lines = ["aluminium = 3", "rubber = 1", "rare_earths = 1"]
    if year >= 1981:
        lines.append("cobalt = 1")
    if year >= 2005:
        lines.append("copper = 1")
    body = "\n".join(f"\t\t\t{ln}" for ln in lines)
    return f"\t\tresources = {{\n{body}\n\t\t}}"


def cw_hull_resources(year: int) -> str:
    lines = ["steel = 3", "chromium = 1"]
    if year >= 1991:
        lines.append("copper = 1")
    body = "\n".join(f"\t\t\t{ln}" for ln in lines)
    return f"\t\tresources = {{\n{body}\n\t\t}}"


def cw_chassis_resources(name: str, year: int) -> str:
    lines = ["steel = 3", "tungsten = 1", "rare_earths = 1"]
    if year >= 2005:
        lines.append("copper = 1")
    if year >= 2015:
        lines.append("cobalt = 1")
    if "light_tank" in name and year >= 2016:
        lines.append("lithium = 1")
    body = "\n".join(f"\t\t\t{ln}" for ln in lines)
    return f"\t\tresources = {{\n{body}\n\t\t}}"


def scale_airframe(name: str, arch: str, parent: str, year: int, ic: float, speed: float, agility: float, defence: float, rng: float, superiority: float) -> str:
    # Unused for live equipment. Combat airframes are complete designs in write_cw_air.py.
    return ""


def hull_variant(name: str, arch: str, parent: str, year: int, ic: float, strength: int, range_: int) -> str:
    return f"""
	{name} = {{
		year = {year}
		archetype = {arch}
		parent = {parent}
		priority = 2000
		module_slots = inherit
		build_cost_ic = {ic}
		naval_range = {range_}
		max_strength = {strength}
		reliability = 0.9
{cw_hull_resources(year)}
	}}
"""


def module_variant(name: str, category: str, parent: str | None, ic: float, stats: str) -> str:
    par = f"\n\t\tparent = {parent}" if parent else ""
    abbr = "d" + format(sum(map(ord, name)) % 1000, "03d")
    return f"""
	{name} = {{
		abbreviation = "{abbr}"
		category = {category}{par}
		sfx = sfx_ui_sd_module_turret
		add_stats = {{
{stats}
			build_cost_ic = {ic}
		}}
	}}
"""


def simple_air_variant(name: str, arch: str, parent: str, year: int, ic: float, speed: float, agility: float, defence: float, rng: float) -> str:
    return f"""
	{name} = {{
		year = {year}
		archetype = {arch}
		parent = {parent}
		priority = 90
		air_range = {int(rng)}
		maximum_speed = {int(speed)}
		air_agility = {int(agility)}
		air_defence = {int(defence)}
		build_cost_ic = {ic}
	}}
"""


def generate_equipment(trees: dict[str, dict]) -> tuple[set[str], list[str], dict[str, dict]]:
    have = existing_equipment()
    wanted: dict[str, dict] = {}
    for tree in trees.values():
        for node in tree["nodes"]:
            for eq in eq_tokens(node["unlocks"]):
                wanted[eq] = node
    land = ["equipments = {\n"]
    air = ["equipments = {\n"]
    hulls = ["equipments = {\n"]
    chassis = ["equipments = {\n"]
    mods = ["equipment_modules = {\n"]

    families: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for eq, node in wanted.items():
        if eq in have and not eq.endswith(("_cw1", "_cw2", "_1")):
            # still allow cw variants even if vanilla 1 exists
            if "cw" not in eq and eq in have:
                continue
        if eq in have and "cw" not in eq:
            continue
        families[re.sub(r"(_cw)?\d+[ab]?$", "", eq)].append((eq, node))

    def sort_key(item: tuple[str, dict]) -> tuple:
        name = item[0]
        m = re.search(r"(\d+)([ab])?$", name)
        n = int(m.group(1)) if m else 0
        extra = 0 if not m or not m.group(2) else (1 if m.group(2) == "a" else 2)
        return (item[1]["year"], n, extra, name)

    created: set[str] = set()

    def need(name: str) -> bool:
        return name not in have and name not in created

    # Infantry kit
    parent = "infantry_equipment_3"
    inf_stats_base = [
        (14, 38, 6, 2.5, 12),
        (16, 42, 7, 3, 14),
        (18, 46, 8, 3.5, 16),
        (21, 52, 9, 4, 18),
        (24, 58, 10, 4.5, 20),
        (27, 64, 11, 5, 22),
        (32, 72, 13, 6, 26),
        (36, 80, 15, 7, 30),
    ]
    for i in range(1, 9):
        name = f"infantry_equipment_cw{i}"
        if not need(name):
            parent = name
            continue
        sa, df, br, ha, ap = inf_stats_base[i - 1]
        node = wanted.get(name, {"year": 1955 + i * 8, "ic": 3 + i})
        land.append(
            land_variant(
                name,
                "infantry_equipment",
                parent,
                node["year"],
                node["ic"] or (2.8 + i),
                {
                    "soft_attack": sa,
                    "defense": df,
                    "breakthrough": br,
                    "hard_attack": ha,
                    "ap_attack": ap,
                    "reliability": 0.85,
                },
            )
        )
        created.add(name)
        parent = name

    mot_parent = "motorized_equipment_1"
    for i, (spd, hard, br) in enumerate([(14, 0.15, 6), (16, 0.25, 8), (18, 0.35, 10)], start=2):
        name = f"motorized_equipment_{i}"
        if not need(name):
            mot_parent = name
            continue
        node = wanted.get(name, {"year": 1985, "ic": 4 + i})
        land.append(
            land_variant(
                name,
                "motorized_equipment",
                mot_parent,
                node["year"],
                node["ic"] or 6,
                {"maximum_speed": spd, "hardness": hard, "breakthrough": br},
            )
        )
        created.add(name)
        mot_parent = name

    mech_parent = "mechanized_equipment_3"
    mech_stats = [
        (14, 40, 12, 0.80, 28, 28),
        (14, 48, 16, 0.85, 40, 36),
        (16, 56, 20, 0.88, 50, 44),
    ]
    for i, st in enumerate(mech_stats, start=4):
        name = f"mechanized_equipment_{i}"
        if not need(name):
            mech_parent = name
            continue
        spd, df, br, hard, armor, ap = st
        node = wanted.get(name, {"year": 1994, "ic": 22})
        land.append(
            land_variant(
                name,
                "mechanized_equipment",
                mech_parent,
                node["year"],
                node["ic"] or 22,
                {
                    "maximum_speed": spd,
                    "defense": df,
                    "breakthrough": br,
                    "hardness": hard,
                    "armor_value": armor,
                    "ap_attack": ap,
                    "hard_attack": 4 + (i - 3) * 4,
                    "air_attack": i - 3,
                },
            )
        )
        created.add(name)
        mech_parent = name

    sup_parent = "support_equipment_1"
    for i in range(1, 6):
        name = f"support_equipment_cw{i}"
        if not need(name):
            continue
        node = wanted.get(name, {"year": 1955, "ic": 8 + i})
        land.append(
            land_variant(
                name,
                "support_equipment",
                sup_parent if i == 1 else f"support_equipment_cw{i-1}",
                node["year"],
                node["ic"] or 10,
                {"reliability": 0.8 + 0.02 * i},
            )
        )
        created.add(name)

    def chain(prefix: str, arch: str, parent0: str | None, count: int, stats_fn, file_list):
        prev = parent0
        for i in range(1, count + 1):
            name = f"{prefix}{i}"
            if name not in wanted and not name.startswith(("mbt_equipment",)):
                if name not in wanted:
                    continue
            if not need(name):
                prev = name
                continue
            node = wanted.get(name) or {"year": 1955, "ic": 10}
            file_list.append(
                land_variant(
                    name,
                    arch,
                    prev,
                    node["year"],
                    node["ic"] or 10,
                    stats_fn(i),
                )
            )
            created.add(name)
            prev = name

    def arty_stats(i):
        return {"soft_attack": 30 + i * 8, "breakthrough": 8 + i * 2, "defense": 12 + i}

    chain("artillery_equipment_cw", "artillery_equipment", "artillery_equipment_3", 4, arty_stats, land)
    chain(
        "rocket_artillery_equipment_cw",
        "rocket_artillery_equipment",
        "rocket_artillery_equipment_2",
        3,
        lambda i: {"soft_attack": 40 + i * 12, "breakthrough": 10 + i * 3},
        land,
    )
    chain(
        "anti_tank_equipment_cw",
        "anti_tank_equipment",
        "anti_tank_equipment_3",
        4,
        lambda i: {"hard_attack": 28 + i * 10, "ap_attack": 80 + i * 25},
        land,
    )
    chain(
        "anti_air_equipment_cw",
        "anti_air_equipment",
        "anti_air_equipment_3",
        1,
        lambda i: {"air_attack": 28 + i * 10},
        land,
    )

    # New archetypes used by subunits / production
    if need("manpads_equipment"):
        land.append(
            """
	manpads_equipment = {
		year = 1968
		is_archetype = yes
		picture = archetype_anti_air_equipment
		is_buildable = no
		type = { anti_air infantry }
		group_by = archetype
		interface_category = interface_category_land
		reliability = 0.8
		defense = 2
		breakthrough = 1
		soft_attack = 1
		hard_attack = 1
		air_attack = 22
		build_cost_ic = 6
		resources = { steel = 1 rare_earths = 1 copper = 1 }
	}
"""
        )
        created.add("manpads_equipment")
    prev = None
    for i in range(1, 5):
        name = f"manpads_equipment_{i}"
        if not need(name):
            continue
        node = wanted.get(name, {"year": 1968, "ic": 6 + i * 2})
        land.append(
            land_variant(
                name,
                "manpads_equipment",
                prev,
                node["year"],
                node["ic"] or 8,
                {"air_attack": 22 + i * 8, "hard_attack": 1 + i},
            )
        )
        created.add(name)
        prev = name

    def new_arch(arch, picture, types, stats):
        if not need(arch):
            return
        stat_l = "".join(f"\n\t\t{k} = {v}" for k, v in stats.items())
        land.append(
            f"""
	{arch} = {{
		year = 1955
		is_archetype = yes
		picture = {picture}
		is_buildable = no
		type = {{ {types} }}
		group_by = archetype
		interface_category = interface_category_land
		reliability = 0.8{stat_l}
		resources = {{ steel = 2 tungsten = 1 rare_earths = 1 copper = 1 }}
	}}
"""
        )
        created.add(arch)

    new_arch(
        "spg_equipment",
        "archetype_artillery_equipment",
        "artillery motorized",
        {"soft_attack": 40, "breakthrough": 12, "defense": 16, "hardness": 0.4, "maximum_speed": 8, "build_cost_ic": 18, "fuel_consumption": 1.8},
    )
    new_arch(
        "dew_equipment",
        "archetype_anti_air_equipment",
        "anti_air",
        {"air_attack": 40, "defense": 6, "build_cost_ic": 28},
    )
    new_arch(
        "prsm_equipment",
        "archetype_rocket_artillery_equipment",
        "rocket motorized",
        {"soft_attack": 70, "hard_attack": 20, "breakthrough": 20, "build_cost_ic": 36, "maximum_speed": 10, "fuel_consumption": 2},
    )

    for prefix, arch, nmax, base, parent0 in (
        ("spg_equipment_", "spg_equipment", 7, {"soft_attack": 40}, None),
        ("shorad_equipment_", "anti_air_equipment", 4, {"air_attack": 40}, "anti_air_equipment_3"),
        ("dew_equipment_", "dew_equipment", 5, {"air_attack": 40}, None),
        ("hpm_equipment_", "dew_equipment", 1, {"air_attack": 36}, None),
        ("prsm_equipment_", "prsm_equipment", 1, {"soft_attack": 70, "hard_attack": 24}, None),
        ("mrc_equipment_", "prsm_equipment", 1, {"soft_attack": 80, "hard_attack": 28}, None),
        ("hypersonic_glcm_equipment_", "prsm_equipment", 1, {"soft_attack": 90, "hard_attack": 36}, None),
        ("mortar_equipment_", "artillery_equipment", 4, {"soft_attack": 18}, "artillery_equipment_3"),
        ("td_equipment_", "anti_tank_equipment", 5, {"hard_attack": 24, "ap_attack": 120}, "anti_tank_equipment_3"),
        ("spaa_equipment_", "anti_air_equipment", 5, {"air_attack": 32}, "anti_air_equipment_3"),
        ("ifpc_equipment_", "anti_air_equipment", 1, {"air_attack": 66}, "anti_air_equipment_3"),
        ("bmd_equipment_", "anti_air_equipment", 1, {"air_attack": 86}, "anti_air_equipment_3"),
        ("sam_equipment_", "anti_air_equipment", 4, {"air_attack": 48}, "anti_air_equipment_3"),
        ("infantry_at_equipment_", "anti_tank_equipment", 8, {"hard_attack": 18, "ap_attack": 70}, "anti_tank_equipment_3"),
    ):
        prev = parent0
        for i in range(1, nmax + 1):
            name = f"{prefix}{i}"
            if name not in wanted and prefix not in ("mortar_equipment_",):
                if name not in wanted:
                    continue
            if not need(name):
                prev = name
                continue
            node = wanted.get(name, {"year": 1955 + i * 8, "ic": 10})
            st = {
                k: v + i * (20 if "ap" in k else 8 if "shorad" in prefix and "air" in k else 4 if "air" in k or "soft" in k or "hard" in k else 1)
                for k, v in base.items()
            }
            land.append(land_variant(name, arch, prev, node["year"], node["ic"] or 12, st))
            created.add(name)
            prev = name

    # Chassis
    def chassis_chain(prefix, arch, parent0, n, armor0, speed0):
        prev = parent0
        for i in range(1, n + 1):
            name = f"{prefix}{i}"
            if name not in wanted:
                continue
            if not need(name):
                prev = name
                continue
            node = wanted[name]
            chassis.append(
                f"""
	{name} = {{
		year = {node['year']}
		archetype = {arch}
		parent = {prev}
		priority = 2000
		module_slots = inherit
		build_cost_ic = {node['ic'] or 20}
		maximum_speed = {speed0 + i * 0.4}
		armor_value = {armor0 + i * 8}
		reliability = 0.95
{cw_chassis_resources(name, node['year'])}
	}}
"""
            )
            created.add(name)
            prev = name

    chassis_chain("mbt_equipment_", "modern_tank_chassis", "modern_tank_chassis_1", 9, 90, 9)
    chassis_chain("light_tank_equipment_cw", "light_tank_chassis", "light_tank_chassis_3", 7, 30, 12)

    # Airframes (BBA)
    fighter = [
        ("fighter_equipment_cw1", 950, 50, 28, 800, 1.0, "small_plane_airframe_5"),
        ("fighter_equipment_cw2", 1200, 62, 32, 1000, 1.15, "fighter_equipment_cw1"),
        ("fighter_equipment_cw3", 1400, 72, 40, 1200, 1.3, "fighter_equipment_cw2"),
        ("fighter_equipment_cw4", 1600, 85, 48, 1400, 1.5, "fighter_equipment_cw3"),
        ("fighter_equipment_cw45", 1700, 92, 52, 1500, 1.7, "fighter_equipment_cw4"),
        ("fighter_equipment_cw5a", 2100, 115, 70, 1800, 2.2, "fighter_equipment_cw45"),
        ("fighter_equipment_cw5b", 1900, 108, 62, 2000, 2.0, "fighter_equipment_cw45"),
        ("fighter_equipment_cw6", 2200, 130, 80, 2200, 2.6, "fighter_equipment_cw5a"),
    ]
    prev_created = "small_plane_airframe_5"
    for name, spd, agi, defence, rng, sup, parent in fighter:
        if not need(name):
            prev_created = name
            continue
        node = wanted.get(name, {"year": 1955, "ic": 24})
        use_parent = parent if parent in have or parent in created or parent == "small_plane_airframe_5" else prev_created
        air.append(
            scale_airframe(
                name,
                "small_plane_airframe",
                use_parent,
                node["year"],
                node["ic"] or 24,
                spd,
                agi,
                defence,
                rng,
                sup,
            )
        )
        created.add(name)
        prev_created = name

    cv_map = [
        ("cv_fighter_equipment_cw2", "cv_small_plane_airframe_4", 1100, 60, 30, 800, 1.15),
        ("cv_fighter_equipment_cw4", "cv_fighter_equipment_cw2", 1550, 82, 44, 1000, 1.5),
        ("cv_fighter_equipment_cw5", "cv_fighter_equipment_cw4", 1850, 100, 58, 1200, 2.0),
    ]
    for name, parent, spd, agi, defence, rng, sup in cv_map:
        if not need(name):
            continue
        node = wanted.get(name, {"year": 1960, "ic": 30})
        air.append(
            scale_airframe(
                name,
                "cv_small_plane_airframe",
                parent if parent in have or parent in created else "cv_small_plane_airframe_4",
                node["year"],
                node["ic"] or 30,
                spd,
                agi,
                defence,
                rng,
                sup,
            )
        )
        created.add(name)

    def plane_chain(names, arch, parent0, speeds):
        prev = parent0
        for name, spd in zip(names, speeds):
            if name not in wanted:
                continue
            if not need(name):
                prev = name
                continue
            node = wanted[name]
            air.append(
                scale_airframe(
                    name,
                    arch,
                    prev,
                    node["year"],
                    node["ic"] or 40,
                    spd,
                    50 + speeds.index(spd) * 8,
                    20 + speeds.index(spd) * 8,
                    1500 + speeds.index(spd) * 300,
                    0.2 + speeds.index(spd) * 0.1,
                )
            )
            created.add(name)
            prev = name

    plane_chain(
        [f"cas_equipment_cw{i}" for i in range(1, 4)],
        "small_plane_airframe",
        "small_plane_airframe_5",
        [850, 950, 1100],
    )
    plane_chain(
        [f"tac_bomber_equipment_cw{i}" for i in range(1, 5)],
        "medium_plane_airframe",
        "medium_plane_airframe_4",
        [900, 1100, 1300, 1400],
    )
    plane_chain(
        [f"strat_bomber_equipment_cw{i}" for i in range(1, 7)],
        "large_plane_airframe",
        "large_plane_airframe_4",
        [800, 1000, 1100, 900, 1000, 1100],
    )
    plane_chain(
        ["scout_plane_equipment_cw1"],
        "medium_plane_airframe",
        "medium_plane_airframe_4",
        [900],
    )

    extra_air = [
        ("cca_equipment_1", "small_plane_airframe", "small_plane_airframe_5", 1600, 90, 40, 1200, 0.6),
        ("cca_equipment_2", "small_plane_airframe", "cca_equipment_1", 1800, 100, 36, 1000, 0.7),
        ("cca_strike_equipment_1", "small_plane_airframe", "small_plane_airframe_5", 1500, 80, 36, 1400, 0.6),
        ("aew_equipment_1", "large_plane_airframe", "large_plane_airframe_4", 700, 30, 40, 4000, 0.1),
        ("aew_equipment_2", "large_plane_airframe", "aew_equipment_1", 750, 32, 48, 5000, 0.1),
        ("aew_equipment_3", "large_plane_airframe", "aew_equipment_2", 800, 36, 52, 5500, 0.15),
        ("hale_uav_equipment_1", "medium_plane_airframe", "medium_plane_airframe_4", 600, 40, 20, 8000, 0.0),
    ]
    for name, arch, parent, spd, agi, defence, rng, sup in extra_air:
        if name not in wanted or not need(name):
            continue
        node = wanted[name]
        air.append(
            scale_airframe(name, arch, parent, node["year"], node["ic"] or 22, spd, agi, defence, rng, sup)
        )
        created.add(name)

    extra_simple_air = [
        ("recon_uav_equipment_2", "recon_uav_equipment", "recon_uav_equipment_1", 420, 45, 10, 1400),
        ("transport_heli_equipment_2", "transport_heli_equipment", "transport_heli_equipment_1", 280, 40, 16, 600),
        ("transport_heli_equipment_3", "transport_heli_equipment", "transport_heli_equipment_2", 320, 50, 20, 800),
        ("guided_missile_equipment_cw", "guided_missile_equipment", "guided_missile_equipment_4", 900, 20, 10, 2500),
    ]
    for name, arch, parent, spd, agi, defence, rng in extra_simple_air:
        if name not in wanted or not need(name):
            continue
        node = wanted[name]
        air.append(simple_air_variant(name, arch, parent, node["year"], node["ic"] or 22, spd, agi, defence, rng))
        created.add(name)

    heli_land = [
        ("attack_heli_equipment_1", "helicopter_equipment_1", 1975, 280, 48, 18, 20, 10, 45, 4),
        ("attack_heli_equipment_2", "attack_heli_equipment_1", 1984, 300, 55, 24, 28, 22, 90, 8),
        ("attack_heli_equipment_3", "attack_heli_equipment_2", 2003, 320, 60, 28, 34, 32, 140, 12),
        ("attack_heli_equipment_4", "attack_heli_equipment_3", 2035, 340, 70, 22, 40, 40, 180, 16),
    ]
    for name, parent, year, spd, df, br, soft, hard, ap, air_atk in heli_land:
        if name not in wanted and name != "attack_heli_equipment_1":
            continue
        if name != "attack_heli_equipment_1" and not need(name):
            continue
        node = wanted.get(name, {"year": year, "ic": 18})
        land.append(
            land_variant(
                name,
                "helicopter_equipment",
                parent,
                node["year"],
                node["ic"] or 18,
                {
                    "maximum_speed": spd / 20,
                    "defense": df,
                    "breakthrough": br,
                    "hardness": 0.45,
                    "soft_attack": soft,
                    "hard_attack": hard,
                    "ap_attack": ap,
                    "air_attack": air_atk,
                },
            )
        )
        created.add(name)

    # Hulls
    hull_specs = [
        ("ship_hull_light_cw", "ship_hull_light", "ship_hull_light_4", 7, 70, 4000),
        ("ship_hull_cruiser_cw", "ship_hull_cruiser", "ship_hull_cruiser_4", 3, 120, 5000),
        ("ship_hull_carrier_cw", "ship_hull_carrier", "ship_hull_carrier_3", 6, 400, 8000),
        ("ship_hull_submarine_cw", "ship_hull_submarine", "ship_hull_submarine_4", 6, 50, 7000),
        ("ship_hull_ssbn_", "ship_hull_nuclear_submarine", "nuclear_submarine", 4, 80, 9000),
        ("ship_hull_amphib_", "ship_hull_cruiser", "ship_hull_cruiser_4", 5, 160, 6000),
        ("ship_hull_usv_", "ship_hull_light", "ship_hull_light_4", 2, 20, 2500),
        ("ship_hull_uuv_", "ship_hull_submarine", "ship_hull_submarine_4", 1, 15, 4000),
        ("ship_hull_submarine_diesel_", "ship_hull_submarine", "ship_hull_submarine_3", 1, 35, 5000),
    ]
    for prefix, arch, parent0, n, str0, rng0 in hull_specs:
        prev = parent0
        for i in range(1, n + 1):
            name = f"{prefix}{i}"
            if name not in wanted:
                continue
            if not need(name):
                prev = name
                continue
            node = wanted[name]
            hulls.append(
                hull_variant(
                    name,
                    arch,
                    prev,
                    node["year"],
                    node["ic"] or 800,
                    str0 + i * 15,
                    rng0 + i * 400,
                )
            )
            created.add(name)
            prev = name

    # Naval modules
    def mod_chain(prefix, category, parent0, n, attack_key, attack0, extra_keys=None):
        prev = parent0
        for i in range(1, n + 1):
            name = f"{prefix}{i}"
            if name not in wanted:
                continue
            if not need(name):
                prev = name
                continue
            node = wanted[name]
            extra = ""
            if extra_keys:
                extra = "".join(f"\n\t\t\t{k} = {v0 + i}" for k, v0 in extra_keys.items())
            mods.append(
                module_variant(
                    name,
                    category,
                    prev if prev and prev != parent0 else parent0,
                    node["ic"] or 150,
                    f"\t\t\t{attack_key} = {attack0 + i}{extra}",
                )
            )
            created.add(name)
            prev = name

    mod_chain("ship_light_battery_cw", "ship_light_battery", "ship_light_battery_4", 4, "lg_attack", 3)
    mod_chain("ship_medium_battery_cw", "ship_medium_battery", "ship_medium_battery_4", 1, "hg_attack", 6)
    mod_chain("ship_sam_battery_", "ship_anti_air", "ship_anti_air_4", 2, "anti_air_attack", 8)
    mod_chain("ship_vls_", "ship_anti_air", "ship_anti_air_4", 4, "anti_air_attack", 12, {"lg_attack": 5, "sub_attack": 2})
    mod_chain("ship_aa_cw", "ship_anti_air", "ship_anti_air_4", 4, "anti_air_attack", 6)
    mod_chain("ship_dew_", "ship_anti_air", "ship_anti_air_4", 2, "anti_air_attack", 14)
    mod_chain("ship_torpedo_cw", "ship_torpedo", "ship_torpedo_4", 5, "torpedo_attack", 4)
    mod_chain("ship_asroc_cw", "ship_mine_layer", "ship_depth_charge_4", 1, "sub_attack", 8)
    mod_chain("ship_sonar_", "ship_sonar", "ship_sonar_2", 5, "sub_detection", 6)
    mod_chain("light_ship_engine_cw", "light_ship_engine", "light_ship_engine_4", 5, "naval_speed", 1)
    mod_chain("ship_radar_cw", "ship_radar", "ship_radar_4", 3, "surface_detection", 8)
    mod_chain("air_radar_", "ship_radar", "ship_radar_4", 2, "surface_detection", 6)
    # hangar / emals as dummy AA-less modules using ship_airplane_launcher if present
    for name, cat, parent, key in (
        ("ship_helipad_1", "ship_airplane_launcher", "ship_airplane_launcher_1", "carrier_size"),
        ("ship_hangar_1", "ship_airplane_launcher", "ship_airplane_launcher_1", "carrier_size"),
        ("ship_hangar_2", "ship_airplane_launcher", "ship_hangar_1", "carrier_size"),
        ("ship_emals_1", "ship_airplane_launcher", "ship_airplane_launcher_2", "carrier_size"),
        ("ship_uav_deck_1", "ship_airplane_launcher", "ship_airplane_launcher_1", "carrier_size"),
    ):
        if name not in wanted or not need(name):
            continue
        node = wanted[name]
        mods.append(module_variant(name, cat, parent, node["ic"] or 100, f"\t\t\t{key} = 1"))
        created.add(name)

    leftover = [e for e in wanted if e not in have and e not in created]
    # Last-resort generic land kit so enable_equipments never points at missing IDs
    for eq in leftover:
        node = wanted[eq]
        if "hull" in eq:
            hulls.append(
                hull_variant(eq, "ship_hull_light", "ship_hull_light_4", node["year"], node["ic"] or 400, 40, 4000)
            )
        elif any(k in eq for k in ("airframe", "plane", "fighter", "cas", "uav", "heli", "aew", "bomber")):
            air.append(
                scale_airframe(
                    eq,
                    "small_plane_airframe",
                    "small_plane_airframe_5",
                    node["year"],
                    node["ic"] or 24,
                    1000,
                    60,
                    30,
                    1200,
                    1.0,
                )
            )
        elif any(k in eq for k in ("battery", "vls", "sonar", "engine", "torpedo", "dew", "radar", "hangar", "helipad", "emals", "asroc")):
            mods.append(module_variant(eq, "ship_anti_air", "ship_anti_air_4", node["ic"] or 120, "\t\t\tanti_air_attack = 4"))
        else:
            land.append(
                land_variant(
                    eq,
                    "infantry_equipment" if "infantry" in eq else "artillery_equipment",
                    None,
                    node["year"],
                    node["ic"] or 10,
                    {"soft_attack": 10},
                )
            )
        created.add(eq)

    leftover = [e for e in wanted if e not in have and e not in created]
    land.append("}\n")
    hulls.append("}\n")
    chassis.append("}\n")
    mods.append("}\n")
    from write_cw_air import EQUIPMENT_NAMES, write as write_armed_air
    for name in EQUIPMENT_NAMES:
        created.add(name)
    write_armed_air()
    from write_cw_armor import write as write_armed_armor
    write_armed_armor()
    (EQ_DIR / "doomsday_cw_land.txt").write_text("".join(land), encoding="utf-8")
    (EQ_DIR / "doomsday_cw_hulls.txt").write_text("".join(hulls), encoding="utf-8")
    (EQ_DIR / "modules" / "doomsday_ship_modules.txt").write_text("".join(mods), encoding="utf-8")
    return created, leftover, wanted


def write_loc(trees: dict[str, dict], created: set[str], wanted: dict[str, dict]) -> None:
    lines = ["l_english:"]
    for tree in trees.values():
        for n in tree["nodes"]:
            desc = n["analogues"].replace('"', "'")
            extra = n["unlocks"].replace('"', "'")
            lines.append(f' {n["id"]}:0 "{n["name"]}"')
            lines.append(f' {n["id"]}_desc:0 "{desc}. {extra}"')
    for eq in sorted(created):
        node = wanted.get(eq)
        label = node["name"] if node else eq.replace("_", " ")
        label = label.replace('"', "'")
        lines.append(f' {eq}:0 "{label}"')
        lines.append(f' {eq}_short:0 "{label}"')
        lines.append(f' {eq}_desc:0 "{label}"')
    LOC.write_bytes("\ufeff".encode("utf-8") + ("\n".join(lines) + "\n").encode("utf-8"))


def write_gfx(trees: dict[str, dict]) -> None:
    lines = ["spriteTypes = {"]
    for tid, tree in trees.items():
        tex = ICON_BY_TREE[tid]
        for n in tree["nodes"]:
            lines.append(
                f"""
	spriteType = {{
		name = "GFX_{n['id']}"
		texturefile = "{tex}"
	}}
	spriteType = {{
		name = "GFX_{n['id']}_medium"
		texturefile = "{tex}"
	}}"""
            )
    lines.append("\n}\n")
    GFX.write_text("\n".join(lines), encoding="utf-8")


def year_label_boxes(folder: str) -> list[str]:
    boxes = []
    for y in range(1955, 2040, 5):
        py = 90 + year_y(y) * 36
        boxes.append(
            f'\t\t\tinstantTextBoxType = {{ name = "dd_yr_{folder}_{y}" '
            f"position = {{ x = 2 y = {py} }} textureFile = \"\" font = \"hoi_22tech\" "
            f'borderSize = {{ x = 0 y = 0 }} text = "{y}" maxWidth = 48 maxHeight = 24 '
            f'format = left Orientation = "UPPER_LEFT" }}'
        )
    return boxes


def write_gui(trees: dict[str, dict]) -> None:
    text = GUI.read_text(encoding="utf-8")
    # Drop previous generated grids and year labels
    text = re.sub(
        r"\n\t\t\t# DD_TECH_GRID_START.*?# DD_TECH_GRID_END\n",
        "\n",
        text,
        flags=re.S,
    )
    text = re.sub(
        r'(name = "[A-Za-z0-9_]*year[A-Za-z0-9_]*"[\s\S]{0,280}?text = )"[^"]+"',
        r'\1""',
        text,
    )
    by_folder: dict[str, list[str]] = defaultdict(list)
    for tid, tree in trees.items():
        col_x = {cid: i for i, (cid, _) in enumerate(tree["columns"])}
        for n in tree["nodes"]:
            if n["id"] in FLOOR_IDS:
                continue
            px = 40 + col_x[n["col"]] * 140
            py = 90 + year_y(n["year"]) * 36
            box = (
                f'\t\t\tgridboxtype = {{ name = "{n["id"]}_tree" '
                f"position = {{ x = {px} y = {py} }} "
                f'slotsize = {{ width = 70 height = 70 }} format = "LEFT" }}'
            )
            for folder in FOLDERS[tid]:
                by_folder[folder].append(box)
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
        block = (
            "\n\t\t\t# DD_TECH_GRID_START\n"
            + "\n".join(year_label_boxes(folder) + boxes)
            + "\n\t\t\t# DD_TECH_GRID_END\n\t\t\t"
        )
        text = text[:insert_at] + block + text[insert_at:]
    for old, new in (
        ("width = 1600 height = 2100", "width = 1800 height = 2100"),
        ("width = 1400 height = 1275", "width = 1800 height = 2100"),
        ("width = 1400 height = 800", "width = 1800 height = 2100"),
        ("width = 1450 height = 1090", "width = 1800 height = 2100"),
        ("width = 1900 height = 1090", "width = 2000 height = 2100"),
        ("width = 1515 height = 1700", "width = 1800 height = 2100"),
        ("width=1700 height=1300", "width=1800 height=2100"),
        ("width = 2240 height = 1600", "width = 2240 height = 2100"),
        ("width = 2500 height = 1600", "width = 2500 height = 2100"),
        ("width = 710 height = 1100", "width = 1800 height = 2100"),
        ("width = 1650 height = 1000", "width = 1800 height = 2100"),
    ):
        text = text.replace(old, new)
    GUI.write_text(text, encoding="utf-8")


def hide_vanilla_folders() -> None:
    from slim_tech_tree import _remove_key_blocks, split_techs

    for name in VANILLA_FOLDER_FILES:
        path = TECH_DIR / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        techs = split_techs(text)
        if not techs:
            continue
        pieces = []
        cursor = 0
        for tname, start, end, body in techs:
            new_body = body
            if not tname.startswith("dd_") and re.search(r"\bfolder\s*=", body):
                new_body = _remove_key_blocks(body, "folder")
            pieces.append(text[cursor:start])
            if new_body == body:
                pieces.append(text[start:end])
            else:
                brace_at = text.find("{", start, end)
                pieces.append(text[start : brace_at + 1] + new_body + "}")
            cursor = end
        pieces.append(text[cursor:])
        path.write_text("".join(pieces), encoding="utf-8")
    # Slots come from dd_slot_1/2/3 only.
    ind = TECH_DIR / "industry.txt"
    text = ind.read_text(encoding="utf-8")
    text = re.sub(r"\n\t\tglobal_building_slots_factor = [0-9.]+", "", text)
    ind.write_text(text, encoding="utf-8")


def patch_history(trees: dict[str, dict]) -> None:
    from slim_tech_tree import build_tech_block, existing_tech_ids

    ids = existing_tech_ids()
    extra = [n["id"] for t in trees.values() for n in t["nodes"] if n["id"] in FLOOR_IDS and n["id"] in ids]
    block = build_tech_block(ids)
    # Insert floor techs before closing brace
    missing = [t for t in extra if f"\t{t} = 1" not in block]
    if missing:
        block = block.replace("\n}", "".join(f"\n\t{t} = 1" for t in missing) + "\n}")
    for path in sorted(HIST.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        new, n = re.subn(r"set_technology = \{.*?\n\}", block, text, count=1, flags=re.S)
        if n:
            path.write_text(new, encoding="utf-8")


def patch_units() -> None:
    aa = ROOT / "common" / "units" / "doomsday_aa.txt"
    text = aa.read_text(encoding="utf-8")
    text = text.replace(
        "anti_air_equipment = 8",
        "manpads_equipment = 8",
        1,
    )
    aa.write_text(text, encoding="utf-8")


def main() -> None:
    trees = parse_canvas()
    counts = {k: len(v["nodes"]) for k, v in trees.items()}
    print("trees", counts, "total", sum(counts.values()))
    print("canvas", CANVAS, "exists", CANVAS.exists())
    write_techs(trees)
    created, leftover, wanted = generate_equipment(trees)
    print("new equipment", len(created), "unclassified leftover", len(leftover))
    if leftover[:12]:
        print(" leftover sample", leftover[:12])
    if "infantry_equipment_cw1" not in created and "infantry_equipment_cw1" not in existing_equipment():
        raise SystemExit("equipment generation missed infantry_equipment_cw1")
    write_loc(trees, created, wanted)
    write_gfx(trees)
    write_gui(trees)
    hide_vanilla_folders()
    # Old nine-node file is replaced by dd_air / dd_artillery
    old = TECH_DIR / "doomsday_techs.txt"
    if old.exists():
        old.write_text(
            "# Replaced by dd_*.txt generated trees. File kept empty so replace_path loads.\n"
            "technologies = {\n}\n",
            encoding="utf-8",
        )
    patch_units()
    patch_history(trees)
    print("wrote techs, equipment, loc, gfx, gui, history")


if __name__ == "__main__":
    main()
