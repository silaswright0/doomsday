#!/usr/bin/env python3
"""Build Doomsday 2026 history, loc, and state CSVs from vanilla states + country sheet."""

from __future__ import annotations

import csv
import os
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV")
STATES_DIR = ROOT / "history" / "states"
VANILLA_STATES = VANILLA / "history" / "states"
COUNTRIES_DIR = ROOT / "history" / "countries"
LOC_DIR = ROOT / "localisation" / "english"
CSV_COUNTRIES = Path(__file__).with_name("doomsday_countries.csv")
CSV_STATES = Path(__file__).with_name("doomsday_states.csv")

CIV_PER_MVA_B = 20.0
CIV_MIN_MVA_B = 2.0
MIL_PROCUREMENT_SHARE = 0.35
MIL_PER_PROC_B = 10.0
WARTIME_MIL_MULT = 2.5
FACTORY_LEVEL_CAP = 40
SHARED_SLOTS_CAP = 50

SOVEREIGN = {
    "USA", "CAN", "MEX", "GUA", "HON", "ELS", "NIC", "COS", "PAN", "CUB", "HAI", "DOM",
    "COL", "VEN", "ECU", "PRU", "BOL", "CHL", "ARG", "URG", "PAR", "BRA",
    "ENG", "IRE", "FRA", "SPR", "POR", "BEL", "HOL", "LUX", "SWI", "ITA", "GER", "AUS",
    "CZE", "SLO", "POL", "HUN", "ROM", "BUL", "GRE", "ALB", "YUG", "SER", "CRO", "SLV",
    "BOS", "MAC", "MNT", "KOS", "DEN", "GRN", "NOR", "SWE", "FIN", "ICE", "EST", "LAT", "LIT",
    "SOV", "UKR", "BLR", "MOL", "PMR", "GEO", "ABK", "SOS", "ARM", "AZR", "KAZ", "UZB", "TMS", "KYR", "TAJ",
    "TUR", "GRE", "CYP", "NCY", "MLT",
    "SAU", "YEM", "HOU", "STC", "OMA", "UAE", "QAT", "KUW", "BHR", "IRQ", "KUR", "PER", "AFG", "NRF", "SYR", "ROJ", "DRZ", "SNA", "LEB",
    "JOR", "ISR", "PAL", "HAM", "HEZ", "EGY", "LBA", "TUN", "ALG", "MOR", "WES",
    "ETH", "ERI", "DJI", "SOM", "SML", "PNT", "JUB", "SHB", "KEN", "UGA", "TZN", "RWA", "BRD", "SUD", "SSD",
    "SAF", "LES", "SWZ", "NMB", "BOT", "ZIM", "ZAM", "MLW", "ANG", "MZB", "MAD", "COG", "M23", "RCG", "GAB",
    "EQG", "CMR", "CAR", "CHA", "NGA", "DAH", "TOG", "GHA", "IVO", "VOL", "MLI", "NGR",
    "SEN", "GAM", "GNA", "GNB", "SIE", "LIB", "MRT",
    "RAJ", "PAK", "BAN", "NEP", "BHU", "SRL", "BRM", "NUG", "SIA", "MAL", "SNG", "INS", "PHI",
    "VIN", "CAM", "LAO", "CHI", "MON", "KOR", "DPK", "JAP", "FOR", "TML", "BRN",
    "AST", "NZL", "PNG", "FIJ", "SOL", "VAN", "SAM", "FSM", "PLU",
    "MLD", "BAH", "JAM", "GYA", "BLZ", "TRI", "ATG", "DMA", "STL", "SVG", "GND", "BRB", "BAS", "SUR", "CRC", "CBV",
    "GDL", "CAY", "TAH", "BRN", "SNG",
    "KIR", "TUV", "NAU", "MHL", "MAU", "COM", "STP", "SEY", "PLU",
}

BANNED_OWNERS = {
    "YUG", "MAN", "MEN", "PRC", "SHX", "XSM", "GXC", "YUN", "SIK", "HBC", "RNG", "WGR",
    "DDR", "AOI", "CSA", "USB", "PRE", "BAY", "MEK", "SAX", "HAN", "WUR", "SHL", "THU",
    "HES", "RHI", "PAP", "TOS", "SPM", "TTS", "LBV", "DIP", "DNZ", "SIL", "KSH", "SDL",
    "RUT", "GAL", "CAT", "NAV", "GLC", "ADU", "BRI", "OCC", "COR", "SCO", "WLS", "NIR",
    "QUE", "HAW", "PUE", "GUM", "TAN", "TIB", "HYD", "MYS", "RJP", "CIP", "RAS",
    "NWF", "KAS", "MPU", "WIS", "KOL", "KHL", "SIN", "KLT", "SKK", "FSA", "BLC", "PSH",
    "KUM", "GSM", "GDC", "KHM", "NXM", "SND", "SIC", "XIC", "PSR", "EZO", "OKN", "ANU",
    "CHM", "SAR", "SAB", "WPG", "BLI", "ATJ", "SSI", "POK", "GOW", "TNE", "CPS", "HRZ",
}

for prefix in ("RK", "RG"):
    pass
BANNED_OWNERS.update({
    "RKB", "RKN", "RKG", "RKU", "RKO", "RKK", "RKT", "RKM", "RKL", "GEN", "RKH", "RKI",
    "RKC", "RGB", "RKA", "RNA", "RKV", "RAN", "RCO", "RUS", "RHD", "RAR", "ROA", "RAA",
})

# 1936 tags that are not 2026 countries. Never dump these on SOV.
BANNED_REMAP = {
    "TIB": "CHI", "MAN": "CHI", "MEN": "CHI", "PRC": "CHI",
    "SHX": "CHI", "XSM": "CHI", "GXC": "CHI", "YUN": "CHI", "SIK": "CHI",
    "HBC": "CHI", "RNG": "CHI", "GDC": "CHI", "SIC": "CHI", "SND": "CHI",
    "XIC": "CHI", "KHM": "CHI", "NXM": "CHI", "GSM": "CHI", "KUM": "CHI",
    "TAN": "SOV",
    "WGR": "GER", "DDR": "GER",
}

CORE_PRIORITY = [
    "KOS", "MNT", "MAC", "SLV", "BOS", "CRO", "SER", "SLO", "CZE",
    "EST", "LAT", "LIT", "PMR", "MOL", "UKR", "BLR", "GEO", "ARM", "PER", "AZR",
    "KAZ", "UZB", "TMS", "KYR", "TAJ",
    "BAN", "PAK", "SRL", "NUG", "BRM", "RAJ", "NEP", "BHU",
    "MLD", "BAH", "JAM", "GYA", "BLZ", "TRI", "ATG", "DMA", "STL", "SVG", "GND", "BRB", "BAS", "SUR", "CRC", "CBV", "GDL",
    "ISR", "PAL", "HAM", "HEZ", "NCY", "CYP", "JOR", "LEB", "ROJ", "DRZ", "SNA", "SYR", "IRQ", "KUW", "UAE", "QAT", "BHR", "OMA", "YEM", "HOU", "STC",
    "DPK", "KOR", "FOR", "VIN", "CAM", "LAO", "MAL", "SNG", "INS", "PHI", "TML", "BRN",
    "PLU", "FSM", "KIR", "TUV", "NAU", "MHL", "FIJ", "VAN", "SOL", "MAU", "COM", "STP", "SEY",
    "ALG", "MOR", "WES", "TUN", "LBA", "EGY", "SUD", "SSD", "ERI", "DJI",
    "KEN", "ETH", "SOM", "SML", "PNT", "JUB", "SHB", "UGA", "TZN", "RWA", "BRD",
    "NGA", "GHA", "IVO", "SEN", "MLI", "NGR", "CHA", "CMR", "COG", "M23", "RCG", "GAB", "ANG",
    "MZB", "ZIM", "ZAM", "MLW", "SAF", "NMB", "BOT", "MAD", "LIB", "SIE", "GNA", "GNB",
    "VOL", "DAH", "TOG", "MRT", "GAM", "CAR", "EQG",
    "POL", "AUS", "CHI", "MON", "AST", "NZL", "CAN", "MEX", "USA",
    "SOV", "GER", "FRA", "ENG", "ITA", "JAP", "HOL", "BEL", "POR", "SPR",
]

FILENAME_OWNER = [
    (r"north korea|hamgyong", "DPK"),
    (r"south korea|gyeongsang|chungcheong|jeolla", "KOR"),
    (r"taiwan", "FOR"),
    (r"actual singapore", "SNG"),
    (r"south sudan", "SSD"),
    (r"transnistria|tiraspol", "PMR"),
    (r"greenland", "GRN"),
    (r"srem|syrmia", "SER"),
    (r"salla", "SOV"),
    (r"146-karelia|karjala", "SOV"),
    (r"abkhazia", "ABK"),
    (r"south ossetia|tskhinval", "SOS"),
    (r"nakhchivan", "AZR"),
    (r"panjshir|bazarak", "NRF"),
    (r"iraqi kurdistan|erbil|duhok|sulaymaniyah", "KUR"),
    (r"rojava|qamishli|northeast syria", "ROJ"),
    (r"marib", "YEM"),
    (r"suwayda", "DRZ"),
    (r"peace spring|tell abyad|ras al-ayn", "SNA"),
    (r"puntland", "PNT"),
    (r"al-shabaab|jilib", "SHB"),
    (r"jubaland", "JUB"),
    (r"goma|north kivu", "M23"),
    (r"lesotho|maseru", "LES"),
    (r"eswatini|swaziland|mbabane", "SWZ"),
    (r"southern transitional|hadhramaut", "STC"),
    (r"bangladesh|east bengal", "BAN"),
    (r"gaza", "HAM"),
    (r"west bank", "PAL"),
    (r"north kashmir|northern kashmir", "PAK"),
    (r"kashmir", "RAJ"),
    (r"palestine", "PAL"),
    (r"israel|tel aviv|haifa", "ISR"),
    (r"kaliningrad|konigsberg|k[oö]nigsberg|ostpreussen|east prussia", "SOV"),
    (r"sakhalin", "SOV"),
    (r"saipan|guam", "USA"),
    (r"hinterpommern|pomerania|oberschlesien|niederschlesien|upper silesia|lower silesia|danzig|west prussia|posen|kattowitz", "POL"),
    (r"bialystok", "POL"),
    (r"memel", "LIT"),
    (r"sudeten", "CZE"),
    (r"crimea", "SOV"),
    (r"hong kong|macau|macao|tibet|shigatse|ngari|chamdo", "CHI"),
    (r"tannu|tuva", "SOV"),
    (r"dutch.*(new guinea|papua)|west papua", "INS"),
    (r"kaiser wilhelm|new britain|bougainville", "PNG"),
    (r"qataghan|maymanah", "AFG"),
    (r"bahawalpur", "PAK"),
    (r"reunion", "FRA"),
    (r"281-india", "MLD"),
    (r"britmex|belize", "BLZ"),
    (r"guyana", "GYA"),
    (r"jamaica", "JAM"),
    (r"southern bahamas", "ENG"),  # Turks and Caicos — before generic Bahamas
    (r"bahama", "BAH"),
    (r"trinidad", "TRI"),
    (r"windward", "BRB"),
    (r"britain sa|leeward", "ATG"),
    (r"british somaliland", "SML"),
    (r"dobrogea", "BUL"),
    (r"northern dobruja", "ROM"),
    (r"christmas island|cocos", "AST"),
    (r"dutch sa|suriname", "SUR"),
    (r"mauritius", "MAU"),
    (r"comoro", "COM"),
    (r"seychelles", "SEY"),
    (r"sao tome", "STP"),
    (r"palau", "PLU"),
    (r"marshall", "MHL"),
    (r"nauru", "NAU"),
    (r"gilbert|maiana|kiribati", "KIR"),
    (r"fongafale|ellice|tuvalu", "TUV"),
    (r"phoenix|line islands", "KIR"),
    (r"american samoa", "USA"),
    (r"rio de oro|western sahara", "WES"),
    (r"sidi ifni", "MOR"),
    (r"petsamo", "SOV"),
    (r"hatay", "TUR"),
    (r"dutch timor", "INS"),
    (r"southern bessarabia", "UKR"),
    (r"haraghe|hararghe", "ETH"),
    (r"garissa", "KEN"),
    (r"curacao", "HOL"),
    (r"french caribbean|guadeloupe|martinique", "FRA"),
    (r"french sa|cayenne|guyane", "FRA"),
    (r"south georgia", "ENG"),
    (r"kuril", "SOV"),
    (r"khyber", "AFG"),  # Jalalabad / Gardez, not Pakistani Khyber
    (r"carpathian|ruthenia|zakarpattia", "UKR"),
    (r"east azerbaijan|gilan", "PER"),
    (r"cape verde", "CBV"),
    (r"iceland", "ICE"),
    (r"brunei", "BRN"),
    (r"south west africa|namibia|karas|kuneme|kavango", "NMB"),
]

IMPERIAL = {"ENG", "FRA", "JAP", "ITA", "HOL", "BEL", "POR", "SPR", "SOV", "RAJ", "USA", "DEN"}
IMPERIAL_KEEP_KEYWORDS = {
    "ENG": r"britain|england|scotland|wales|london|ulster|gibraltar|falkland|bermuda|cayman|helena|ascension|pitcairn|anguilla|montserrat|channel|orkney|shetland|hebrides",
    "SPR": r"spain|madrid|catalonia|castile|galicia|andalus|canary|balear|basque|aragon|valencia|sevilla|granada|navarre|asturias|leon|extremadura|murcia|cordoba|salamanca|valladolid",
    "FRA": r"france|paris|provence|normandy|burgundy|alsace|lorraine|picardy|brittany|corsica|savoy|reunion|caledonia|tahiti|martinique|guadeloupe|mayotte|pierre|guyane|polynesia",
    "JAP": r"japan|kanto|kansai|kyushu|hokkaido|shikoku|tohoku|chubu|okinawa",
    "ITA": r"italy|piedmont|lombardy|venetia|tuscany|sicily|sardinia|rome|naples|emilia",
    "HOL": r"holland|nether|brabant|friesland|gelder",
    "BEL": r"belgium|flanders|wallon|brussels",
    "POR": r"portugal|lisbon|oporto|azores|madeira",
    "SOV": r"russia|moscow|leningrad|petersburg|siberia|ural|volga|caucasus|novgorod|smolensk|rostov|kursk|tula|orenburg|irkutsk|yakut|kamchatka|murmansk|archangel|perm|omsk|tomsk|krasno|stavropol",
    "RAJ": r"india|delhi|bombay|madras|bengal|punjab|gujarat|rajasthan|hyderabad|mysore|kashmir|assam|orissa|bihar|kerala|lucknow",
    "USA": r"america|washington|california|texas|alaska|hawaii|york|florida|ohio|illinois|virginia|carolina|dakota|oregon|arizona|nevada|colorado|utah|kansas|iowa|wisconsin|minnesota|michigan|georgia|alabama|mississippi|louisiana|tennessee|kentucky|indiana|missouri|oklahoma|arkansas|nebraska|montana|idaho|wyoming|maine|vermont|hampshire|massachusetts|connecticut|jersey|maryland|delaware|rhode|puerto|guam|samoa|wake",
    "DEN": r"denmark|jland|juttland|zealand|copenhagen|greenland|faro",
}

STATE_RE = {
    "id": re.compile(r"\bid\s*=\s*(\d+)"),
    "name": re.compile(r'\bname\s*=\s*"([^"]+)"'),
    "manpower": re.compile(r"\bmanpower\s*=\s*(\d+)"),
    "category": re.compile(r"\bstate_category\s*=\s*(\w+)"),
    "owner": re.compile(r"\bowner\s*=\s*([A-Z]{3})"),
    "core": re.compile(r"\badd_core_of\s*=\s*([A-Z]{3})"),
    "factor": re.compile(r"\bbuildings_max_level_factor\s*=\s*([0-9.]+)"),
    "supplies": re.compile(r"\blocal_supplies\s*=\s*([0-9.]+)"),
}


def read_csv_countries() -> dict[str, dict]:
    out = {}
    with CSV_COUNTRIES.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            tag = (row.get("tag") or "").strip()
            if not tag or tag in out:
                continue
            out[tag] = row
    return out


def parse_tags() -> list[tuple[str, str]]:
    tags = []
    # Never write history for zz_dynamic_countries (D01-D75). Those slots are
    # reserved; giving them country files can lock scenario init.
    for path in [
        VANILLA / "common" / "country_tags" / "00_countries.txt",
        ROOT / "common" / "country_tags" / "doomsday_countries.txt",
    ]:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            m = re.match(r"\s*([A-Z0-9]{3})\s*=\s*\"countries/([^\"]+)\"", line)
            if m:
                tags.append((m.group(1), m.group(2)))
    return tags


def vanilla_capitals() -> dict[str, int]:
    caps = {}
    folder = VANILLA / "history" / "countries"
    if not folder.exists():
        return caps
    for path in folder.glob("*.txt"):
        tag = path.name.split(" ")[0].strip()
        text = path.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"capital\s*=\s*(\d+)", text)
        if m:
            caps[tag] = int(m.group(1))
    return caps


def vanilla_history_names() -> dict[str, str]:
    names = {}
    folder = VANILLA / "history" / "countries"
    if folder.exists():
        for path in folder.glob("*.txt"):
            tag = path.name.split(" ")[0].strip()
            names[tag] = path.name
    names["DPK"] = "DPK - North Korea.txt"
    names["SSD"] = "SSD - South Sudan.txt"
    names["KIR"] = "KIR - Kiribati.txt"
    names["TUV"] = "TUV - Tuvalu.txt"
    names["NAU"] = "NAU - Nauru.txt"
    names["MHL"] = "MHL - Marshall Islands.txt"
    names["MAU"] = "MAU - Mauritius.txt"
    names["COM"] = "COM - Comoros.txt"
    names["STP"] = "STP - Sao Tome.txt"
    names["SEY"] = "SEY - Seychelles.txt"
    names["SML"] = "SML - Somaliland.txt"
    names["NCY"] = "NCY - Northern Cyprus.txt"
    names["HAM"] = "HAM - Hamas.txt"
    names["HEZ"] = "HEZ - Hezbollah.txt"
    names["HOU"] = "HOU - Houthis.txt"
    names["NUG"] = "NUG - Myanmar Spring Revolution.txt"
    names["ATG"] = "ATG - Antigua and Barbuda.txt"
    names["DMA"] = "DMA - Dominica.txt"
    names["STL"] = "STL - Saint Lucia.txt"
    names["SVG"] = "SVG - Saint Vincent.txt"
    names["GND"] = "GND - Grenada.txt"
    names["BRB"] = "BRB - Barbados.txt"
    names["PMR"] = "PMR - Transnistria.txt"
    names["ROJ"] = "ROJ - Rojava.txt"
    names["STC"] = "STC - Southern Transitional Council.txt"
    names["DRZ"] = "DRZ - Suwayda.txt"
    names["SNA"] = "SNA - Syrian National Army.txt"
    names["PNT"] = "PNT - Puntland.txt"
    names["JUB"] = "JUB - Jubaland.txt"
    names["SHB"] = "SHB - Al-Shabaab.txt"
    names["M23"] = "M23 - M23.txt"
    names["SOS"] = "SOS - South Ossetia.txt"
    names["NRF"] = "NRF - National Resistance Front.txt"
    names["LES"] = "LES - Lesotho.txt"
    names["SWZ"] = "SWZ - Eswatini.txt"
    return names


def extract_block(text: str, start: int) -> tuple[str, int]:
    i = text.find("{", start)
    if i < 0:
        return "", start
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i : j + 1], j + 1
    return text[i:], len(text)


def parse_state(path: Path) -> dict:
    return parse_state_text(path.read_text(encoding="utf-8", errors="ignore"), path)


def parse_state_text(text: str, path: Path) -> dict:
    sid = STATE_RE["id"].search(text)
    data = {
        "file": path.name,
        "path": path,
        "raw": text,
        "id": int(sid.group(1)) if sid else 0,
        "loc_name": (STATE_RE["name"].search(text) or type("x", (), {"group": lambda *_: ""})).group(1) if STATE_RE["name"].search(text) else "",
        "manpower": int((STATE_RE["manpower"].search(text) or type("x", (), {"group": lambda *_: "1000"})).group(1)),
        "category": (STATE_RE["category"].search(text) or type("x", (), {"group": lambda *_: "rural"})).group(1),
        "owner": (STATE_RE["owner"].search(text) or type("x", (), {"group": lambda *_: "XXX"})).group(1),
        "cores": STATE_RE["core"].findall(text),
        "factor": (STATE_RE["factor"].search(text) or type("x", (), {"group": lambda *_: "1"})).group(1),
        "supplies": (STATE_RE["supplies"].search(text) or type("x", (), {"group": lambda *_: "0.0"})).group(1),
        "impassable": bool(re.search(r"\bimpassable\s*=\s*yes", text)),
        "resources": "",
        "provinces": "",
        "victory_points": [],
        "province_buildings": [],
        "air_base": 0,
        "naval_in_buildings": False,
    }
    rm = re.search(r"\bresources\s*=", text)
    if rm:
        block, _ = extract_block(text, rm.start())
        data["resources"] = block
    pm = re.search(r"\bprovinces\s*=", text)
    if pm:
        block, _ = extract_block(text, pm.start())
        data["provinces"] = block
    for vp in re.finditer(r"\bvictory_points\s*=", text):
        block, _ = extract_block(text, vp.start())
        data["victory_points"].append(block)
    bm = re.search(r"\bbuildings\s*=", text)
    if bm:
        block, _ = extract_block(text, bm.start())
        inner = block[block.find("{") + 1 : block.rfind("}")]
        # keep province-level subblocks and air/naval flavor
        pos = 0
        while True:
            m = re.search(r"(\d+)\s*=", inner[pos:])
            if not m:
                break
            abs_i = pos + m.start()
            sub, end = extract_block(inner, abs_i)
            data["province_buildings"].append(m.group(1) + " = " + sub)
            pos = end
        am = re.search(r"\bair_base\s*=\s*(\d+)", inner)
        if am:
            data["air_base"] = min(int(am.group(1)), 5)
        if "naval_base" in inner:
            data["naval_in_buildings"] = True
    return data


def add_provinces_to_raw(text: str, extra: list[int]) -> str:
    pm = re.search(r"\bprovinces\s*=", text)
    if not pm:
        return text
    block, end = extract_block(text, pm.start())
    brace = text.find("{", pm.start())
    have = [int(n) for n in re.findall(r"\d+", block)]
    for pid in extra:
        if pid not in have:
            have.append(pid)
    return text[:brace] + "{\n\t\t" + " ".join(str(n) for n in have) + "\n\t}" + text[end:]


def drop_provinces_from_raw(text: str, drop: set[int]) -> str:
    pm = re.search(r"\bprovinces\s*=", text)
    if not pm:
        return text
    block, end = extract_block(text, pm.start())
    brace = text.find("{", pm.start())
    kept = [n for n in re.findall(r"\d+", block) if int(n) not in drop]
    return text[:brace] + "{\n\t\t" + " ".join(kept) + "\n\t}" + text[end:]


def drop_vps_for_provinces(text: str, drop: set[int]) -> str:
    def repl(m: re.Match) -> str:
        nums = [int(n) for n in re.findall(r"\d+", m.group(0))]
        if nums and nums[0] in drop:
            return ""
        return m.group(0)
    return re.sub(r"victory_points\s*=\s*\{[^}]*\}", repl, text)


def drop_province_building_blocks(text: str, drop: set[int]) -> str:
    for pid in drop:
        while True:
            m = re.search(rf"\n[ \t]*{pid}\s*=", text)
            if not m:
                break
            block, end = extract_block(text, m.start())
            if not block:
                break
            text = text[: m.start()] + text[end:]
    return text


# New state IDs after vanilla 1081 must be consecutive with no gaps.
# Coastal new states get naval_base_spawn via tools/patch_doomsday_map.py.
# Occupier must also be at war with the owner (START_WARS) or CreateMapModes hangs.
OCCUPIED_BY = {
    227: "SOV",  # Donetsk / Stalino — Russian-held Jan 2026
    228: "SOV",  # Luhansk — Russian-held Jan 2026
}

SPLIT_NEW_STATES = [
    {
        "id": 1082,
        "file": "1082-Balta.txt",
        "from_id": 834,
        "provinces": [3757],
        "owner": "UKR",
        "cores": ["UKR"],
        "category": "rural",
        "manpower": 73500,
        "vps": [(3757, 2)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1083,
        "file": "1083-Ceuta.txt",
        "from_id": 290,
        "provinces": [9945],
        "owner": "SPR",
        "cores": ["SPR"],
        "category": "enclave",
        "manpower": 83000,
        "vps": [(9945, 3)],
        "buildings": (
            "\t\t\tinfrastructure = 3\n"
            "\t\t\t9945 = { naval_base = 3 }\n"
        ),
    },
    {
        "id": 1084,
        "file": "1084-Mayotte.txt",
        "from_id": 708,
        "provinces": [13414],
        "owner": "FRA",
        "cores": ["FRA"],
        "category": "tiny_island",
        "manpower": 32000,
        "vps": [(13414, 1)],
        "buildings": "\t\t\tinfrastructure = 2\n\t\t\t13414 = { naval_base = 1 }\n",
        "parent_drop": set(),  # Mayotte is a new province; parent keeps 13072
    },
    {
        "id": 1085,
        "file": "1085-Gaza.txt",
        "from_id": 454,
        "provinces": [4088],
        "owner": "HAM",
        "cores": ["HAM", "PAL", "ISR"],
        "category": "enclave",
        "manpower": 220000,
        "vps": [(4088, 2)],
        "buildings": (
            "\t\t\tinfrastructure = 3\n"
            "\t\t\t4088 = { naval_base = 1 }\n"
        ),
    },
    {
        "id": 1086,
        "file": "1086-West Bank.txt",
        "from_id": 454,
        "provinces": [7107],
        "owner": "PAL",
        "cores": ["PAL", "ISR"],
        "category": "rural",
        "manpower": 330000,
        "vps": [(7107, 2)],
        "buildings": "\t\t\tinfrastructure = 3\n",
    },
    {
        "id": 1087,
        "file": "1087-Northern Cyprus.txt",
        "from_id": 183,
        "provinces": [11984],
        "owner": "NCY",
        "cores": ["NCY", "CYP"],
        "category": "enclave",
        "manpower": 120000,
        "vps": [(11984, 5)],
        "buildings": (
            "\t\t\tinfrastructure = 3\n"
            "\t\t\t11984 = { naval_base = 1 }\n"
        ),
    },
    {
        "id": 1088,
        "file": "1088-Golan Heights.txt",
        "from_id": 554,
        "provinces": [1074],
        "owner": "ISR",
        "cores": ["ISR", "SYR"],
        "category": "pastoral",
        "manpower": 50000,
        "vps": [(1074, 1)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1089,
        "file": "1089-South Lebanon.txt",
        "from_id": 553,
        "provinces": [11919],
        "owner": "HEZ",
        "cores": ["HEZ", "LEB"],
        "category": "rural",
        "manpower": 350000,
        "vps": [(11919, 2)],
        "buildings": (
            "\t\t\tinfrastructure = 3\n"
            "\t\t\t11919 = { naval_base = 1 }\n"
        ),
    },
    {
        "id": 1090,
        "file": "1090-US Virgin Islands.txt",
        "from_id": 686,
        "provinces": [4155],
        "owner": "USA",
        "cores": ["USA"],
        "category": "tiny_island",
        "manpower": 110000,
        "vps": [(4155, 1)],
        "buildings": "\t\t\tinfrastructure = 3\n\t\t\t4155 = { naval_base = 1 }\n",
    },
    {
        "id": 1091,
        "file": "1091-Martinique.txt",
        "from_id": 694,
        "provinces": [177],
        "owner": "FRA",
        "cores": ["FRA"],
        "category": "small_island",
        "manpower": 180000,
        "vps": [(177, 2)],
        "buildings": "\t\t\tinfrastructure = 4\n\t\t\t177 = { naval_base = 3 }\n",
    },
    {
        "id": 1092,
        "file": "1092-Saint Martin.txt",
        "from_id": 694,
        "provinces": [13084],
        "owner": "FRA",
        "cores": ["FRA"],
        "category": "tiny_island",
        "manpower": 40000,
        "vps": [(13084, 1)],
        "buildings": "\t\t\tinfrastructure = 3\n\t\t\t13084 = { naval_base = 1 }\n",
    },
    {
        "id": 1093,
        "file": "1093-Dominica.txt",
        "from_id": 308,
        "provinces": [7123],
        "owner": "DMA",
        "cores": ["DMA"],
        "category": "tiny_island",
        "manpower": 12000,
        "vps": [(7123, 1)],
        "buildings": "\t\t\tinfrastructure = 2\n\t\t\t7123 = { naval_base = 1 }\n",
    },
    {
        "id": 1094,
        "file": "1094-Saint Lucia.txt",
        "from_id": 692,
        "provinces": [13009],
        "owner": "STL",
        "cores": ["STL"],
        "category": "tiny_island",
        "manpower": 15000,
        "vps": [(13009, 1)],
        "buildings": "\t\t\tinfrastructure = 3\n\t\t\t13009 = { naval_base = 1 }\n",
    },
    {
        "id": 1095,
        "file": "1095-Saint Vincent.txt",
        "from_id": 692,
        "provinces": [379],
        "owner": "SVG",
        "cores": ["SVG"],
        "category": "tiny_island",
        "manpower": 13000,
        "vps": [(379, 1)],
        "buildings": "\t\t\tinfrastructure = 3\n\t\t\t379 = { naval_base = 1 }\n",
    },
    {
        "id": 1096,
        "file": "1096-Grenada.txt",
        "from_id": 692,
        "provinces": [11106],
        "owner": "GND",
        "cores": ["GND"],
        "category": "tiny_island",
        "manpower": 13000,
        "vps": [(11106, 1)],
        "buildings": "\t\t\tinfrastructure = 3\n\t\t\t11106 = { naval_base = 1 }\n",
    },
    {
        "id": 1097,
        "file": "1097-Melilla.txt",
        "from_id": 290,
        "provinces": [12100],
        "owner": "SPR",
        "cores": ["SPR"],
        "category": "enclave",
        "manpower": 86000,
        "vps": [(12100, 2)],
        "buildings": (
            "\t\t\tinfrastructure = 3\n"
            "\t\t\t12100 = { naval_base = 3 }\n"
        ),
    },
    {
        "id": 1098,
        "file": "1098-Srem.txt",
        "from_id": 109,
        "provinces": [11580],
        "owner": "SER",
        "cores": ["SER"],
        "category": "rural",
        "manpower": 280000,
        "vps": [(11580, 2)],
        "buildings": "\t\t\tinfrastructure = 3\n",
    },
    {
        "id": 1099,
        "file": "1099-Iraqi Kurdistan.txt",
        "from_id": 676,
        "provinces": [3916, 6826, 5014, 10811],
        "owner": "KUR",
        "cores": ["KUR", "IRQ"],
        "category": "town",
        "manpower": 530000,
        "vps": [(3916, 5), (6826, 3), (10811, 2)],
        "buildings": "\t\t\tinfrastructure = 3\n",
    },
    {
        "id": 1100,
        "file": "1100-Rojava.txt",
        "from_id": 680,
        "provinces": [1549, 1578, 1606, 1634, 6883, 901, 2013, 10882, 12316],
        "owner": "ROJ",
        "cores": ["ROJ", "SYR"],
        "category": "rural",
        "manpower": 220000,
        "vps": [(1549, 5), (6883, 3)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1101,
        "file": "1101-South Ossetia.txt",
        "from_id": 231,
        "provinces": [9626],
        "owner": "SOS",
        "cores": ["SOS", "GEO"],
        "category": "enclave",
        "manpower": 56000,
        "vps": [(9626, 2)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1102,
        "file": "1102-Marib.txt",
        "from_id": 293,
        "provinces": [4924],
        "owner": "YEM",
        "cores": ["YEM", "HOU"],
        "category": "rural",
        "manpower": 400000,
        "vps": [(4924, 3)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1103,
        "file": "1103-Suwayda.txt",
        "from_id": 554,
        "provinces": [4486],
        "owner": "DRZ",
        "cores": ["DRZ", "SYR"],
        "category": "rural",
        "manpower": 80000,
        "vps": [(4486, 2)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1104,
        "file": "1104-Peace Spring.txt",
        "from_id": 1100,
        "provinces": [1578, 1634],
        "owner": "SNA",
        "cores": ["SNA", "SYR", "ROJ"],
        "category": "pastoral",
        "manpower": 50000,
        "vps": [(1578, 2)],
        "buildings": "\t\t\tinfrastructure = 1\n",
    },
    {
        "id": 1105,
        "file": "1105-Puntland.txt",
        "from_id": 559,
        "provinces": [1966, 10891, 4909],
        "owner": "PNT",
        "cores": ["PNT", "SOM"],
        "category": "rural",
        "manpower": 190000,
        "vps": [(1966, 2), (10891, 1)],
        "buildings": (
            "\t\t\tinfrastructure = 1\n"
            "\t\t\t1966 = { naval_base = 1 }\n"
        ),
    },
    {
        "id": 1106,
        "file": "1106-Jilib.txt",
        "from_id": 844,
        "provinces": [11014],
        "owner": "SHB",
        "cores": ["SHB", "SOM"],
        "category": "pastoral",
        "manpower": 400000,
        "vps": [(11014, 2)],
        "buildings": "\t\t\tinfrastructure = 1\n",
    },
    {
        "id": 1107,
        "file": "1107-Goma.txt",
        "from_id": 890,
        "provinces": [1181],
        "owner": "M23",
        "cores": ["M23", "COG"],
        "category": "town",
        "manpower": 250000,
        "vps": [(1181, 5)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1108,
        "file": "1108-Nakhchivan.txt",
        "from_id": 230,
        "provinces": [6997],
        "owner": "AZR",
        "cores": ["AZR"],
        "category": "rural",
        "manpower": 150000,
        "vps": [(6997, 2)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1109,
        "file": "1109-Panjshir.txt",
        "from_id": 1005,
        "provinces": [10781],
        "owner": "NRF",
        "cores": ["NRF", "AFG"],
        "category": "enclave",
        "manpower": 140000,
        "vps": [(10781, 2)],
        "buildings": "\t\t\tinfrastructure = 1\n",
    },
    {
        "id": 1110,
        "file": "1110-Lesotho.txt",
        "from_id": 719,
        "provinces": [4556],
        "owner": "LES",
        "cores": ["LES"],
        "category": "town",
        "manpower": 440000,
        "vps": [(4556, 3)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1111,
        "file": "1111-Eswatini.txt",
        "from_id": 719,
        "provinces": [7900],
        "owner": "SWZ",
        "cores": ["SWZ"],
        "category": "town",
        "manpower": 300000,
        "vps": [(7900, 3)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
]

# Move existing provinces onto another leftover state (no new ID).
MOVE_PROVINCES = [
    {"from_id": 198, "to_id": 834, "provinces": [9423]},  # Moldova-border tile west of Rîbnița → Transnistria
    {"from_id": 559, "to_id": 1106, "provinces": [2063]},  # south-central inland → Al-Shabaab
]


# Attacker -> targets. Occupied controllers without a matching war hang CreateMapModes.
START_WARS = {
    "SOV": ["UKR"],
    "ISR": ["HAM", "HEZ"],
    "HOU": ["YEM"],
    "YEM": ["STC"],
    "BRM": ["NUG"],
    "SOM": ["SHB", "JUB"],
    "COG": ["M23"],
    "NRF": ["AFG"],
}

# Overlord tag -> list of (subject, autonomy type, freedom 0-1).
# Written into the overlord country file. Do not also set controller=.
PUPPETS = {
    "DEN": [("GRN", "autonomy_puppet", 0.40)],
    "IRQ": [("KUR", "autonomy_puppet", 0.50)],
}


def _make_split_state_raw(spec: dict) -> str:
    vp = "".join(f"\t\tvictory_points = {{ {p} {v} }}\n" for p, v in spec["vps"])
    cores = "".join(f"\t\tadd_core_of = {c}\n" for c in spec["cores"])
    provs = " ".join(str(p) for p in spec["provinces"])
    return (
        f"state = {{\n"
        f"\tid = {spec['id']}\n"
        f'\tname = "STATE_{spec["id"]}"\n'
        f"\tmanpower = {spec['manpower']}\n"
        f"\tstate_category = {spec['category']}\n"
        f"\thistory = {{\n"
        f"\t\towner = {spec['owner']}\n"
        f"{cores}"
        f"{vp}"
        f"\t\tbuildings = {{\n{spec['buildings']}\t\t}}\n"
        f"\t}}\n"
        f"\tprovinces = {{\n\t\t{provs}\n\t}}\n"
        f"\tlocal_supplies = 0.0\n"
        f"}}\n"
    )


def apply_map_splits(parsed: list[dict]) -> None:
    for stale in (STATES_DIR / "1083-Ceuta Melilla.txt",):
        if stale.exists():
            stale.unlink()
    by_id = {s["id"]: s for s in parsed}
    for spec in SPLIT_NEW_STATES:
        drop = set(spec.get("parent_drop", spec["provinces"]))
        parent = by_id.get(spec["from_id"])
        if parent:
            if drop:
                parent["raw"] = drop_provinces_from_raw(parent["raw"], drop)
                parent["raw"] = drop_vps_for_provinces(parent["raw"], drop)
                parent["raw"] = drop_province_building_blocks(parent["raw"], drop)
            parent["manpower"] = max(1000, parent["manpower"] - spec["manpower"])
        raw = _make_split_state_raw(spec)
        path = STATES_DIR / spec["file"]
        parsed.append(parse_state_text(raw, path))
        by_id[spec["id"]] = parsed[-1]
    by_id = {s["id"]: s for s in parsed}
    for spec in MOVE_PROVINCES:
        move = spec["provinces"]
        src = by_id.get(spec["from_id"])
        dst = by_id.get(spec["to_id"])
        if src:
            src["raw"] = drop_provinces_from_raw(src["raw"], set(move))
            src["raw"] = drop_vps_for_provinces(src["raw"], set(move))
            src["raw"] = drop_province_building_blocks(src["raw"], set(move))
        if dst:
            dst["raw"] = add_provinces_to_raw(dst["raw"], move)


def pick_owner(state: dict) -> str:
    sid = state["id"]
    # Hard 2026 overrides win over misleading vanilla filenames
    # (784 is "Ermland-Masuren.txt" but loc is Vilnius; 336 is "Singapore.txt" but loc is Kuala Lumpur).
    HARD = {
        5: "POL",      # Warmia–Masuria (Allenstein); Kaliningrad is 763
        85: "POL",     # Danzig
        63: "POL",
        66: "POL",
        67: "POL",
        68: "POL",
        97: "POL",     # Białystok
        188: "LIT",    # Klaipėda / Memel
        763: "SOV",    # Königsberg / Kaliningrad
        784: "LIT",    # Vilnius
        73: "UKR",     # Zakarpattia (Carpathian Ruthenia)
        524: "FOR",    # Taiwan island
        957: "ARG",    # Argentine Formosa
        336: "MAL",    # Kuala Lumpur
        1021: "SNG",   # Actual Singapore
        525: "KOR",
        1029: "KOR",
        1030: "KOR",
        1031: "KOR",
        527: "DPK",
        1028: "DPK",   # Hamgyong
        608: "CHI",
        322: "CHI",    # Tibet
        757: "CHI",    # Shigatse
        758: "CHI",    # Ngari
        219: "SOV",
        193: "UKR",
        202: "UKR",
        669: "INS",    # West Papua
        1057: "INS",   # Dutch southern New Guinea
        523: "PNG",
        737: "PNG",
        979: "PNG",
        1070: "PNG",
        1073: "PNG",
        1005: "AFG",   # Qataghan leftover (Kunduz / Baghlan)
        1007: "AFG",   # Maymanah
        1006: "AFG",   # Jalalabad / Gardez (Afghan side of the Durand Line)
        989: "PAK",    # Bahawalpur
        419: "PER",    # Iranian West Azerbaijan
        420: "PER",    # Gilan
        1000: "PER",   # Iranian East Azerbaijan (Tabriz)
        229: "AZR",    # Republic of Azerbaijan (includes Karabakh after 2023)
        230: "ARM",    # Armenia proper
        555: "SOV",    # Kuril Islands
        310: "FRA",    # French Guiana / Cayenne
        694: "FRA",    # Guadeloupe
        1091: "FRA",   # Martinique
        1092: "FRA",   # Saint Martin / Saint Barthélemy
        641: "FRA",    # French Polynesia
        695: "HOL",    # Curaçao / Aruba / Bonaire (Kingdom of the Netherlands)
        690: "BAH",    # Bahamas
        693: "ENG",    # Turks and Caicos
        308: "ATG",    # Antigua and Barbuda (St Kitts/Montserrat lumped — one province)
        1093: "DMA",   # Dominica
        692: "BRB",    # Barbados
        1094: "STL",   # Saint Lucia
        1095: "SVG",   # Saint Vincent
        1096: "GND",   # Grenada
        686: "USA",    # Puerto Rico
        1090: "USA",   # US Virgin Islands
        720: "ENG",    # South Georgia
        706: "FRA",    # Réunion
        635: "FRA",    # New Caledonia
        884: "SSD",
        885: "SSD",
        430: "BAN",
        1023: "BRN",
        541: "NMB",
        893: "NMB",
        894: "NMB",
        895: "NMB",
        137: "SOV",    # Crimea — Russian control January 2026
        196: "UKR",    # Kherson
        766: "UKR",    # Budjak / Southern Bessarabia
        834: "PMR",    # Transnistria (Tiraspol + north)
        1082: "UKR",   # Balta
        826: "ABK",    # Abkhazia
        1101: "SOS",   # South Ossetia
        1108: "AZR",   # Nakhchivan
        1109: "NRF",   # Panjshir
        1110: "LES",   # Lesotho
        1111: "SWZ",   # Eswatini
        231: "GEO",    # Georgia proper
        101: "GRN",    # Greenland — Kingdom of Denmark puppet
        78: "MOL",
        699: "WES",    # Western Sahara / Rio de Oro
        783: "MOR",    # Sidi Ifni (Morocco proper)
        77: "BUL",     # Southern Dobruja (Dobrich) — Bulgarian since 1940
        971: "ROM",    # Northern Dobruja (Constanța)
        290: "MOR",    # Rif / Tétouan
        1083: "SPR",   # Ceuta
        1097: "SPR",   # Melilla
        835: "ETH",    # Hararghe / Ogaden
        836: "ETH",    # Bale
        903: "KEN",    # Garissa
        269: "SML",    # Somaliland (Hargeisa / Berbera)
        559: "SOM",    # Mogadishu / remaining Somalia
        844: "JUB",    # Jubaland (Kismayo)
        1105: "PNT",   # Puntland (Bosaso horn)
        1106: "SHB",   # Al-Shabaab (Jilib + south-central)
        722: "SOV",    # Petsamo / Pechenga
        146: "SOV",    # Karjala / Karelian Isthmus (Vyborg) — Russian since 1944
        147: "SOV",    # Salla — ceded strip, Russian since 1944
        799: "TUR",    # Hatay
        1054: "INS",   # West Timor
        647: "PLU",    # Palau
        633: "MHL",    # Marshall Islands
        684: "FSM",    # Caroline Islands / Micronesia
        639: "KIR",    # Gilbert Islands
        642: "KIR",    # Phoenix Islands
        727: "KIR",    # Line Islands
        643: "TUV",    # Tuvalu / Ellice
        725: "NAU",    # Nauru
        1072: "USA",   # American Samoa
        726: "SAM",    # Independent Samoa
        707: "MAU",    # Mauritius
        708: "COM",    # Comoros
        1084: "FRA",   # Mayotte
        454: "ISR",    # Israel proper (Jerusalem, Tel Aviv, Negev)
        1085: "HAM",   # Gaza — Hamas
        1086: "PAL",   # West Bank — PA
        1087: "NCY",   # Northern Cyprus
        183: "CYP",    # Republic of Cyprus
        1088: "ISR",   # Golan Heights
        1089: "HEZ",   # South Lebanon — Hezbollah
        293: "HOU",    # Houthi-held North Yemen / Sana'a
        1102: "YEM",   # Marib — PLC leftover on 1 Jan 2026
        992: "STC",    # Aden — STC peak
        659: "STC",    # Hadhramaut — STC December drive
        906: "STC",    # Socotra
        997: "NUG",    # Rakhine — Arakan Army / Spring Revolution
        998: "NUG",    # Sagaing
        999: "NUG",    # Shan
        993: "NUG",    # Eastern Shan / Kentung
        288: "BRM",    # Magwe — junta
        640: "BRM",    # Mandalay
        995: "BRM",    # Yangon / Pegu
        996: "BRM",    # Irrawaddy
        994: "BRM",    # Tenasserim
        441: "RAJ",    # Indian-administered Jammu and Kashmir
        787: "PAK",    # Gilgit-Baltistan / Azad Kashmir
        109: "CRO",
        103: "CRO",
        107: "SER",
        45: "SER",
        1098: "SER",  # Srem — Novi Sad–Belgrade corridor (Fruška Gora)
        676: "IRQ",   # Mosul / Kirkuk — federal Iraq
        1099: "KUR",  # Iraqi Kurdistan (Erbil, Duhok, Sulaymaniyah)
        350: "TUR",   # Diyarbakır — not KRG
        352: "TUR",   # Hakkari
        353: "TUR",   # Erzurum
        800: "TUR",   # Van
        680: "SYR",   # Deir ez-Zor city and southern desert
        1100: "ROJ",  # Rojava / AANES leftover after Peace Spring
        1103: "DRZ",  # Suwayda National Guard
        1104: "SNA",  # Peace Spring (Tell Abyad / Ras al-Ayn)
        1107: "M23",  # Goma / M23 Kivu
        890: "COG",   # Kalemie leftover after Goma split
        705: "STP",    # São Tomé and Príncipe
        709: "SEY",    # Seychelles
        636: "FIJ",
    }
    if sid in HARD:
        return HARD[sid]

    fname = state["file"].lower()
    for pat, tag in FILENAME_OWNER:
        if re.search(pat, fname):
            return tag

    owner = state["owner"]
    if owner in BANNED_REMAP:
        return BANNED_REMAP[owner]

    cores = [c for c in state["cores"] if c in SOVEREIGN and c not in BANNED_OWNERS]
    if cores:
        for pref in CORE_PRIORITY:
            if pref in cores:
                return pref
        return cores[0]

    owner = state["owner"]
    if owner in SOVEREIGN and owner not in BANNED_OWNERS:
        if owner in IMPERIAL:
            keep = IMPERIAL_KEEP_KEYWORDS.get(owner)
            if keep and re.search(keep, fname):
                return owner
            # leftover colony with no useful core: try keyword map below
        else:
            return owner

    KEYWORDS = [
        (r"ukraine|kiev|kyiv|odessa|khark|donetsk|lviv|dnipro|zaporiz|vinnyts|poltava|chernig|sumy|kherson|mykola", "UKR"),
        (r"belarus|minsk|gomel|brest|vitebsk|mogilev", "BLR"),
        (r"estonia|tallinn", "EST"),
        (r"latvia|riga", "LAT"),
        (r"lithuania|vilnius|kaunas|aukstait", "LIT"),
        (r"moldova|bessarabia|chisinau", "MOL"),
        (r"tbilisi|(?<!south )georgia", "GEO"),
        (r"armenia|yerevan", "ARM"),
        (r"baku|(?<!east )azerbaijan", "AZR"),
        (r"kazakh|almaty|astana|pavlodar", "KAZ"),
        (r"uzbek|tashkent", "UZB"),
        (r"turkmen|ashgabat", "TMS"),
        (r"kyrgyz|bishkek", "KYR"),
        (r"tajik|dushanbe", "TAJ"),
        (r"pakistan|karachi|lahore|sind|baluch|baloch|peshawar", "PAK"),
        (r"bangladesh|east bengal|dhaka", "BAN"),
        (r"burma|myanmar|rangoon", "BRM"),
        (r"vietnam|tonkin|annam|cochin", "VIN"),
        (r"cambodia|phnom", "CAM"),
        (r"laos|vientiane", "LAO"),
        (r"indonesia|java|sumatra|borneo|celebes|sulawesi", "INS"),
        (r"malaysia|malaya|sarawak|sabah", "MAL"),
        (r"philippin|luzon|mindanao|palawan", "PHI"),
        (r"algeria", "ALG"),
        (r"morocco|casablanca|rif", "MOR"),
        (r"tunisia", "TUN"),
        (r"libya|tripoli|cyrenaica", "LBA"),
        (r"egypt|cairo|alexandria", "EGY"),
        (r"sudan|khartoum", "SUD"),
        (r"kenya", "KEN"),
        (r"uganda", "UGA"),
        (r"tanzania|tanganyika", "TZN"),
        (r"nigeria|lagos", "NGA"),
        (r"congo", "COG"),
        (r"angola", "ANG"),
        (r"mozambique", "MZB"),
        (r"madagascar", "MAD"),
        (r"ivory|cote", "IVO"),
        (r"ghana|gold coast", "GHA"),
        (r"senegal", "SEN"),
        (r"cameroon", "CMR"),
        (r"ethiopia", "ETH"),
        (r"libya", "LBA"),
        (r"syria", "SYR"),
        (r"lebanon", "LEB"),
        (r"jordan|transjordan", "JOR"),
        (r"iraq|baghdad|mosul", "IRQ"),
        (r"manchu|mukden|beijing|nanjing|guangdong|sichuan|yunnan|xinjiang|qinghai|shanxi|shandong|hebei|hunan|hubei|fujian|zhejiang|jiangsu|anhui|jiangxi|guizhou|guangxi|gansu", "CHI"),
        (r"korea", "KOR"),
        (r"slovak", "SLO"),
        (r"czech|bohemia|moravia", "CZE"),
        (r"croatia", "CRO"),
        (r"slovenia", "SLV"),
        (r"bosnia|herzegovina", "BOS"),
        (r"macedonia", "MAC"),
        (r"montenegro", "MNT"),
        (r"kosovo", "KOS"),
        (r"serbia|belgrade", "SER"),
        (r"canada|ontario|quebec|alberta|saskatchewan|manitoba|yukon|nunavut|brunswick|scotia|columbia", "CAN"),
        (r"australia|queensland|nsw|victoria|tasmania", "AST"),
        (r"new zealand", "NZL"),
    ]
    for pat, tag in KEYWORDS:
        if re.search(pat, fname):
            return tag

    if owner in SOVEREIGN and owner not in BANNED_OWNERS:
        return owner
    if cores:
        return cores[0]
    if owner in BANNED_REMAP:
        return BANNED_REMAP[owner]
    return owner if owner not in BANNED_OWNERS else "CHI"


def factories_for(row: dict) -> tuple[int, int, int, int]:
    mva = float(row.get("mva_b") or 0)
    sipri = float(row.get("sipri_b") or 0)
    wartime = str(row.get("wartime") or "0").strip() in {"1", "yes", "true"}
    docks = int(float(row.get("docks") or 0))
    infra = max(1, min(5, int(float(row.get("infra") or 2))))
    civs = 0
    if mva >= CIV_MIN_MVA_B:
        civs = max(1, int(round(mva / CIV_PER_MVA_B)))
    elif mva >= 0.5:
        civs = 1
    mils = int(round(sipri * MIL_PROCUREMENT_SHARE / MIL_PER_PROC_B))
    if wartime:
        mils = max(mils, int(round(mils * WARTIME_MIL_MULT))) if mils else int(round(sipri * MIL_PROCUREMENT_SHARE * WARTIME_MIL_MULT / MIL_PER_PROC_B))
    mils = max(0, mils)
    return civs, mils, docks, infra


def cap_distribute(total: int, weights: list[int], cap: int) -> list[int]:
    out = distribute(total, weights)
    leftover = 0
    for i, n in enumerate(out):
        if n > cap:
            leftover += n - cap
            out[i] = cap
    if leftover and out:
        order = sorted(range(len(out)), key=lambda i: weights[i], reverse=True)
        changed = True
        while leftover and changed:
            changed = False
            for i in order:
                if leftover <= 0:
                    break
                if out[i] < cap:
                    out[i] += 1
                    leftover -= 1
                    changed = True
    return out


def distribute(total: int, weights: list[int]) -> list[int]:
    if total <= 0 or not weights:
        return [0] * len(weights)
    s = sum(weights) or len(weights)
    raw = [total * w / s for w in weights]
    out = [int(x) for x in raw]
    rem = total - sum(out)
    order = sorted(range(len(raw)), key=lambda i: raw[i] - out[i], reverse=True)
    for i in order:
        if rem <= 0:
            break
        out[i] += 1
        rem -= 1
    return out


def strip_dated_history(text: str) -> str:
    """Remove 1939.1.1 = { ... } style blocks so they do not apply in 2026."""
    pattern = re.compile(r"^\s*\d{4}\.\d{1,2}\.\d{1,2}\s*=", re.M)
    while True:
        m = pattern.search(text)
        if not m:
            return text
        block, end = extract_block(text, m.start())
        if not block:
            return text
        text = text[: m.start()] + text[end:]


def write_state(state: dict, owner: str, manpower: int, civs: int, mils: int, docks: int, infra: int):
    text = state["raw"]
    text = strip_dated_history(text)
    text = re.sub(r"\bowner\s*=\s*[A-Z]{3}", f"owner = {owner}", text, count=1)
    occupier = OCCUPIED_BY.get(state["id"])
    if occupier:
        if re.search(r"\bcontroller\s*=", text):
            text = re.sub(r"\bcontroller\s*=\s*[A-Z]{3}", f"controller = {occupier}", text, count=1)
        else:
            text = re.sub(r"(\bowner\s*=\s*[A-Z]{3})", rf"\1\n\t\tcontroller = {occupier}", text, count=1)
    else:
        # Vanilla leftover controller=TAG after an owner rewrite is illegal occupation
        # (no war) and hangs InitGameState while CreateMapModes paints political/occupation.
        text = re.sub(r"\n[ \t]*controller\s*=\s*[A-Z0-9\-]+\s*", "\n", text)
    text = re.sub(r"\bmanpower\s*=\s*\d+", f"manpower = {max(1000, manpower)}", text, count=1)
    text = re.sub(r"\s*set_demilitarized_zone\s*=\s*yes", "", text)
    if not re.search(rf"\badd_core_of\s*=\s*{owner}\b", text):
        text = re.sub(r"(\bowner\s*=\s*[A-Z]{3})", rf"\1\n\t\tadd_core_of = {owner}", text, count=1)
    cat_slots = {
        "megalopolis": 12, "metropolis": 10, "large_city": 8, "city": 6,
        "large_town": 5, "town": 4, "large_island": 3, "rural": 2,
        "small_island": 1, "pastoral": 1, "wasteland": 0, "tiny_island": 0, "enclave": 0,
    }.get(state.get("category") or "rural", 2)
    extra_cap = max(0, SHARED_SLOTS_CAP - cat_slots)
    slots = min(civs + mils + docks + 4, extra_cap)
    if "add_extra_state_shared_building_slots" not in text:
        text = re.sub(
            r"(\bowner\s*=\s*[A-Z]{3})",
            rf"\1\n\t\tadd_extra_state_shared_building_slots = {slots}",
            text,
            count=1,
        )

    def replace_or_insert(block: str, key: str, value: int) -> str:
        if re.search(rf"\b{key}\s*=", block):
            return re.sub(rf"\b{key}\s*=\s*\d+", f"{key} = {value}", block, count=1)
        insert = f"\n\t\t\t{key} = {value}"
        return re.sub(r"\{", "{" + insert, block, count=1)

    bm = re.search(r"\bbuildings\s*=", text)
    if bm:
        block, end = extract_block(text, bm.start())
        new_block = block
        new_block = replace_or_insert(new_block, "infrastructure", infra)
        new_block = replace_or_insert(new_block, "industrial_complex", civs)
        new_block = replace_or_insert(new_block, "arms_factory", mils)
        if docks:
            new_block = replace_or_insert(new_block, "dockyard", docks)
        elif re.search(r"\bdockyard\s*=", new_block):
            new_block = re.sub(r"\n\t+\bdockyard\s*=\s*\d+[^\n]*", "", new_block, count=1)
        text = text[: bm.start()] + f"buildings = {new_block}" + text[end:]
    state["path"].write_text(text, encoding="utf-8")


TECH_BLOCK = """set_technology = {
	infantry_weapons = 1
	infantry_weapons1 = 1
	tech_support = 1
	tech_engineers = 1
	tech_recon = 1
	gw_artillery = 1
	tech_trucks = 1
	motorised_infantry = 1
	electronic_mechanical_engineering = 1
	radio = 1
	mechanical_computing = 1
	basic_machine_tools = 1
	construction1 = 1
	fuel_silos = 1
}
"""


def write_country(tag: str, filename: str, row: dict | None, capital: int, faction_members: dict[str, list[str]]):
    name = (row or {}).get("name") or tag
    ideology = (row or {}).get("ideology") or "neutrality"
    sub = (row or {}).get("subideology") or ("oligarchism" if ideology == "neutrality" else "conservatism" if ideology == "democratic" else "marxism" if ideology == "communism" else "fascism_ideology")
    dem = int(float((row or {}).get("dem") or 25))
    com = int(float((row or {}).get("com") or 15))
    fas = int(float((row or {}).get("fas") or 10))
    neu = int(float((row or {}).get("neu") or 50))
    total = dem + com + fas + neu
    if total != 100 and total > 0:
        neu = max(0, 100 - dem - com - fas)
    leader = (row or {}).get("leader") or f"{name} Government"
    elections = str((row or {}).get("elections") or "no").lower() in {"yes", "1", "true"}
    pop = float((row or {}).get("pop") or 0)
    gdp = (row or {}).get("gdp_b") or "0"
    debt = (row or {}).get("debt_gdp") or "0"
    faction = (row or {}).get("faction") or ""
    convoys = 50 if pop > 5_000_000 else 10
    slots = 4 if tag in {"USA", "CHI", "SOV", "RAJ", "ENG", "FRA", "GER", "JAP"} else 3
    stab = 0.55 if ideology == "democratic" else 0.45
    ws = 0.25 if str((row or {}).get("wartime") or "0") in {"1", "yes"} else 0.10

    lines = [
        f"# {name} - Doomsday 2026 skeleton",
        f"capital = {capital}",
        "oob = \"DOOMSDAY_EMPTY\"",
        f"set_research_slots = {slots}",
        f"set_stability = {stab}",
        f"set_war_support = {ws}",
        f"set_convoys = {convoys}",
        TECH_BLOCK,
        "set_politics = {",
        f"	ruling_party = {intology(ideology)}",
        '	last_election = "2024.1.1"',
        "	election_frequency = 48",
        f"	elections_allowed = {'yes' if elections else 'no'}",
        "}",
        "set_popularities = {",
        f"	democratic = {dem}",
        f"	communism = {com}",
        f"	fascism = {fas}",
        f"	neutrality = {neu}",
        "}",
        f"set_variable = {{ gdp = {gdp} }}",
        f"set_variable = {{ debt_to_gdp = {debt} }}",
        "create_country_leader = {",
        f'	name = "{leader}"',
        f"	desc = {tag}_LEADER_DESC",
        "	picture = GFX_portrait_unknown",
        f"	ideology = {sub}",
        "	traits = { }",
        "}",
    ]
    if tag == "USA" and "NATO" in faction_members:
        lines.append("create_faction = NATO")
        for member in faction_members["NATO"]:
            if member != "USA":
                lines.append(f"add_to_faction = {member}")
    elif tag == "SOV" and "CSTO" in faction_members:
        lines.append("create_faction = CSTO")
        for member in faction_members["CSTO"]:
            if member != "SOV":
                lines.append(f"add_to_faction = {member}")
    for target in START_WARS.get(tag, []):
        lines.append("declare_war_on = {")
        lines.append(f"	target = {target}")
        lines.append("	type = annex_everything")
        lines.append("}")
    for subject, autonomy, freedom in PUPPETS.get(tag, []):
        lines.append("set_autonomy = {")
        lines.append(f"	target = {subject}")
        lines.append(f"	autonomous_state = {autonomy}")
        lines.append(f"	freedom_level = {freedom}")
        lines.append("}")
    COUNTRIES_DIR.mkdir(parents=True, exist_ok=True)
    (COUNTRIES_DIR / filename).write_text("\n".join(lines) + "\n", encoding="utf-8")


def intology(ideology: str) -> str:
    return ideology if ideology in {"democratic", "communism", "fascism", "neutrality"} else "neutrality"


def write_loc(countries: dict[str, dict], tags: list[tuple[str, str]]):
    LOC_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "l_english:",
        ' DOOMSDAY_NAME:0 "Doomsday"',
        ' DOOMSDAY_DESC:0 "The world of January 2026. Industry sits where factories actually are. The old wartime coalitions are gone."',
        ' USA_DOOMSDAY_DESC:0 "The United States remains the preeminent military power, even as its manufacturing base has thinned."',
        ' CHI_DOOMSDAY_DESC:0 "The People\'s Republic of China is the workshop of the world."',
        ' SOV_DOOMSDAY_DESC:0 "The Russian Federation is a mobilized petrostate at war."',
        ' RAJ_DOOMSDAY_DESC:0 "India is a crowded democracy with a growing industrial core."',
        ' ENG_DOOMSDAY_DESC:0 "The United Kingdom is wealthy, nuclear-armed, and deindustrialized."',
        ' FRA_DOOMSDAY_DESC:0 "France remains a nuclear power whose factories no longer match its diplomacy."',
        ' GER_DOOMSDAY_DESC:0 "Germany is Europe\'s remaining industrial heavyweight."',
        ' JAP_DOOMSDAY_DESC:0 "Japan is a high-tech workshop with a constrained military."',
        ' OTHER_DOOMSDAY_DESC:0 "Every other government on the 2026 map."',
        ' NATO:0 "NATO"',
        ' CSTO:0 "CSTO"',
        ' SOV:0 "Russia"',
        ' SOV_DEF:0 "Russia"',
        ' SOV_ADJ:0 "Russian"',
        ' RAJ:0 "India"',
        ' RAJ_DEF:0 "India"',
        ' RAJ_ADJ:0 "Indian"',
        ' CHI:0 "China"',
        ' CHI_DEF:0 "China"',
        ' CHI_ADJ:0 "Chinese"',
        ' PER:0 "Iran"',
        ' PER_DEF:0 "Iran"',
        ' PER_ADJ:0 "Iranian"',
        ' SIA:0 "Thailand"',
        ' HOL:0 "Netherlands"',
        ' HOL_DEF:0 "the Netherlands"',
        ' DPK:0 "North Korea"',
        ' DPK_DEF:0 "North Korea"',
        ' DPK_ADJ:0 "North Korean"',
        ' SSD:0 "South Sudan"',
        ' SSD_DEF:0 "South Sudan"',
        ' SSD_ADJ:0 "South Sudanese"',
        ' FOR:0 "Taiwan"',
        ' FOR_DEF:0 "Taiwan"',
        ' FOR_ADJ:0 "Taiwanese"',
        ' KOR:0 "South Korea"',
        ' KOR_DEF:0 "South Korea"',
        ' KOR_ADJ:0 "South Korean"',
        ' KIR:0 "Kiribati"',
        ' TUV:0 "Tuvalu"',
        ' NAU:0 "Nauru"',
        ' MHL:0 "Marshall Islands"',
        ' MAU:0 "Mauritius"',
        ' COM:0 "Comoros"',
        ' STP:0 "Sao Tome and Principe"',
        ' SEY:0 "Seychelles"',
        ' WES:0 "Western Sahara"',
        ' WES_DEF:0 "Western Sahara"',
        ' WES_ADJ:0 "Sahrawi"',
        ' SML:0 "Somaliland"',
        ' SML_DEF:0 "Somaliland"',
        ' SML_ADJ:0 "Somalilander"',
        ' NCY:0 "Northern Cyprus"',
        ' NCY_DEF:0 "Northern Cyprus"',
        ' NCY_ADJ:0 "Northern Cypriot"',
        ' HAM:0 "Hamas"',
        ' HAM_DEF:0 "Hamas"',
        ' HAM_ADJ:0 "Hamas"',
        ' HEZ:0 "Hezbollah"',
        ' HEZ_DEF:0 "Hezbollah"',
        ' HEZ_ADJ:0 "Hezbollah"',
        ' HOU:0 "Houthis"',
        ' HOU_DEF:0 "the Houthis"',
        ' HOU_ADJ:0 "Houthi"',
        ' NUG:0 "Myanmar Spring Revolution"',
        ' NUG_DEF:0 "the Spring Revolution"',
        ' NUG_ADJ:0 "Spring Revolution"',
        ' ATG:0 "Antigua and Barbuda"',
        ' DMA:0 "Dominica"',
        ' STL:0 "Saint Lucia"',
        ' SVG:0 "Saint Vincent and the Grenadines"',
        ' GND:0 "Grenada"',
        ' BRB:0 "Barbados"',
        ' PMR:0 "Transnistria"',
        ' PMR_DEF:0 "Transnistria"',
        ' PMR_ADJ:0 "Transnistrian"',
        ' GRN:0 "Greenland"',
        ' GRN_DEF:0 "Greenland"',
        ' GRN_ADJ:0 "Greenlandic"',
        ' KUR:0 "Kurdistan Region"',
        ' KUR_DEF:0 "the Kurdistan Region"',
        ' KUR_ADJ:0 "Kurdish"',
        ' ROJ:0 "Rojava"',
        ' ROJ_DEF:0 "Rojava"',
        ' ROJ_ADJ:0 "Rojavan"',
        ' STC:0 "Southern Transitional Council"',
        ' STC_DEF:0 "the Southern Transitional Council"',
        ' STC_ADJ:0 "Southern"',
        ' DRZ:0 "Suwayda"',
        ' DRZ_DEF:0 "Suwayda"',
        ' DRZ_ADJ:0 "Suwaydan"',
        ' SNA:0 "Syrian National Army"',
        ' SNA_DEF:0 "the Syrian National Army"',
        ' SNA_ADJ:0 "SNA"',
        ' PNT:0 "Puntland"',
        ' PNT_DEF:0 "Puntland"',
        ' PNT_ADJ:0 "Puntland"',
        ' JUB:0 "Jubaland"',
        ' JUB_DEF:0 "Jubaland"',
        ' JUB_ADJ:0 "Jubaland"',
        ' SHB:0 "Al-Shabaab"',
        ' SHB_DEF:0 "Al-Shabaab"',
        ' SHB_ADJ:0 "Al-Shabaab"',
        ' M23:0 "M23"',
        ' M23_DEF:0 "M23"',
        ' M23_ADJ:0 "M23"',
        ' ABK:0 "Abkhazia"',
        ' ABK_DEF:0 "Abkhazia"',
        ' ABK_ADJ:0 "Abkhaz"',
        ' SOS:0 "South Ossetia"',
        ' SOS_DEF:0 "South Ossetia"',
        ' SOS_ADJ:0 "South Ossetian"',
        ' CZE:0 "Czechia"',
        ' CZE_DEF:0 "Czechia"',
        ' CZE_ADJ:0 "Czech"',
        ' STATE_430:0 "Bangladesh"',
        ' STATE_454:0 "Israel"',
        ' STATE_834:0 "Transnistria"',
        ' STATE_1082:0 "Balta"',
        ' STATE_146:0 "Karelian Isthmus"',
        ' STATE_147:0 "Salla"',
        ' STATE_1083:0 "Ceuta"',
        ' STATE_1097:0 "Melilla"',
        ' STATE_1098:0 "Srem"',
        ' VICTORY_POINTS_11580:0 "Sremski Karlovci"',
        ' STATE_1099:0 "Iraqi Kurdistan"',
        ' STATE_1100:0 "Northeast Syria"',
        ' STATE_826:0 "Abkhazia"',
        ' STATE_1101:0 "South Ossetia"',
        ' VICTORY_POINTS_9626:0 "Tskhinvali"',
        ' STATE_1108:0 "Nakhchivan"',
        ' VICTORY_POINTS_6997:0 "Nakhchivan"',
        ' NRF:0 "National Resistance Front"',
        ' NRF_DEF:0 "the National Resistance Front"',
        ' NRF_ADJ:0 "NRF"',
        ' STATE_1109:0 "Panjshir"',
        ' VICTORY_POINTS_10781:0 "Bazarak"',
        ' LES:0 "Lesotho"',
        ' LES_DEF:0 "Lesotho"',
        ' LES_ADJ:0 "Basotho"',
        ' SWZ:0 "Eswatini"',
        ' SWZ_DEF:0 "Eswatini"',
        ' SWZ_ADJ:0 "Swazi"',
        ' STATE_1110:0 "Lesotho"',
        ' STATE_1111:0 "Eswatini"',
        ' VICTORY_POINTS_4556:0 "Maseru"',
        ' VICTORY_POINTS_7900:0 "Mbabane"',
        ' STATE_676:0 "Mosul"',
        ' STATE_680:0 "Deir ez-Zor"',
        ' STATE_1084:0 "Mayotte"',
        ' STATE_1085:0 "Gaza"',
        ' STATE_1086:0 "West Bank"',
        ' STATE_1087:0 "Northern Cyprus"',
        ' STATE_1088:0 "Golan Heights"',
        ' STATE_1089:0 "South Lebanon"',
        ' STATE_1090:0 "US Virgin Islands"',
        ' STATE_1091:0 "Martinique"',
        ' STATE_1092:0 "Saint Martin"',
        ' STATE_308:0 "Antigua and Barbuda"',
        ' STATE_1093:0 "Dominica"',
        ' STATE_692:0 "Barbados"',
        ' STATE_1094:0 "Saint Lucia"',
        ' STATE_1095:0 "Saint Vincent"',
        ' STATE_1096:0 "Grenada"',
        ' STATE_694:0 "Guadeloupe"',
        ' VICTORY_POINTS_4155:0 "Charlotte Amalie"',
        ' VICTORY_POINTS_177:0 "Fort-de-France"',
        ' VICTORY_POINTS_13084:0 "Marigot"',
        ' VICTORY_POINTS_7123:0 "Roseau"',
        ' VICTORY_POINTS_4450:0 "Saint John\'s"',
        ' VICTORY_POINTS_13009:0 "Castries"',
        ' VICTORY_POINTS_379:0 "Kingstown"',
        ' VICTORY_POINTS_11106:0 "Saint George\'s"',
        ' STATE_441:0 "Jammu and Kashmir"',
        ' STATE_787:0 "Gilgit-Baltistan"',
        ' STATE_1006:0 "Nangarhar"',
        ' STATE_293:0 "North Yemen"',
        ' STATE_1102:0 "Marib"',
        ' STATE_992:0 "Aden"',
        ' STATE_659:0 "Hadhramaut"',
        ' STATE_1103:0 "Suwayda"',
        ' STATE_1104:0 "Peace Spring"',
        ' STATE_1105:0 "Puntland"',
        ' STATE_844:0 "Jubaland"',
        ' STATE_1106:0 "Jilib"',
        ' STATE_1107:0 "Goma"',
        ' STATE_890:0 "Kalemie"',
        ' VICTORY_POINTS_4924:0 "Marib"',
        ' VICTORY_POINTS_1578:0 "Ras al-Ayn"',
        ' VICTORY_POINTS_1966:0 "Bosaso"',
        ' VICTORY_POINTS_10891:0 "Qardho"',
        ' VICTORY_POINTS_11014:0 "Jilib"',
        ' VICTORY_POINTS_1181:0 "Goma"',
        ' VICTORY_POINTS_1074:0 "Quneitra"',
        ' VICTORY_POINTS_11919:0 "Tyre"',
        ' STATE_77:0 "Dobrudja"',
        ' STATE_269:0 "Somaliland"',
        ' STATE_559:0 "Somalia"',
        ' STATE_699:0 "Western Sahara"',
        ' STATE_693:0 "Turks and Caicos"',
        ' STATE_311:0 "Belize"',
        ' VICTORY_POINTS_4088:0 "Gaza"',
        ' VICTORY_POINTS_7107:0 "Ramallah"',
        ' VICTORY_POINTS_13414:0 "Mamoudzou"',
    ]
    for tag, row in countries.items():
        leader = row.get("leader") or tag
        country = row.get("name") or tag
        lines.append(f' {tag}_LEADER_DESC:0 "{leader} leads {country} in 2026."')
        if tag not in {"SOV", "RAJ", "CHI", "PER", "SIA", "HOL", "DPK", "SSD", "FOR", "KOR", "CZE", "KIR", "TUV", "NAU", "MHL", "MAU", "COM", "STP", "SEY", "WES", "SML", "NCY", "HAM", "HEZ", "HOU", "NUG", "ATG", "DMA", "STL", "SVG", "GND", "BRB", "PMR", "GRN", "KUR", "ROJ", "ABK", "SOS", "STC", "DRZ", "SNA", "PNT", "JUB", "SHB", "M23", "NRF", "LES", "SWZ"}:
            lines.append(f' {tag}:0 "{country}"')
    text = "\n".join(lines) + "\n"
    path = LOC_DIR / "doomsday_l_english.yml"
    path.write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))


def main():
    countries = read_csv_countries()
    tags = parse_tags()
    hist_names = vanilla_history_names()
    capitals = vanilla_capitals()
    capitals["CHI"] = 608
    capitals["SOV"] = 219
    capitals["DPK"] = 527
    capitals["SSD"] = 549
    capitals["FOR"] = 524
    capitals["KOR"] = 525
    capitals["BAN"] = 430
    capitals["PAL"] = 1086
    capitals["HAM"] = 1085
    capitals["WES"] = 699
    capitals["SML"] = 269
    capitals["NCY"] = 1087
    capitals["HEZ"] = 1089
    capitals["HOU"] = 293
    capitals["NUG"] = 999
    capitals["YEM"] = 1102
    capitals["STC"] = 992
    capitals["DRZ"] = 1103
    capitals["SNA"] = 1104
    capitals["PNT"] = 1105
    capitals["JUB"] = 844
    capitals["SHB"] = 1106
    capitals["M23"] = 1107
    capitals["ATG"] = 308
    capitals["DMA"] = 1093
    capitals["STL"] = 1094
    capitals["SVG"] = 1095
    capitals["GND"] = 1096
    capitals["BRB"] = 692
    capitals["PMR"] = 834
    capitals["GRN"] = 101
    capitals["KUR"] = 1099
    capitals["ROJ"] = 1100
    capitals["ABK"] = 826
    capitals["SOS"] = 1101
    capitals["SAF"] = 275
    capitals["NRF"] = 1109
    capitals["LES"] = 1110
    capitals["SWZ"] = 1111
    capitals["BRN"] = 1023
    capitals["NMB"] = 541
    capitals["KIR"] = 639
    capitals["TUV"] = 643
    capitals["NAU"] = 725
    capitals["MHL"] = 633
    capitals["MAU"] = 707
    capitals["COM"] = 708
    capitals["STP"] = 705
    capitals["SEY"] = 709
    capitals["PLU"] = 647

    STATES_DIR.mkdir(parents=True, exist_ok=True)
    from patch_doomsday_map import ensure_map_splits
    ensure_map_splits()
    source_dir = VANILLA_STATES if VANILLA_STATES.exists() else STATES_DIR
    parsed = [parse_state(p) for p in sorted(source_dir.glob("*.txt"))]
    parsed = [s for s in parsed if s["id"]]
    apply_map_splits(parsed)
    # Always write into the mod folder, even when the source is vanilla.
    for state in parsed:
        state["path"] = STATES_DIR / state["file"]

    leftovers = []
    for state in parsed:
        owner = pick_owner(state)
        state["new_owner"] = owner
        if state["owner"] in IMPERIAL and owner == state["owner"]:
            leftovers.append(f"{state['id']} {state['file']} kept {owner}")

    by_owner = defaultdict(list)
    for state in parsed:
        by_owner[state["new_owner"]].append(state)

    # Validate / fix capitals
    for tag, row in countries.items():
        cap = row.get("capital") or ""
        if str(cap).strip().isdigit():
            capitals[tag] = int(cap)
        owned_ids = {s["id"] for s in by_owner.get(tag, [])}
        if tag in capitals and owned_ids and capitals[tag] not in owned_ids:
            # pick most populated owned state
            owned = sorted(by_owner[tag], key=lambda s: s["manpower"], reverse=True)
            capitals[tag] = owned[0]["id"]
        elif tag not in capitals:
            if owned_ids:
                capitals[tag] = sorted(by_owner[tag], key=lambda s: s["manpower"], reverse=True)[0]["id"]
            else:
                capitals[tag] = 1

    # Scale manpower and place buildings
    state_plan = {}
    for tag, states in by_owner.items():
        row = countries.get(tag)
        vanilla_pop = sum(s["manpower"] for s in states) or 1
        target_pop = int(float((row or {}).get("pop") or vanilla_pop))
        if target_pop <= 0:
            target_pop = vanilla_pop
        civs, mils, docks, infra = factories_for(row) if row else (0, 0, 0, 2)
        weights = [max(s["manpower"], 1000) for s in states]
        # Bias factories toward already-urban categories
        cat_bonus = {"megalopolis": 4, "metropolis": 3, "large_city": 3, "city": 2, "large_town": 2, "town": 1}
        factory_w = [max(s["manpower"], 1000) * cat_bonus.get(s["category"], 1) for s in states]
        dock_w = [factory_w[i] if states[i]["naval_in_buildings"] else 1 for i in range(len(states))]
        civ_d = cap_distribute(civs, factory_w, FACTORY_LEVEL_CAP)
        mil_d = cap_distribute(mils, factory_w, FACTORY_LEVEL_CAP)
        dock_d = cap_distribute(docks, dock_w, FACTORY_LEVEL_CAP)
        pops = distribute(target_pop, weights)
        for i, state in enumerate(states):
            state_plan[state["id"]] = {
                "owner": tag,
                "manpower": max(1000, pops[i]),
                "civs": civ_d[i],
                "mils": mil_d[i],
                "docks": dock_d[i],
                "infra": infra,
            }

    for state in parsed:
        plan = state_plan.get(state["id"], {
            "owner": state["new_owner"],
            "manpower": state["manpower"],
            "civs": 0, "mils": 0, "docks": 0, "infra": 2,
        })
        write_state(state, plan["owner"], plan["manpower"], plan["civs"], plan["mils"], plan["docks"], plan["infra"])

    with CSV_STATES.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["state_id", "file", "owner_2026", "manpower", "civs", "mils", "docks", "infra", "category"])
        for state in parsed:
            p = state_plan.get(state["id"], {})
            w.writerow([
                state["id"], state["file"], p.get("owner", state["new_owner"]),
                p.get("manpower", state["manpower"]), p.get("civs", 0), p.get("mils", 0),
                p.get("docks", 0), p.get("infra", 2), state["category"],
            ])

    faction_members = defaultdict(list)
    for tag, row in countries.items():
        fac = (row.get("faction") or "").strip()
        if fac:
            faction_members[fac].append(tag)

    for tag, country_file in tags:
        fname = hist_names.get(tag, f"{tag} - {country_file}")
        write_country(tag, fname, countries.get(tag), capitals.get(tag, 1), faction_members)
    for leftover in COUNTRIES_DIR.glob("D[0-9][0-9]*.txt"):
        leftover.unlink()

    write_loc(countries, tags)

    owned_counts = {k: len(v) for k, v in sorted(by_owner.items(), key=lambda kv: -len(kv[1]))}
    print("states", len(parsed))
    print("country files", len(list(COUNTRIES_DIR.glob('*.txt'))))
    print("top owners", list(owned_counts.items())[:20])
    print("imperial leftovers", len(leftovers))
    for line in leftovers[:40]:
        print(" ", line)
    civ_total = sum(p.get("civs", 0) for p in state_plan.values())
    mil_total = sum(p.get("mils", 0) for p in state_plan.values())
    print("world civs", civ_total, "world mils", mil_total)


if __name__ == "__main__":
    main()
