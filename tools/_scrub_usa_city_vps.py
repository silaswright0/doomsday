#!/usr/bin/env python3
"""Keep only verified US city VPs; drop projection-guessed / mismatched names."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(".")
STATES = ROOT / "history" / "states"
LOC = ROOT / "localisation" / "english" / "doomsday_usa_cities_l_english.yml"
VANILLA = pathlib.Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\localisation\english\victory_points_l_english.yml"
)

CAT_VP = {1: 25, 2: 12, 3: 5, 4: 2}
VP_OVERRIDE = {
    "New York": 35,
    "Los Angeles": 30,
    "Chicago": 30,
    "Houston": 25,
    "Washington": 20,
}

# Only hand-verified province placements (real city at that province).
# Format: name -> (province_id, category)
VERIFIED: dict[str, tuple[int, int]] = {
    # Cat 1
    "New York": (3878, 1),
    "Los Angeles": (9814, 1),
    "Chicago": (9450, 1),
    "Houston": (10337, 1),
    "Phoenix": (853, 1),
    "Philadelphia": (6845, 1),
    "San Antonio": (12782, 1),
    "San Diego": (1562, 1),
    "Dallas": (3960, 1),
    "Fort Worth": (7981, 1),
    "Jacksonville": (10352, 1),
    "Austin": (6798, 1),
    # Cat 2
    "San Jose": (6861, 2),
    "Charlotte": (7138, 2),
    "Columbus": (6855, 2),
    "Indianapolis": (1595, 2),
    "San Francisco": (9671, 2),
    "Seattle": (7315, 2),
    "Denver": (1827, 2),
    "Oklahoma City": (5103, 2),
    "Nashville": (12501, 2),
    "Washington": (3957, 2),
    "Las Vegas": (4799, 2),
    "El Paso": (1998, 2),
    "Boston": (6732, 2),
    "Detroit": (6710, 2),
    "Louisville": (6696, 2),
    "Portland": (3513, 2),
    "Memphis": (7797, 2),
    "Baltimore": (6984, 2),
    "Milwaukee": (12357, 2),
    "Albuquerque": (4975, 2),
    "Fresno": (6694, 2),
    "Tucson": (3834, 2),
    "Sacramento": (9713, 2),
    "Atlanta": (12384, 2),
    "Kansas City": (10717, 2),
    "Raleigh": (10081, 2),
    # Cat 3
    "Omaha": (12586, 3),
    "Colorado Springs": (868, 3),
    "Virginia Beach": (873, 3),
    "Miami": (1843, 3),
    "Oakland": (4518, 3),
    "Minneapolis": (1866, 3),
    "Tulsa": (1806, 3),
    "Bakersfield": (610, 3),
    "Wichita": (4740, 3),
    "New Orleans": (7552, 3),
    "Tampa": (7388, 3),
    "Honolulu": (4180, 3),
    "Corpus Christi": (805, 3),
    "Saint Louis": (4569, 3),
    "Pittsburgh": (11800, 3),
    "Stockton": (9637, 3),
    "Anchorage": (13091, 3),
    "Cincinnati": (6874, 3),
    "Saint Paul": (6752, 3),
    "Greensboro": (12054, 3),
    "Toledo": (9808, 3),
    "Newark": (6882, 3),
    "Orlando": (1572, 3),
    "Buffalo": (11654, 3),
    "Madison": (1560, 3),
    "Norfolk": (788, 3),
    "Lubbock": (2055, 3),
    "Reno": (4607, 3),
    "Baton Rouge": (1453, 3),
    "Richmond": (10412, 3),
    "Boise": (9616, 3),
    "Durham": (7045, 3),
    "Laredo": (5061, 3),
    # Cat 4 — only where province placement is confident
    "Spokane": (1690, 4),
    "Des Moines": (1770, 4),
    "Tacoma": (7255, 4),
    "Birmingham": (12735, 4),
    "Salt Lake City": (4865, 4),
    "Grand Rapids": (6769, 4),
    "Amarillo": (3972, 4),
    "Akron": (882, 4),
    "Little Rock": (12489, 4),
    "Augusta": (11975, 4),
    "Shreveport": (12401, 4),
    "Columbus GA": (12325, 4),
    "Tallahassee": (12381, 4),
    "Huntsville": (4756, 4),
    "Mobile": (7480, 4),
    "Knoxville": (8014, 4),
    "Worcester": (3715, 4),
    "Providence": (3906, 4),
    "Chattanooga": (1758, 4),
    "Salem": (12211, 4),
    "Eugene": (10305, 4),
    "Springfield MO": (10370, 4),
    "Rockford": (12305, 4),
    "Fort Collins": (10588, 4),
    "Macon": (10437, 4),
    "Syracuse": (9664, 4),
    "Rochester": (3702, 4),
    "Waco": (12341, 4),
    "Savannah": (12498, 4),
    "Dayton": (9775, 4),
    "Gainesville": (10407, 4),
    "Lafayette": (7555, 4),
    "Hartford": (9675, 4),
    "Ann Arbor": (9724, 4),
    "Fargo": (1870, 4),
    "Lansing": (11656, 4),
    "Springfield IL": (7831, 4),
    "Charleston SC": (7202, 4),
    "Columbia SC": (4491, 4),
    "Jackson": (4565, 4),
    "Brooklyn": (3894, 4),
    "Vancouver": (12214, 4),
    "Sioux Falls": (10595, 4),
    "Allentown": (9789, 4),
    "Montgomery": (4622, 4),
    "Lexington": (12568, 4),
    "Fort Wayne": (11637, 4),
    "Bridgeport": (9850, 4),
    "New Haven": (3710, 4),
    "Stamford": (9847, 4),
    "West Palm Beach": (9834, 4),
    "Port St Lucie": (1913, 4),
    "McAllen": (12369, 4),
    "Brownsville": (6785, 4),
    "Midland": (4955, 4),
    "Riverside": (823, 4),
    "San Bernardino": (7517, 4),
    "Alexandria": (951, 4),
    "Provo": (1740, 4),
    "Aurora IL": (9682, 4),
    "Naperville": (6737, 4),
    "Yonkers": (11660, 4),
    "Aurora CO": (12642, 4),
    "Fayetteville": (4168, 4),
}


def display_name(key: str) -> str:
    for suffix in (" CO", " TX", " AZ", " IL", " FL", " GA", " MO", " SC"):
        if key.endswith(suffix):
            base = key[: -len(suffix)]
            if base in {
                "Aurora",
                "Columbus",
                "Columbia",
                "Springfield",
                "Charleston",
                "Arlington",
                "Glendale",
                "Pasadena",
                "Hollywood",
                "Peoria",
                "Concord",
            }:
                return base
    return key


def find_state_file(sid: int) -> pathlib.Path | None:
    for p in STATES.glob("*.txt"):
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if re.search(rf"^\s*id\s*=\s*{sid}\b", t, re.M):
            return p
    return None


def get_provinces(text: str) -> set[int]:
    m = re.search(r"provinces\s*=\s*\{([^}]*)\}", text, re.S)
    if not m:
        return set()
    return {int(x) for x in re.findall(r"\d+", m.group(1))}


def replace_vps(text: str, entries: list[tuple[int, int, str]]) -> str:
    text2 = re.sub(r"\n?\s*victory_points\s*=\s*\{[^}]*\}", "", text)
    if not entries:
        return text2
    block = "\t\tvictory_points = {\n"
    for pid, vp, name in sorted(entries, key=lambda e: (-e[1], e[2])):
        block += f"\t\t\t{pid} {vp} # {name}\n"
    block += "\t\t}\n"
    m = re.search(r"(add_core_of\s*=\s*USA\s*\n)", text2)
    if m:
        return text2[: m.end()] + block + text2[m.end() :]
    m2 = re.search(r"(\n\tprovinces\s*=)", text2)
    if m2:
        hist = text2.rfind("}", 0, m2.start())
        return text2[:hist] + block + "\t" + text2[hist:]
    return text2


def main() -> None:
    # Load all US-ish state province membership
    us_sids = (
        [261]
        + list(range(357, 397))
        + [463, 629, 686, 816]
        + list(range(1124, 1138))
    )
    pid_to_sid: dict[int, int] = {}
    sid_text: dict[int, tuple[pathlib.Path, str]] = {}
    for sid in us_sids:
        path = find_state_file(sid)
        if not path:
            continue
        text = path.read_text(encoding="utf-8")
        sid_text[sid] = (path, text)
        for pid in get_provinces(text):
            pid_to_sid[pid] = sid

    # Build verified entries; drop if province not in any US state
    by_state: dict[int, list[tuple[int, int, str]]] = {}
    kept = []
    dropped = []
    used_pids: set[int] = set()
    # Prefer higher category if two verified cities somehow share a province
    ranked = sorted(VERIFIED.items(), key=lambda kv: (kv[1][1], -CAT_VP[kv[1][1]], kv[0]))
    for name, (pid, cat) in ranked:
        if pid not in pid_to_sid:
            dropped.append(f"{name} ({pid}) province not in US states")
            continue
        if pid in used_pids:
            dropped.append(f"{name} ({pid}) province already used")
            continue
        used_pids.add(pid)
        sid = pid_to_sid[pid]
        dname = display_name(name)
        vp = VP_OVERRIDE.get(name, CAT_VP[cat])
        by_state.setdefault(sid, []).append((pid, vp, dname))
        kept.append(f"{dname} -> {pid} cat{cat} vp{vp}")

    # Rewrite every US state: verified VPs only (clears guessed names)
    for sid, (path, text) in sid_text.items():
        entries = by_state.get(sid, [])
        # Preserve vanilla leftovers only for states with no verified cities
        # and that still have unlabeled legacy VPs outside our rewrite set.
        # User asked to remove made-up names: wipe and rewrite from verified only.
        new_text = replace_vps(text, entries)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8", newline="\n")
        print(f"{path.name}: {len(entries)} VPs")

    # Loc only for verified
    loc_lines = ["l_english:\n"]
    all_loc = {}
    for entries in by_state.values():
        for pid, vp, name in entries:
            all_loc[pid] = name
    for pid, name in sorted(all_loc.items()):
        loc_lines.append(f' VICTORY_POINTS_{pid}:0 "{name}"\n')
    LOC.write_text("".join(loc_lines), encoding="utf-8", newline="\n")

    print(f"\nkept {len(kept)} verified cities")
    print(f"dropped {len(dropped)}")
    for d in dropped:
        print(" ", d)


if __name__ == "__main__":
    main()
