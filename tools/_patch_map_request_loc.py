# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

def patch_cities(path: Path) -> None:
    raw = path.read_bytes()
    bom = raw[:3] == b"\xef\xbb\xbf"
    text = raw.decode("utf-8-sig")
    lines = []
    for ln in text.splitlines(keepends=True):
        if re.match(r"\s*VICTORY_POINTS_(3710|9850):", ln):
            continue
        lines.append(ln)
    body = "".join(lines)
    # rewrite Bridgeport/New Haven keys
    if "VICTORY_POINTS_6909:" in body:
        body = re.sub(r'VICTORY_POINTS_6909:\d*\s*"[^"]*"', 'VICTORY_POINTS_6909:0 "Bridgeport"', body)
    else:
        body = body.rstrip() + '\n VICTORY_POINTS_6909:0 "Bridgeport"\n'
    if "VICTORY_POINTS_9832:" in body:
        body = re.sub(r'VICTORY_POINTS_9832:\d*\s*"[^"]*"', 'VICTORY_POINTS_9832:0 "New Haven"', body)
    else:
        body = body.rstrip() + '\n VICTORY_POINTS_9832:0 "New Haven"\n'
    if not body.endswith("\n"):
        body += "\n"
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + body.encode("utf-8"))
    print("patched", path.relative_to(ROOT))

for rel in [
    "localisation/english/doomsday_usa_cities_l_english.yml",
    "localisation/english/replace/doomsday_usa_cities_l_english.yml",
]:
    patch_cities(ROOT / rel)

# USA loc state names + drop gang country names
usa = ROOT / "localisation/english/doomsday_usa_l_english.yml"
raw = usa.read_bytes()
bom = raw[:3] == b"\xef\xbb\xbf"
text = raw.decode("utf-8-sig")
text = text.replace('STATE_1125:0 "Wall Street"', 'STATE_1125:0 "New York Island"')
text = text.replace('STATE_1136:0 "Patriot Front"', 'STATE_1136:0 "Rhode Island"')
# remove EME/NFA loc block
text = re.sub(
    r"\n EME:0.*?\n NFA_sovereign_democracy:0 \"Nuestra Familia\"",
    "",
    text,
    count=1,
    flags=re.S,
)
usa.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
print("patched usa loc")
