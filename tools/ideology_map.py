"""Doomsday 2026 ideologies. Parent token = ruling_party; type = leader ideology."""

from __future__ import annotations

# (token, type, loc name, type loc, noun, color RGB, rules_kind, icon family)
# rules_kind: elected / illiberal / authoritarian / far_left / far_right
IDEOLOGIES: list[tuple] = [
    ("social_democracy", "social_democrat", "Social Democracy", "Social Democracy", "Social Democrats", (220, 50, 90), "elected", "democratic"),
    ("social_liberalism", "social_liberal", "Social Liberalism", "Social Liberalism", "Social Liberals", (255, 200, 40), "elected", "democratic"),
    ("liberal_conservatism", "liberal_conservative", "Liberal Conservatism", "Liberal Conservatism", "Liberal Conservatives", (30, 70, 180), "elected", "democratic"),
    ("progressive_populism", "progressive_populist", "Progressive Populism", "Progressive Populism", "Progressive Populists", (0, 160, 150), "elected", "democratic"),
    ("national_populism", "national_populist", "National Populism", "National Populism", "National Populists", (150, 75, 25), "illiberal", "fascism"),
    ("sovereign_democracy", "oligarch", "Sovereign Democracy", "Oligarchy", "Sovereign Democrats", (90, 90, 100), "authoritarian", "neutrality"),
    ("military_junta", "junta", "Military Junta", "Military Junta", "Junta", (70, 90, 45), "authoritarian", "neutrality"),
    ("absolute_monarchy", "absolute_monarchist", "Absolute Monarchy", "Absolute Monarchy", "Monarchists", (150, 120, 40), "authoritarian", "neutrality"),
    ("state_socialism", "vanguardist", "State Socialism", "Vanguardism", "Vanguardists", (170, 30, 30), "far_left", "communism"),
    ("left_wing_nationalism", "left_nationalist", "Left-Wing Nationalism", "Left-Wing Nationalism", "Left Nationalists", (200, 80, 20), "far_left", "communism"),
    ("islamic_democracy", "islamic_democrat", "Islamic Democracy", "Islamic Democracy", "Islamic Democrats", (0, 120, 70), "elected", "democratic"),
    ("theocratic_absolutism", "theocrat", "Theocratic Absolutism", "Theocratic Absolutism", "Theocrats", (40, 80, 45), "authoritarian", "neutrality"),
    ("jihadist_fundamentalism", "jihadist", "Jihadist Fundamentalism", "Jihadist Fundamentalism", "Jihadists", (20, 45, 25), "far_right", "fascism"),
    ("democratic_confederalism", "confederalist", "Democratic Confederalism", "Democratic Confederalism", "Confederalists", (200, 70, 140), "elected", "democratic"),
    ("fascism", "fascism_ideology", "Fascism", "Fascism", "Fascists", (90, 50, 15), "far_right", "fascism"),
    ("communism", "marxism", "Communism", "Communism", "Communists", (80, 0, 8), "far_left", "communism"),
    ("technocracy", "technocrat", "Technocracy", "Technocracy", "Technocrats", (80, 140, 170), "authoritarian", "neutrality"),
    ("anarcho_communism", "anarcho_communist", "Anarcho-Communism", "Anarcho-Communism", "Anarcho-Communists", (120, 0, 0), "far_left", "anarchism"),
]

PARENTS = [row[0] for row in IDEOLOGIES]
TYPE_OF = {row[0]: row[1] for row in IDEOLOGIES}
KIND_OF = {row[0]: row[6] for row in IDEOLOGIES}
ELECTED_KINDS = {"elected", "illiberal"}

ELECTED = [p for p, k in KIND_OF.items() if k in ELECTED_KINDS]
AUTHORITARIAN = [p for p, k in KIND_OF.items() if k == "authoritarian"]
FAR_LEFT = [p for p, k in KIND_OF.items() if k == "far_left"]
FAR_RIGHT = [p for p, k in KIND_OF.items() if k == "far_right"]

FALLBACK = {
    ("democratic", "socialism"): "social_democracy",
    ("democratic", "liberalism"): "social_liberalism",
    ("democratic", "conservatism"): "liberal_conservatism",
    ("democratic", "populism"): "progressive_populism",
    ("communism", "marxism"): "state_socialism",
    ("communism", "stalinism"): "state_socialism",
    ("communism", "leninism"): "state_socialism",
    ("communism", "anarchist_communism"): "anarcho_communism",
    ("fascism", "fascism_ideology"): "fascism",
    ("fascism", "nazism"): "fascism",
    ("neutrality", "oligarchism"): "sovereign_democracy",
    ("neutrality", "despotism"): "military_junta",
    ("neutrality", "moderatism"): "liberal_conservatism",
    ("neutrality", "centrism"): "social_liberalism",
}

# 2026 start. Overrides beat FALLBACK.
TAG_IDEOLOGY = {
    "USA": "national_populism",
    "CHI": "state_socialism",
    "SOV": "sovereign_democracy",
    "RAJ": "national_populism",
    "ENG": "social_democracy",
    "FRA": "social_liberalism",
    "GER": "liberal_conservatism",
    "JAP": "liberal_conservatism",
    "ITA": "national_populism",
    "CAN": "social_liberalism",
    "KOR": "social_democracy",
    "DPK": "state_socialism",
    "BRA": "social_democracy",
    "MEX": "progressive_populism",
    "INS": "liberal_conservatism",
    "TUR": "national_populism",
    "SAU": "absolute_monarchy",
    "AST": "social_democracy",
    "SPR": "social_democracy",
    "POL": "liberal_conservatism",
    "HOL": "liberal_conservatism",
    "BEL": "liberal_conservatism",
    "SWE": "liberal_conservatism",
    "NOR": "social_democracy",
    "DEN": "social_democracy",
    "GRN": "social_democracy",
    "FIN": "liberal_conservatism",
    "SWI": "liberal_conservatism",
    "AUS": "liberal_conservatism",
    "IRE": "liberal_conservatism",
    "POR": "liberal_conservatism",
    "GRE": "liberal_conservatism",
    "CZE": "liberal_conservatism",
    "SLO": "national_populism",
    "HUN": "national_populism",
    "ROM": "liberal_conservatism",
    "BUL": "liberal_conservatism",
    "SER": "national_populism",
    "CRO": "liberal_conservatism",
    "SLV": "social_liberalism",
    "ALB": "social_democracy",
    "KOS": "left_wing_nationalism",
    "UKR": "social_liberalism",
    "BLR": "sovereign_democracy",
    "EST": "social_liberalism",
    "LAT": "liberal_conservatism",
    "LIT": "social_democracy",
    "MOL": "social_liberalism",
    "GEO": "sovereign_democracy",
    "ARM": "social_liberalism",
    "AZR": "sovereign_democracy",
    "KAZ": "sovereign_democracy",
    "UZB": "sovereign_democracy",
    "TMS": "sovereign_democracy",
    "KYR": "sovereign_democracy",
    "TAJ": "sovereign_democracy",
    "PAK": "islamic_democracy",
    "MAL": "islamic_democracy",
    "VIN": "state_socialism",
    "SNG": "technocracy",
    "FOR": "social_liberalism",
    "CAM": "sovereign_democracy",
    "LAO": "state_socialism",
    "NEP": "social_democracy",
    "SRL": "social_democracy",
    "AFG": "jihadist_fundamentalism",
    "PER": "theocratic_absolutism",
    "IRQ": "islamic_democracy",
    "SYR": "jihadist_fundamentalism",
    "ROJ": "democratic_confederalism",
    "HEZ": "theocratic_absolutism",
    "JOR": "absolute_monarchy",
    "ISR": "national_populism",
    "PAL": "sovereign_democracy",
    "HAM": "jihadist_fundamentalism",
    "EGY": "military_junta",
    "LNA": "military_junta",
    "TUN": "sovereign_democracy",
    "ALG": "sovereign_democracy",
    "MOR": "absolute_monarchy",
    "WES": "left_wing_nationalism",
    "SAF": "social_democracy",
    "SWZ": "absolute_monarchy",
    "ETH": "sovereign_democracy",
    "BRM": "military_junta",
    "NUG": "social_liberalism",
    "SIA": "progressive_populism",
    "PHI": "liberal_conservatism",
    "SHB": "jihadist_fundamentalism",
    "RWA": "sovereign_democracy",
    "UGA": "sovereign_democracy",
    "MLI": "military_junta",
    "NGR": "military_junta",
    "CHA": "military_junta",
    "VOL": "military_junta",
    "GNA": "military_junta",
    "GAB": "military_junta",
    "SUD": "military_junta",
    "RSF": "military_junta",
    "SSD": "military_junta",
    "SIO": "military_junta",
    "M23": "military_junta",
    "VEN": "left_wing_nationalism",
    "BOL": "left_wing_nationalism",
    "NIC": "left_wing_nationalism",
    "CUB": "state_socialism",
    "UAE": "absolute_monarchy",
    "QAT": "absolute_monarchy",
    "KUW": "absolute_monarchy",
    "OMA": "absolute_monarchy",
    "BHR": "absolute_monarchy",
    "BRN": "absolute_monarchy",
    "HOU": "theocratic_absolutism",
    "ARG": "liberal_conservatism",
    "CHL": "social_democracy",
    "COL": "progressive_populism",
    "ELS": "national_populism",
    "HON": "progressive_populism",
    "URG": "social_democracy",
    "GHA": "social_democracy",
    "SEN": "progressive_populism",
    "ICE": "social_democracy",
    "NZL": "liberal_conservatism",
    "CMR": "sovereign_democracy",
    "RCG": "sovereign_democracy",
    "EQG": "sovereign_democracy",
    "TOG": "sovereign_democracy",
    "ERI": "sovereign_democracy",
    "ZIM": "sovereign_democracy",
    "ANG": "sovereign_democracy",
    "COG": "social_liberalism",
    "NGA": "liberal_conservatism",
    "LBA": "sovereign_democracy",
    "YEM": "sovereign_democracy",
    "PMR": "sovereign_democracy",
    "ABK": "sovereign_democracy",
    "SOE": "sovereign_democracy",
}

OPP_DEM = "liberal_conservatism"
OPP_COM = "communism"
OPP_FAS = "fascism"
OPP_NEU = "sovereign_democracy"


def resolve(tag: str, old_ideology: str = "", old_sub: str = "") -> str:
    tag = (tag or "").upper()
    if tag in TAG_IDEOLOGY:
        return TAG_IDEOLOGY[tag]
    if old_ideology in TYPE_OF:
        return old_ideology
    mapped = FALLBACK.get((old_ideology, old_sub))
    if mapped:
        return mapped
    if old_ideology == "democratic":
        return "liberal_conservatism"
    if old_ideology == "communism":
        return "state_socialism"
    if old_ideology == "fascism":
        return "fascism"
    return "sovereign_democracy"


def popularities(ruling: str, dem: int, com: int, fas: int, neu: int) -> dict[str, int]:
    pops = {
        OPP_DEM: dem,
        OPP_COM: com,
        OPP_FAS: fas,
        OPP_NEU: neu,
    }
    if ruling not in pops:
        donor = max(pops, key=pops.get)
        pops[ruling] = pops.pop(donor)
    total = sum(pops.values())
    if total != 100 and total > 0:
        gap = 100 - total
        pops[ruling] = pops.get(ruling, 0) + gap
    if ruling == "state_socialism":
        share = pops.get("state_socialism", 0)
        if share >= 20:
            remnant = max(5, share // 8)
            pops["state_socialism"] = share - remnant
            pops[OPP_COM] = pops.get(OPP_COM, 0) + remnant
    pops = {k: v for k, v in pops.items() if v > 0}
    if ruling not in pops:
        pops[ruling] = 100
    return pops
