#!/usr/bin/env python3
"""Hide WWI/WWII combat techs from research folders without deleting IDs.

Floor (identical start for every tag until national trees exist):
  Cuba, Eritrea, North Korea, Taliban Afghanistan, Somalia, South Sudan.
  Typical kit still in service: AK-pattern rifles, trucks/technicals, towed guns,
  BM-21, APC/BMP, T-55/T-62 class MBT, MiG-21-class jets, cheap UAV, MANPADS.

Do not hide Cold War nodes. Do not start 4th-gen air, 2020s infantry kits,
strike UAV, cruise/SRBM/area SAM. Those stay visible and researchable.

Vanilla focuses still resolve because every hidden ID remains in the files and
is granted in history set_technology.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TECH_DIR = ROOT / "common" / "technologies"

# --- hide from UI (IDs stay) -------------------------------------------------
HIDE_TECHS = frozenset(
    {
        # Infantry: Great War / 1930s rifles. AK-class starts at improved_infantry_weapons.
        "infantry_weapons",
        "infantry_weapons1",
        "infantry_weapons2",
        "support_weapons",
        "support_weapons2",
        "armored_car1",
        "bicycle_infantry",
        "camelry",
        "elephantry",
        "penal_infantry",
        # Armor: interwar through Panther / heavies / amphibious. Keep MBT.
        "gwtank",
        "basic_light_tank",
        "basic_light_td",
        "basic_light_art",
        "basic_light_spaa",
        "improved_light_tank",
        "improved_light_td",
        "improved_light_art",
        "improved_light_spaa",
        "advanced_light_tank",
        "advanced_light_td",
        "advanced_light_art",
        "advanced_light_spaa",
        "amphibious_tank",
        "amphibious_tank_2",
        "basic_medium_tank",
        "basic_medium_td",
        "basic_medium_art",
        "basic_medium_spaa",
        "improved_medium_tank",
        "improved_medium_td",
        "improved_medium_art",
        "improved_medium_spaa",
        "advanced_medium_tank",
        "advanced_medium_td",
        "advanced_medium_art",
        "advanced_medium_spaa",
        "basic_heavy_tank",
        "basic_heavy_td",
        "basic_heavy_art",
        "basic_heavy_spaa",
        "improved_heavy_tank",
        "improved_heavy_td",
        "improved_heavy_art",
        "improved_heavy_spaa",
        "advanced_heavy_tank",
        "advanced_heavy_td",
        "advanced_heavy_art",
        "advanced_heavy_spaa",
        "super_heavy_tank",
        "super_heavy_td",
        "super_heavy_art",
        "super_heavy_spaa",
        "mountain_tanks",
        "jungle_tanks",
        "jungle_heavy_tanks",
        "gwtank_chassis",
        "basic_light_tank_chassis",
        "improved_light_tank_chassis",
        "advanced_light_tank_chassis",
        "amphibious_tank_chassis",
        "amphibious_drive",
        "basic_medium_tank_chassis",
        "improved_medium_tank_chassis",
        "advanced_medium_tank_chassis",
        "basic_heavy_tank_chassis",
        "improved_heavy_tank_chassis",
        "advanced_heavy_tank_chassis",
        "super_heavy_tank_chassis",
        "sp_armored_advanced_flamethrower_tech",
        "sp_armored_lc_naval_engine_conversion_tech",
        "sp_armored_lc_transmission_improvements_tech",
        "sp_armored_lc_specialized_field_manuals_tech",
        "sp_armored_lc_weapon_fire_control_tech",
        "sp_armored_lc_high_impact_obliterator_cannon_tech",
        # Air: piston / biplane / 1944 props. Keep jets, CAS3, late transport.
        "early_fighter",
        "fighter1",
        "fighter2",
        "fighter3",
        "cv_early_fighter",
        "cv_fighter1",
        "cv_fighter2",
        "cv_fighter3",
        "CAS1",
        "CAS2",
        "cv_CAS1",
        "cv_CAS2",
        "naval_bomber1",
        "naval_bomber2",
        "naval_bomber3",
        "cv_naval_bomber1",
        "cv_naval_bomber2",
        "cv_naval_bomber3",
        "early_bomber",
        "heavy_fighter1",
        "heavy_fighter2",
        "heavy_fighter3",
        "scout_plane1",
        "scout_plane2",
        "tactical_bomber1",
        "tactical_bomber2",
        "tactical_bomber3",
        "strategic_bomber1",
        "strategic_bomber2",
        "strategic_bomber3",
        "suicide_craft",
        "early_transport_plane",
        "iw_small_airframe",
        "basic_small_airframe",
        "improved_small_airframe",
        "iw_medium_airframe",
        "basic_medium_airframe",
        "improved_medium_airframe",
        "iw_large_airframe",
        "basic_large_airframe",
        "improved_large_airframe",
        "early_bombs",
        "heavy_bombs",
        "armor_piercing_bombs",
        "photo_reconnaisance",
        "air_torpedoe_1",
        "air_torpedoe_2",
        "aa_lmg",
        "aa_hmg",
        "aa_cannon_1",
        "engines_1",
        "engines_2",
        "engines_3",
        "range_improvements",
        "aircraft_construction",
        "survivability_studies",
        "suicide_charge",
        "bba_early_transport_plane",
        "reinforced_wings_mothership",
        "miniature_fighters",
        "aerial_hangars",
        "sp_centrifugal_jet_tech",
        # Artillery: GW / interwar / 1939. Keep 1940+ as D-30 / M-46 class.
        "gw_artillery",
        "interwar_artillery",
        "artillery1",
        "interwar_antiair",
        "antiair1",
        "interwar_antitank",
        "antitank1",
        "mountain_gun",
        "sp_artillery_rocket_assisted_projectiles_tech",
        "sp_artillery_purpose_built_gun_motor_carriages_tech",
        "sp_shock_hardening_techniques",
        "sp_variable_time_fuze_shells",
        "sp_advance_sabot_shells",
        "sp_land_large_caliber_kinetic_energy_sabot_gd_tech",
        "sp_land_large_caliber_kinetic_energy_sabot_no_gd_tech",
        # Navy: battleships, cruisers, carriers. Keep destroyers and subs.
        "early_light_cruiser",
        "basic_light_cruiser",
        "improved_light_cruiser",
        "advanced_light_cruiser",
        "early_heavy_cruiser",
        "basic_heavy_cruiser",
        "improved_heavy_cruiser",
        "advanced_heavy_cruiser",
        "early_battlecruiser",
        "basic_battlecruiser",
        "early_battleship",
        "basic_battleship",
        "improved_battleship",
        "advanced_battleship",
        "heavy_battleship",
        "heavy_battleship2",
        "early_carrier",
        "basic_carrier",
        "improved_carrier",
        "advanced_carrier",
        "early_destroyer",
        "early_submarine",
        "torpedo_cruiser",
        "early_ship_hull_light",
        "early_ship_hull_cruiser",
        "basic_ship_hull_cruiser",
        "improved_ship_hull_cruiser",
        "advanced_ship_hull_cruiser",
        "basic_cruiser_armor_scheme",
        "early_ship_hull_heavy",
        "basic_ship_hull_heavy",
        "improved_ship_hull_heavy",
        "advanced_ship_hull_heavy",
        "ship_hull_super_heavy",
        "basic_heavy_armor_scheme",
        "improved_heavy_armor_scheme",
        "early_ship_hull_carrier",
        "basic_ship_hull_carrier",
        "improved_ship_hull_carrier",
        "advanced_ship_hull_carrier",
        "early_ship_hull_submarine",
        "panzerschiffe",
        "torpedo_cruiser_mtg",
        "pre_dreadnoughts",
        "coastal_defense_ships",
        "smoke_generator",
        "sp_refined_pykrete",
        "sp_ice_composite_runawayas",
        "basic_heavy_battery",
        "improved_heavy_battery",
        "advanced_heavy_battery",
        "basic_heavy_shell",
        "improved_heavy_shell",
        # Support: railway guns, not infantry support companies.
        "railway_gun",
        "armored_train",
    }
)

# Cold War / 2026 nodes that must remain on the tree after slimming.
KEEP_VISIBLE = frozenset(
    {
        "improved_infantry_weapons",
        "improved_infantry_weapons_2",
        "advanced_infantry_weapons",
        "advanced_infantry_weapons2",
        "infantry_at",
        "infantry_at2",
        "mechanised_infantry",
        "mechanised_infantry2",
        "mechanised_infantry3",
        "main_battle_tank",
        "main_battle_tank_chassis",
        "jet_fighter1",
        "jet_fighter2",
        "CAS3",
        "modern_small_airframe",
        "advanced_small_airframe",
        "artillery2",
        "rocket_artillery",
        "basic_destroyer",
        "basic_submarine",
        "dd_recon_uav",
        "dd_strike_uav",
        "dd_transport_heli",
        "dd_manpads",
        "dd_shorad",
        "dd_cruise_missile",
        "dd_srbm",
        "dd_sam",
    }
)

# WWII special-project gates on leftover Cold War / 4th-gen nodes. History unlock
# bypasses allow; research does not. Strip so jet_fighter2 / 4th-gen airframes
# can be researched in 2026 without completing 1940s special projects.
CLEAR_SP_ALLOW = frozenset(
    {
        "jet_fighter1",
        "jet_fighter2",
        "jet_tactical_bomber1",
        "jet_tactical_bomber2",
        "jet_strategic_bomber1",
        "modern_small_airframe",
        "modern_medium_airframe",
        "modern_large_airframe",
        "supersonic_small_airframe",
        "CAS3",
    }
)

# Researched at start. Hidden parents are included so focuses and equipment
# chains resolve. Visible 4th-gen / strike / missile techs are omitted.
VISIBLE_START = (
    # Small arms floor = AK (infantry_equipment_2). 2020s kit stays researchable.
    "improved_infantry_weapons",
    "improved_infantry_weapons_2",
    "infantry_at",
    "support_weapons3",
    "support_weapons4",
    "tech_trucks",
    "motorised_infantry",
    "mechanised_infantry",
    "mechanised_infantry2",
    "marines",
    "paratroopers",
    "tech_mountaineers",
    "tech_support",
    "tech_engineers",
    "tech_engineers2",
    "tech_recon",
    "tech_recon2",
    "tech_military_police",
    "tech_maintenance_company",
    "tech_field_hospital",
    "tech_logistics_company",
    "tech_signal_company",
    "basic_train",
    "artillery2",
    "artillery3",
    "antiair2",
    "antiair3",
    "antitank2",
    "antitank3",
    "rocket_artillery",
    "main_battle_tank",
    "modern_td",
    "modern_art",
    "modern_spaa",
    "main_battle_tank_chassis",
    "armor_tech_1",
    "armor_tech_2",
    "engine_tech_1",
    "engine_tech_2",
    "jet_fighter1",
    "improved_transport_plane",
    "advanced_small_airframe",
    "advanced_medium_airframe",
    "engines_4",
    "aa_cannon_2",
    "air_torpedoe_3",
    "bba_improved_transport_plane",
    "basic_destroyer",
    "improved_destroyer",
    "basic_submarine",
    "transport",
    "landing_craft",
    "basic_ship_hull_light",
    "improved_ship_hull_light",
    "basic_ship_hull_submarine",
    "basic_battery",
    "basic_light_battery",
    "basic_torpedo",
    "mtg_transport",
    "sonar",
    "basic_depth_charges",
    "electronic_mechanical_engineering",
    "radio",
    "improved_radio",
    "mechanical_computing",
    "computing_machine",
    "radio_detection",
    "experimental_rockets",
    "rocket_engines",
    "jet_engines",
    "basic_machine_tools",
    "improved_machine_tools",
    "advanced_machine_tools",
    "construction1",
    "construction2",
    "construction3",
    "excavation1",
    "fuel_silos",
    "fuel_refining",
    "dd_recon_uav",
    "dd_transport_heli",
    "dd_shorad",
    "dd_manpads",
)

MUST_NOT_START = frozenset(
    {
        "advanced_infantry_weapons",
        "advanced_infantry_weapons2",
        "mechanised_infantry3",
        "modern_small_airframe",
        "jet_fighter2",
        "CAS3",
        "dd_strike_uav",
        "dd_loitering_munition",
        "dd_cruise_missile",
        "dd_srbm",
        "dd_sam",
    }
)


def _matching_brace(text: str, open_idx: int) -> int:
    depth = 0
    i = open_idx
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def split_techs(text: str) -> list[tuple[str, int, int, str]]:
    """Return (name, start, end, body) for each tech. start/end slice the full assignment."""
    match = re.search(r"technologies\s*=\s*\{", text)
    if not match:
        return []
    i = match.end()
    n = len(text)
    techs: list[tuple[str, int, int, str]] = []
    while i < n:
        while i < n and text[i] in " \t\r\n":
            i += 1
        if i >= n or text[i] == "}":
            break
        if text[i] in "#@":
            while i < n and text[i] != "\n":
                i += 1
            continue
        km = re.match(r"([a-zA-Z0-9_]+)\s*=\s*\{", text[i:])
        if not km:
            i += 1
            continue
        name = km.group(1)
        brace = i + km.end() - 1
        close = _matching_brace(text, brace)
        if close < 0:
            break
        body = text[brace + 1 : close]
        techs.append((name, i, close + 1, body))
        i = close + 1
    return techs


def existing_tech_ids(tech_dir: Path | None = None) -> set[str]:
    found: set[str] = set()
    for path in sorted((tech_dir or TECH_DIR).glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        for name, *_ in split_techs(text):
            found.add(name)
    return found


def _remove_key_blocks(body: str, key: str) -> str:
    pattern = re.compile(rf"(?:\n[ \t]*)?{re.escape(key)}\s*=")
    while True:
        match = pattern.search(body)
        if not match:
            return body
        j = match.end()
        while j < len(body) and body[j] in " \t":
            j += 1
        if j < len(body) and body[j] == "{":
            close = _matching_brace(body, j)
            if close < 0:
                return body
            body = body[: match.start()] + body[close + 1 :]
            continue
        endl = body.find("\n", match.end())
        body = body[: match.start()] + (body[endl:] if endl >= 0 else "")


def _strip_sp_gate(body: str) -> str:
    if "is_special_project_completed" not in body:
        body = _remove_key_blocks(body, "is_special_project_tech")
        return body
    body = _remove_key_blocks(body, "allow")
    body = _remove_key_blocks(body, "is_special_project_tech")
    return body


def slim_file(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    techs = split_techs(text)
    if not techs:
        return 0, 0
    pieces: list[str] = []
    cursor = 0
    stripped = 0
    ungated = 0
    for name, start, end, body in techs:
        new_body = body
        if name in HIDE_TECHS and re.search(r"\bfolder\s*=", new_body):
            new_body = _remove_key_blocks(new_body, "folder")
            stripped += 1
        if name in CLEAR_SP_ALLOW:
            before = new_body
            new_body = _strip_sp_gate(new_body)
            if new_body != before:
                ungated += 1
        pieces.append(text[cursor:start])
        if new_body == body:
            pieces.append(text[start:end])
        else:
            brace_at = text.find("{", start, end)
            pieces.append(text[start : brace_at + 1] + new_body + "}")
        cursor = end
    pieces.append(text[cursor:])
    new_text = "".join(pieces)
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
    return stripped, ungated


def apply_slim(root: Path | None = None) -> dict[str, int]:
    tech_dir = (root or ROOT) / "common" / "technologies"
    hidden = 0
    ungated = 0
    for path in sorted(tech_dir.glob("*.txt")):
        s, u = slim_file(path)
        hidden += s
        ungated += u
    ids = existing_tech_ids(tech_dir)
    missing_ids = sorted(t for t in KEEP_VISIBLE if t not in ids)
    lost_folder: list[str] = []
    still_folded: list[str] = []
    for path in tech_dir.glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        for name, _, _, body in split_techs(text):
            if name in HIDE_TECHS and re.search(r"\bfolder\s*=", body):
                still_folded.append(name)
            if name in KEEP_VISIBLE and not re.search(r"\bfolder\s*=", body):
                lost_folder.append(f"{name} in {path.name}")
    if still_folded:
        raise RuntimeError(f"folder strip missed: {still_folded[:20]}")
    if missing_ids:
        raise RuntimeError(f"keep-visible techs missing from files: {missing_ids}")
    if lost_folder:
        raise RuntimeError(f"keep-visible techs lost their folder: {lost_folder[:20]}")
    return {"hidden_folders": hidden, "cleared_sp": ungated}


def start_techs(ids: set[str] | None = None) -> list[str]:
    present = ids if ids is not None else existing_tech_ids()
    ordered: list[str] = []
    seen: set[str] = set()
    for name in list(sorted(HIDE_TECHS)) + list(VISIBLE_START):
        if name in seen or name not in present:
            continue
        if name in MUST_NOT_START:
            continue
        seen.add(name)
        ordered.append(name)
    leaked = [t for t in ordered if t in MUST_NOT_START]
    if leaked:
        raise RuntimeError(f"start list includes modern techs: {leaked}")
    return ordered


def build_tech_block(ids: set[str] | None = None) -> str:
    lines = [
        "# Cold War floor: Cuba/Eritrea/NK/Taliban-style inventories.",
        "# WWI/WWII weapon IDs stay researched (hidden from the tree) so vanilla focuses resolve.",
        "set_technology = {",
    ]
    for name in start_techs(ids):
        lines.append(f"\t{name} = 1")
    lines.append("}")
    return "\n".join(lines)


def main() -> int:
    stats = apply_slim(ROOT)
    block = build_tech_block()
    print(f"stripped folders={stats['hidden_folders']} cleared_sp={stats['cleared_sp']}")
    print(f"start techs={block.count(' = 1')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
