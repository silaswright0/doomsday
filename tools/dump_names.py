import json
from pathlib import Path
from collections import defaultdict

d = json.loads(Path("tools/data/state_inventory.json").read_text(encoding="utf-8"))
by = defaultdict(list)
for s in d["states"]:
    by[s["owner"]].append(s)
out = Path("tools/data/state_names_by_tag.txt")
lines = []
for tag in sorted(by):
    lines.append(f"==== {tag} {len(by[tag])}")
    for s in by[tag]:
        lines.append(f"{s['id']:4d} | {s['pretty']} | {s['category']} | {s['manpower_old']}")
    lines.append("")
out.write_text("\n".join(lines), encoding="utf-8")
print("wrote", out, "tags", len(by))
