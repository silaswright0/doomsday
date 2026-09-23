#!/usr/bin/env python3
"""2026 starting laws for every on-map tag.

Sources (see tools/data/SOURCES.md): OECD SOCX/Revenue Statistics 2024–25,
WHO abortion map 2026, Freedom on the Net 2025, EU AI Act 2024/1689 as
amended 2026/1744, World Population Review conscription 2026, IISS/open
defence lists. Country-scoped. No random.

Tuple: welf edu imm tax wom mino inv sec health labor fert aid rel med ai
       cons trade econ

Immigration vs minority and women vs fertility must stay pairing-legal.
Never assign welfare 5 (UBI), fertility 5, women 5, or aid 5 — none exist
as national policy in 2026.
"""

from __future__ import annotations

# imm 1->mino 1-2; 2->1-3; 3->2-4; 4->3-5; 5->4-5
# wom 4 => fert>=3; wom 5 => fert>=4

KEYS = (
    "welf", "edu", "imm", "tax", "wom", "mino", "inv", "sec", "health",
    "labor", "fert", "aid", "rel", "med", "ai", "cons", "trade", "econ",
)

# tag: (welf, edu, imm, tax, wom, mino, inv, sec, health, labor, fert, aid, rel, med, ai, cons, trade, econ)
POLICIES: dict[str, tuple] = {
    # --- North America ---
    "USA": (3, 4, 4, 2, 3, 3, 2, 4, 2, 2, 3, 4, 3, 4, 1, "volunteer_only", "export_focus", "civilian_economy"),
    "CAN": (4, 4, 4, 3, 4, 4, 3, 3, 4, 4, 4, 4, 4, 4, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "MEX": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "GRN": (4, 5, 3, 3, 4, 4, 3, 2, 4, 4, 3, 2, 4, 4, 3, "volunteer_only", "free_trade", "civilian_economy"),
    # --- Western / Nordic Europe ---
    "ENG": (4, 4, 3, 3, 3, 3, 3, 3, 4, 3, 3, 4, 2, 4, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "FRA": (4, 5, 3, 4, 4, 3, 4, 3, 5, 4, 3, 4, 4, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "GER": (4, 5, 4, 3, 3, 3, 3, 3, 5, 4, 3, 4, 4, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "ITA": (4, 4, 3, 4, 3, 3, 3, 3, 4, 4, 3, 3, 3, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "SPR": (4, 4, 4, 3, 4, 3, 3, 3, 4, 4, 3, 3, 4, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "POR": (4, 4, 3, 3, 3, 3, 3, 3, 4, 4, 3, 3, 4, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "BEL": (4, 4, 4, 4, 3, 3, 3, 3, 5, 4, 3, 4, 3, 3, 4, "volunteer_only", "free_trade", "civilian_economy"),
    "HOL": (4, 4, 4, 3, 4, 3, 3, 3, 5, 4, 4, 4, 4, 3, 4, "volunteer_only", "free_trade", "civilian_economy"),
    "LUX": (4, 4, 4, 3, 3, 3, 2, 3, 5, 4, 3, 3, 4, 3, 4, "volunteer_only", "free_trade", "civilian_economy"),
    "IRE": (3, 4, 4, 2, 3, 3, 2, 3, 4, 3, 3, 3, 3, 4, 4, "volunteer_only", "free_trade", "civilian_economy"),
    "AUS": (4, 5, 3, 4, 3, 3, 3, 3, 5, 4, 3, 3, 3, 3, 4, "limited_conscription", "export_focus", "civilian_economy"),
    "SWI": (4, 4, 3, 2, 3, 3, 2, 3, 5, 4, 3, 3, 4, 4, 3, "limited_conscription", "export_focus", "civilian_economy"),
    "SWE": (4, 5, 3, 4, 4, 3, 3, 3, 5, 4, 3, 4, 4, 4, 4, "limited_conscription", "export_focus", "civilian_economy"),
    "NOR": (4, 5, 3, 4, 4, 3, 3, 3, 5, 4, 3, 4, 4, 4, 3, "limited_conscription", "export_focus", "civilian_economy"),
    "DEN": (4, 5, 2, 4, 4, 3, 3, 3, 5, 4, 3, 4, 4, 4, 4, "limited_conscription", "export_focus", "civilian_economy"),
    "FIN": (4, 5, 2, 4, 4, 3, 3, 3, 5, 4, 3, 4, 4, 4, 4, "limited_conscription", "export_focus", "early_mobilization"),
    "ICE": (4, 5, 3, 3, 4, 3, 2, 2, 5, 4, 3, 3, 4, 4, 3, "volunteer_only", "free_trade", "civilian_economy"),
    # --- Central / Eastern Europe ---
    "POL": (4, 5, 2, 3, 3, 3, 3, 3, 4, 3, 2, 3, 2, 3, 4, "volunteer_only", "export_focus", "early_mobilization"),
    "CZE": (4, 5, 3, 3, 3, 3, 3, 3, 4, 3, 3, 2, 4, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "SLO": (3, 5, 2, 3, 3, 3, 3, 3, 4, 3, 3, 2, 3, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "HUN": (3, 5, 2, 3, 3, 3, 3, 4, 4, 3, 2, 2, 2, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "ROM": (3, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "BUL": (3, 5, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "SER": (3, 4, 2, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "CRO": (3, 5, 3, 3, 3, 3, 3, 3, 4, 3, 3, 2, 3, 3, 4, "limited_conscription", "export_focus", "civilian_economy"),
    "SLV": (4, 5, 3, 3, 3, 3, 3, 3, 4, 4, 3, 2, 4, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "BOS": (3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "MAC": (3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "ALB": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 4, "volunteer_only", "export_focus", "civilian_economy"),
    "MNT": (3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 4, "volunteer_only", "free_trade", "civilian_economy"),
    "KOS": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 4, "volunteer_only", "free_trade", "civilian_economy"),
    "GRE": (4, 5, 3, 3, 3, 3, 3, 3, 4, 3, 3, 2, 2, 3, 4, "limited_conscription", "export_focus", "civilian_economy"),
    "CYP": (3, 5, 3, 3, 3, 3, 3, 3, 4, 3, 3, 2, 3, 3, 4, "limited_conscription", "export_focus", "civilian_economy"),
    "NCY": (3, 4, 2, 2, 3, 3, 3, 3, 3, 3, 3, 1, 2, 3, 3, "limited_conscription", "free_trade", "civilian_economy"),
    "MLT": (4, 4, 3, 3, 3, 3, 2, 3, 4, 3, 1, 2, 2, 3, 4, "volunteer_only", "free_trade", "civilian_economy"),
    "EST": (3, 5, 3, 3, 3, 3, 3, 3, 4, 3, 3, 2, 4, 4, 4, "limited_conscription", "export_focus", "early_mobilization"),
    "LAT": (3, 5, 3, 3, 3, 3, 3, 3, 4, 3, 3, 2, 3, 3, 4, "limited_conscription", "export_focus", "early_mobilization"),
    "LIT": (3, 5, 3, 3, 3, 3, 3, 3, 4, 3, 3, 2, 3, 3, 4, "limited_conscription", "export_focus", "early_mobilization"),
    "UKR": (3, 4, 2, 3, 3, 3, 3, 4, 3, 5, 3, 1, 2, 3, 3, "extensive_conscription", "limited_exports", "war_economy"),
    "BLR": (3, 5, 2, 3, 3, 2, 4, 5, 3, 4, 2, 1, 4, 2, 2, "limited_conscription", "limited_exports", "partial_economic_mobilisation"),
    "MOL": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 3, "limited_conscription", "export_focus", "civilian_economy"),
    "PMR": (3, 4, 2, 2, 3, 2, 4, 4, 3, 4, 3, 1, 4, 2, 2, "limited_conscription", "limited_exports", "partial_economic_mobilisation"),
    "SOV": (3, 5, 2, 3, 3, 2, 4, 5, 3, 4, 2, 2, 2, 2, 2, "limited_conscription", "limited_exports", "war_economy"),
    # --- Caucasus / Central Asia ---
    "GEO": (3, 4, 2, 2, 3, 3, 3, 4, 3, 3, 3, 1, 2, 3, 2, "limited_conscription", "export_focus", "early_mobilization"),
    "ABK": (2, 3, 2, 2, 3, 2, 3, 4, 2, 3, 3, 1, 2, 2, 2, "limited_conscription", "limited_exports", "partial_economic_mobilisation"),
    "SOE": (2, 3, 2, 2, 3, 2, 3, 4, 2, 3, 3, 1, 2, 2, 2, "limited_conscription", "limited_exports", "partial_economic_mobilisation"),
    "ARM": (3, 4, 2, 2, 3, 3, 3, 3, 3, 3, 3, 1, 2, 3, 2, "limited_conscription", "export_focus", "early_mobilization"),
    "AZR": (3, 4, 2, 2, 2, 2, 4, 4, 3, 3, 2, 2, 2, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "KAZ": (3, 4, 2, 2, 3, 3, 4, 4, 3, 3, 3, 2, 4, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "UZB": (3, 4, 2, 2, 2, 2, 4, 4, 3, 3, 2, 1, 2, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "TMS": (3, 3, 1, 2, 2, 2, 5, 5, 3, 4, 2, 1, 2, 1, 2, "limited_conscription", "closed_economy", "civilian_economy"),
    "KYR": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 2, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "TAJ": (3, 3, 2, 2, 2, 2, 3, 4, 2, 3, 2, 1, 2, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "MON": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 4, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    # --- East Asia ---
    "CHI": (3, 4, 2, 3, 3, 1, 5, 5, 3, 5, 2, 3, 4, 2, 1, "limited_conscription", "limited_exports", "civilian_economy"),
    "FOR": (4, 4, 3, 2, 3, 3, 4, 3, 4, 3, 3, 2, 4, 4, 3, "limited_conscription", "export_focus", "early_mobilization"),
    "JAP": (4, 4, 2, 3, 3, 3, 4, 3, 4, 4, 2, 4, 4, 4, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "KOR": (4, 4, 3, 3, 3, 3, 4, 3, 4, 3, 2, 3, 3, 4, 3, "extensive_conscription", "export_focus", "early_mobilization"),
    "DPK": (1, 2, 1, 4, 2, 1, 5, 5, 1, 1, 2, 1, 5, 1, 2, "extensive_conscription", "closed_economy", "partial_economic_mobilisation"),
    "VIN": (3, 4, 2, 3, 3, 3, 5, 4, 3, 5, 3, 2, 4, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "LAO": (2, 4, 2, 2, 3, 3, 5, 4, 2, 4, 1, 1, 4, 2, 2, "limited_conscription", "limited_exports", "civilian_economy"),
    "CAM": (2, 4, 3, 2, 3, 3, 4, 4, 2, 3, 3, 1, 3, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "SNG": (3, 4, 4, 2, 3, 3, 4, 4, 4, 2, 2, 2, 3, 3, 3, "extensive_conscription", "free_trade", "civilian_economy"),
    "MAL": (3, 4, 3, 2, 2, 2, 3, 3, 3, 3, 2, 2, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "INS": (3, 4, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "PHI": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 1, 2, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "BRN": (4, 4, 3, 1, 2, 2, 4, 4, 4, 2, 2, 2, 2, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "TML": (2, 3, 3, 2, 3, 3, 3, 2, 2, 3, 3, 1, 3, 3, 3, "limited_conscription", "free_trade", "civilian_economy"),
    "BRM": (2, 4, 2, 2, 2, 1, 3, 5, 2, 2, 2, 1, 2, 2, 2, "limited_conscription", "limited_exports", "war_economy"),
    "NUG": (2, 3, 3, 2, 3, 3, 2, 3, 2, 3, 3, 1, 3, 4, 3, "limited_conscription", "free_trade", "war_economy"),
    "SIA": (3, 4, 3, 2, 3, 3, 3, 3, 4, 3, 3, 2, 2, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    # --- South Asia ---
    "RAJ": (3, 4, 3, 3, 3, 4, 4, 3, 3, 3, 3, 2, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "PAK": (3, 4, 2, 2, 2, 2, 3, 4, 2, 3, 2, 2, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "BAN": (3, 4, 2, 2, 3, 3, 3, 3, 3, 3, 2, 2, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "NEP": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "BHU": (3, 4, 1, 2, 3, 2, 3, 3, 3, 3, 3, 1, 2, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "SRL": (3, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "MLD": (3, 4, 3, 2, 2, 3, 2, 3, 3, 3, 2, 1, 2, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "AFG": (1, 1, 1, 2, 1, 1, 2, 5, 1, 2, 1, 1, 1, 2, 5, "extensive_conscription", "closed_economy", "partial_economic_mobilisation"),
    "NRF": (2, 3, 2, 2, 3, 3, 2, 3, 2, 3, 3, 1, 2, 3, 3, "limited_conscription", "free_trade", "war_economy"),
    # --- Middle East ---
    "TUR": (3, 5, 3, 2, 2, 2, 3, 4, 3, 3, 2, 2, 2, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "PER": (3, 4, 2, 3, 2, 2, 4, 5, 3, 3, 2, 2, 1, 2, 2, "limited_conscription", "limited_exports", "partial_economic_mobilisation"),
    "IRQ": (3, 4, 2, 2, 2, 2, 3, 4, 2, 3, 1, 2, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "SYR": (1, 4, 1, 2, 1, 1, 2, 5, 1, 2, 1, 1, 1, 2, 2, "extensive_conscription", "closed_economy", "war_economy"),
    "ROJ": (2, 3, 3, 2, 4, 4, 3, 3, 2, 3, 3, 1, 4, 3, 3, "limited_conscription", "limited_exports", "war_economy"),
    "DRZ": (2, 3, 2, 2, 3, 3, 2, 4, 2, 3, 2, 1, 2, 3, 3, "limited_conscription", "limited_exports", "war_economy"),
    "SNA": (2, 2, 2, 2, 2, 2, 2, 4, 2, 2, 2, 1, 2, 2, 2, "limited_conscription", "limited_exports", "war_economy"),
    "LEB": (3, 4, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "HEZ": (2, 3, 2, 2, 1, 2, 3, 5, 2, 2, 1, 1, 1, 2, 2, "extensive_conscription", "closed_economy", "war_economy"),
    "ISR": (4, 4, 4, 3, 3, 3, 3, 4, 4, 3, 3, 2, 2, 4, 1, "extensive_conscription", "export_focus", "war_economy"),
    "PAL": (2, 3, 2, 2, 3, 3, 2, 3, 2, 3, 3, 1, 2, 3, 3, "volunteer_only", "limited_exports", "civilian_economy"),
    "HAM": (1, 2, 1, 2, 1, 1, 2, 5, 1, 2, 1, 1, 1, 2, 2, "extensive_conscription", "closed_economy", "war_economy"),
    "JOR": (3, 4, 3, 2, 2, 3, 3, 4, 3, 3, 2, 2, 2, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "SAU": (4, 5, 2, 1, 2, 2, 4, 5, 4, 2, 2, 3, 2, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "UAE": (4, 5, 2, 1, 2, 2, 4, 5, 4, 2, 2, 3, 2, 2, 2, "limited_conscription", "free_trade", "civilian_economy"),
    "QAT": (4, 5, 2, 1, 2, 2, 4, 4, 4, 2, 2, 3, 2, 2, 2, "limited_conscription", "free_trade", "civilian_economy"),
    "KUW": (4, 5, 2, 1, 2, 2, 4, 4, 4, 2, 2, 2, 2, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "OMA": (3, 5, 2, 1, 2, 2, 4, 4, 4, 2, 2, 2, 2, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "BHR": (3, 5, 2, 1, 2, 2, 3, 5, 4, 2, 2, 2, 2, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "YEM": (2, 4, 2, 2, 2, 2, 2, 4, 1, 2, 2, 1, 2, 3, 3, "limited_conscription", "limited_exports", "war_economy"),
    "HOU": (1, 2, 1, 2, 1, 1, 2, 5, 1, 2, 1, 1, 1, 2, 2, "extensive_conscription", "closed_economy", "war_economy"),
    "YNR": (2, 2, 2, 2, 2, 2, 2, 4, 1, 2, 2, 1, 2, 3, 2, "limited_conscription", "limited_exports", "war_economy"),
    "STC": (2, 2, 2, 2, 2, 2, 2, 4, 1, 2, 2, 1, 2, 3, 2, "limited_conscription", "limited_exports", "war_economy"),
    # --- North Africa ---
    "EGY": (3, 4, 2, 3, 2, 2, 4, 5, 3, 3, 1, 2, 2, 2, 2, "limited_conscription", "export_focus", "partial_economic_mobilisation"),
    "LBA": (3, 4, 2, 1, 2, 2, 3, 3, 2, 3, 2, 1, 2, 3, 2, "limited_conscription", "export_focus", "partial_economic_mobilisation"),
    "LNA": (2, 3, 2, 1, 2, 2, 3, 4, 2, 2, 2, 1, 2, 2, 2, "limited_conscription", "export_focus", "war_economy"),
    "TUN": (3, 4, 2, 3, 3, 3, 3, 4, 3, 3, 2, 1, 2, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "ALG": (3, 4, 2, 3, 2, 2, 4, 4, 3, 4, 2, 2, 2, 2, 2, "limited_conscription", "limited_exports", "civilian_economy"),
    "MOR": (3, 4, 2, 3, 2, 2, 3, 4, 3, 3, 2, 2, 2, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    # --- Sub-Saharan Africa ---
    "SAF": (3, 4, 3, 3, 3, 3, 3, 3, 3, 4, 3, 2, 3, 4, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "NGA": (2, 4, 3, 2, 3, 3, 3, 3, 2, 3, 3, 1, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "ETH": (2, 3, 2, 2, 3, 2, 3, 4, 2, 3, 2, 1, 2, 3, 2, "limited_conscription", "export_focus", "partial_economic_mobilisation"),
    "KEN": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "GHA": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 2, 2, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "COG": (2, 4, 2, 2, 3, 3, 2, 2, 2, 2, 2, 1, 3, 3, 3, "limited_conscription", "export_focus", "war_economy"),
    "M23": (1, 2, 2, 1, 2, 2, 1, 4, 1, 2, 2, 1, 3, 3, 3, "limited_conscription", "closed_economy", "war_economy"),
    "RCG": (2, 4, 3, 2, 3, 3, 3, 4, 2, 3, 1, 1, 3, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "ANG": (2, 4, 2, 2, 3, 3, 4, 4, 2, 3, 2, 1, 3, 2, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "MZB": (2, 3, 3, 2, 3, 3, 3, 3, 2, 3, 3, 1, 3, 3, 3, "limited_conscription", "export_focus", "civilian_economy"),
    "ZIM": (2, 4, 2, 3, 3, 3, 4, 4, 2, 3, 3, 1, 3, 2, 2, "volunteer_only", "limited_exports", "civilian_economy"),
    "ZAM": (2, 4, 3, 2, 3, 3, 3, 3, 2, 3, 3, 1, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "MLW": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "BOT": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "NMB": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "LES": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "SWZ": (2, 3, 2, 2, 2, 2, 3, 4, 2, 2, 2, 1, 2, 2, 2, "volunteer_only", "free_trade", "civilian_economy"),
    "MAD": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "UGA": (2, 3, 2, 2, 3, 2, 3, 4, 2, 3, 2, 1, 2, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "TZN": (2, 3, 3, 2, 3, 3, 3, 3, 2, 3, 3, 1, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "RWA": (3, 4, 2, 2, 3, 2, 4, 5, 3, 3, 3, 2, 3, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "BRD": (2, 3, 2, 2, 3, 3, 2, 3, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "SSD": (1, 4, 2, 2, 2, 2, 2, 4, 1, 2, 2, 1, 2, 3, 3, "limited_conscription", "limited_exports", "war_economy"),
    "SIO": (1, 2, 2, 1, 2, 2, 1, 4, 1, 2, 2, 1, 2, 3, 3, "limited_conscription", "closed_economy", "war_economy"),
    "SUD": (2, 4, 2, 2, 2, 2, 2, 5, 1, 2, 2, 1, 2, 2, 2, "limited_conscription", "limited_exports", "war_economy"),
    "RSF": (1, 1, 2, 1, 1, 1, 1, 5, 1, 1, 2, 1, 2, 2, 2, "extensive_conscription", "closed_economy", "war_economy"),
    "SOM": (2, 2, 2, 2, 2, 2, 2, 3, 1, 2, 2, 1, 2, 3, 3, "limited_conscription", "limited_exports", "war_economy"),
    "SML": (2, 3, 2, 2, 2, 3, 2, 3, 2, 3, 2, 1, 2, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "PNT": (2, 2, 2, 2, 2, 2, 2, 3, 1, 2, 2, 1, 2, 3, 3, "limited_conscription", "free_trade", "partial_economic_mobilisation"),
    "JUB": (1, 2, 2, 1, 2, 2, 1, 4, 1, 2, 2, 1, 2, 3, 3, "limited_conscription", "closed_economy", "war_economy"),
    "SHB": (1, 1, 1, 1, 1, 1, 1, 5, 1, 1, 1, 1, 1, 2, 5, "extensive_conscription", "closed_economy", "war_economy"),
    "DJI": (2, 3, 3, 2, 2, 3, 3, 3, 2, 3, 2, 2, 2, 3, 2, "volunteer_only", "free_trade", "civilian_economy"),
    "ERI": (1, 3, 1, 3, 2, 1, 5, 5, 1, 1, 2, 1, 4, 1, 5, "extensive_conscription", "closed_economy", "partial_economic_mobilisation"),
    "SEN": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 1, 2, 2, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "MLI": (2, 3, 2, 2, 2, 2, 3, 5, 2, 2, 2, 1, 2, 2, 2, "limited_conscription", "limited_exports", "war_economy"),
    "AZA": (1, 2, 2, 1, 2, 2, 1, 4, 1, 2, 2, 1, 1, 3, 3, "limited_conscription", "closed_economy", "war_economy"),
    "NGR": (2, 3, 2, 2, 2, 2, 3, 5, 2, 2, 2, 1, 2, 2, 2, "limited_conscription", "limited_exports", "partial_economic_mobilisation"),
    "CHA": (2, 3, 2, 2, 2, 2, 3, 5, 2, 2, 2, 1, 2, 2, 2, "limited_conscription", "export_focus", "partial_economic_mobilisation"),
    "VOL": (2, 3, 2, 2, 2, 2, 3, 5, 2, 2, 2, 1, 2, 2, 2, "limited_conscription", "limited_exports", "war_economy"),
    "GNA": (2, 3, 2, 2, 3, 3, 3, 4, 2, 3, 3, 1, 2, 2, 2, "volunteer_only", "export_focus", "partial_economic_mobilisation"),
    "GNB": (2, 3, 3, 2, 3, 3, 2, 3, 2, 3, 3, 1, 3, 3, 3, "limited_conscription", "free_trade", "civilian_economy"),
    "GAM": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 2, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "MRT": (2, 3, 2, 2, 2, 2, 3, 4, 2, 2, 1, 1, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "CMR": (2, 4, 2, 2, 3, 2, 3, 4, 2, 3, 3, 1, 3, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "GAB": (3, 4, 3, 2, 3, 3, 3, 4, 3, 3, 3, 1, 3, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "EQG": (2, 3, 2, 1, 2, 2, 4, 5, 2, 2, 3, 1, 2, 1, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "CAR": (1, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 1, 3, 3, 3, "limited_conscription", "limited_exports", "war_economy"),
    "TOG": (2, 3, 3, 2, 3, 3, 3, 4, 2, 3, 3, 1, 3, 2, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "DAH": (2, 3, 3, 2, 3, 3, 3, 3, 2, 3, 3, 1, 3, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "IVO": (3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "LIB": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "SIE": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 1, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "CBV": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "limited_conscription", "free_trade", "civilian_economy"),
    "STP": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "COM": (2, 3, 3, 2, 2, 3, 2, 2, 2, 3, 2, 1, 2, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "SEY": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "MAU": (3, 5, 3, 2, 3, 3, 2, 3, 4, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    # --- Latin America ---
    "BRA": (3, 5, 3, 3, 3, 3, 3, 3, 4, 4, 2, 2, 3, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "ARG": (2, 5, 3, 2, 3, 3, 1, 3, 3, 2, 3, 1, 3, 4, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "CHL": (3, 5, 3, 2, 4, 3, 2, 3, 4, 3, 3, 2, 4, 4, 3, "limited_conscription", "export_focus", "civilian_economy"),
    "COL": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 2, 3, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "PRU": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "VEN": (3, 4, 2, 4, 3, 3, 5, 5, 2, 5, 3, 1, 4, 2, 2, "limited_conscription", "closed_economy", "partial_economic_mobilisation"),
    "BOL": (3, 4, 3, 3, 3, 4, 4, 3, 3, 4, 3, 1, 3, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "PAR": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "URG": (4, 5, 3, 3, 3, 3, 3, 3, 4, 4, 3, 2, 4, 4, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "ECU": (3, 4, 3, 2, 3, 3, 3, 3, 3, 3, 3, 1, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "GYA": (3, 3, 3, 2, 3, 3, 2, 3, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "SUR": (3, 3, 3, 2, 3, 3, 3, 3, 3, 3, 1, 1, 3, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "CUB": (3, 5, 2, 3, 3, 3, 5, 5, 4, 5, 4, 1, 4, 1, 2, "limited_conscription", "closed_economy", "partial_economic_mobilisation"),
    "DOM": (3, 4, 3, 2, 3, 3, 2, 3, 3, 3, 3, 1, 3, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "HAI": (1, 4, 2, 2, 3, 3, 1, 1, 1, 2, 3, 1, 3, 4, 3, "volunteer_only", "free_trade", "partial_economic_mobilisation"),
    "JAM": (3, 4, 3, 2, 3, 3, 2, 3, 3, 3, 1, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "TRI": (3, 4, 3, 2, 3, 3, 2, 3, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "BAH": (3, 4, 3, 2, 3, 3, 2, 3, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "BLZ": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "GUA": (2, 4, 3, 2, 3, 3, 2, 3, 2, 3, 1, 1, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "HON": (2, 4, 3, 2, 3, 3, 2, 3, 2, 3, 1, 1, 2, 3, 2, "volunteer_only", "export_focus", "civilian_economy"),
    "ELS": (3, 4, 2, 2, 3, 3, 2, 5, 3, 2, 1, 1, 2, 3, 2, "limited_conscription", "export_focus", "civilian_economy"),
    "NIC": (2, 4, 2, 3, 3, 3, 4, 5, 3, 4, 1, 1, 4, 2, 2, "volunteer_only", "limited_exports", "civilian_economy"),
    "COS": (4, 4, 3, 3, 4, 3, 3, 2, 4, 4, 3, 2, 4, 4, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "PAN": (3, 4, 3, 2, 3, 3, 2, 3, 3, 3, 3, 1, 3, 3, 2, "volunteer_only", "free_trade", "civilian_economy"),
    "ATG": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 1, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "BRB": (3, 5, 3, 3, 3, 3, 2, 3, 4, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "DMA": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 1, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "GND": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "STL": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "SVG": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    # --- Oceania ---
    "AST": (4, 4, 4, 3, 3, 3, 3, 3, 4, 3, 3, 4, 4, 4, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "NZL": (4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, 3, 4, 4, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "PNG": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "export_focus", "civilian_economy"),
    "FIJ": (3, 3, 3, 2, 3, 3, 2, 3, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "SOL": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "VAN": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "SAM": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 2, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "KIR": (2, 3, 3, 2, 3, 3, 2, 2, 2, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "TUV": (2, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "NAU": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "PLU": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 1, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "FSM": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
    "MHL": (3, 3, 3, 2, 3, 3, 2, 2, 3, 3, 3, 1, 3, 3, 3, "volunteer_only", "free_trade", "civilian_economy"),
}

IDEA_ORDER = (
    "dd_welfare_{welf}", "dd_education_{edu}", "dd_immigration_{imm}",
    "dd_taxes_{tax}", "dd_women_{wom}", "dd_minority_{mino}",
    "dd_investment_{inv}", "dd_security_{sec}", "dd_healthcare_{health}",
    "dd_labor_{labor}", "dd_fertility_{fert}", "dd_aid_{aid}",
    "dd_religion_{rel}", "dd_media_{med}", "dd_civil_military_{ai}",
    "{cons}", "{trade}", "{econ}",
)


def _imm_mino_ok(imm: int, mino: int) -> bool:
    return mino in {
        1: {1, 2},
        2: {1, 2, 3},
        3: {2, 3, 4},
        4: {3, 4, 5},
        5: {4, 5},
    }[imm]


def _wom_fert_ok(wom: int, fert: int) -> bool:
    if wom >= 5 and fert < 4:
        return False
    if wom >= 4 and fert < 3:
        return False
    if fert <= 2 and wom >= 4:
        return False
    if fert == 3 and wom >= 5:
        return False
    return True


def validate() -> list[str]:
    errors = []
    for tag, row in POLICIES.items():
        d = dict(zip(KEYS, row))
        for k in KEYS[:15]:
            v = int(d[k])
            if v < 1 or v > 5:
                errors.append(f"{tag} {k}={v} out of 1-5")
        if not _imm_mino_ok(int(d["imm"]), int(d["mino"])):
            errors.append(f"{tag} imm={d['imm']} mino={d['mino']} pairing illegal")
        if not _wom_fert_ok(int(d["wom"]), int(d["fert"])):
            errors.append(f"{tag} wom={d['wom']} fert={d['fert']} pairing illegal")
        if int(d["welf"]) == 5 or int(d["fert"]) == 5 or int(d["wom"]) == 5 or int(d["aid"]) == 5:
            errors.append(f"{tag} banned extreme tier welf/fert/wom/aid")
        if d["cons"] not in {
            "volunteer_only", "limited_conscription", "extensive_conscription",
            "service_by_requirement", "scraping_the_barrel",
        }:
            errors.append(f"{tag} bad cons {d['cons']}")
        if d["trade"] not in {"free_trade", "export_focus", "limited_exports", "closed_economy"}:
            errors.append(f"{tag} bad trade {d['trade']}")
        if d["econ"] not in {
            "civilian_economy", "early_mobilization", "partial_economic_mobilisation",
            "war_economy", "tot_economic_mobilisation",
        }:
            errors.append(f"{tag} bad econ {d['econ']}")
    return errors


def ideas_for(tag: str) -> list[str]:
    row = POLICIES.get(tag)
    if not row:
        return []
    d = dict(zip(KEYS, row))
    return [s.format(**d) for s in IDEA_ORDER]
