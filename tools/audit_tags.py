#!/usr/bin/env python3
"""Write tools/doomsday_tag_map.csv and print the 2026 on-map roster."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV")
TAG_RE = re.compile(r'\s*([A-Z0-9]{3})\s*=\s*"countries/([^"]+)"')

RENAME = {
    "SOV": "Russia",
    "RAJ": "India",
    "CHI": "China",
    "PER": "Iran",
    "SIA": "Thailand",
    "HOL": "Netherlands",
    "FOR": "Taiwan",
    "KOR": "South Korea",
    "CZE": "Czechia",
    "DPK": "North Korea",
    "SSD": "South Sudan",
    "SIO": "SPLM-IO",
    "AZA": "Azawad",
    "ENG": "United Kingdom",
}


def parse_tags() -> dict[str, tuple[str, str]]:
    tags: dict[str, tuple[str, str]] = {}
    files = [
        (VANILLA / "common" / "country_tags" / "00_countries.txt", "vanilla"),
        (VANILLA / "common" / "country_tags" / "zz_dynamic_countries.txt", "dynamic"),
        (ROOT / "common" / "country_tags" / "doomsday_countries.txt", "doomsday_new"),
    ]
    for path, src in files:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            match = TAG_RE.match(line)
            if match:
                tags[match.group(1)] = (match.group(2).replace(".txt", ""), src)
    return tags


def main() -> None:
    tags = parse_tags()
    owners: dict[str, int] = defaultdict(int)
    states_csv = ROOT / "tools" / "doomsday_states.csv"
    if states_csv.exists():
        with states_csv.open(encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                owners[row["owner_2026"]] += 1

    sheet: dict[str, str] = {}
    with (ROOT / "tools" / "doomsday_countries.csv").open(encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            sheet[row["tag"]] = row.get("name") or ""

    rows = []
    for tag, (raw_name, source) in sorted(tags.items()):
        name = sheet.get(tag) or RENAME.get(tag) or raw_name
        n_states = owners.get(tag, 0)
        if source == "dynamic":
            status = "civil_war_temp"
        elif n_states > 0:
            status = "on_map"
        elif tag in sheet:
            status = "stub_in_sheet"
        else:
            status = "releasable_or_dead"
        rows.append((tag, raw_name, name, source, status, n_states))

    out = ROOT / "tools" / "doomsday_tag_map.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["tag", "vanilla_file_name", "doomsday_name", "tag_source", "status", "states_owned"])
        writer.writerows(rows)

    counts = Counter(row[4] for row in rows)
    print(f"tags={len(rows)} {dict(counts)}")
    print("new tags:", [row[0] for row in rows if row[3] == "doomsday_new"])
    print("on_map countries:")
    for row in rows:
        if row[4] == "on_map":
            print(f"  {row[0]:4} {row[2]:32} states={row[5]:3}  ({row[3]})")


if __name__ == "__main__":
    main()
