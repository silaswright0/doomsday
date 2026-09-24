#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path

base = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV")
mod = Path(r"c:\Users\siwri\Documents\Paradox Interactive\Hearts of Iron IV\mod\doomsday")
out = mod / "tools" / "_dlc_gates.txt"

pat = re.compile(r'has_dlc\s*=\s*"([^"]+)"')

lines = []
for folder in ["raids", "intelligence_agencies", "intelligence_agency_upgrades", "operations", "special_projects"]:
    p = base / "common" / folder
    if not p.exists():
        lines.append(f"MISS {folder}")
        continue
    lines.append(f"\n## {folder}")
    for f in sorted(p.rglob("*.txt")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        gates = sorted(set(pat.findall(text)))
        # also allow_without_dlc / required_dlc patterns
        req = re.findall(r"required_dlc\s*=\s*\{([^}]+)\}", text, re.S)
        lines.append(f"  {f.relative_to(base/'common')}: gates={gates or '-'} req_blocks={len(req)}")

# Raid types allow triggers
lines.append("\n## raid type allow snippets")
for f in (base / "common" / "raids").glob("*.txt"):
    text = f.read_text(encoding="utf-8", errors="ignore")
    for m in re.finditer(r"(\w+)\s*=\s*\{[^{}]{0,200}allowed\s*=\s*\{([^}]{0,300})\}", text, re.S):
        if "has_dlc" in m.group(2) or "always" in m.group(2):
            lines.append(f"  {f.name}::{m.group(1)} allowed={m.group(2).strip()[:120]}")

# Equipment market: search scripted triggers
lines.append("\n## market scripted")
for f in (base / "common").rglob("*.txt"):
    if "market" in f.name.lower() or "equipment_market" in f.read_text(encoding="utf-8", errors="ignore")[:500].lower():
        if "market" in f.name.lower():
            lines.append(f"  {f.relative_to(base)}")

# Mod replace_path blockers vs systems
lines.append("\n## mod replace_path impact")
desc = (mod / "descriptor.mod").read_text(encoding="utf-8")
replaces = re.findall(r'replace_path="([^"]+)"', desc)
for r in replaces:
    lines.append(f"  REPLACE {r}")

# Compare key unit files present
lines.append("\n## support battalion presence (mod)")
for name in [
    "flame_tank.txt", "engineer.txt", "recon.txt", "signal.txt", "maintenance.txt",
    "logistics.txt", "field_hospital.txt", "military_police.txt", "armored_car_battalion.txt",
    "land_cruiser.txt", "railway_gun.txt", "helicopter_brigade.txt", "hq_support.txt",
]:
    lines.append(f"  {'HAS' if (mod/'common'/'units'/name).exists() else 'NO '} {name}")

# Tech unlocks for flame / armored support in mod tech
lines.append("\n## mod tech mentions")
tech_dir = mod / "common" / "technologies"
for key in ["flame", "armored_support", "armored_car", "land_cruiser", "railway_gun", "super_heavy_railway"]:
    hits = []
    for f in tech_dir.glob("*.txt"):
        t = f.read_text(encoding="utf-8", errors="ignore")
        if key in t:
            hits.append(f.name)
    lines.append(f"  {key}: {hits}")

# Special projects list
lines.append("\n## special project files")
sp = base / "common" / "special_projects" / "projects"
if sp.exists():
    for f in sorted(sp.glob("*.txt"))[:40]:
        lines.append(f"  {f.name}")

text = "\n".join(lines) + "\n"
out.write_text(text, encoding="utf-8")
print(text)
