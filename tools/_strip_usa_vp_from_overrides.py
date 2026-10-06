# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OV = ROOT / "localisation" / "replace" / "doomsday_overrides_l_english.yml"
CIT = ROOT / "localisation" / "english" / "replace" / "doomsday_usa_cities_l_english.yml"

usa = set(map(int, re.findall(r"VICTORY_POINTS_([0-9]+)", CIT.read_text(encoding="utf-8-sig"))))
raw = OV.read_bytes()
bom = raw[:3] == b"\xef\xbb\xbf"
text = raw.decode("utf-8-sig")
kept = []
removed = 0
for ln in text.splitlines(keepends=True):
    m = re.match(r"\s*VICTORY_POINTS_([0-9]+):", ln)
    if m and int(m.group(1)) in usa:
        removed += 1
        continue
    kept.append(ln)
new = "".join(kept)
if not new.endswith("\n"):
    new += "\n"
OV.write_bytes((b"\xef\xbb\xbf" if bom else b"") + new.encode("utf-8"))
print(f"removed {removed}; remaining VP keys {len(re.findall(r'VICTORY_POINTS_', new))}")
