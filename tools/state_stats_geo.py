"""Country ISO/WPP lookup, official subnational populations, and facility keywords.

Subnational figures are weights. allocate_state_stats.py scales each tag to its
control total so country sums stay on UN WPP / World Bank / IRENA / UNCTAD.
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

VANILLA_LOC = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV"
    r"\localisation\english\state_names_l_english.yml"
)

from state_stats_manual import HOI4_ISO2, MANUAL_POP  # noqa: E402

# HOI4 tag -> UN WPP 2026 area name(s) and ISO3 for World Bank.
TAG_META: dict[str, dict] = {
    "USA": {"iso3": "USA", "wpp": ["United States of America"], "irena": ["United States of America"], "unctad": "United States of America", "ei": "United States of America", "steel": "United States of America"},
    "CHI": {"iso3": "CHN", "wpp": ["China"], "irena": ["China"], "unctad": "China", "ei": "China", "steel": "China"},
    "SOV": {"iso3": "RUS", "wpp": ["Russian Federation"], "irena": ["Russian Federation"], "unctad": "Russian Federation", "ei": "Russian Federation", "steel": "Russian Federation"},
    "RAJ": {"iso3": "IND", "wpp": ["India"], "irena": ["India"], "unctad": "India", "ei": "India", "steel": "India"},
    "ENG": {"iso3": "GBR", "wpp": ["United Kingdom"], "irena": ["United Kingdom"], "unctad": "United Kingdom", "ei": "United Kingdom", "steel": "United Kingdom"},
    "FRA": {"iso3": "FRA", "wpp": ["France"], "irena": ["France"], "unctad": "France", "ei": "France", "steel": "France"},
    "GER": {"iso3": "DEU", "wpp": ["Germany"], "irena": ["Germany"], "unctad": "Germany", "ei": "Germany", "steel": "Germany"},
    "JAP": {"iso3": "JPN", "wpp": ["Japan"], "irena": ["Japan"], "unctad": "Japan", "ei": "Japan", "steel": "Japan"},
    "ITA": {"iso3": "ITA", "wpp": ["Italy"], "irena": ["Italy"], "unctad": "Italy", "ei": "Italy", "steel": "Italy"},
    "CAN": {"iso3": "CAN", "wpp": ["Canada"], "irena": ["Canada"], "unctad": "Canada", "ei": "Canada", "steel": "Canada"},
    "KOR": {"iso3": "KOR", "wpp": ["Republic of Korea"], "irena": ["Republic of Korea", "Korea, Republic of"], "unctad": "Republic of Korea", "ei": "Republic of Korea", "steel": "Republic of Korea"},
    "DPK": {"iso3": "PRK", "wpp": ["Dem. People's Republic of Korea"], "irena": ["Dem. People's Republic of Korea"], "unctad": "", "ei": "Dem. People's Republic of Korea", "steel": "Dem. People's Republic of Korea"},
    "BRA": {"iso3": "BRA", "wpp": ["Brazil"], "irena": ["Brazil"], "unctad": "Brazil", "ei": "Brazil", "steel": "Brazil"},
    "MEX": {"iso3": "MEX", "wpp": ["Mexico"], "irena": ["Mexico"], "unctad": "Mexico", "ei": "Mexico", "steel": "Mexico"},
    "INS": {"iso3": "IDN", "wpp": ["Indonesia"], "irena": ["Indonesia"], "unctad": "", "ei": "Indonesia", "steel": "Indonesia"},
    "TUR": {"iso3": "TUR", "wpp": ["Türkiye"], "irena": ["Türkiye", "Turkey"], "unctad": "Turkey", "ei": "Turkey", "steel": "Turkey"},
    "SAU": {"iso3": "SAU", "wpp": ["Saudi Arabia"], "irena": ["Saudi Arabia"], "unctad": "", "ei": "Saudi Arabia", "steel": "Saudi Arabia"},
    "AST": {"iso3": "AUS", "wpp": ["Australia"], "irena": ["Australia"], "unctad": "", "ei": "Australia", "steel": "Australia"},
    "SPR": {"iso3": "ESP", "wpp": ["Spain"], "irena": ["Spain"], "unctad": "Spain", "ei": "Spain", "steel": "Spain"},
    "POL": {"iso3": "POL", "wpp": ["Poland"], "irena": ["Poland"], "unctad": "Poland", "ei": "Poland", "steel": "Poland"},
    "HOL": {"iso3": "NLD", "wpp": ["Netherlands"], "irena": ["Netherlands"], "unctad": "Netherlands", "ei": "Netherlands", "steel": "Netherlands"},
    "BEL": {"iso3": "BEL", "wpp": ["Belgium"], "irena": ["Belgium"], "unctad": "Belgium", "ei": "Belgium", "steel": "Belgium"},
    "SWE": {"iso3": "SWE", "wpp": ["Sweden"], "irena": ["Sweden"], "unctad": "", "ei": "Sweden", "steel": "Sweden"},
    "NOR": {"iso3": "NOR", "wpp": ["Norway"], "irena": ["Norway"], "unctad": "Norway", "ei": "Norway", "steel": "Norway"},
    "DEN": {"iso3": "DNK", "wpp": ["Denmark"], "irena": ["Denmark"], "unctad": "", "ei": "Denmark", "steel": "Denmark"},
    "GRN": {"iso3": "GRL", "wpp": ["Greenland"], "irena": ["Greenland"], "unctad": "", "ei": "", "steel": ""},
    "FIN": {"iso3": "FIN", "wpp": ["Finland"], "irena": ["Finland"], "unctad": "Finland", "ei": "Finland", "steel": "Finland"},
    "SWI": {"iso3": "CHE", "wpp": ["Switzerland"], "irena": ["Switzerland"], "unctad": "", "ei": "Switzerland", "steel": "Switzerland"},
    "AUS": {"iso3": "AUT", "wpp": ["Austria"], "irena": ["Austria"], "unctad": "", "ei": "Austria", "steel": "Austria"},
    "IRE": {"iso3": "IRL", "wpp": ["Ireland"], "irena": ["Ireland"], "unctad": "", "ei": "Ireland", "steel": "Ireland"},
    "POR": {"iso3": "PRT", "wpp": ["Portugal"], "irena": ["Portugal"], "unctad": "", "ei": "Portugal", "steel": "Portugal"},
    "GRE": {"iso3": "GRC", "wpp": ["Greece"], "irena": ["Greece"], "unctad": "", "ei": "Greece", "steel": "Greece"},
    "CZE": {"iso3": "CZE", "wpp": ["Czechia"], "irena": ["Czechia"], "unctad": "", "ei": "Czechia", "steel": "Czechia"},
    "SLO": {"iso3": "SVK", "wpp": ["Slovakia"], "irena": ["Slovakia"], "unctad": "", "ei": "Slovakia", "steel": "Slovakia"},
    "HUN": {"iso3": "HUN", "wpp": ["Hungary"], "irena": ["Hungary"], "unctad": "", "ei": "Hungary", "steel": "Hungary"},
    "ROM": {"iso3": "ROU", "wpp": ["Romania"], "irena": ["Romania"], "unctad": "Romania", "ei": "Romania", "steel": "Romania"},
    "BUL": {"iso3": "BGR", "wpp": ["Bulgaria"], "irena": ["Bulgaria"], "unctad": "", "ei": "Bulgaria", "steel": "Bulgaria"},
    "SER": {"iso3": "SRB", "wpp": ["Serbia"], "irena": ["Serbia"], "unctad": "", "ei": "Serbia", "steel": "Serbia"},
    "CRO": {"iso3": "HRV", "wpp": ["Croatia"], "irena": ["Croatia"], "unctad": "Croatia", "ei": "Croatia", "steel": "Croatia"},
    "SLV": {"iso3": "SVN", "wpp": ["Slovenia"], "irena": ["Slovenia"], "unctad": "", "ei": "Slovenia", "steel": "Slovenia"},
    "BOS": {"iso3": "BIH", "wpp": ["Bosnia and Herzegovina"], "irena": ["Bosnia and Herzegovina"], "unctad": "", "ei": "", "steel": ""},
    "MAC": {"iso3": "MKD", "wpp": ["North Macedonia"], "irena": ["North Macedonia"], "unctad": "", "ei": "", "steel": ""},
    "ALB": {"iso3": "ALB", "wpp": ["Albania"], "irena": ["Albania"], "unctad": "", "ei": "Albania", "steel": ""},
    "MNT": {"iso3": "MNE", "wpp": ["Montenegro"], "irena": ["Montenegro"], "unctad": "", "ei": "", "steel": ""},
    "KOS": {"iso3": "XKX", "wpp": ["Kosovo (under UNSC res. 1244)"], "irena": [], "unctad": "", "ei": "Kosovo (under UNSC res. 1244)", "steel": ""},
    "UKR": {"iso3": "UKR", "wpp": ["Ukraine"], "irena": ["Ukraine"], "unctad": "", "ei": "Ukraine", "steel": "Ukraine"},
    "BLR": {"iso3": "BLR", "wpp": ["Belarus"], "irena": ["Belarus"], "unctad": "", "ei": "Belarus", "steel": "Belarus"},
    "EST": {"iso3": "EST", "wpp": ["Estonia"], "irena": ["Estonia"], "unctad": "", "ei": "Estonia", "steel": ""},
    "LAT": {"iso3": "LVA", "wpp": ["Latvia"], "irena": ["Latvia"], "unctad": "", "ei": "Latvia", "steel": ""},
    "LIT": {"iso3": "LTU", "wpp": ["Lithuania"], "irena": ["Lithuania"], "unctad": "", "ei": "Lithuania", "steel": ""},
    "MOL": {"iso3": "MDA", "wpp": ["Republic of Moldova"], "irena": ["Moldova"], "unctad": "", "ei": "Moldova", "steel": ""},
    "GEO": {"iso3": "GEO", "wpp": ["Georgia"], "irena": ["Georgia"], "unctad": "", "ei": "Georgia", "steel": "Georgia"},
    "ARM": {"iso3": "ARM", "wpp": ["Armenia"], "irena": ["Armenia"], "unctad": "", "ei": "Armenia", "steel": ""},
    "AZR": {"iso3": "AZE", "wpp": ["Azerbaijan"], "irena": ["Azerbaijan"], "unctad": "", "ei": "Azerbaijan", "steel": "Azerbaijan"},
    "KAZ": {"iso3": "KAZ", "wpp": ["Kazakhstan"], "irena": ["Kazakhstan"], "unctad": "", "ei": "Kazakhstan", "steel": "Kazakhstan"},
    "UZB": {"iso3": "UZB", "wpp": ["Uzbekistan"], "irena": ["Uzbekistan"], "unctad": "", "ei": "Uzbekistan", "steel": "Uzbekistan"},
    "TMS": {"iso3": "TKM", "wpp": ["Turkmenistan"], "irena": [], "unctad": "", "ei": "Turkmenistan", "steel": ""},
    "KYR": {"iso3": "KGZ", "wpp": ["Kyrgyzstan"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "TAJ": {"iso3": "TJK", "wpp": ["Tajikistan"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "MON": {"iso3": "MNG", "wpp": ["Mongolia"], "irena": ["Mongolia"], "unctad": "", "ei": "Mongolia", "steel": ""},
    "PAK": {"iso3": "PAK", "wpp": ["Pakistan"], "irena": ["Pakistan"], "unctad": "", "ei": "Pakistan", "steel": "Pakistan"},
    "BAN": {"iso3": "BGD", "wpp": ["Bangladesh"], "irena": ["Bangladesh"], "unctad": "", "ei": "", "steel": "Bangladesh"},
    "BRM": {"iso3": "MMR", "wpp": ["Myanmar"], "irena": ["Myanmar"], "unctad": "", "ei": "", "steel": "Myanmar"},
    "SIA": {"iso3": "THA", "wpp": ["Thailand"], "irena": ["Thailand"], "unctad": "", "ei": "Thailand", "steel": "Thailand"},
    "MAL": {"iso3": "MYS", "wpp": ["Malaysia"], "irena": ["Malaysia"], "unctad": "", "ei": "Malaysia", "steel": "Malaysia"},
    "VIN": {"iso3": "VNM", "wpp": ["Viet Nam"], "irena": ["Viet Nam"], "unctad": "Viet Nam", "ei": "Viet Nam", "steel": "Viet Nam"},
    "PHI": {"iso3": "PHL", "wpp": ["Philippines"], "irena": ["Philippines"], "unctad": "Philippines", "ei": "Philippines", "steel": "Philippines"},
    "SNG": {"iso3": "SGP", "wpp": ["Singapore"], "irena": ["Singapore"], "unctad": "", "ei": "Singapore", "steel": "Singapore"},
    "FOR": {"iso3": "TWN", "wpp": ["China, Taiwan Province of China"], "irena": ["Taiwan", "China, Taiwan Province of China"], "unctad": "", "ei": "", "steel": "Taiwan"},
    "CAM": {"iso3": "KHM", "wpp": ["Cambodia"], "irena": ["Cambodia"], "unctad": "", "ei": "", "steel": "Cambodia"},
    "LAO": {"iso3": "LAO", "wpp": ["Lao People's Democratic Republic"], "irena": ["Lao People's Democratic Republic"], "unctad": "", "ei": "Lao People's Democratic Republic", "steel": ""},
    "NEP": {"iso3": "NPL", "wpp": ["Nepal"], "irena": ["Nepal"], "unctad": "", "ei": "", "steel": ""},
    "BHU": {"iso3": "BTN", "wpp": ["Bhutan"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "SRL": {"iso3": "LKA", "wpp": ["Sri Lanka"], "irena": ["Sri Lanka"], "unctad": "", "ei": "", "steel": "Sri Lanka"},
    "AFG": {"iso3": "AFG", "wpp": ["Afghanistan"], "irena": ["Afghanistan"], "unctad": "", "ei": "", "steel": ""},
    "PER": {"iso3": "IRN", "wpp": ["Iran (Islamic Republic of)"], "irena": ["Iran (Islamic Republic of)"], "unctad": "", "ei": "Iran (Islamic Republic of)", "steel": "Iran (Islamic Republic of)"},
    "IRQ": {"iso3": "IRQ", "wpp": ["Iraq"], "irena": ["Iraq"], "unctad": "", "ei": "Iraq", "steel": "Iraq"},
    "SYR": {"iso3": "SYR", "wpp": ["Syrian Arab Republic"], "irena": [], "unctad": "", "ei": "Syrian Arab Republic", "steel": ""},
    "LEB": {"iso3": "LBN", "wpp": ["Lebanon"], "irena": ["Lebanon"], "unctad": "", "ei": "Lebanon", "steel": ""},
    "JOR": {"iso3": "JOR", "wpp": ["Jordan"], "irena": ["Jordan"], "unctad": "", "ei": "Jordan", "steel": ""},
    "ISR": {"iso3": "ISR", "wpp": ["Israel"], "irena": ["Israel"], "unctad": "", "ei": "Israel", "steel": ""},
    "EGY": {"iso3": "EGY", "wpp": ["Egypt"], "irena": ["Egypt"], "unctad": "", "ei": "Egypt", "steel": "Egypt"},
    "TUN": {"iso3": "TUN", "wpp": ["Tunisia"], "irena": ["Tunisia"], "unctad": "", "ei": "Tunisia", "steel": "Tunisia"},
    "ALG": {"iso3": "DZA", "wpp": ["Algeria"], "irena": ["Algeria"], "unctad": "", "ei": "Algeria", "steel": "Algeria"},
    "MOR": {"iso3": "MAR", "wpp": ["Morocco"], "irena": ["Morocco"], "unctad": "", "ei": "Morocco", "steel": "Morocco"},
    "SAF": {"iso3": "ZAF", "wpp": ["South Africa"], "irena": ["South Africa"], "unctad": "", "ei": "South Africa", "steel": "South Africa"},
    "NGA": {"iso3": "NGA", "wpp": ["Nigeria"], "irena": ["Nigeria"], "unctad": "", "ei": "Nigeria", "steel": "Nigeria"},
    "ETH": {"iso3": "ETH", "wpp": ["Ethiopia"], "irena": ["Ethiopia"], "unctad": "", "ei": "", "steel": ""},
    "KEN": {"iso3": "KEN", "wpp": ["Kenya"], "irena": ["Kenya"], "unctad": "", "ei": "", "steel": "Kenya"},
    "GHA": {"iso3": "GHA", "wpp": ["Ghana"], "irena": ["Ghana"], "unctad": "", "ei": "Ghana", "steel": ""},
    "COG": {"iso3": "COD", "wpp": ["Democratic Republic of the Congo"], "irena": ["Democratic Republic of the Congo"], "unctad": "", "ei": "", "steel": ""},
    "ANG": {"iso3": "AGO", "wpp": ["Angola"], "irena": ["Angola"], "unctad": "", "ei": "Angola", "steel": ""},
    "MZB": {"iso3": "MOZ", "wpp": ["Mozambique"], "irena": ["Mozambique"], "unctad": "", "ei": "", "steel": ""},
    "ZIM": {"iso3": "ZWE", "wpp": ["Zimbabwe"], "irena": ["Zimbabwe"], "unctad": "", "ei": "", "steel": ""},
    "SUD": {"iso3": "SDN", "wpp": ["Sudan"], "irena": ["Sudan"], "unctad": "", "ei": "", "steel": ""},
    "SSD": {"iso3": "SSD", "wpp": ["South Sudan"], "irena": [], "unctad": "", "ei": "South Sudan", "steel": ""},
    "SOM": {"iso3": "SOM", "wpp": ["Somalia"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "UGA": {"iso3": "UGA", "wpp": ["Uganda"], "irena": ["Uganda"], "unctad": "", "ei": "", "steel": ""},
    "TZN": {"iso3": "TZA", "wpp": ["United Republic of Tanzania"], "irena": ["Tanzania"], "unctad": "", "ei": "", "steel": ""},
    "RWA": {"iso3": "RWA", "wpp": ["Rwanda"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "SEN": {"iso3": "SEN", "wpp": ["Senegal"], "irena": ["Senegal"], "unctad": "", "ei": "", "steel": ""},
    "IVO": {"iso3": "CIV", "wpp": ["Côte d'Ivoire"], "irena": ["Côte d'Ivoire"], "unctad": "", "ei": "", "steel": ""},
    "CMR": {"iso3": "CMR", "wpp": ["Cameroon"], "irena": ["Cameroon"], "unctad": "", "ei": "Cameroon", "steel": ""},
    "MLI": {"iso3": "MLI", "wpp": ["Mali"], "irena": ["Mali"], "unctad": "", "ei": "", "steel": ""},
    "NGR": {"iso3": "NER", "wpp": ["Niger"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "CHA": {"iso3": "TCD", "wpp": ["Chad"], "irena": [], "unctad": "", "ei": "Chad", "steel": ""},
    "ARG": {"iso3": "ARG", "wpp": ["Argentina"], "irena": ["Argentina"], "unctad": "", "ei": "Argentina", "steel": "Argentina"},
    "CHL": {"iso3": "CHL", "wpp": ["Chile"], "irena": ["Chile"], "unctad": "", "ei": "Chile", "steel": "Chile"},
    "COL": {"iso3": "COL", "wpp": ["Colombia"], "irena": ["Colombia"], "unctad": "", "ei": "Colombia", "steel": "Colombia"},
    "PRU": {"iso3": "PER", "wpp": ["Peru"], "irena": ["Peru"], "unctad": "", "ei": "Peru", "steel": "Peru"},
    "VEN": {"iso3": "VEN", "wpp": ["Venezuela (Bolivarian Republic of)"], "irena": ["Venezuela (Bolivarian Republic of)"], "unctad": "", "ei": "Venezuela (Bolivarian Republic of)", "steel": "Venezuela (Bolivarian Republic of)"},
    "BOL": {"iso3": "BOL", "wpp": ["Bolivia (Plurinational State of)"], "irena": ["Bolivia (Plurinational State of)"], "unctad": "", "ei": "Bolivia (Plurinational State of)", "steel": ""},
    "ECU": {"iso3": "ECU", "wpp": ["Ecuador"], "irena": ["Ecuador"], "unctad": "", "ei": "Ecuador", "steel": ""},
    "URG": {"iso3": "URY", "wpp": ["Uruguay"], "irena": ["Uruguay"], "unctad": "", "ei": "", "steel": ""},
    "PAR": {"iso3": "PRY", "wpp": ["Paraguay"], "irena": ["Paraguay"], "unctad": "", "ei": "", "steel": ""},
    "CUB": {"iso3": "CUB", "wpp": ["Cuba"], "irena": ["Cuba"], "unctad": "", "ei": "", "steel": ""},
    "DOM": {"iso3": "DOM", "wpp": ["Dominican Republic"], "irena": ["Dominican Republic"], "unctad": "", "ei": "", "steel": ""},
    "HAI": {"iso3": "HTI", "wpp": ["Haiti"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "PAN": {"iso3": "PAN", "wpp": ["Panama"], "irena": ["Panama"], "unctad": "", "ei": "", "steel": ""},
    "COS": {"iso3": "CRI", "wpp": ["Costa Rica"], "irena": ["Costa Rica"], "unctad": "", "ei": "", "steel": ""},
    "GUA": {"iso3": "GTM", "wpp": ["Guatemala"], "irena": ["Guatemala"], "unctad": "", "ei": "", "steel": ""},
    "HON": {"iso3": "HND", "wpp": ["Honduras"], "irena": ["Honduras"], "unctad": "", "ei": "", "steel": ""},
    "NIC": {"iso3": "NIC", "wpp": ["Nicaragua"], "irena": ["Nicaragua"], "unctad": "", "ei": "", "steel": ""},
    "ELS": {"iso3": "SLV", "wpp": ["El Salvador"], "irena": ["El Salvador"], "unctad": "", "ei": "", "steel": ""},
    "ICE": {"iso3": "ISL", "wpp": ["Iceland"], "irena": ["Iceland"], "unctad": "", "ei": "Iceland", "steel": ""},
    "LUX": {"iso3": "LUX", "wpp": ["Luxembourg"], "irena": ["Luxembourg"], "unctad": "", "ei": "Luxembourg", "steel": "Luxembourg"},
    "MLT": {"iso3": "MLT", "wpp": ["Malta"], "irena": ["Malta"], "unctad": "", "ei": "", "steel": ""},
    "CYP": {"iso3": "CYP", "wpp": ["Cyprus"], "irena": ["Cyprus"], "unctad": "", "ei": "Cyprus", "steel": ""},
    "UAE": {"iso3": "ARE", "wpp": ["United Arab Emirates"], "irena": ["United Arab Emirates"], "unctad": "", "ei": "United Arab Emirates", "steel": "United Arab Emirates"},
    "QAT": {"iso3": "QAT", "wpp": ["Qatar"], "irena": ["Qatar"], "unctad": "", "ei": "Qatar", "steel": "Qatar"},
    "KUW": {"iso3": "KWT", "wpp": ["Kuwait"], "irena": ["Kuwait"], "unctad": "", "ei": "Kuwait", "steel": ""},
    "OMA": {"iso3": "OMN", "wpp": ["Oman"], "irena": ["Oman"], "unctad": "", "ei": "Oman", "steel": "Oman"},
    "BHR": {"iso3": "BHR", "wpp": ["Bahrain"], "irena": ["Bahrain"], "unctad": "", "ei": "Bahrain", "steel": ""},
    "NZL": {"iso3": "NZL", "wpp": ["New Zealand"], "irena": ["New Zealand"], "unctad": "", "ei": "New Zealand", "steel": "New Zealand"},
    "PNG": {"iso3": "PNG", "wpp": ["Papua New Guinea"], "irena": ["Papua New Guinea"], "unctad": "", "ei": "Papua New Guinea", "steel": ""},
    "FIJ": {"iso3": "FJI", "wpp": ["Fiji"], "irena": ["Fiji"], "unctad": "", "ei": "", "steel": ""},
    "LIB": {"iso3": "LBR", "wpp": ["Liberia"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "SIE": {"iso3": "SLE", "wpp": ["Sierra Leone"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "GNA": {"iso3": "GIN", "wpp": ["Guinea"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "GNB": {"iso3": "GNB", "wpp": ["Guinea-Bissau"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "GAM": {"iso3": "GMB", "wpp": ["Gambia"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "MRT": {"iso3": "MRT", "wpp": ["Mauritania"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "NMB": {"iso3": "NAM", "wpp": ["Namibia"], "irena": ["Namibia"], "unctad": "", "ei": "", "steel": ""},
    "BOT": {"iso3": "BWA", "wpp": ["Botswana"], "irena": ["Botswana"], "unctad": "", "ei": "", "steel": ""},
    "ZAM": {"iso3": "ZMB", "wpp": ["Zambia"], "irena": ["Zambia"], "unctad": "", "ei": "", "steel": ""},
    "MLW": {"iso3": "MWI", "wpp": ["Malawi"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "MAD": {"iso3": "MDG", "wpp": ["Madagascar"], "irena": ["Madagascar"], "unctad": "", "ei": "", "steel": ""},
    "GAB": {"iso3": "GAB", "wpp": ["Gabon"], "irena": [], "unctad": "", "ei": "Gabon", "steel": ""},
    "RCG": {"iso3": "COG", "wpp": ["Congo"], "irena": [], "unctad": "", "ei": "Congo", "steel": ""},
    "CAR": {"iso3": "CAF", "wpp": ["Central African Republic"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "EQG": {"iso3": "GNQ", "wpp": ["Equatorial Guinea"], "irena": [], "unctad": "", "ei": "Equatorial Guinea", "steel": ""},
    "TOG": {"iso3": "TGO", "wpp": ["Togo"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "DAH": {"iso3": "BEN", "wpp": ["Benin"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "VOL": {"iso3": "BFA", "wpp": ["Burkina Faso"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "ERI": {"iso3": "ERI", "wpp": ["Eritrea"], "irena": [], "unctad": "", "ei": "Eritrea", "steel": ""},
    "DJI": {"iso3": "DJI", "wpp": ["Djibouti"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "BRD": {"iso3": "BDI", "wpp": ["Burundi"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "TML": {"iso3": "TLS", "wpp": ["Timor-Leste"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "BRN": {"iso3": "BRN", "wpp": ["Brunei Darussalam"], "irena": [], "unctad": "", "ei": "Brunei Darussalam", "steel": ""},
    "MLD": {"iso3": "MDV", "wpp": ["Maldives"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "BAH": {"iso3": "BHS", "wpp": ["Bahamas"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "JAM": {"iso3": "JAM", "wpp": ["Jamaica"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "GYA": {"iso3": "GUY", "wpp": ["Guyana"], "irena": ["Guyana"], "unctad": "", "ei": "Guyana", "steel": ""},
    "BLZ": {"iso3": "BLZ", "wpp": ["Belize"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "TRI": {"iso3": "TTO", "wpp": ["Trinidad and Tobago"], "irena": [], "unctad": "", "ei": "Trinidad and Tobago", "steel": ""},
    "ATG": {"iso3": "ATG", "wpp": ["Antigua and Barbuda"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "DMA": {"iso3": "DMA", "wpp": ["Dominica"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "STL": {"iso3": "LCA", "wpp": ["Saint Lucia"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "SVG": {"iso3": "VCT", "wpp": ["Saint Vincent and the Grenadines"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "GND": {"iso3": "GRD", "wpp": ["Grenada"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "BRB": {"iso3": "BRB", "wpp": ["Barbados"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "SUR": {"iso3": "SUR", "wpp": ["Suriname"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "CBV": {"iso3": "CPV", "wpp": ["Cabo Verde"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "KIR": {"iso3": "KIR", "wpp": ["Kiribati"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "TUV": {"iso3": "TUV", "wpp": ["Tuvalu"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "NAU": {"iso3": "NRU", "wpp": ["Nauru"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "MHL": {"iso3": "MHL", "wpp": ["Marshall Islands"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "MAU": {"iso3": "MUS", "wpp": ["Mauritius"], "irena": ["Mauritius"], "unctad": "", "ei": "", "steel": ""},
    "COM": {"iso3": "COM", "wpp": ["Comoros"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "STP": {"iso3": "STP", "wpp": ["Sao Tome and Principe"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "SEY": {"iso3": "SYC", "wpp": ["Seychelles"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "LES": {"iso3": "LSO", "wpp": ["Lesotho"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "SWZ": {"iso3": "SWZ", "wpp": ["Eswatini"], "irena": [], "unctad": "", "ei": "Eswatini", "steel": ""},
    "WES": {"iso3": "", "wpp": ["Western Sahara"], "irena": [], "unctad": "", "ei": "", "steel": ""},
    "PAL": {"iso3": "", "wpp": ["State of Palestine"], "irena": [], "unctad": "", "ei": "", "steel": ""},
}

# Tags that together make one UN country: split WPP by existing CSV pop shares.
WPP_GROUPS: dict[str, list[str]] = {
    "Libya": ["LBA", "LNA"],
    "Yemen": ["YEM", "HOU", "YNR", "STC"],
    "Syrian Arab Republic": ["SYR", "ROJ", "DRZ", "SNA"],
    "Myanmar": ["BRM", "NUG"],
    "Sudan": ["SUD", "RSF"],
    "South Sudan": ["SSD", "SIO"],
    "Somalia": ["SOM", "SML", "PNT", "JUB", "SHB"],
    "Mali": ["MLI", "AZA"],
    "Democratic Republic of the Congo": ["COG", "M23"],
    "State of Palestine": ["PAL", "HAM"],
    "Afghanistan": ["AFG", "NRF"],
    "Iraq": ["IRQ", "KUR"],
    "Cyprus": ["CYP", "NCY"],
    "Georgia": ["GEO", "ABK", "SOE"],
    "Republic of Moldova": ["MOL", "PMR"],
    "Lebanon": ["LEB", "HEZ"],
}

# US Census Bureau Vintage 2024 state resident population (July 1, 2024).
# New England is the HOI4 combined state (ME+NH+VT+MA+RI+CT). Maryland includes DC.
US_CENSUS_2024 = {
    "california": 39431263,
    "texas": 31290831,
    "florida": 23372215,
    "newyork": 19867314,
    "pennsylvania": 13078751,
    "illinois": 12693575,
    "ohio": 11883304,
    "georgia": 11180878,
    "northcarolina": 11046024,
    "michigan": 10083783,
    "newjersey": 9500851,
    "virginia": 8811195,
    "washington": 7952791,
    "arizona": 7582384,
    "tennessee": 7204002,
    "tennesse": 7204002,
    "massachusetts": 7114283,
    "indiana": 6924275,
    "missouri": 6215144,
    "maryland": 6965470,  # MD + DC
    "wisconsin": 5931367,
    "colorado": 5957615,
    "minnesota": 5778348,
    "southcarolina": 5478831,
    "alabama": 5143033,
    "louisiana": 4573749,
    "kentucky": 4584297,
    "oregon": 4272371,
    "oklahoma": 4108103,
    "connecticut": 3644883,
    "utah": 3454232,
    "iowa": 3219171,
    "nevada": 3267467,
    "arkansas": 3089060,
    "kansas": 2944376,
    "mississippi": 2941991,
    "newmexico": 2130256,
    "nebraska": 2001176,
    "idaho": 2001619,
    "westvirginia": 1766107,
    "hawaii": 1434697,
    "newhampshire": 1409032,
    "maine": 1402106,
    "montana": 1137233,
    "rhodeisland": 1106341,
    "delaware": 1044321,
    "southdakota": 924669,
    "northdakota": 788940,
    "alaska": 733536,
    "vermont": 647464,
    "wyoming": 587618,
    "newengland": 15324109,
    "puertorico": 3205691,
    "guam": 170185,
    "americansamoa": 45319,
    "usvirginislands": 83400,
    "saipan": 42914,
}

# China NBS 2023 year-end population (persons), municipalities included.
CN_NBS_2023 = {
    "guangdong": 127133000,
    "guangzhou": 127133000,
    "shandong": 101232800,
    "jinan": 101232800,
    "qingdao": 101232800,
    "henan": 98150000,
    "jiangsu": 85260000,
    "jiansu": 85260000,
    "suzhou": 85260000,
    "nanjing": 85260000,
    "sichuan": 83680000,
    "chengdu": 83680000,
    "liangshan": 83680000,
    "hebei": 73930000,
    "hebeichahar": 73930000,
    "easthebei": 73930000,
    "hunan": 65683000,
    "changde": 65683000,
    "anhui": 61210000,
    "huangshan": 61210000,
    "hubei": 58300000,
    "wuhan": 58300000,
    "zhejiang": 66270000,
    "guangxi": 50127000,
    "guanxi": 50127000,
    "nanning": 50127000,
    "fangchenggang": 50127000,
    "yunnan": 46730000,
    "dalibai": 46730000,
    "jiangxi": 45150000,
    "liaoning": 41820000,
    "liaotung": 41820000,
    "dalian": 41820000,
    "fujian": 41870000,
    "shaanxi": 39520000,
    "xian": 39520000,
    "yanan": 39520000,
    "shaanbei": 39520000,
    "heilongjiang": 30499000,
    "heilungkiang": 30499000,
    "chuho": 30499000,
    "shanxi": 34660000,
    "guizhou": 38560000,
    "zunyi": 38560000,
    "chongqing": 31910000,
    "jilin": 23388000,
    "manchukuo": 23388000,
    "gansu": 24650000,
    "wuwei": 24650000,
    "yulin": 24650000,
    "guyuan": 24650000,
    "jiuquan": 24650000,
    "gannan": 24650000,
    "innermongolia": 24000000,
    "ordos": 24000000,
    "alxa": 24000000,
    "pailingmiao": 24000000,
    "hulunbuir": 24000000,
    "suiyuan": 24000000,
    "xilingol": 24000000,
    "chahar": 24000000,
    "jehol": 24000000,
    "xinjiang": 25980000,
    "sinkiang": 25980000,
    "urumqi": 25980000,
    "dzungaria": 25980000,
    "yarkand": 25980000,
    "khotan": 25980000,
    "dabancheng": 25980000,
    "kunlun": 25980000,
    "shanghai": 24870000,
    "beijing": 21840000,
    "beiping": 21840000,
    "tianjin": 13640000,
    "hainan": 10430000,
    "ningxia": 7290000,
    "qinghai": 5940000,
    "golog": 5940000,
    "haixi": 5940000,
    "tibet": 3650000,
    "shigatse": 3650000,
    "ngari": 3650000,
    "chamdo": 3650000,
    "hongkong": 7378602,
    "hongkong": 7378602,
    "macau": 723188,
    "guangzhouwan": 500000,
    "aksiachin": 20000,
    "aksaichin": 20000,
}

# India MoSPI / census projections ~2024, mapped onto HOI4 British-era states.
IN_POP = {
    "unitedprovinces": 252000000,  # UP + Uttarakhand
    "delhi": 22000000,
    "bombay": 128000000,  # Maharashtra
    "madras": 77000000,  # Tamil Nadu
    "madrasstates": 35000000,  # Kerala
    "calcutta": 100000000,  # West Bengal
    "bihar": 171000000,  # Bihar + Jharkhand
    "rajputana": 82000000,
    "hyderabad": 91000000,  # Telangana + inland AP remnant
    "mysore": 68000000,
    "orissa": 46000000,
    "assam": 50000000,
    "andrapradesh": 53000000,
    "westernindianstates": 72000000,  # Gujarat
    "centralprovinces": 117000000,  # MP + Chhattisgarh
    "centralindianprovinces": 20000000,
    "eastpunjab": 72000000,  # Punjab + Haryana + HP
    "kashmir": 13600000,
    "arunachalpradesh": 1600000,
    "goa": 1600000,
    "frenchindia": 1400000,
    "manipur": 3200000,
    "sikkim": 700000,
    "andaman": 400000,
    "deccanstates": 8000000,
    "bastar": 3000000,
    "gwalior": 15000000,
}

# ONS 2023 UK country/region approximations for HOI4 English states.
UK_POP = {
    "greaterlondonarea": 9800000,
    "sussex": 1800000,
    "southeastengland": 7400000,
    "westmidlands": 6000000,
    "eastmidlands": 4900000,
    "yorkshire": 5500000,
    "northernengland": 2700000,
    "northwestengland": 7500000,
    "eastanglia": 6400000,
    "cornwall": 570000,
    "gloucestershire": 900000,
    "wales": 3100000,
    "northernireland": 1910000,
    "scottishlowlands": 2200000,
    "scottishhighlands": 400000,
    "strathclyde": 1800000,
    "aberdeenshire": 580000,
    "cumbria": 500000,
    "shetland": 23000,
    "isleofman": 84000,
    "gibralter": 34000,
    "bermuda": 64000,
}

# Destatis 2023 Länder mapped onto HOI4 German states (shared keys split by area).
DE_POP = {
    "rhineland": 17900000,  # NRW west
    "moselland": 17900000,  # NRW
    "westfalen": 17900000,
    "baden": 11300000,
    "actualbaden": 11300000,
    "wuttemberg": 11300000,
    "oberbayern": 13400000,
    "bayreuth": 13400000,
    "nassau": 6300000,  # Hesse
    "weserems": 8100000,
    "osthannover": 8100000,
    "sudhannover": 8100000,
    "schleswigholstein": 3000000,
    "southschleswig": 3000000,
    "mecklenburg": 1600000,
    "pommern": 1600000,
    "brandenburg": 6300000,  # Berlin + BB
    "sachsen": 4000000,
}

# IBGE 2024 Brazilian state populations (approx).
BR_POP = {
    "saopaulo": 46000000,
    "saolpaulo": 46000000,
    "riodejaneiro": 17400000,
    "riodejanerio": 17400000,
    "minasgerais": 21000000,
    "bahia": 14800000,
    "parana": 11800000,
    "riograndedosul": 11200000,
    "riograndesul": 11200000,
    "pernambuco": 9500000,
    "ceara": 9200000,
    "para": 8600000,
    "maranhao": 7000000,
    "goias": 7200000,
    "amazonas": 4300000,
    "santacatarina": 8000000,
    "matogrosso": 3800000,
    "riogrande": 3600000,
    "iguacu": 2000000,
    "brazil": 21000000,  # leftover Minas/Centro
}

# Japan prefecture groups (MIC 2024).
JP_POP = {
    "kanto": 43000000,  # Tokyo metro / Kanto
    "osaka": 22000000,  # Keihanshin
    "nagoya": 10000000,  # Chubu
    "nagasaki": 13000000,  # Kyushu north
    "southkyushu": 4500000,
    "hiroshima": 7000000,  # Chugoku
    "tokushima": 3700000,  # Shikoku
    "niigata": 2200000,
    "nagano": 2000000,
    "akita": 2400000,  # Tohoku north
    "southtohoku": 5000000,
    "sanin": 1300000,
    "hokkaido": 5100000,
    "okinawa": 1460000,
}

# Korea: HOI4 has four coarse states. Figures are Wikidata P1082 on ISO 3166-2 units
# (tools/data/wikidata_admin1_pop.json), grouped to the map.
KR_POP = {
    "gyeonggi": 13103188 + 9668465 + 3049315,  # Gyeonggi + Seoul + Incheon
    "southkorea": 13103188 + 9668465 + 3049315,
    "gyeongsang": 3453198 + 3350350 + 2546960 + 2444412 + 1127553,  # Busan + S/N Gyeongsang + Daegu + Ulsan
    "chungcheongjeolla": 2181416 + 1790352 + 1769607 + 1595058 + 1490092 + 1475221 + 670837 + 391984,
    "chungcheong": 2181416 + 1790352 + 1769607 + 1595058 + 1490092 + 1475221 + 670837 + 391984,
    "jeolla": 2181416 + 1790352 + 1769607 + 1595058 + 1490092 + 1475221 + 670837 + 391984,
    "gangwon": 1539274,
}

ALIASES = {
    "beiping": "beijing",
    "peking": "beijing",
    "leningrad": "saintpetersburg",
    "leningradarea": "saintpetersburg",
    "stalingrad": "volgograd",
    "stalingradarea": "volgograd",
    "moscowarea": "moscow",
    "iledefrance": "iledefrance",
    "corsica": "corse",
    "greaterlondonarea": "greaterlondon",
}

# HOI4 states that span several GADM-1 units. Lookup takes the max VIIRS mean.
NTL_NAME_ALIASES = {
    "swissplateau": ["zurich", "bern", "aargau", "luzern", "zug", "geneve", "geneva", "basel"],
    "newengland": ["massachusetts", "connecticut", "rhodeisland"],
    "greaterlondonarea": ["greaterlondon", "london"],
    "southkorea": ["seoul", "gyeonggi"],
    "gyeonggi": ["seoul", "gyeonggi"],
    "kanto": ["tokyo", "kanagawa", "saitama", "chiba"],
    "kansai": ["osaka", "kyoto", "hyogo"],
    "osaka": ["osaka", "kyoto", "hyogo"],
    "southernontario": ["ontario"],
    "leinster": ["dublin"],
    "sjaelland": ["hovedstaden", "capitalregion", "sjaelland", "zealand"],
    "loweraustria": ["wien", "vienna", "niederosterreich"],
    "flanders": ["brussels", "bruxelles", "vlaanderen"],
    "sodermanland": ["stockholm"],
    "akmolinsk": ["astana", "akmola", "nur-sultan"],
    "easthebei": ["tianjin"],
    "hebei": ["tianjin"],
    "sussex": ["hampshire", "southampton", "south east"],
    "southeastengland": ["hampshire", "southampton"],
}


def norm_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = (
        text.replace("ł", "l")
        .replace("Ł", "l")
        .replace("đ", "d")
        .replace("ø", "o")
        .replace("Ø", "o")
        .replace("ß", "ss")
        .replace("æ", "ae")
        .replace("œ", "oe")
    )
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def load_state_loc_names(mod_root: Path) -> dict[int, str]:
    names: dict[int, str] = {}
    paths = [VANILLA_LOC]
    paths += list((mod_root / "localisation" / "english").glob("*.yml"))
    paths += list((mod_root / "localisation" / "replace").glob("*.yml"))
    key_re = re.compile(r"^\s*STATE_(\d+):(?:\d+)?\s*\"([^\"]+)\"", re.M)
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in key_re.finditer(text):
            names[int(m.group(1))] = m.group(2)
    return names


# Sub-state loc names that share one official admin population (split by map area).
CN_CANON = {
    "guangzhou": "guangdong",
    "fangchenggang": "guangxi",
    "nanning": "guangxi",
    "guanxi": "guangxi",
    "suzhou": "jiangsu",
    "nanjing": "jiangsu",
    "jiansu": "jiangsu",
    "jinan": "shandong",
    "qingdao": "shandong",
    "chengdu": "sichuan",
    "liangshan": "sichuan",
    "hebeichahar": "hebei",
    "easthebei": "hebei",
    "changde": "hunan",
    "huangshan": "anhui",
    "wuhan": "hubei",
    "xian": "shaanxi",
    "yanan": "shaanxi",
    "shaanbei": "shaanxi",
    "heilungkiang": "heilongjiang",
    "chuho": "heilongjiang",
    "liaotung": "liaoning",
    "dalian": "liaoning",
    "zunyi": "guizhou",
    "wuwei": "gansu",
    "yulin": "gansu",
    "guyuan": "gansu",
    "jiuquan": "gansu",
    "gannan": "gansu",
    "ordos": "innermongolia",
    "alxa": "innermongolia",
    "pailingmiao": "innermongolia",
    "hulunbuir": "innermongolia",
    "suiyuan": "innermongolia",
    "xilingol": "innermongolia",
    "chahar": "innermongolia",
    "jehol": "innermongolia",
    "sinkiang": "xinjiang",
    "urumqi": "xinjiang",
    "dzungaria": "xinjiang",
    "yarkand": "xinjiang",
    "khotan": "xinjiang",
    "dabancheng": "xinjiang",
    "kunlun": "xinjiang",
    "beiping": "beijing",
    "shigatse": "tibet",
    "ngari": "tibet",
    "chamdo": "tibet",
    "golog": "qinghai",
    "haixi": "qinghai",
    "manchukuo": "jilin",
}

DE_CANON = {
    "rhineland": "nrw",
    "moselland": "nrw",
    "westfalen": "nrw",
    "baden": "bw",
    "actualbaden": "bw",
    "wuttemberg": "bw",
    "oberbayern": "by",
    "bayreuth": "by",
    "weserems": "ni",
    "osthannover": "ni",
    "sudhannover": "ni",
    "schleswigholstein": "sh",
    "southschleswig": "sh",
    "mecklenburg": "mv",
    "pommern": "mv",
}


_WD_BY_ISO3: dict[str, list[dict]] | None = None


def _wikidata_admin1() -> dict[str, list[dict]]:
    """ISO 3166-2 rows from ingest. Empty dict if the snapshot is missing."""
    global _WD_BY_ISO3
    if _WD_BY_ISO3 is not None:
        return _WD_BY_ISO3
    path = Path(__file__).resolve().parent / "data" / "wikidata_admin1_pop.json"
    by: dict[str, list[dict]] = defaultdict(list)
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload.get("rows") or []:
                iso3 = (row.get("iso3") or "").strip()
                if iso3 and row.get("pop"):
                    by[iso3].append(row)
        except (OSError, json.JSONDecodeError, TypeError):
            pass
    _WD_BY_ISO3 = dict(by)
    return _WD_BY_ISO3


_WD_SUFFIXES = (
    "province",
    "oblast",
    "krai",
    "prefecture",
    "governorate",
    "department",
    "region",
    "county",
    "district",
    "republic",
    "territory",
    "voivodeship",
)
_WD_PREFIXES = (
    "north",
    "south",
    "east",
    "west",
    "northern",
    "southern",
    "eastern",
    "western",
    "upper",
    "lower",
)


def _folded_admin_keys(name: str) -> list[str]:
    n = norm_name(name)
    keys = [n]
    stripped = n
    for suf in _WD_SUFFIXES:
        if stripped.endswith(suf) and len(stripped) > len(suf) + 3:
            stripped = stripped[: -len(suf)]
            keys.append(stripped)
            break
    for pre in _WD_PREFIXES:
        if stripped.startswith(pre) and len(stripped) > len(pre) + 3:
            keys.append(stripped[len(pre) :])
            break
    return keys


def _wikidata_match(iso3: str, needles: list[str]) -> tuple[str | None, float]:
    rows = _wikidata_admin1().get(iso3) or []
    needles = [n for n in needles if n]
    if not rows or not needles:
        return None, 0.0

    # Several ISO-3166-2 units can share one HOI4 name (North/South X).
    for needle in needles:
        if len(needle) < 5:
            continue
        siblings = []
        for row in rows:
            labels = _folded_admin_keys(row.get("name") or "")
            for alt in row.get("alts") or []:
                labels.extend(_folded_admin_keys(alt))
            if needle in labels:
                siblings.append(row)
        if len(siblings) >= 2:
            siblings.sort(key=lambda r: -float(r["pop"]))
            total = sum(float(r["pop"]) for r in siblings)
            parent = siblings[0]
            rest = total - float(parent["pop"])
            if rest > 0 and float(parent["pop"]) >= 0.8 * rest:
                return norm_name(parent.get("iso2") or parent.get("name") or ""), float(parent["pop"])
            return f"sum{needle}", total

    best = None
    best_score = 0
    best_pop = -1.0
    for row in rows:
        labels = _folded_admin_keys(row.get("name") or "")
        for alt in row.get("alts") or []:
            labels.extend(_folded_admin_keys(alt))
        pop = float(row["pop"])
        score = 0
        for n in labels:
            if len(n) < 4:
                continue
            for needle in needles:
                if n == needle:
                    score = max(score, 1000 + len(n))
                elif len(n) >= 5 and len(needle) >= 5 and (n in needle or needle in n):
                    score = max(score, 100 + min(len(n), len(needle)))
        if score > best_score or (score == best_score and score > 0 and pop > best_pop):
            best_score = score
            best_pop = pop
            best = row
    if not best:
        return None, 0.0
    region = norm_name(best.get("iso2") or best.get("name") or "")
    return region, float(best["pop"])


_WD_ISO2_INDEX: dict[tuple[str, str], dict] | None = None


def _wd_iso2_index() -> dict[tuple[str, str], dict]:
    global _WD_ISO2_INDEX
    if _WD_ISO2_INDEX is not None:
        return _WD_ISO2_INDEX
    idx: dict[tuple[str, str], dict] = {}
    for iso3, rows in _wikidata_admin1().items():
        for row in rows:
            code = (row.get("iso2") or "").strip().upper()
            if not code:
                continue
            prev = idx.get((iso3, code))
            if prev is None or float(row["pop"]) > float(prev["pop"]):
                idx[(iso3, code)] = row
    _WD_ISO2_INDEX = idx
    return idx


def _mapped_region(owner: str, keys: list[str]) -> tuple[str | None, float]:
    iso3 = (TAG_META.get(owner) or {}).get("iso3") or ""
    iso_map = HOI4_ISO2.get(owner) or {}
    man_map = MANUAL_POP.get(owner) or {}
    idx = _wd_iso2_index()
    for k in keys:
        codes = iso_map.get(k)
        if codes:
            total = 0.0
            used: list[str] = []
            for code in codes:
                rec = idx.get((iso3, code.upper()))
                if rec:
                    total += float(rec["pop"])
                    used.append(code.upper())
            if total > 0:
                return f"{owner}:iso:{'+'.join(used)}", total
        man = man_map.get(k)
        if man:
            return f"{owner}:man:{man[0]}", float(man[1])
    return None, 0.0


def official_region(owner: str, loc_name: str, pretty: str) -> tuple[str | None, float]:
    """Return (region_key, official_pop) or (None, 0). Shared keys are split later."""
    keys = [norm_name(loc_name), norm_name(pretty)]
    for k in list(keys):
        if k in ALIASES:
            keys.append(ALIASES[k])
    table = None
    canon = {}
    if owner == "USA":
        table = US_CENSUS_2024
    elif owner == "CHI":
        table = CN_NBS_2023
        canon = CN_CANON
    elif owner == "RAJ":
        table = IN_POP
    elif owner == "ENG":
        table = UK_POP
    elif owner == "GER":
        table = DE_POP
        canon = DE_CANON
    elif owner == "BRA":
        table = BR_POP
    elif owner == "JAP":
        table = JP_POP
    elif owner == "KOR":
        table = KR_POP
    if table:
        for k in keys:
            if k in table:
                region = canon.get(k, k)
                pop = float(table.get(region, table[k]))
                return f"{owner}:{region}", pop
            if k in canon:
                region = canon[k]
                if region in table:
                    return f"{owner}:{region}", float(table[region])
    mapped_key, mapped_pop = _mapped_region(owner, keys)
    if mapped_key:
        return mapped_key, mapped_pop
    iso3 = (TAG_META.get(owner) or {}).get("iso3") or ""
    region, pop = _wikidata_match(iso3, keys)
    if region:
        return f"{owner}:wd:{region}", pop
    return None, 0.0


def official_weight(owner: str, loc_name: str, pretty: str) -> float:
    _key, pop = official_region(owner, loc_name, pretty)
    return pop


def ntl_lookup_keys(owner: str, loc_name: str, pretty: str) -> list[str]:
    keys = [norm_name(loc_name), norm_name(pretty)]
    extra: list[str] = []
    for k in list(keys):
        if k in ALIASES:
            extra.append(ALIASES[k])
        extra.extend(NTL_NAME_ALIASES.get(k) or [])
    region, _pop = official_region(owner, loc_name, pretty)
    if region:
        tail = region.split(":")[-1]
        extra.append(norm_name(tail))
    out: list[str] = []
    seen: set[str] = set()
    for k in keys + extra:
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


# GADM puts some HOI4 tags' land under a different ISO3 (HK as HKG, not CHN).
NTL_KEY_ISO3 = {
    "hongkong": "HKG",
    "macau": "MAC",
    "macao": "MAC",
}
# These ISO3 units are city-states / small islands whose GADM-1 rows are districts.
NTL_COUNTRY_MAX = frozenset({"SGP", "HKG", "MAC", "MLT", "BHR", "QAT", "MDV", "BRN", "BHS"})


def ntl_mean_for(owner: str, loc_name: str, pretty: str, by_iso3: dict) -> float | None:
    iso3 = (TAG_META.get(owner) or {}).get("iso3") or ""
    keys = ntl_lookup_keys(owner, loc_name, pretty)
    tables = []
    if iso3:
        tables.append(by_iso3.get(iso3) or {})
    for k in keys:
        extra = NTL_KEY_ISO3.get(k)
        if extra:
            tables.append(by_iso3.get(extra) or {})
    hits: list[float] = []
    for table in tables:
        hits.extend(table[k] for k in keys if k in table)
    if hits:
        return max(hits)
    for table in tables:
        for k in keys:
            if len(k) < 6:
                continue
            matched = [v for name, v in table.items() if k in name or name in k]
            if len(matched) == 1:
                return matched[0]
    if iso3 in NTL_COUNTRY_MAX:
        table = by_iso3.get(iso3) or {}
        if table:
            return max(table.values())
    for k in keys:
        extra = NTL_KEY_ISO3.get(k)
        if extra and extra in NTL_COUNTRY_MAX:
            table = by_iso3.get(extra) or {}
            if table:
                return max(table.values())
    return None


# Keyword bonuses added to allocation weights. Numbers are relative, not buildings.
CIV_KEYWORDS = {
    "USA": {"california": 8, "illinois": 6, "ohio": 6, "michigan": 5, "indiana": 5, "texas": 5, "pennsylvania": 4, "newyork": 4, "northcarolina": 3, "georgia": 2},
    "CHI": {"guangdong": 10, "guangzhou": 10, "jiangsu": 9, "jiansu": 9, "suzhou": 8, "zhejiang": 8, "shandong": 7, "shanghai": 7, "beijing": 5, "beiping": 5, "chongqing": 4, "henan": 3, "hubei": 4, "wuhan": 4, "liaoning": 4, "fujian": 4, "tianjin": 3},
    "GER": {"westfalen": 8, "rhineland": 8, "moselland": 7, "baden": 6, "wuttemberg": 6, "sachsen": 5, "nassau": 4, "oberbayern": 4},
    "JAP": {"kanto": 8, "osaka": 8, "nagoya": 6, "hiroshima": 3, "nagasaki": 3},
    "KOR": {"gyeongsang": 10, "southkorea": 8, "chungcheong": 4},
    "RAJ": {"bombay": 8, "madras": 6, "calcutta": 5, "delhi": 4, "gujarat": 4, "westernindian": 4, "mysore": 3},
    "ITA": {"lombardy": 8, "piedmont": 5, "veneto": 4, "emilia": 4, "latium": 3},
    "ENG": {"westmidlands": 6, "northwest": 5, "yorkshire": 4, "greaterlondon": 2},
    "FRA": {"iledefrance": 4, "rhone": 5, "nord": 4, "alsace": 4, "provence": 2},
    "BRA": {"saopaulo": 10, "minas": 4, "riodejaneiro": 3, "parana": 3, "riograndesul": 2},
    "MEX": {"mexico": 6, "nuevo": 5, "jalisco": 4, "coahuila": 3},
    "SOV": {"moscow": 6, "sverdlovsk": 5, "chelyabinsk": 4, "samara": 3, "tatarstan": 3, "nizhny": 3},
}

MIL_KEYWORDS = {
    "USA": {
        "texas": 12, "arizona": 12, "missouri": 10, "alabama": 10, "ohio": 9,
        "california": 8, "georgia": 8, "pennsylvania": 8, "iowa": 8, "tennessee": 7,
        "connecticut": 7, "newengland": 7, "florida": 6, "wisconsin": 6,
        "virginia": 6, "indiana": 5, "southcarolina": 5, "washington": 4,
        "westvirginia": -6,
    },
    "CHI": {
        "chengdu": 12, "xian": 10, "liaoning": 10, "liaotung": 10, "liaobei": 8,
        "beijing": 8, "beiping": 8, "wuhan": 8, "hubei": 6, "sichuan": 8,
        "guizhou": 5, "heilungkiang": 5, "ordos": 6, "shaanxi": 5, "heilongjiang": 4,
    },
    "SOV": {
        "sverdlovsk": 14, "chelyabinsk": 8, "tula": 8, "udmurtia": 6, "izhevsk": 0,
        "perm": 6, "gorky": 6, "kazan": 6, "moscow": 5, "stalingrad": 4,
        "volgograd": 4, "ufa": 3, "omsk": 8, "kurgan": 6, "tomsk": -10,
    },
    "UKR": {"kharkiv": 6, "kharkov": 6, "dnipro": 5, "zaporizhzhia": 4, "kyiv": 8, "kiev": 8, "lviv": 6, "mykolaiv": 2},
    "KOR": {"gyeongsang": 12, "southkorea": 4, "gyeonggi": 5},
    "JAP": {"kanto": 8, "osaka": 5, "nagoya": 8, "hiroshima": 3, "nagasaki": 2},
    "ISR": {"palestine": 4, "israel": 8, "telaviv": 6, "haifa": 8},
    "ENG": {"lancashire": 8, "yorkshire": 4, "scotland": 3, "gloucestershire": 6, "westmidlands": 6, "northernengland": 4},
    "FRA": {"iledefrance": 6, "rhone": 8, "aquitaine": 6, "gironde": 6, "bretagne": 2, "toulon": 2, "provence": 3, "centre": 5, "bourges": 6},
    "GER": {"westfalen": 10, "hannover": 8, "sachsen": 6, "franken": 5, "bayreuth": 4, "rhineland": 5, "moselland": 4, "brandenburg": 4, "oberbayern": 6},
    "RAJ": {"hyderabad": 6, "bangalore": 8, "mysore": 8, "bombay": 4, "delhi": 4, "madras": 5, "tamil": 4},
    "PAK": {"punjab": 8, "karachi": 4, "sindh": 3, "sind": 3, "peshawar": 3},
    "TUR": {"ankara": 10, "istanbul": 4, "konya": 6, "kayseri": 4, "izmir": 3},
    "PER": {"tehran": 8, "esfahan": 6, "isfahan": 6, "khuzestan": 4},
    "ITA": {"lombardy": 8, "piedmont": 8, "lazio": 3, "campania": 3, "tuscany": 4},
    "SWE": {"ostergotland": 8, "ostergötland": 8, "vastergotland": 4, "västergötland": 4, "skane": 2, "skåne": 2},
    "POL": {
        "warsaw": 4, "kielce": 8, "katowice": 6, "uppersilesia": 5, "oberschlesien": 5,
        "lublin": 4, "krakow": 3, "kraków": 3, "lodz": 2,
    },
    "SPR": {"sevilla": 4, "madrid": 3, "galicia": 2, "cadiz": 2},
    "BRA": {"saopaulo": 8, "minas": 3, "riodejaneiro": 2},
    "DPK": {"pyongan": 8, "hwanghae": 6, "hamgyong": 4},
    "FOR": {"taiwan": 8, "formosa": 8},
    "CZE": {"bohemia": 5, "moravia": 4, "czechoslovakia": 4},
    "NOR": {"oslofjord": 6, "telemark": 2},
    "FIN": {"uusimaa": 3, "hame": 5, "häme": 5},
    "SWI": {"swissplateau": 6},
    "SER": {"serbia": 6, "morava": 3},
    "BLR": {"minsk": 6},
    "BRM": {"magwe": 4, "mandalay": 3, "pegu": 2},
    "EGY": {"cairo": 6, "alexandria": 3},
    "VIN": {"tonkin": 5, "cochinchina": 3, "saigon": 3},
    "SAF": {"transvaal": 6},
    "INS": {"westjava": 6, "java": 3},
    "AST": {
        "victoria": 5, "newsouthwales": 4, "queensland": 8,
        "northqueensland": -6, "southwestqueensland": -6, "westqueensland": -6,
    },
    "CAN": {
        "southernontario": 12, "ontario": 2, "quebec": 2,
        "northernontario": -10, "districtsofontario": -10,
    },
    "UAE": {"abudhabi": 10},
    "SNG": {"singapore": 8},
    "DEN": {"denmark": 4, "jutland": 6},
    "SLO": {"slovakia": 8},
    "CRO": {"croatia": 6},
    "BOS": {"bosnia": 6},
    "ETH": {"ethiopia": 8},
    "MAL": {"kedah": 6, "perak": 4, "johor": 3},
    "BAN": {"bangladesh": 8},
    "KAZ": {"northernkazakhstan": 8, "petropavl": 8},
    "AZR": {"baku": 8},
    "JOR": {"jordan": 8},
    "SUD": {"khartoum": 8},
    "SAU": {"dammam": 6},
    "HOL": {"holland": 4, "brabant": 2},
    "BEL": {"wallonia": 8, "flanders": 2},
    "AUS": {"upperaustria": 6, "loweraustria": 2},
    "HUN": {"southtransdanubia": 8, "northtransdanubia": 3},
    "BUL": {"plovdiv": 6, "sofia": 2},
    "ROM": {"muntenia": 5},
    "GRE": {"attica": 4, "athens": 4},
    "MEX": {"mexicocity": 6, "mexico": 3},
    "ALG": {"algiers": 6, "constantine": 3},
    "ARG": {"buenosaires": 5},
    "CHL": {"santiago": 4},
    "COL": {"cundinamarca": 4, "bogota": 4},
    "SIA": {"bangkok": 4},
    "CAR": {"equatorialafrica": 4},
    "HOU": {"northyemen": 8, "yemen": 4},
    "HAM": {"gaza": 8},
    "HEZ": {"southlebanon": 8, "lebanon": 3},
    "PAL": {"westbank": 8},
    "ROJ": {"northeast": 8, "rojava": 8},
    "SYR": {"damascus": 8, "aleppo": 4},
    "SNA": {"peacespring": 8},
    "DRZ": {"suwayda": 8},
    "YEM": {"marib": 8},
    "STC": {"aden": 8, "hadhramaut": 3},
    "YNR": {"mocha": 8},
    "NUG": {"shan": 6, "sagaing": 5, "arakan": 3},
    "M23": {"goma": 8},
    "RSF": {"southdarfur": 6, "northdarfur": 3},
    "AZA": {"gao": 6, "kidal": 3},
    "SHB": {"jilib": 8},
    "JUB": {"jubaland": 8},
    "SOM": {"somalia": 6, "mogadishu": 4},
    "SML": {"somaliland": 8},
    "PNT": {"puntland": 8},
    "SSD": {"bahr": 6, "uppernile": 3},
    "SIO": {"jonglei": 8},
    "LNA": {"benghasi": 8, "cyrenaica": 5, "derna": 2},
    "LBA": {"tripoli": 8, "tripolitania": 4},
    "NRF": {"panjshir": 8},
    "PMR": {"transnistria": 8},
    "ABK": {"abkhazia": 8},
    "SOE": {"southossetia": 8},
}

DOCK_KEYWORDS = {
    "CHI": {
        "shanghai": 12, "liaoning": 8, "dalian": 8, "jiangsu": 7, "jiansu": 7,
        "guangdong": 6, "guangzhou": 6, "shandong": 5, "zhejiang": 5, "fujian": 4,
        "liaobei": -20,
    },
    "KOR": {"gyeongsang": 20, "southkorea": 4},
    "JAP": {"nagasaki": 8, "osaka": 6, "kanto": 5, "hiroshima": 5, "southkyushu": 3, "nagoya": 3},
    "USA": {
        "virginia": 10, "mississippi": 8, "newengland": 12, "alabama": 3,
        "california": 5, "connecticut": 3, "maine": 3,
        "washington": 1, "hawaii": 0, "westvirginia": -20,
        # Marinette is real, but Wisconsin has no ocean province.
    },
    "VIN": {"saigon": 2, "haiphong": 4, "tonkin": 2, "cochinchina": 1},
    "ENG": {
        "cumbria": 20, "strathclyde": 8, "lanark": 8, "lothian": 6,
        "scottishhighlands": -8, "belfast": -6, "northernireland": -6,
    },
    "FRA": {"brittany": 8, "bretagne": 8, "normandy": 6, "loire": 6, "var": 6, "toulon": 6, "provence": 2},
    "ITA": {"piedmont": 8, "liguria": 8, "genoa": 8, "campania": 6, "napoli": 6, "trieste": 5, "tuscany": 2, "sardinia": -6},
    "GER": {"holstein": 10, "hamburg": 6, "schleswig": 2, "southschleswig": -10, "weserems": 2},
    "HOL": {"holland": 6, "rotterdam": 4},
    "SOV": {
        "arkhangelsk": 12, "leningrad": 6, "konigsberg": 6, "kaliningrad": 6,
        "vladivostok": 5, "murmansk": -2,
        # Amur Shipyard is Komsomolsk-on-Amur: river, no sea province.
    },
    "BRA": {"riodejaneiro": 6},
    "INS": {"eastjava": 8, "surabaya": 8, "java": 2},
    "RAJ": {"bombay": 8, "calcutta": 6, "northernmadras": 6, "madrasstates": 5, "southernmadras": 2},
    "TUR": {"istanbul": 8, "izmit": 8, "golcuk": 6, "ankara": -4},
    "SPR": {"galicia": 10, "sevilla": 8, "cadiz": 6, "murcia": 4, "ceuta": -10, "melilla": -8},
    "AST": {"southaustralia": 10, "westernaustralia": 8, "newsouthwales": -4},
    "CAN": {"novascotia": 10, "halifax": 8, "britishcolumbia": 6, "newfoundland": -6},
    "FOR": {"taiwan": 8, "formosa": 8},
    "DPK": {"hamgyong": 8, "pyongan": 6},
    "SNG": {"singapore": 8},
    "PAK": {"karachi": 8, "sind": 4},
    "EGY": {"alexandria": 8, "cairo": -4},
    "SWE": {"skane": 6, "blekinge": 8, "gotland": -4},
    "CHL": {"chile": 6, "santiago": 4, "easterisland": -8},
    "PRU": {"lima": 6, "callao": 8},
    "POL": {"gdynia": 8, "danzig": 6, "pomorskie": 4},
    "UAE": {"abudhabi": 8},
    "MAL": {"lumut": 6, "perak": 4, "johor": 2},
}

RENEW_KEYWORDS = {
    "CHI": {"innermongolia": 12, "xinjiang": 10, "sinkiang": 10, "sichuan": 8, "chengdu": 6, "qinghai": 7, "gansu": 6, "hebei": 5, "shandong": 5, "jiangsu": 4, "yunnan": 6, "ningxia": 4, "tibet": 2},
    "USA": {"california": 10, "texas": 10, "iowa": 5, "oklahoma": 4, "kansas": 4, "illinois": 3, "washington": 4, "newyork": 3, "oregon": 3, "colorado": 3, "northdakota": 2, "minnesota": 2},
    "BRA": {"para": 6, "amazonas": 4, "parana": 5, "saopaulo": 3, "minas": 3, "riograndesul": 3, "bahia": 2},
    "IND": {},
    "RAJ": {"bombay": 3, "mysore": 4, "rajputana": 4, "madras": 3, "unitedprovinces": 2, "gujarat": 3, "westernindian": 3},
    "GER": {"brandenburg": 3, "sachsen": 2, "schleswig": 3, "westfalen": 2, "niedersachsen": 3, "weserems": 3, "osthannover": 2},
    "JAP": {"hokkaido": 3, "kyushu": 3, "southkyushu": 3, "tohoku": 3, "southtohoku": 3, "kanto": 2},
    "CAN": {"quebec": 8, "britishcolumbia": 5, "ontario": 4, "manitoba": 2, "alberta": 3},
    "FRA": {"rhone": 3, "occitanie": 2, "hautsdefrance": 2, "grandest": 2, "normandy": 2, "brittany": 2},
    "SPA": {},
    "SPR": {"andalucia": 4, "castile": 3, "aragon": 3, "galicia": 3, "catalonia": 2},
    "ITA": {"lombardy": 2, "apulia": 3, "sicily": 3, "sardinia": 2},
    "AUS": {},
    "AST": {"southaustralia": 4, "victoria": 3, "newsouthwales": 3, "westernaustralia": 4, "queensland": 3, "tasmania": 2},
    "MEX": {"oaxaca": 3, "sonora": 3, "baja": 2, "jalisco": 2},
    "TUR": {"izmir": 3, "ankara": 2, "konya": 2},
    "VIN": {"tonkin": 4, "annam": 3, "cochinchina": 2},
    "NOR": {"telemark": 4, "vestland": 4, "nordland": 3, "oslo": 1},
    "SWE": {"norrland": 4, "svealand": 3, "gotaland": 2},
    "SOV": {"krasnoyarsk": 4, "irkutsk": 3, "volga": 3, "northwest": 2, "leningrad": 2},
}

OIL_KEYWORDS = {
    "USA": {"texas": 20, "northdakota": 8, "newmexico": 6, "oklahoma": 5, "alaska": 5, "colorado": 4, "california": 3, "louisiana": 4, "wyoming": 3, "pennsylvania": 1},
    "SAU": {"neijd": 8, "riyadh": 6, "eastern": 12, "alhasa": 10, "dhahran": 10},
    "SOV": {"khanty": 10, "tyumen": 8, "tatarstan": 4, "bashkort": 4, "sakhalin": 3, "komi": 2, "astrakhan": 2},
    "CAN": {"alberta": 12, "saskatchewan": 4, "newfoundland": 3, "britishcolumbia": 1},
    "IRQ": {"kirkuk": 6, "basra": 8, "baghdad": 2, "mosul": 3},
    "CHI": {"heilongjiang": 4, "xinjiang": 4, "shaanxi": 3, "tianjin": 2, "shandong": 2},
    "UAE": {"abudhabi": 10, "dubai": 2},
    "PER": {"khuzestan": 10, "bushehr": 4, "tehran": 1},
    "BRA": {"riodejaneiro": 6, "santos": 3, "espirito": 2, "amazonas": 1},
    "KUW": {"kuwait": 10},
    "MEX": {"campeche": 6, "tabasco": 4, "veracruz": 3, "tamaulipas": 2},
    "NOR": {"northsea": 6, "vestland": 4, "rogaland": 5, "troms": 2},
    "NGA": {"nigerdelta": 8, "rivers": 6, "bayelsa": 5, "delta": 4},
    "KAZ": {"atyrau": 6, "mangystau": 5, "aktobe": 2},
    "QAT": {"qatar": 10},
    "ANG": {"cabinda": 6, "luanda": 3, "zaires": 2},
    "ALG": {"hassi": 6, "ouargla": 5, "inamenas": 4, "southern": 3},
    "LBA": {"sirte": 4, "tripoli": 2},
    "LNA": {"cyrenaica": 5, "sirte": 3},
    "OMA": {"dhofar": 3, "interior": 2},
    "GYA": {"guyana": 8},
    "VEN": {"zulia": 6, "orinoc": 5, "anzoategui": 4},
    "COL": {"meta": 3, "casanare": 3, "arauca": 2},
    "GBR": {},
    "ENG": {"scotland": 3, "aberdeenshire": 4, "shetland": 2, "eastanglia": 1},
}

COAL_KEYWORDS = {
    "CHI": {"shanxi": 12, "innermongolia": 10, "shaanxi": 8, "xinjiang": 5, "shandong": 4, "anhui": 3, "henan": 3, "guizhou": 3, "heilongjiang": 2},
    "RAJ": {"bihar": 6, "orissa": 5, "centralprovinces": 5, "westbengal": 3, "calcutta": 3, "telangana": 2, "hyderabad": 2},
    "INS": {"kalimantan": 10, "sumatra": 6, "southsumatra": 6},
    "USA": {"wyoming": 10, "westvirginia": 6, "pennsylvania": 5, "kentucky": 4, "illinois": 4, "montana": 3, "indiana": 2, "texas": 1},
    "AST": {"queensland": 6, "newsouthwales": 5, "westernaustralia": 2},
    "SOV": {"kuznetsk": 8, "kemerovo": 8, "komi": 4, "yakutia": 3, "rostov": 2},
    "SAF": {"mpumalanga": 8, "limpopo": 3, "gauteng": 2},
    "KAZ": {"karagandy": 6, "pavlodar": 4, "ekibastuz": 4},
    "GER": {"westfalen": 3, "sachsen": 3, "brandenburg": 2},
    "POL": {"silesia": 8, "katowice": 6, "krakow": 2},
    "COL": {"cesar": 4, "guajira": 5, "magdalena": 2},
    "TUR": {"zonguldak": 4, "afyon": 2},
    "AUS": {},
}

STEEL_KEYWORDS = {
    "CHI": {"hebei": 12, "jiangsu": 6, "liaoning": 6, "shandong": 5, "shanxi": 5, "shanghai": 3, "hubei": 3, "anhui": 2},
    "RAJ": {"orissa": 5, "bombay": 4, "centralprovinces": 4, "calcutta": 3, "andrapradesh": 2},
    "JAP": {"kanto": 4, "osaka": 4, "nagoya": 3, "hiroshima": 3, "nagasaki": 2},
    "USA": {"indiana": 8, "ohio": 7, "pennsylvania": 6, "michigan": 4, "alabama": 3, "arkansas": 2},
    "SOV": {"chelyabinsk": 6, "sverdlovsk": 5, "lipetsk": 4, "vologda": 3, "kemerovo": 3, "magnitogorsk": 5},
    "KOR": {"gyeongsang": 10, "southkorea": 3},
    "GER": {"westfalen": 6, "sachsen": 4, "saar": 2, "bremen": 2, "weserems": 2},
    "TUR": {"iskenderun": 4, "marmara": 3, "istanbul": 3},
    "BRA": {"minas": 6, "riodejaneiro": 4, "saopaulo": 3, "espirito": 3},
    "PER": {"isfahan": 5, "khuzestan": 3, "yazd": 2},
}

ALUM_KEYWORDS = {
    "CHI": {"shandong": 6, "henan": 5, "xinjiang": 4, "guangxi": 4, "inner": 3, "yunnan": 3, "gansu": 2},
    "RAJ": {"orissa": 6, "andrapradesh": 3, "gujarat": 2, "westernindian": 2},
    "SOV": {"krasnoyarsk": 6, "irkutsk": 4, "sverdlovsk": 3, "komi": 2},
    "CAN": {"quebec": 8, "britishcolumbia": 4, "newfoundland": 2},
    "UAE": {"abudhabi": 6, "dubai": 2},
    "AUS": {},
    "AST": {"queensland": 5, "tasmania": 3, "westernaustralia": 3, "victoria": 2},
    "NOR": {"vestland": 4, "nordland": 3, "telemark": 2},
    "USA": {"kentucky": 3, "indiana": 2, "washington": 2, "southcarolina": 2, "texas": 1},
    "BHR": {"bahrain": 8},
    "ISL": {},
    "ICE": {"iceland": 8},
}

TUNGSTEN_KEYWORDS = {
    "CHI": {"jiangxi": 8, "hunan": 6, "henan": 3, "fujian": 3, "guangdong": 2, "yunnan": 2},
    "VIN": {"tonkin": 6, "annam": 3},
    "SOV": {"primorsky": 4, "kabardino": 2, "northcaucasus": 2},
    "BOL": {"potosi": 6, "oruro": 4},
    "RWA": {"rwanda": 6},
    "POR": {"norte": 4},
    "SPA": {},
    "SPR": {"castile": 3, "extremadura": 2},
}

CHROME_KEYWORDS = {
    "SAF": {"limpopo": 8, "mpumalanga": 4, "northwest": 3},
    "TUR": {"elazig": 4, "adana": 3, "mersin": 2, "erzurum": 2},
    "KAZ": {"aktobe": 8, "khromtau": 6},
    "RAJ": {"orissa": 5, "karnataka": 3, "mysore": 3, "jharkhand": 2},
    "FIN": {"lappi": 6, "oulu": 3},
}

COPPER_KEYWORDS = {
    "CHL": {"atacama": 8, "antofagasta": 10, "northernchile": 8, "arica": 2},
    "PRU": {"arequipa": 6, "cusco": 4, "tacna": 3, "moquegua": 4, "junin": 2},
    "COG": {"katanga": 10, "elisabethville": 8, "hautkatanga": 8},
    "CHI": {"jiangxi": 4, "anhui": 3, "innermongolia": 3, "tibet": 2, "yunnan": 2},
    "USA": {"arizona": 8, "utah": 4, "newmexico": 3, "nevada": 2, "montana": 2},
    "SOV": {"norilsk": 6, "krasnoyarsk": 4, "ural": 3, "chita": 2},
    "INS": {"papua": 6, "sulawesi": 3},
    "AST": {"southaustralia": 4, "queensland": 3, "newsouthwales": 2, "westernaustralia": 3},
    "ZAM": {"copperbelt": 8, "zambia": 4},
    "MEX": {"sonora": 5, "zacatecas": 3, "chihuahua": 2},
    "CAN": {"britishcolumbia": 4, "ontario": 3, "quebec": 2},
    "KAZ": {"karagandy": 4, "balkhash": 4, "eastern": 3},
    "POL": {"silesia": 4, "legnica": 3},
}

GRAPHITE_KEYWORDS = {
    "CHI": {"heilongjiang": 6, "shandong": 5, "inner": 4, "hunan": 3, "jilin": 2},
    "MZB": {"cabo": 6, "nampula": 4},
    "MAD": {"madagascar": 6},
    "BRA": {"minas": 5, "bahia": 2},
    "RAJ": {"andrapradesh": 3, "orissa": 2, "tamil": 2, "madras": 2},
}

LITHIUM_KEYWORDS = {
    "AST": {"westernaustralia": 12, "southaustralia": 2},
    "CHL": {"atacama": 12, "antofagasta": 8, "northernchile": 8},
    "CHI": {"qinghai": 6, "jiangxi": 4, "sichuan": 4, "tibet": 2},
    "ARG": {"jujuy": 6, "salta": 5, "catamarca": 5, "northwest": 4},
    "BRA": {"minas": 4},
    "ZIM": {"zimbabwe": 4},
    "USA": {"nevada": 6, "northcarolina": 2, "california": 1},
}

COBALT_KEYWORDS = {
    "COG": {"katanga": 16, "elisabethville": 12, "hautkatanga": 10, "lualaba": 8},
    "INS": {"sulawesi": 8, "maluku": 3},
    "SOV": {"norilsk": 6, "murmansk": 3},
    "AST": {"westernaustralia": 4, "queensland": 2},
    "CAN": {"ontario": 4, "quebec": 2},
    "CUB": {"oriente": 4, "holguin": 3},
    "PHI": {"mindanao": 3, "palawan": 2},
}

REE_KEYWORDS = {
    "CHI": {"innermongolia": 12, "jiangxi": 6, "sichuan": 4, "shandong": 3, "guangdong": 2},
    "USA": {"california": 6, "texas": 2, "wyoming": 1},
    "BRM": {"kachin": 6, "shan": 4, "nug": 2},
    "NUG": {"shan": 4, "kachin": 3},
    "AST": {"westernaustralia": 6, "northernterritory": 3},
    "SIA": {"thailand": 3},
    "RAJ": {"andrapradesh": 2, "orissa": 1},
}

RUBBER_KEYWORDS = {
    "SIA": {"south": 6, "bangkok": 2, "isaan": 2, "malay": 4},
    "INS": {"sumatra": 8, "kalimantan": 4, "java": 2, "riau": 4},
    "VIN": {"cochinchina": 6, "saigon": 4, "annam": 2},
    "IVO": {"ivory": 6, "abidjan": 4},
    "CHI": {"hainan": 4, "yunnan": 4, "guangdong": 2},
    "RAJ": {"kerala": 4, "madrasstates": 4, "assam": 2, "tripura": 2},
    "MAL": {"peninsular": 4, "johor": 3, "perak": 2},
    "CAM": {"cambodia": 4},
    "BRM": {"irrawaddy": 3, "tenasserim": 3},
    "PHI": {"mindanao": 2},
    "BRA": {"amazonas": 3, "acre": 2, "para": 2},
    "LIB": {"liberia": 4},
}


FINANCE_KEYWORDS = {
    "USA": {
        "newyork": 12, "california": 10, "illinois": 6, "maryland": 5,
        "newengland": 4, "florida": 2, "washington": -12, "westvirginia": -8,
    },
    "CHI": {
        "hongkong": 12, "shanghai": 10, "guangdong": 8, "beijing": 6, "beiping": 6,
        "guangzhou": 5, "chengdu": 4, "qingdao": 3,
    },
    "ENG": {"greaterlondon": 12, "lothian": 4, "lanark": 3, "strathclyde": 3},
    "SNG": {"singapore": 10},
    "JAP": {"kanto": 10, "osaka": 6, "kansai": 6},
    "KOR": {"gyeonggi": 10, "southkorea": 8, "gyeongsang": 4},
    "GER": {"hessen": 10, "nassau": 10},
    "SWI": {"swissplateau": 10},
    "FRA": {"iledefrance": 10, "bretagne": -4, "brittany": -4, "corsica": -8, "corse": -8},
    "UAE": {"abudhabi": 10},
    "CAN": {"southernontario": 8, "quebec": 4, "britishcolumbia": 4, "nordduquebec": -8},
    "AST": {"newsouthwales": 8, "victoria": 6},
    "RAJ": {"bombay": 8, "gujarat": 6, "westernindian": 6, "delhi": 2},
    "HOL": {"holland": 10},
    "IRE": {"leinster": 10, "ireland": 4},
    "LUX": {"luxembourg": 10, "luxemburg": 10},
    "ITA": {"lombardy": 8, "lazio": 4},
    "FOR": {"taiwan": 10, "formosa": 8},
    "TUR": {"istanbul": 10},
    "POL": {"warsaw": 10},
    "MEX": {"mexicocity": 10, "mexico": 4},
    "CHL": {"santiago": 8, "chile": 2},
    "SWE": {"sodermanland": 10, "stockholm": 10},
    "DEN": {"sjaelland": 10, "denmark": 2, "jutland": -4},
    "MAL": {"kualalumpur": 10, "singapore": -8},
    "BRA": {"saopaulo": 10},
    "SAU": {"nejd": 8, "riyadh": 8},
    "ISR": {"telaviv": 10},
    "SPR": {"madrid": 10},
    "BEL": {"flanders": 6, "antwerp": 4, "brussels": 8},
    "AUS": {"loweraustria": 10, "austria": 4},
    "KAZ": {"akmolinsk": 10, "northernkazakhstan": 6},
}

REFINERY_KEYWORDS = {
    "USA": {
        "texas": 12, "louisiana": 8, "california": 5, "indiana": 4,
        "washington": -6, "westvirginia": -8,
    },
    "CHI": {
        "zhejiang": 8, "dalian": 8, "jiangsu": 6, "jiansu": 6, "guangdong": 5,
        "shandong": 5, "fujian": 4, "liaoning": 3, "beijing": 3, "beiping": 3,
    },
    "KOR": {"gyeongsang": 12, "chungcheong": 8, "jeolla": 8},
    "RAJ": {"gujarat": 12, "westernindian": 10, "bombay": 6, "madrasstates": 4, "orissa": 3},
    "SAU": {"dammam": 12, "hejaz": 6, "madinah": 4},
    "SNG": {"singapore": 10},
    "JAP": {"kanto": 8, "hiroshima": 6, "sanyo": 6, "osaka": 5, "kansai": 5},
    "VEN": {"zulia": 8, "paraguana": 10, "falcon": 8},
    "HOL": {"holland": 10},
    "GER": {"baden": 8, "wurttemberg": 4, "sachsen": 4},
    "ENG": {"sussex": 8, "lancashire": 6, "lothian": 5},
    "FRA": {"normandy": 8, "loire": 6, "bouchesdurhone": 6, "provence": 3},
    "ITA": {"sicily": 8, "sardinia": 8},
    "SPR": {"murcia": 6, "andalucia": 5, "cadiz": 4, "sevilla": 3},
    "BRA": {"saopaulo": 6, "riodejaneiro": 6},
    "MEX": {"mexico": 4, "oaxaca": 4, "veracruz": 3},
    "SOV": {"omsk": 10, "leningrad": 8, "ryazan": 6, "yaroslavl": 4},
    "PER": {"khuzestan": 10, "hormozgan": 8},
    "KUW": {"kuwait": 10},
    "UAE": {"abudhabi": 10},
    "IRQ": {"basra": 8},
    "NGA": {"lagos": 10},
    "INS": {"eastjava": 6, "centraljava": 5, "java": 2},
    "MAL": {"johor": 10},
    "SIA": {"bangkok": 8},
    "TUR": {"izmit": 10},
    "CAN": {"alberta": 8, "southernontario": 4},
    "AST": {"victoria": 6, "queensland": 3},
    "EGY": {"cairo": 6, "suez": 4},
    "SAF": {"transvaal": 8, "natal": 4},
}

SILO_KEYWORDS = {
    "USA": {"texas": 10, "louisiana": 10, "california": -4, "washington": -6},
    "CHI": {
        "zhejiang": 10, "dalian": 8, "shandong": 6, "guangdong": 6,
        "easthebei": 5, "beijing": 3, "beiping": 3, "tianjin": 8,
    },
    "JAP": {"hokkaido": 8, "kanto": 6, "osaka": 5, "kansai": 5, "nagasaki": 3},
    "KOR": {"gyeongsang": 8, "gyeonggi": 6, "southkorea": 4},
    "RAJ": {"mysore": 6, "madrasstates": 5, "calcutta": 3, "orissa": 3},
    "GER": {"holstein": 6, "niedersachsen": 5, "weserems": 4},
    "FRA": {"provence": 6, "alpes": 4, "bouchesdurhone": 4, "iledefrance": -4},
    "ENG": {"sussex": 6, "hampshire": 4},
    "HOL": {"holland": 10},
    "SPR": {"madrid": 4, "catalonia": 3},
    "ITA": {"lazio": 4, "sicily": 3},
    "SNG": {"singapore": 10},
    "SAU": {"dammam": 10, "hejaz": 6},
    "UAE": {"abudhabi": 8},
    "CAN": {"alberta": 6, "southernontario": 5},
    "AST": {"victoria": 6, "newsouthwales": 4},
    "BRA": {"saopaulo": 6, "riodejaneiro": 4},
    "SOV": {"moscow": 6, "leningrad": 4, "primorye": 4, "vladivostok": 4},
    "PER": {"khuzestan": 8},
    "KUW": {"kuwait": 8},
}

GRID_KEYWORDS = {
    "USA": {
        "california": 8, "texas": 8, "illinois": 6, "pennsylvania": 6,
        "newyork": 6, "washington": 6, "westvirginia": -8,
    },
    "CHI": {
        "beijing": 8, "beiping": 8, "shanghai": 8, "guangdong": 7, "hubei": 6,
        "sichuan": 6, "chengdu": 4, "liaoning": 5, "xinjiang": 4, "urumqi": 4,
    },
    "ENG": {"greaterlondon": 8, "sussex": 4, "lothian": 5, "lanark": 4},
    "FRA": {"iledefrance": 8, "alpes": 6, "rhone": 5},
    "GER": {"rhineland": 6, "westfalen": 5, "brandenburg": 5, "nassau": 4},
    "JAP": {"kanto": 8, "osaka": 6, "kansai": 6},
    "KOR": {"gyeonggi": 8, "southkorea": 6},
    "RAJ": {"delhi": 8, "bombay": 6, "madras": 5, "southernmadras": 4},
    "SOV": {"moscow": 8, "leningrad": 6, "krasnoyarsk": 5},
    "BRA": {"saopaulo": 8, "parana": 5, "riodejaneiro": 3},
    "CAN": {"southernontario": 8, "quebec": 6, "nordduquebec": -6},
    "AST": {"newsouthwales": 8},
    "ITA": {"lazio": 6, "lombardy": 4},
    "SPR": {"madrid": 6, "catalonia": 4},
    "HOL": {"holland": 8},
    "POL": {"warsaw": 8},
    "SWE": {"sodermanland": 6, "stockholm": 6},
    "NOR": {"oslofjord": 6, "oslo": 6},
    "TUR": {"istanbul": 8},
    "SAU": {"nejd": 6, "dammam": 6},
    "UAE": {"abudhabi": 8},
    "FOR": {"taiwan": 8, "formosa": 8},
    "SNG": {"singapore": 10},
    "MEX": {"mexicocity": 8, "mexico": 3},
    "INS": {"westjava": 6, "java": 2},
    "VIN": {"tonkin": 8},
    "EGY": {"cairo": 8},
    "SAF": {"transvaal": 8},
    "UKR": {"kyiv": 8, "kiev": 8},
    "PAK": {"punjab": 6},
    "PER": {"tehran": 8},
    "ARG": {"buenosaires": 8},
    "CHL": {"santiago": 8},
    "MAL": {"kualalumpur": 6, "johor": 2},
    "SIA": {"bangkok": 8},
    "AUS": {"loweraustria": 6, "vienna": 6},
    "BEL": {"flanders": 6},
    "SWI": {"swissplateau": 8},
    "CZE": {"bohemia": 6},
    "ROM": {"muntenia": 6},
}


def keyword_bonus(owner: str, loc_name: str, pretty: str, table: dict) -> float:
    blob = norm_name(loc_name) + " " + norm_name(pretty)
    bonus = 0.0
    for kw, val in (table.get(owner) or {}).items():
        if kw and kw in blob:
            bonus += float(val)
    return bonus
