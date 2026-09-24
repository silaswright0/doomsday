#!/usr/bin/env python3
"""Scan fulldlcfiles/ for gameplay-relevant DLC content (exclude focuses/cosmetics)."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "fulldlcfiles" / "dlc"
OUT = Path(__file__).resolve().parents[1] / "tools" / "_dlc_scan_report.txt"

GAMEPLAY_COMMON = {
    "raids",
    "intelligence_agencies",
    "intelligence_agency_upgrades",
    "operations",
    "operation_phases",
    "operation_tokens",
    "units",
    "technologies",
    "buildings",
    "special_projects",
    "military_industrial_organization",
    "abilities",
    "doctrines",
    "scripted_effects",
    "scripted_triggers",
    "scripted_guis",
    "defines",
    "modifiers",
    "dynamic_modifiers",
    "peace_conference",
    "occupation_laws",
    "resistance_activity",
    "scientist_traits",
    "timed_activities",
    "equipment_groups",
    "unit_leader",
    "unit_medals",
    "wargoals",
    "decisions",
    "on_actions",
    "ideas",
    "idea_tags",
    "ai_templates",
    "ai_equipment",
    "continuous_focus",
    "factions",
    "resources",
    "terrain",
    "map_modes",
    "modifier_definitions",
    "script_constants",
    "autonomous_states",
    "bop",
    "generation",
    "mtth",
    "names",
    "opinion_modifiers",
    "scorers",
    "strategic_locations",
    "technology_sharing",
    "technology_tags",
    "unit_tags",
    "medals",
    "resistance_compliance_modifiers",
    "state_category",
    "game_rules",
    "aces",
    "ai_navy",
    "ai_areas",
}

UI_HINTS = (
    "raid",
    "intel",
    "agency",
    "market",
    "operat",
    "special_project",
    "mio",
    "tank_designer",
    "ship_designer",
    "air_designer",
    "peace",
    "scientist",
    "support",
)


def classify(rel: Path) -> str:
    parts = [p.lower() for p in rel.parts]
    top = parts[0] if parts else ""
    joined = "/".join(parts)

    if top == "national_focus" or "national_focus" in parts:
        return "focus"
    if top in {"history", "events", "characters", "countries"}:
        return "country_content"
    if top in {"ai_strategy", "ai_strategy_plans", "bookmarks"}:
        return "focus_ai"
    if top in {"sound", "music", "movies"}:
        return "cosmetic_audio"
    if top == "gfx":
        if any(h in joined for h in UI_HINTS):
            return "gameplay_gfx"
        return "cosmetic_gfx"
    if top == "interface":
        if any(h in joined for h in UI_HINTS):
            return "gameplay_ui"
        return "cosmetic_ui"
    if top == "localisation":
        return "loc"
    if top == "map":
        return "map"
    if top == "common":
        sub = parts[1] if len(parts) > 1 else "other"
        if sub in GAMEPLAY_COMMON:
            return f"common/{sub}"
        return f"common/{sub}"
    return top or "root"


def main() -> None:
    lines: list[str] = []
    pack_rows: list[dict] = []

    for pack in sorted(ROOT.iterdir()):
        if not pack.is_dir():
            continue
        counts: dict[str, int] = defaultdict(int)
        samples: dict[str, list[str]] = defaultdict(list)
        n = 0
        for f in pack.rglob("*"):
            if not f.is_file():
                continue
            n += 1
            cat = classify(f.relative_to(pack))
            counts[cat] += 1
            if len(samples[cat]) < 4:
                samples[cat].append(str(f.relative_to(pack)).replace("\\", "/"))
        pack_rows.append({"id": pack.name, "files": n, "counts": dict(counts), "samples": dict(samples)})

    lines.append("FULLDLCFILES GAMEPLAY SCAN")
    lines.append("=" * 72)
    for r in pack_rows:
        lines.append(f"\n## {r['id']}  ({r['files']} files)")
        if r["files"] == 0:
            lines.append("  EMPTY — content likely folded into base game folders.")
            continue
        for cat, c in sorted(r["counts"].items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"  {c:4d}  {cat}")
            for s in r["samples"].get(cat, [])[:2]:
                lines.append(f"        e.g. {s}")

    # Targeted system hunt
    keywords = {
        "raids": ("raid",),
        "spy_agency": ("intelligence_agency", "operations", "operation_phase", "operative"),
        "intl_market": ("international_market", "market_"),
        "support_eq": ("support_equipment", "flame_tank", "engineer_equipment", "recon_equipment", "armored_car"),
        "special_projects": ("special_project", "scientist"),
        "mio": ("military_industrial_organization", "mio_"),
        "tank_designer": ("tank_modules", "tank_chassis"),
        "ship_designer": ("ship_modules", "ship_hull"),
        "air_designer": ("plane_modules", "airframe"),
        "peace": ("peace_conference",),
        "bop": ("balance_of_power", "/bop/"),
    }

    lines.append("\n\nTARGETED FILE HITS (by keyword)")
    lines.append("=" * 72)
    for label, keys in keywords.items():
        lines.append(f"\n### {label}")
        hits = []
        for r in pack_rows:
            pack = ROOT / r["id"]
            for f in pack.rglob("*"):
                if not f.is_file():
                    continue
                s = str(f.relative_to(pack)).replace("\\", "/").lower()
                if any(k in s for k in keys):
                    # skip pure operative portraits flood for spy unless script
                    if label == "spy_agency" and "/gfx/" in s and s.endswith(".dds"):
                        continue
                    hits.append(f"{r['id']}/{s}")
        if not hits:
            lines.append("  (none in fulldlcfiles — check base game common/)")
        for h in hits[:40]:
            lines.append(f"  {h}")
        if len(hits) > 40:
            lines.append(f"  ... +{len(hits) - 40} more")

    # Cross-check base game for systems missing from DLC packs
    base = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV")
    lines.append("\n\nBASE GAME SYSTEM FOLDERS (integrated post-DLC)")
    lines.append("=" * 72)
    for sub in [
        "common/raids",
        "common/intelligence_agencies",
        "common/intelligence_agency_upgrades",
        "common/operations",
        "common/operation_phases",
        "common/operation_tokens",
        "common/special_projects",
        "common/military_industrial_organization",
        "common/peace_conference",
        "common/scientist_traits",
        "common/timed_activities",
        "common/equipment_groups",
        "interface/international_market",
        "gfx/interface/international_market",
    ]:
        p = base / sub
        if p.exists():
            n = sum(1 for _ in p.rglob("*") if _.is_file()) if p.is_dir() else 1
            lines.append(f"  OK  {sub}  ({n} files)")
        else:
            lines.append(f"  MISS {sub}")

    # Battalion / support equipment in base units
    lines.append("\n\nBASE UNIT / EQUIP SUPPORT SIGNALS")
    lines.append("=" * 72)
    units = base / "common" / "units"
    for pat in ["support", "flame", "amphibious", "railway", "super_heavy", "land_cruiser", "armored_car"]:
        matches = [f.name for f in units.rglob("*") if f.is_file() and pat in f.name.lower()]
        eq = base / "common" / "units" / "equipment"
        matches += [f"equipment/{f.name}" for f in eq.rglob("*") if f.is_file() and pat in f.name.lower()]
        lines.append(f"  '{pat}': {matches[:20]}")

    text = "\n".join(lines) + "\n"
    OUT.write_text(text, encoding="utf-8")
    print(text)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
