#!/usr/bin/env python3
"""Build Doomsday 2026 history, loc, and state CSVs from vanilla states + country sheet."""

from __future__ import annotations

import csv
import os
import re
from collections import defaultdict
from pathlib import Path

from slim_tech_tree import apply_slim, build_tech_block

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV")
STATES_DIR = ROOT / "history" / "states"
VANILLA_STATES = VANILLA / "history" / "states"
COUNTRIES_DIR = ROOT / "history" / "countries"
LOC_DIR = ROOT / "localisation" / "english"
CSV_COUNTRIES = Path(__file__).with_name("doomsday_countries.csv")
CSV_STATES = Path(__file__).with_name("doomsday_states.csv")

from state_stats_lib import (  # noqa: E402
    factories_from_goods,
    goods_va_b,
    mils_from_dib,
)
FACTORY_LEVEL_CAP = 40
SHARED_SLOTS_CAP = 50
URBAN_CATS = frozenset({"megalopolis", "metropolis", "large_city", "city", "large_town"})
LAUNCH_TAGS = frozenset({
    "USA", "SOV", "CHI", "ENG", "FRA", "DPK", "RAJ", "PAK", "ISR", "PER", "KOR",
})

SOVEREIGN = {
    "USA", "CAN", "MEX", "GUA", "HON", "ELS", "NIC", "COS", "PAN", "CUB", "HAI", "DOM",
    "COL", "VEN", "ECU", "PRU", "BOL", "CHL", "ARG", "URG", "PAR", "BRA",
    "ENG", "IRE", "FRA", "SPR", "POR", "BEL", "HOL", "LUX", "SWI", "ITA", "GER", "AUS",
    "CZE", "SLO", "POL", "HUN", "ROM", "BUL", "GRE", "ALB", "YUG", "SER", "CRO", "SLV",
    "BOS", "MAC", "MNT", "KOS", "DEN", "GRN", "NOR", "SWE", "FIN", "ICE", "EST", "LAT", "LIT",
    "SOV", "UKR", "BLR", "MOL", "PMR", "GEO", "ABK", "SOE", "ARM", "AZR", "KAZ", "UZB", "TMS", "KYR", "TAJ",
    "TUR", "GRE", "CYP", "NCY", "MLT",
    "SAU", "YEM", "HOU", "YNR", "STC", "OMA", "UAE", "QAT", "KUW", "BHR", "IRQ", "KUR", "PER", "AFG", "NRF", "SYR", "ROJ", "DRZ", "SNA", "LEB",
    "JOR", "ISR", "PAL", "HAM", "HEZ", "EGY", "LBA", "LNA", "TUN", "ALG", "MOR", "WES",
    "ETH", "ERI", "DJI", "SOM", "SML", "PNT", "JUB", "SHB", "KEN", "UGA", "TZN", "RWA", "BRD", "SUD", "RSF", "SSD", "SIO",
    "SAF", "LES", "SWZ", "NMB", "BOT", "ZIM", "ZAM", "MLW", "ANG", "MZB", "MAD", "COG", "M23", "RCG", "GAB",
    "EQG", "CMR", "CAR", "CHA", "NGA", "DAH", "TOG", "GHA", "IVO", "VOL", "MLI", "AZA", "NGR",
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
    "ISR", "PAL", "HAM", "HEZ", "NCY", "CYP", "JOR", "LEB", "ROJ", "DRZ", "SNA", "SYR", "IRQ", "KUW", "UAE", "QAT", "BHR", "OMA", "YEM", "HOU", "YNR", "STC",
    "DPK", "KOR", "FOR", "VIN", "CAM", "LAO", "MAL", "SNG", "INS", "PHI", "TML", "BRN",
    "PLU", "FSM", "KIR", "TUV", "NAU", "MHL", "FIJ", "VAN", "SOL", "MAU", "COM", "STP", "SEY",
    "ALG", "MOR", "WES", "TUN", "LBA", "EGY", "SUD", "RSF", "SSD", "SIO", "ERI", "DJI",
    "KEN", "ETH", "SOM", "SML", "PNT", "JUB", "SHB", "UGA", "TZN", "RWA", "BRD",
    "NGA", "GHA", "IVO", "SEN", "MLI", "AZA", "NGR", "CHA", "CMR", "COG", "M23", "RCG", "GAB", "ANG",
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
    (r"jonglei", "SIO"),
    (r"transnistria|tiraspol", "PMR"),
    (r"greenland", "GRN"),
    (r"srem|syrmia", "SER"),
    (r"salla", "SOV"),
    (r"146-karelia|karjala", "SOV"),
    (r"abkhazia", "ABK"),
    (r"south ossetia|tskhinval", "SOE"),
    (r"nakhchivan", "AZR"),
    (r"panjshir|bazarak", "NRF"),
    (r"iraqi kurdistan|erbil|duhok|sulaymaniyah", "KUR"),
    (r"rojava|qamishli|northeast syria", "ROJ"),
    (r"mocha|tihama|national resistance", "YNR"),
    (r"marib", "YEM"),
    (r"suwayda", "DRZ"),
    (r"peace spring|tell abyad|ras al-ayn", "SNA"),
    (r"puntland", "PNT"),
    (r"al-shabaab|jilib", "SHB"),
    (r"jubaland", "JUB"),
    (r"goma|north kivu", "M23"),
    (r"lesotho|maseru", "LES"),
    (r"eswatini|swaziland|mbabane", "SWZ"),
    (r"trieste", "ITA"),
    (r"southern transitional|hadhramaut", "STC"),
    (r"bangladesh|east bengal", "BAN"),
    (r"gaza", "HAM"),
    (r"gao", "AZA"),
    (r"tombouctou|timbuktu", "AZA"),
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
    (r"rio de oro|western sahara", "MOR"),
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
    names["YNR"] = "YNR - Yemeni National Resistance.txt"
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
    names["SOE"] = "SOE - South Ossetia.txt"
    names["NRF"] = "NRF - National Resistance Front.txt"
    names["LES"] = "LES - Lesotho.txt"
    names["SWZ"] = "SWZ - Eswatini.txt"
    names["LNA"] = "LNA - Libyan National Army.txt"
    names["RSF"] = "RSF - Rapid Support Forces.txt"
    names["SIO"] = "SIO - SPLM-IO.txt"
    names["AZA"] = "AZA - Azawad.txt"
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
# Jan 1 2026 front: Russia ~18% of Ukraine (Crimea, ~98% Luhansk, ~60% Donetsk,
# ~65% Zaporizhzhia south of the city, Kherson left bank). Pokrovsk still
# Ukrainian until late January 2026. Occupier must be at war with owner.
OCCUPIED_BY = {
    137: "SOV",   # Crimea — occupied since 2014
    227: "SOV",   # Donetsk city / Mariupol / Avdiivka belt
    228: "SOV",   # Luhansk — nearly all oblast
    1113: "SOV",  # Azov Zaporizhzhia — Melitopol land bridge
    1114: "SOV",  # Kherson left bank / Kakhovka
}

SPLIT_NEW_STATES = [
    {
        "id": 1082,
        "file": "1082-Balta.txt",
        "from_id": 192,
        "provinces": [3575, 9714],
        "owner": "UKR",
        "cores": ["UKR", "SOV"],
        "category": "rural",
        "manpower": 340904,
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
        "owner": "IRQ",
        "cores": ["IRQ", "KUR"],
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
        "owner": "SOE",
        "cores": ["SOE", "GEO"],
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
    {
        "id": 1112,
        "file": "1112-Guantanamo Bay.txt",
        "from_id": 315,
        "provinces": [7590],
        "owner": "USA",
        "cores": ["USA", "CUB"],
        "category": "enclave",
        "manpower": 8000,
        "vps": [(7590, 1)],
        "buildings": (
            "\t\t\tinfrastructure = 3\n"
            "\t\t\t7590 = { naval_base = 2 }\n"
        ),
    },
    {
        "id": 1113,
        "file": "1113-Azov Zaporizhzhia.txt",
        "from_id": 200,
        "provinces": [588, 3767, 6596, 9571, 9729, 11700],
        "owner": "UKR",
        "cores": ["UKR", "SOV"],
        "category": "rural",
        "manpower": 720000,
        "vps": [(11700, 3)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1114,
        "file": "1114-Left Bank Kherson.txt",
        "from_id": 196,
        "provinces": [568, 721, 737, 767, 3573, 6771, 9712],
        "owner": "UKR",
        "cores": ["UKR", "SOV"],
        "category": "rural",
        "manpower": 430000,
        "vps": [(737, 2)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1115,
        "file": "1115-Kramatorsk.txt",
        "from_id": 227,
        "provinces": [502, 3466, 3491],
        "owner": "UKR",
        "cores": ["UKR", "SOV"],
        "category": "town",
        "manpower": 1100000,
        "vps": [(502, 5)],
        "buildings": "\t\t\tinfrastructure = 2\n",
    },
    {
        "id": 1116,
        "file": "1116-Mocha.txt",
        "from_id": 293,
        "provinces": [10752],
        "owner": "YNR",
        "cores": ["YNR", "YEM", "HOU"],
        "category": "rural",
        "manpower": 500000,
        "vps": [(10752, 3)],
        "buildings": (
            "\t\t\tinfrastructure = 2\n"
            "\t\t\t10752 = { naval_base = 1 }\n"
        ),
    },
    {
        "id": 1117,
        "file": "1117-Trieste.txt",
        "from_id": 736,
        "provinces": [6626],
        "owner": "ITA",
        "cores": ["ITA"],
        "category": "city",
        "manpower": 230000,
        "vps": [(6626, 5)],
        "buildings": (
            "\t\t\tinfrastructure = 4\n"
            "\t\t\t6626 = { naval_base = 5 }\n"
        ),
    },
    {
        "id": 1118,
        "file": "1118-Sahrawi Free Zone.txt",
        "from_id": 699,
        "provinces": [7979, 4920, 13415, 13416],
        "owner": "WES",
        "cores": ["WES"],
        "claims": ["MOR"],
        "category": "wasteland",
        "manpower": 30000,
        "vps": [],
        "buildings": (
            "\t\t\tinfrastructure = 1\n"
            "\t\t\t13415 = { naval_base = 1 }\n"
        ),
    },
    {
        "id": 1119,
        "file": "1119-Aksai Chin.txt",
        "from_id": 441,
        "provinces": [5042],
        "owner": "CHI",
        "cores": ["RAJ", "PAK"],
        "claims": ["CHI"],
        "category": "wasteland",
        "manpower": 20000,
        "vps": [],
        "buildings": "\t\t\tinfrastructure = 1\n",
    },
    {
        "id": 1120,
        "file": "1120-Tel Aviv.txt",
        "from_id": 454,
        "provinces": [1065, 1201, 4206],
        "owner": "ISR",
        "cores": ["PAL", "ISR"],
        "category": "town",
        "manpower": 5500000,
        "vps": [(4206, 1), (1065, 1)],
        "buildings": (
            "\t\t\tinfrastructure = 4\n"
            "\t\t\tair_base = 2\n"
            "\t\t\t4206 = { naval_base = 3 }\n"
        ),
    },
    {
        "id": 1121,
        "file": "1121-Jonglei.txt",
        "from_id": 884,
        "provinces": [10859, 12800],
        "owner": "SIO",
        "cores": ["SIO", "SSD", "SUD"],
        "category": "pastoral",
        "manpower": 3000000,
        "vps": [(12800, 2), (10859, 1)],
        "buildings": "\t\t\tinfrastructure = 1\n",
    },
]

# Move existing provinces onto another leftover state (no new ID).
MOVE_PROVINCES = [
    {"from_id": 198, "to_id": 834, "provinces": [9423]},  # Moldova-border tile west of Rîbnița → Transnistria
    {"from_id": 559, "to_id": 1106, "provinces": [2063]},  # south-central inland → Al-Shabaab
    {"from_id": 449, "to_id": 448, "provinces": [1041]},  # Abu Grein coast west of Sirte → GNU
    {"from_id": 834, "to_id": 1082, "provinces": [3757]},  # Balta off Transnistria → Balta
    {"from_id": 197, "to_id": 196, "provinces": [3755, 574, 9573]},  # even Kherson / Mykolaiv split
    {"from_id": 108, "to_id": 802, "provinces": [6953]},  # Eastern Serbia hills next to Pristina → Kosovo
]

# Absorb a leftover vanilla state into another (provinces, VPs, manpower).
MERGE_STATES = []

# New provinces painted inside an existing state (city pockets, not new states).
ADD_PROVINCES = {
    782: [13417, 13418, 13419],  # Tinzaouaten, Tessalit, Kidal
    898: [13420],  # Timbuktu
}

# Owner keeps the state; listed tag occupies these provinces at start (must be at war).
PROVINCE_CONTROLLERS = {
    782: ("MLI", [13419, 13418]),  # Kidal, Tessalit
    898: ("MLI", [13420]),  # Timbuktu
}

# Extra cores on leftover vanilla states (civil-war claims). Owner core is added separately.
EXTRA_CORES = {
    448: ["LNA"],  # Tripoli — GNU-held, LNA claims
    661: ["LNA"],  # Tripolitania / Nafusa
    699: ["WES"],  # Moroccan-administered Western Sahara; Polisario core
    551: ["RSF"],  # Khartoum — SAF-held, RSF claims
    549: ["RSF"],  # Kordofan
    883: ["RSF"],  # Kassala / Port Sudan
    886: ["RSF"],  # Blue Nile
    767: ["SUD"],  # North Darfur — RSF-held, SAF claims
    887: ["SUD"],  # South Darfur
    884: ["SIO"],  # Juba / Unity leftover — SPLM-IO claims
    885: ["SIO"],  # Bahr al Ghazal — Kiir heartland, IO claims
    898: ["MLI"],  # Gao — Azawad-held, Mali cores the north
    782: ["MLI"],  # Kidal / Taoudenni — Azawad-held, Mali cores
}

# Morocco claims Western Sahara; it does not core the leftover coast or the Free Zone.
SKIP_OWNER_CORE = {699, 1119}
EXTRA_CLAIMS = {
    699: ["MOR"],
    1118: ["MOR"],
    1119: ["CHI"],
}

# VPs missing from vanilla leftovers.
EXTRA_VPS = {
    448: [(9980, 3)],   # Misrata
    662: [(7136, 5), (8069, 2)],  # Sirte + Al Jufra
    767: [(10900, 3)],  # El Fasher
    887: [(10857, 5)],  # Nyala
    736: [(599, 2)],    # Koper
    196: [(3755, 3)],  # Kherson city after even split from 197
    782: [(13417, 5), (13419, 3), (13418, 2)],  # Tinzaouaten, Kidal, Tessalit
    898: [(13420, 3)],  # Timbuktu city pocket
}

# Province naval bases on leftover states after MOVE_PROVINCES.
EXTRA_PROVINCE_PORTS = {
    448: [(1041, 1)],  # Abu Grein, moved off El Agheila
    736: [(599, 1)],   # Koper after Trieste keeps 6626's port
}

# History-file lines that are not ideas (event targets, flags).
COUNTRY_HISTORY_EXTRAS = {
    "CHI": [
        "save_global_event_target_as = WTT_communist_china",
        "save_global_event_target_as = WTT_current_china_leader",
    ],
}

COUNTRY_IDEAS = {
    "TUR": ["TUR_western_libya_mission"],
    "LBA": ["LBA_turkish_support"],
    "LNA": ["LNA_foreign_backing"],
    "JAP": ["JAP_boj_home_bias"],
}


# Attacker -> targets. Occupied controllers without a matching war hang CreateMapModes.
START_WARS = {
    "SOV": ["UKR"],
    "ISR": ["HAM", "HEZ"],
    "HOU": ["YEM", "YNR"],
    "YEM": ["STC"],
    "BRM": ["NUG"],
    "SOM": ["SHB", "JUB"],
    "COG": ["M23"],
    "NRF": ["AFG"],
    "SYR": ["ROJ", "SNA", "DRZ"],
    "ROJ": ["SNA"],
    "SUD": ["RSF"],
    "SSD": ["SIO"],
    "MLI": ["AZA"],
    "WES": ["MOR"],
}

# Named world tension. One entry per theater. Civil 1, offensive 3, Russia-Ukraine 8.
START_THREATS = {
    "SOV": [(8, "DD_THREAT_RUSSIA_UKRAINE")],
    "ISR": [(3, "DD_THREAT_ISR_HAMAS"), (3, "DD_THREAT_ISR_HEZBOLLAH")],
    "HOU": [(1, "DD_THREAT_YEMEN")],
    "SOM": [(1, "DD_THREAT_SOMALIA")],
    "SYR": [(1, "DD_THREAT_SYRIA")],
    "BRM": [(1, "DD_THREAT_MYANMAR")],
    "SUD": [(1, "DD_THREAT_SUDAN")],
    "SSD": [(1, "DD_THREAT_SOUTH_SUDAN")],
    "COG": [(1, "DD_THREAT_CONGO")],
    "NRF": [(1, "DD_THREAT_AFGHANISTAN")],
    "MLI": [(1, "DD_THREAT_SAHEL")],
    "WES": [(1, "DD_THREAT_WESTERN_SAHARA")],
}

# Overlord tag -> list of (subject, autonomy type, freedom 0-1).
# Written into the overlord country file. Do not also set controller=.
PUPPETS = {
    "DEN": [("GRN", "autonomy_puppet", 0.40)],
}


def _make_split_state_raw(spec: dict) -> str:
    vp = "".join(f"\t\tvictory_points = {{ {p} {v} }}\n" for p, v in spec["vps"])
    cores = "".join(f"\t\tadd_core_of = {c}\n" for c in spec["cores"])
    claims = "".join(f"\t\tadd_claim_by = {c}\n" for c in spec.get("claims", []))
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
        f"{claims}"
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
    by_id = {s["id"]: s for s in parsed}
    for spec in MERGE_STATES:
        src = by_id.get(spec["from_id"])
        dst = by_id.get(spec["to_id"])
        if not src or not dst:
            continue
        pm = re.search(r"\bprovinces\s*=\s*\{([^}]+)\}", src["raw"])
        src_provs = [int(n) for n in re.findall(r"\d+", pm.group(1))] if pm else []
        if src_provs:
            dst["raw"] = add_provinces_to_raw(dst["raw"], src_provs)
        for vm in re.finditer(r"victory_points\s*=\s*\{[^}]+\}", src["raw"]):
            block = vm.group(0)
            if block not in dst["raw"]:
                dst["raw"] = re.sub(
                    r"(\bowner\s*=\s*[A-Z]{3})",
                    rf"\1\n\t\t{block}",
                    dst["raw"],
                    count=1,
                )
        dst["manpower"] = dst["manpower"] + src["manpower"]
        stale = STATES_DIR / spec["file"]
        if stale.exists():
            stale.unlink()
    parsed[:] = [s for s in parsed if s["id"] not in {m["from_id"] for m in MERGE_STATES}]
    by_id = {s["id"]: s for s in parsed}
    for sid, extra in ADD_PROVINCES.items():
        dst = by_id.get(sid)
        if dst:
            dst["raw"] = add_provinces_to_raw(dst["raw"], extra)


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
        1121: "SIO",   # Jonglei / Nasir — White Army and SPLM-IO, 1 Jan 2026
        430: "BAN",
        1023: "BRN",
        541: "NMB",
        893: "NMB",
        894: "NMB",
        895: "NMB",
        137: "UKR",    # Crimea — Ukrainian owner, Russian occupation
        196: "UKR",    # Kherson right bank (4 provinces)
        197: "UKR",    # Mykolaiv (5 provinces)
        1120: "ISR",   # Tel Aviv / Nazareth / 1201
        1119: "CHI",   # Aksai Chin / Shaksgam — Chinese-held, RAJ+PAK cores
        1113: "UKR",   # Azov Zaporizhzhia — occupied
        1114: "UKR",   # Kherson left bank — occupied
        1115: "UKR",   # Kramatorsk / west Donetsk — Ukrainian-held Jan 1 2026
        766: "UKR",    # Budjak / Southern Bessarabia
        834: "PMR",    # Transnistria (Tiraspol + north)
        826: "ABK",    # Abkhazia
        1101: "SOE",   # South Ossetia (not SOS — vanilla alias is Stalinist SOV)
        1108: "AZR",   # Nakhchivan
        1109: "NRF",   # Panjshir
        1110: "LES",   # Lesotho
        1111: "SWZ",   # Eswatini
        1112: "USA",   # Guantanamo Bay (south-coast inlet of 7590)
        231: "GEO",    # Georgia proper
        101: "GRN",    # Greenland — Kingdom of Denmark puppet
        78: "MOL",
        699: "MOR",    # Western Sahara — Morocco administers the coast and cities
        1118: "WES",   # Sahrawi Free Zone — Polisario
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
        454: "ISR",    # Israel leftover (Jerusalem / Negev)
        1085: "HAM",   # Gaza — Hamas
        1086: "PAL",   # West Bank — PA
        1087: "NCY",   # Northern Cyprus
        183: "CYP",    # Republic of Cyprus
        1088: "ISR",   # Golan Heights
        1089: "HEZ",   # South Lebanon — Hezbollah
        293: "HOU",    # Houthi-held North Yemen / Sana'a
        1102: "YEM",   # Marib — PLC leftover on 1 Jan 2026
        1116: "YNR",   # Mocha / west coast — National Resistance
        1117: "ITA",   # Trieste
        736: "SLV",    # Primorska leftover after Trieste split
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
        1099: "IRQ",  # Iraqi Kurdistan — federal Iraq; KUR core stays for release
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
        551: "SUD",   # Khartoum — SAF recaptured 2025
        549: "SUD",   # Kordofan — contested, army holds the populated belt
        883: "SUD",   # Kassala / Port Sudan — SAF east
        886: "SUD",   # Blue Nile — SAF
        767: "RSF",   # North Darfur / El Fasher — RSF from Oct 2025
        887: "RSF",   # South Darfur / Nyala — RSF capital
        898: "AZA",   # Gao — Azawad desert; Mali holds Timbuktu city pocket
        782: "AZA",   # Kidal / Taoudenni — Azawad; Mali holds Kidal and Tessalit pockets
        705: "STP",    # São Tomé and Príncipe
        709: "SEY",    # Seychelles
        636: "FIJ",
        448: "LBA",   # Tripoli — GNU
        661: "LBA",   # Tripolitania / Nafusa / Zintan — GNU
        662: "LNA",   # Sirte + Al Jufra — LNA (273 force-links here)
        449: "LNA",   # El Agheila leftover east of Abu Grein — LNA
        450: "LNA",   # Benghazi — LNA capital
        451: "LNA",   # Derna / Tobruk
        663: "LNA",   # Cyrenaica inland
        273: "LNA",   # Fezzan / Libyan Desert (force_link_ownership_to 662)
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
        (r"tripoli|tripolitania", "LBA"),
        (r"sirte|bengh|derna|cyrenaica|libyan coast|el agheila|italian africa", "LNA"),
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
    goods = goods_va_b(
        float(row.get("ind_b") or 0),
        float(row.get("agr_b") or 0),
        float(row.get("mva_b") or 0),
    )
    docks = int(float(row.get("docks") or 0))
    infra = max(1, min(5, int(float(row.get("infra") or 2))))
    civs = factories_from_goods(goods)
    mils = mils_from_dib(str(row.get("tag") or ""))
    return civs, mils, docks, infra


def extra_buildings_for(tag: str, row: dict | None, state: dict, is_capital: bool, civs: int, mils: int) -> dict[str, int]:
    """Place finance/services/renewable/silos. Deterministic. No new spawn types."""
    extras: dict[str, int] = {}
    gdp = float((row or {}).get("gdp_b") or 0)
    cat = state.get("category") or "rural"
    urban = cat in URBAN_CATS or is_capital

    if urban and gdp >= 80:
        services = 1
        if is_capital and gdp >= 400:
            services += 1
        if civs >= 4:
            services += 1
        extras["services_building"] = min(4, services)
    if urban and gdp >= 400 and (is_capital or cat in {"megalopolis", "metropolis", "large_city"}):
        extras["finance_center"] = 2 if is_capital and gdp >= 2000 else 1
    if urban and gdp >= 250:
        extras["renewable_park"] = 2 if is_capital and gdp >= 1500 else 1

    if tag in LAUNCH_TAGS and (is_capital or cat in {"megalopolis", "metropolis"}):
        if is_capital and tag in {"USA", "SOV", "CHI"}:
            extras["rocket_site"] = 3
        elif is_capital:
            extras["rocket_site"] = 2
        else:
            extras["rocket_site"] = 1

    return extras


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


def strip_all_sam_from_buildings(block: str) -> str:
    """Remove leftover sam_site lines and empty province buildings blocks."""
    block = re.sub(r"(?m)^[ \t]*sam_site\s*=\s*\d+[^\n]*\n?", "", block)
    empty = re.compile(r"(?m)^[ \t]*\d+\s*=\s*\{\s*\}[ \t]*\n?")
    while True:
        new = empty.sub("", block)
        if new == block:
            return block
        block = new


def provincial_sam_provinces(state_text: str, n: int) -> list[int]:
    """Unused. SAM is aircraft, not a map building."""
    return []


def strip_state_level_sam(block: str) -> tuple[str, int]:
    return strip_all_sam_from_buildings(block), 0


def ensure_province_sam(block: str, pid: int) -> str:
    return block


def place_sam_in_buildings_block(block: str, state_text: str, n: int) -> str:
    return strip_all_sam_from_buildings(block)


def convert_existing_sam_to_provincial() -> int:
    changed = 0
    for path in sorted(STATES_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        bm = re.search(r"\bbuildings\s*=", text)
        if not bm:
            continue
        block, end = extract_block(text, bm.start())
        new_block = strip_all_sam_from_buildings(block)
        if new_block == block:
            continue
        path.write_text(text[: bm.start()] + f"buildings = {new_block}" + text[end:], encoding="utf-8")
        changed += 1
    return changed


def write_state(
    state: dict,
    owner: str,
    manpower: int,
    civs: int,
    mils: int,
    docks: int,
    infra: int,
    extra_buildings: dict[str, int] | None = None,
):
    text = state["raw"]
    text = strip_dated_history(text)
    text = re.sub(r"\bowner\s*=\s*[A-Z]{3}", f"owner = {owner}", text, count=1)
    # Vanilla North Darfur is impassable and force-linked to Khartoum. RSF cannot
    # own it independently unless both flags come off.
    if state["id"] in {767, 887, 782}:
        text = re.sub(r"\n[ \t]*impassable\s*=\s*yes", "", text)
        text = re.sub(r"\n[ \t]*force_link_ownership_to\s*=\s*\d+[^\n]*", "", text)
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
    if state["id"] in SKIP_OWNER_CORE:
        text = re.sub(rf"\n[ \t]*add_core_of\s*=\s*{owner}\b", "", text)
    elif not re.search(rf"\badd_core_of\s*=\s*{owner}\b", text):
        text = re.sub(r"(\bowner\s*=\s*[A-Z]{3})", rf"\1\n\t\tadd_core_of = {owner}", text, count=1)
    for extra in EXTRA_CORES.get(state["id"], []):
        if not re.search(rf"\badd_core_of\s*=\s*{extra}\b", text):
            text = re.sub(r"(\bowner\s*=\s*[A-Z]{3})", rf"\1\n\t\tadd_core_of = {extra}", text, count=1)
    for claim in EXTRA_CLAIMS.get(state["id"], []):
        if not re.search(rf"\badd_claim_by\s*=\s*{claim}\b", text):
            text = re.sub(r"(\bowner\s*=\s*[A-Z]{3})", rf"\1\n\t\tadd_claim_by = {claim}", text, count=1)
    for pid, val in EXTRA_VPS.get(state["id"], []):
        if not re.search(rf"victory_points\s*=\s*\{{\s*{pid}\b", text):
            text = re.sub(
                r"(\bowner\s*=\s*[A-Z]{3})",
                rf"\1\n\t\tvictory_points = {{ {pid} {val} }}",
                text,
                count=1,
            )
    text = re.sub(
        r"\n[ \t]*[A-Z]{3}\s*=\s*\{\s*(?:set_province_controller\s*=\s*\d+\s*)+\}",
        "",
        text,
    )
    occ = PROVINCE_CONTROLLERS.get(state["id"])
    if occ:
        tag, pids = occ
        inner = "".join(f"\n\t\t\tset_province_controller = {pid}" for pid in pids)
        text = re.sub(
            r"(\bowner\s*=\s*[A-Z]{3})",
            rf"\1\n\t\t{tag} = {{{inner}\n\t\t}}",
            text,
            count=1,
        )
    cat_slots = {
        "megalopolis": 12, "metropolis": 10, "large_city": 8, "city": 6,
        "large_town": 5, "town": 4, "large_island": 3, "rural": 2,
        "small_island": 1, "pastoral": 1, "wasteland": 0, "tiny_island": 0, "enclave": 0,
    }.get(state.get("category") or "rural", 2)
    extra_buildings = extra_buildings or {}
    shared_extra = (
        extra_buildings.get("finance_center", 0)
        + extra_buildings.get("services_building", 0)
        + extra_buildings.get("renewable_park", 0)
    )
    extra_cap = max(0, SHARED_SLOTS_CAP - cat_slots)
    slots = min(civs + mils + docks + shared_extra + 4, extra_cap)
    if re.search(r"add_extra_state_shared_building_slots", text):
        text = re.sub(
            r"add_extra_state_shared_building_slots\s*=\s*\d+",
            f"add_extra_state_shared_building_slots = {slots}",
            text,
            count=1,
        )
    else:
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
        for key, value in extra_buildings.items():
            if key == "sam_site":
                continue
            if value:
                new_block = replace_or_insert(new_block, key, value)
        new_block = strip_all_sam_from_buildings(new_block)
        for pid, level in EXTRA_PROVINCE_PORTS.get(state["id"], []):
            if not re.search(rf"\b{pid}\s*=", new_block):
                new_block = new_block[:-1] + f"\n\t\t\t{pid} = {{\n\t\t\t\tnaval_base = {level}\n\t\t\t}}\n\t\t}}"
        text = text[: bm.start()] + f"buildings = {new_block}" + text[end:]
    if re.search(rf"\badd_core_of\s*=\s*{owner}\b", text):
        text = re.sub(r"\n[ \t]*start_resistance[^\n]*", "", text)
        text = re.sub(r"\n[ \t]*set_resistance\s*=\s*\d+[^\n]*", "", text)
        text = re.sub(r"\n[ \t]*set_compliance\s*=\s*\d+[^\n]*", "", text)
    state["path"].write_text(text, encoding="utf-8")


TECH_BLOCK = build_tech_block()


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
    try:
        gdp_f = float(gdp)
        debt_ratio = float(debt)
    except (TypeError, ValueError):
        gdp_f = 0.0
        debt_ratio = 0.0
    abs_debt = gdp_f * debt_ratio
    treasury = max(1.0, gdp_f * 0.02)
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
    ]
    sipri_f = float((row or {}).get("sipri_b") or 0)
    if sipri_f >= 5:
        ammo = min(200, max(8, int(round(sipri_f * 0.3))))
        lines.append(
            f"add_equipment_to_stockpile = {{ type = sam_missile_equipment_1 amount = {ammo} producer = {tag} }}"
        )
    for idea in COUNTRY_IDEAS.get(tag, []):
        lines.append(f"add_ideas = {idea}")
    for extra in COUNTRY_HISTORY_EXTRAS.get(tag, []):
        lines.append(extra)
    lines += [
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
        f"set_variable = {{ debt = {abs_debt:.4f} }}",
        f"set_variable = {{ treasury = {treasury:.4f} }}",
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
    for amount, key in START_THREATS.get(tag, []):
        lines.append("add_named_threat = {")
        lines.append(f"	threat = {amount}")
        lines.append(f"	name = {key}")
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
        ' SIO:0 "SPLM-IO"',
        ' SIO_DEF:0 "the SPLM-IO"',
        ' SIO_ADJ:0 "SPLM-IO"',
        ' STATE_1121:0 "Jonglei"',
        ' VICTORY_POINTS_12800:0 "Nasir"',
        ' VICTORY_POINTS_10859:0 "Akobo"',
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
        ' YNR:0 "Yemeni National Resistance"',
        ' YNR_DEF:0 "the Yemeni National Resistance"',
        ' YNR_ADJ:0 "National Resistance"',
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
        ' SOE:0 "South Ossetia"',
        ' SOE_DEF:0 "South Ossetia"',
        ' SOE_ADJ:0 "South Ossetian"',
        ' CZE:0 "Czechia"',
        ' CZE_DEF:0 "Czechia"',
        ' CZE_ADJ:0 "Czech"',
        ' STATE_430:0 "Bangladesh"',
        ' STATE_454:0 "Israel"',
        ' STATE_834:0 "Transnistria"',
        ' STATE_146:0 "Karelian Isthmus"',
        ' STATE_147:0 "Salla"',
        ' STATE_1082:0 "Balta"',
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
        ' STATE_1112:0 "Guantanamo Bay"',
        ' STATE_1113:0 "Azov Zaporizhzhia"',
        ' STATE_1114:0 "Left-Bank Kherson"',
        ' STATE_1115:0 "Kramatorsk"',
        ' VICTORY_POINTS_11700:0 "Melitopol"',
        ' VICTORY_POINTS_737:0 "Kakhovka"',
        ' VICTORY_POINTS_502:0 "Kramatorsk"',
        ' VICTORY_POINTS_4556:0 "Maseru"',
        ' VICTORY_POINTS_7900:0 "Mbabane"',
        ' VICTORY_POINTS_7590:0 "Guantanamo Bay"',
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
        ' STATE_1116:0 "Mocha"',
        ' VICTORY_POINTS_10752:0 "Mocha"',
        ' STATE_1117:0 "Trieste"',
        ' STATE_1118:0 "Sahrawi Free Zone"',
        ' STATE_1119:0 "Aksai Chin"',
        ' STATE_1120:0 "Tel Aviv"',
        ' VICTORY_POINTS_3755:0 "Kherson"',
        ' STATE_736:0 "Slovenian Littoral"',
        ' VICTORY_POINTS_599:0 "Koper"',
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
        ' LBA:0 "Government of National Unity"',
        ' LBA_DEF:0 "the Government of National Unity"',
        ' LBA_ADJ:0 "GNU"',
        ' LNA:0 "Libyan National Army"',
        ' LNA_DEF:0 "the Libyan National Army"',
        ' LNA_ADJ:0 "LNA"',
        ' VICTORY_POINTS_7136:0 "Sirte"',
        ' VICTORY_POINTS_9980:0 "Misrata"',
        ' VICTORY_POINTS_8069:0 "Al Jufra"',
        ' TUR_western_libya_mission:0 "Western Libya Mission"',
        ' TUR_western_libya_mission_desc:0 "Turkish drone bases and military advisors remain in western Libya, backing the Government of National Unity from Mitiga and the Tripoli hinterland."',
        ' LBA_turkish_support:0 "Turkish Military Mission"',
        ' LBA_turkish_support_desc:0 "Ankara supplies the GNU with advisors, Bayraktar drones, and a residual training mission along the western coast."',
        ' LNA_foreign_backing:0 "Foreign Backing"',
        ' LNA_foreign_backing_desc:0 "The LNA holds the Sirte-Jufra line with Russian Africa Corps contractors at Al Jufra, Egyptian border cover, and Emirati finance."',
        ' RSF:0 "Rapid Support Forces"',
        ' RSF_DEF:0 "the Rapid Support Forces"',
        ' RSF_ADJ:0 "RSF"',
        ' VICTORY_POINTS_10900:0 "El Fasher"',
        ' VICTORY_POINTS_10857:0 "Nyala"',
        ' STATE_767:0 "North Darfur"',
        ' STATE_887:0 "South Darfur"',
        ' AZA:0 "Azawad"',
        ' AZA_DEF:0 "Azawad"',
        ' AZA_ADJ:0 "Azawadi"',
        ' STATE_898:0 "Gao"',
        ' STATE_782:0 "Kidal"',
        ' VICTORY_POINTS_13417:0 "Tinzaouaten"',
        ' VICTORY_POINTS_13418:0 "Tessalit"',
        ' VICTORY_POINTS_13419:0 "Kidal"',
        ' VICTORY_POINTS_13420:0 "Timbuktu"',
    ]
    LEADER_DESCS = {
        "LBA": "Abdul Hamid Dbeibeh heads the Tripoli-based Government of National Unity. Mohamed al-Menfi remains Presidential Council chair, but the GNU's western ministries and militias answer to the prime minister.",
        "LNA": "Field Marshal Khalifa Haftar commands the Benghazi-based Libyan National Army. His sons, notably Saddam Haftar, hold the key army and security posts that keep Cyrenaica and Fezzan in line.",
        "YNR": "Tareq Saleh commands the National Resistance from Mocha. His Republican Guard veterans and Tihama units hold the Red Sea coast against the Houthis and are not under Marib or Aden command.",
        "RSF": "Mohamed Hamdan Dagalo (Hemedti) commands the Rapid Support Forces from Nyala. After taking El Fasher in late 2025 his army holds Darfur against Burhan's SAF in Khartoum and the east.",
        "AZA": "Bilal Ag Acherif leads the Azawad coalitions from Tinzaouaten. The FLA holds the northern desert while Malian garrisons sit in Kidal, Tessalit, and Timbuktu.",
        "SIO": "Riek Machar remains the SPLM-IO leader from house arrest in Juba. The Nuer White Army and IO units hold Nasir and eastern Jonglei against Kiir's SSPDF.",
    }
    for tag, row in countries.items():
        leader = row.get("leader") or tag
        country = row.get("name") or tag
        if tag in LEADER_DESCS:
            lines.append(f' {tag}_LEADER_DESC:0 "{LEADER_DESCS[tag]}"')
        else:
            lines.append(f' {tag}_LEADER_DESC:0 "{leader} leads {country} in 2026."')
    # Vanilla country names live in countries_l_english.yml. Do not rewrite
    # them here (loc key collisions). Overrides go to localisation/replace/.
    replace_keys = {
        "SOV", "SOV_DEF", "SOV_ADJ", "RAJ", "RAJ_DEF", "RAJ_ADJ", "CHI", "CHI_DEF", "CHI_ADJ",
        "PER", "PER_DEF", "PER_ADJ", "SIA", "HOL", "HOL_DEF", "DPK", "DPK_DEF", "DPK_ADJ",
        "FOR", "FOR_DEF", "FOR_ADJ", "KOR", "KOR_DEF", "KOR_ADJ", "CZE", "CZE_DEF", "CZE_ADJ",
        "WES", "WES_DEF", "WES_ADJ", "COG", "CRC", "CRC_DEF", "BAS", "BAS_DEF",
        "GRN_ADJ", "LBA", "LBA_DEF", "LBA_ADJ",
        "BRM", "ENG", "GAM", "IVO", "KUR", "KUR_ADJ", "KUR_DEF", "MAC", "PNG", "RCG",
        "SAU", "TML", "UAE", "USA", "VOL",
        "STATE_430", "STATE_441", "STATE_454", "STATE_559", "STATE_834", "STATE_146", "STATE_147",
        "STATE_308", "STATE_676", "STATE_680", "STATE_692", "STATE_693", "STATE_694", "STATE_736",
        "STATE_77", "STATE_269", "STATE_293", "STATE_311", "STATE_699", "STATE_1118", "STATE_1119", "STATE_1120", "STATE_767", "STATE_887",
        "STATE_890", "STATE_826", "STATE_844", "STATE_992", "STATE_659", "STATE_1006", "STATE_787",
        "STATE_782",
        "VICTORY_POINTS_10752", "VICTORY_POINTS_10781", "VICTORY_POINTS_7590", "VICTORY_POINTS_3755",
    }
    main_lines = ["l_english:"]
    replace_lines = ["l_english:"]
    for line in lines[1:]:
        key = line.strip().split(":")[0]
        (replace_lines if key in replace_keys else main_lines).append(line)
    path = LOC_DIR / "doomsday_l_english.yml"
    path.write_bytes(b"\xef\xbb\xbf" + ("\n".join(main_lines) + "\n").encode("utf-8"))
    replace_dir = ROOT / "localisation" / "replace"
    replace_dir.mkdir(parents=True, exist_ok=True)
    (replace_dir / "doomsday_overrides_l_english.yml").write_bytes(
        b"\xef\xbb\xbf" + ("\n".join(replace_lines) + "\n").encode("utf-8")
    )


def main():
    apply_slim(ROOT)
    global TECH_BLOCK
    TECH_BLOCK = build_tech_block()
    countries = read_csv_countries()
    tags = parse_tags()
    hist_names = vanilla_history_names()
    capitals = vanilla_capitals()
    capitals["CHI"] = 608
    capitals["SOV"] = 219
    capitals["DPK"] = 527
    capitals["SSD"] = 884
    capitals["SIO"] = 1121
    capitals["FOR"] = 524
    capitals["KOR"] = 525
    capitals["BAN"] = 430
    capitals["PAL"] = 1086
    capitals["HAM"] = 1085
    capitals["WES"] = 1118
    capitals["SML"] = 269
    capitals["NCY"] = 1087
    capitals["HEZ"] = 1089
    capitals["HOU"] = 293
    capitals["YNR"] = 1116
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
    capitals["SOE"] = 1101
    capitals["SAF"] = 275
    capitals["NRF"] = 1109
    capitals["LES"] = 1110
    capitals["SWZ"] = 1111
    capitals["LNA"] = 450
    capitals["RSF"] = 887
    capitals["AZA"] = 782
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
        capital_id = capitals.get(tag)
        for i, state in enumerate(states):
            extras = extra_buildings_for(
                tag,
                row,
                state,
                is_capital=state["id"] == capital_id,
                civs=civ_d[i],
                mils=mil_d[i],
            )
            state_plan[state["id"]] = {
                "owner": tag,
                "manpower": max(1000, pops[i]),
                "civs": civ_d[i],
                "mils": mil_d[i],
                "docks": dock_d[i],
                "infra": infra,
                "extra_buildings": extras,
            }

    for state in parsed:
        plan = state_plan.get(state["id"], {
            "owner": state["new_owner"],
            "manpower": state["manpower"],
            "civs": 0, "mils": 0, "docks": 0, "infra": 2,
        })
        write_state(
            state,
            plan["owner"],
            plan["manpower"],
            plan["civs"],
            plan["mils"],
            plan["docks"],
            plan["infra"],
            plan.get("extra_buildings") or {},
        )

    ensure_map_splits()

    with CSV_STATES.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([
            "state_id", "file", "owner_2026", "manpower", "civs", "mils", "docks", "infra",
            "finance", "services", "renewable", "sam_site", "rocket_site", "category",
        ])
        for state in parsed:
            p = state_plan.get(state["id"], {})
            extras = p.get("extra_buildings") or {}
            w.writerow([
                state["id"], state["file"], p.get("owner", state["new_owner"]),
                p.get("manpower", state["manpower"]), p.get("civs", 0), p.get("mils", 0),
                p.get("docks", 0), p.get("infra", 2),
                extras.get("finance_center", 0), extras.get("services_building", 0),
                extras.get("renewable_park", 0), extras.get("sam_site", 0),
                extras.get("rocket_site", 0), state["category"],
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
