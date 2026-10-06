#!/usr/bin/env python3
"""Assign verified US city victory points by population category."""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(".")
STATES = ROOT / "history" / "states"
LOC = ROOT / "localisation" / "english" / "replace" / "doomsday_usa_cities_l_english.yml"
LOC_ENGLISH = ROOT / "localisation" / "english" / "doomsday_usa_cities_l_english.yml"

CAT_VP = {1: 25, 2: 12, 3: 5, 4: 2}
VP_OVERRIDE = {
    "New York": 35,
    "Los Angeles": 30,
    "Chicago": 30,
    "Houston": 25,
    "Washington": 20,
}

# name -> (province_id, category)
# Suburbs that share a province are listed so they collapse under the higher category.
CITIES: dict[str, tuple[int, int]] = {
    # --- Category 1 ---
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
    # --- Category 2 ---
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
    "Mesa": (853, 2),  # collapses into Phoenix
    "Raleigh": (10081, 2),
    # --- Category 3 ---
    "Omaha": (12586, 3),
    "Colorado Springs": (868, 3),
    "Long Beach": (9814, 3),
    "Virginia Beach": (873, 3),
    "Miami": (1843, 3),
    "Oakland": (4518, 3),
    "Minneapolis": (1866, 3),
    "Tulsa": (1806, 3),
    "Bakersfield": (610, 3),
    "Wichita": (4740, 3),
    "Aurora CO": (12642, 3),
    "New Orleans": (7552, 3),
    "Arlington TX": (7981, 3),
    "Tampa": (7388, 3),
    "Honolulu": (4180, 3),
    "Anaheim": (9814, 3),
    "Santa Ana": (9814, 3),
    "Corpus Christi": (805, 3),
    "Riverside": (823, 3),
    "Saint Louis": (4569, 3),
    "Lexington": (12568, 3),
    "Pittsburgh": (11800, 3),
    "Stockton": (9637, 3),
    "Anchorage": (13091, 3),
    "Cincinnati": (6874, 3),
    "Saint Paul": (6752, 3),
    "Greensboro": (12054, 3),
    "Toledo": (9808, 3),
    "Newark": (6882, 3),
    "Plano": (3960, 3),
    "Henderson": (4799, 3),
    "Lincoln": (12586, 3),
    "Orlando": (1572, 3),
    "Jersey City": (6882, 3),
    "Chula Vista": (1562, 3),
    "Buffalo": (11654, 3),
    "Fort Wayne": (11637, 3),
    "Chandler": (853, 3),
    "Saint Petersburg": (7388, 3),
    "Laredo": (5061, 3),
    "Durham": (7045, 3),
    "Irvine": (9814, 3),
    "Madison": (1560, 3),
    "Norfolk": (788, 3),
    "Lubbock": (2055, 3),
    "Gilbert": (853, 3),
    "Winston-Salem": (12054, 3),
    "Glendale AZ": (853, 3),
    "Reno": (4607, 3),
    "Hialeah": (1843, 3),
    "Garland": (3960, 3),
    "Scottsdale": (853, 3),
    "Irving": (7981, 3),
    "Chesapeake": (788, 3),
    "North Las Vegas": (4799, 3),
    "Fremont": (6861, 3),
    "Baton Rouge": (1453, 3),
    "Richmond": (10412, 3),
    "Boise": (9616, 3),
    # --- Category 4 ---
    "Spokane": (1690, 4),
    "Des Moines": (1770, 4),
    "Tacoma": (7255, 4),
    "San Bernardino": (7517, 4),
    "Modesto": (9637, 4),
    "Fontana": (7517, 4),
    "Santa Clarita": (9814, 4),
    "Birmingham": (12735, 4),
    "Oxnard": (9814, 4),
    "Fayetteville": (4168, 4),
    "Rochester": (3702, 4),
    "Huntington Beach": (9814, 4),
    "Salt Lake City": (4865, 4),
    "Grand Rapids": (6769, 4),
    "Amarillo": (3972, 4),
    "Yonkers": (11660, 4),
    "Aurora IL": (9682, 4),
    "Montgomery": (4622, 4),
    "Akron": (882, 4),
    "Little Rock": (12489, 4),
    "Augusta": (11975, 4),
    "Shreveport": (12401, 4),
    "Columbus GA": (12325, 4),
    "Grand Prairie": (7981, 4),
    "Tallahassee": (12381, 4),
    "Huntsville": (4756, 4),
    "Mobile": (7480, 4),
    "Tempe": (853, 4),
    "Knoxville": (8014, 4),
    "Worcester": (3715, 4),
    "Newport News": (788, 4),
    "Brownsville": (6785, 4),
    "Providence": (3906, 4),
    "Santa Rosa": (9671, 4),
    "Peoria AZ": (853, 4),
    "Oceanside": (1562, 4),
    "Fort Lauderdale": (1843, 4),
    "Chattanooga": (1758, 4),
    "Ontario": (7517, 4),
    "Cary": (10081, 4),
    "Elk Grove": (9713, 4),
    "Salem": (12211, 4),
    "Lancaster": (9814, 4),
    "Corona": (823, 4),
    "Eugene": (10305, 4),
    "Palmdale": (9814, 4),
    "Salinas": (6861, 4),
    "Springfield MO": (10370, 4),
    "Pasadena TX": (10337, 4),
    "Rockford": (12305, 4),
    "Pomona": (9814, 4),
    "Hayward": (4518, 4),
    "Fort Collins": (10588, 4),
    "Escondido": (1562, 4),
    "Sunnyvale": (6861, 4),
    "Alexandria": (951, 4),
    "Lakewood": (1827, 4),
    "Hollywood FL": (1843, 4),
    "Clarksville": (12670, 4),
    "Torrance": (9814, 4),
    "Victorville": (7517, 4),
    "Bridgeport": (9850, 4),
    "Macon": (10437, 4),
    "Warren": (6710, 4),
    "Syracuse": (9664, 4),
    "Naperville": (6737, 4),
    "Midland": (4955, 4),
    "Roseville": (9713, 4),
    "Killeen": (1927, 4),
    "Surprise": (853, 4),
    "Denton": (3960, 4),
    "Fullerton": (9814, 4),
    "Mesquite": (3960, 4),
    "Savannah": (12498, 4),
    "McAllen": (12369, 4),
    "Paterson": (6882, 4),
    "Waco": (12341, 4),
    "Visalia": (6694, 4),
    "Olathe": (10717, 4),
    "Thornton": (12642, 4),
    "Orange": (9814, 4),
    "Thousand Oaks": (9814, 4),
    "Hampton": (788, 4),
    "Miramar": (1843, 4),
    "Dayton": (9775, 4),
    "Gainesville": (10407, 4),
    "West Valley City": (4865, 4),
    "Coral Springs": (1843, 4),
    "Cedar Rapids": (1770, 4),
    "Sterling Heights": (6710, 4),
    "New Haven": (3710, 4),
    "Stamford": (9847, 4),
    "Elizabeth": (6882, 4),
    "Concord CA": (4518, 4),
    "Kent": (7255, 4),
    "Lafayette": (7555, 4),
    "Simi Valley": (9814, 4),
    "Santa Clara": (6861, 4),
    "Athens": (11975, 4),
    "Hartford": (9675, 4),
    "Vallejo": (9671, 4),
    "Berkeley": (4518, 4),
    "Round Rock": (6798, 4),
    "Ann Arbor": (9724, 4),
    "Fargo": (1870, 4),
    "Columbia MO": (10370, 4),
    "Provo": (1740, 4),
    "Lansing": (11656, 4),
    "El Monte": (9814, 4),
    "Springfield IL": (7831, 4),
    "Fairfield": (9671, 4),
    "Miami Gardens": (1843, 4),
    "Temecula": (823, 4),
    "Costa Mesa": (9814, 4),
    "College Station": (4577, 4),
    "Elgin": (9682, 4),
    "Murrieta": (823, 4),
    "Gresham": (3513, 4),
    "High Point": (12054, 4),
    "Antioch": (4518, 4),
    "Inglewood": (9814, 4),
    "Cambridge": (6732, 4),
    "Burbank": (9814, 4),
    "Greeley": (10588, 4),
    "San Mateo": (9671, 4),
    "El Cajon": (1562, 4),
    "Charleston SC": (7202, 4),
    "Florida City": (1843, 4),
    "West Palm Beach": (9834, 4),
    "Columbia SC": (4491, 4),
    "Port St Lucie": (1913, 4),
    "Jackson": (4565, 4),
    "Brooklyn": (3894, 4),
    "Vancouver": (12214, 4),
    "Frisco": (3960, 4),
    "Sioux Falls": (10595, 4),
    "Allentown": (9789, 4),
}


def display_name(key: str) -> str:
    for suffix in (" CO", " TX", " AZ", " IL", " FL", " GA", " MO", " SC", " CA"):
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
                "Hollywood",
                "Pasadena",
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
    # One province per block (wiki). Comments ONLY on the brace line —
    # inline "# name" after the numbers triggers error.log:
    # "set victory points takes 2 parameters" on every 2nd+ block.
    block = ""
    for pid, vp, name in sorted(entries, key=lambda e: (-e[1], e[2])):
        block += (
            f"\t\tvictory_points = {{ # {name}\n"
            f"\t\t\t{pid} {vp}\n"
            "\t\t}\n"
        )
    m = re.search(r"(add_core_of\s*=\s*USA\s*\n)", text2)
    if m:
        return text2[: m.end()] + block + text2[m.end() :]
    m2 = re.search(r"(\n\tprovinces\s*=)", text2)
    if m2:
        hist = text2.rfind("}", 0, m2.start())
        return text2[:hist] + block + "\t" + text2[hist:]
    return text2


def main() -> None:
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

    # Best city per province (lower category number wins; then higher VP)
    best: dict[int, tuple[int, str, int]] = {}
    missing = []
    collapsed = 0
    for name, (pid, cat) in CITIES.items():
        if pid not in pid_to_sid:
            missing.append(f"{name} ({pid})")
            continue
        dname = display_name(name)
        vp = VP_OVERRIDE.get(name, CAT_VP[cat])
        if pid not in best:
            best[pid] = (cat, dname, vp)
        else:
            old_cat, old_name, old_vp = best[pid]
            collapsed += 1
            if cat < old_cat or (cat == old_cat and vp > old_vp):
                best[pid] = (cat, dname, vp)

    by_state: dict[int, list[tuple[int, int, str]]] = {}
    for pid, (cat, name, vp) in best.items():
        sid = pid_to_sid[pid]
        by_state.setdefault(sid, []).append((pid, vp, name))

    for sid, (path, text) in sid_text.items():
        entries = by_state.get(sid, [])
        new_text = replace_vps(text, entries)
        path.write_text(new_text, encoding="utf-8", newline="\n")
        if entries:
            print(f"{path.name}: {len(entries)} VPs")

    loc = ["l_english:\n"]
    for pid, (_, name, _) in sorted(best.items()):
        loc.append(f' VICTORY_POINTS_{pid}:0 "{name}"\n')
    LOC.parent.mkdir(parents=True, exist_ok=True)
    # HOI4 English localisation requires UTF-8 with BOM or the file is ignored
    # (victory points then fall back to the state name, e.g. "California").
    # localisation/replace/ is where this mod's working VP overrides already live.
    payload = b"\xef\xbb\xbf" + "".join(loc).encode("utf-8")
    LOC.write_bytes(payload)
    LOC_ENGLISH.parent.mkdir(parents=True, exist_ok=True)
    LOC_ENGLISH.write_bytes(payload)

    print(f"\ncities listed: {len(CITIES)}")
    print(f"unique provinces: {len(best)}")
    print(f"collapsed into shared provinces: {collapsed}")
    if missing:
        print("MISSING provinces:")
        for m in missing:
            print(" ", m)

    print("\nCat1:")
    for name, (pid, cat) in CITIES.items():
        if cat != 1:
            continue
        winner = best.get(pid, (None, "?", None))[1]
        print(f"  {name} -> {pid} ({winner})")


if __name__ == "__main__":
    main()
