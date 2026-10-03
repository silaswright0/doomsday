"""Place titanium, uranium, and microchips on 2026 states.

Reads tools/data/new_resource_nodes.json. Mines stay on keyword states.
Chip output follows fab states, then civilian industry if the name misses.
Does not rewrite other resources.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_geo import (  # noqa: E402
    MICROCHIP_KEYWORDS,
    TITANIUM_KEYWORDS,
    URANIUM_KEYWORDS,
    keyword_bonus,
    load_state_loc_names,
)
from state_stats_lib import (  # noqa: E402
    ROOT,
    STATES_CSV,
    distribute,
    extract_block,
    group_by_owner,
    load_all_states,
)

KEYS = ("titanium", "uranium", "microchips")
TABLES = {
    "titanium": TITANIUM_KEYWORDS,
    "uranium": URANIUM_KEYWORDS,
    "microchips": MICROCHIP_KEYWORDS,
}


def weights(owned: list[dict], table: dict, key: str) -> list[float]:
    scored = []
    for state in owned:
        if state["impassable"]:
            scored.append(0.0)
            continue
        bonus = keyword_bonus(state["owner"], state["loc_pretty"], state["pretty"], table)
        if key == "microchips":
            industry = float(state["buildings"].get("industrial_complex") or 0)
            scored.append(bonus * 40.0 + industry)
        else:
            scored.append(bonus)
    if sum(scored) <= 0 and owned:
        best = max(range(len(owned)), key=lambda i: owned[i]["manpower"])
        scored = [1.0 if i == best else 0.0 for i in range(len(owned))]
    return scored


def merge_resources(text: str, extra: dict[str, int]) -> str:
    positive = {k: v for k, v in extra.items() if v > 0}
    if not positive:
        return text
    match_at = text.find("resources=")
    if match_at < 0:
        match_at = text.find("resources =")
    if match_at < 0:
        anchor = None
        for token in ("state_category", "manpower"):
            import re

            found = re.search(rf"{token}\s*=\s*\S+", text)
            if found:
                anchor = found
                break
        body = "".join(f"\n\t\t{k}={v}" for k, v in positive.items())
        block = "{\n" + body + "\n\t}"
        if anchor:
            return text[: anchor.end()] + f"\n\n\tresources={block}\n" + text[anchor.end() :]
        return text
    _old, end = extract_block(text, match_at)
    block = text[match_at:end]
    for key in KEYS:
        import re

        block = re.sub(rf"\n[ \t]*{key}\s*=\s*\d+", "", block)
    insert = "".join(f"\n\t\t{k}={v}" for k, v in positive.items())
    close = block.rfind("}")
    block = block[:close] + insert + "\n\t" + block[close:]
    return text[:match_at] + block + text[end:]


def main() -> None:
    nodes = json.loads((ROOT / "tools" / "data" / "new_resource_nodes.json").read_text(encoding="utf-8"))
    states = load_all_states()
    names = load_state_loc_names(ROOT)
    for state in states:
        state["loc_pretty"] = names.get(state["id"]) or state["pretty"]
    by_owner = group_by_owner(states)
    placed: dict[int, dict[str, int]] = defaultdict(dict)
    missing_tags = []
    for key in KEYS:
        for tag, total in (nodes.get(key) or {}).items():
            owned = [s for s in by_owner.get(tag, []) if not s["impassable"]]
            if not owned:
                missing_tags.append(f"{tag}:{key}")
                continue
            shares = distribute(int(total), weights(owned, TABLES[key], key))
            for state, amount in zip(owned, shares):
                if amount:
                    placed[state["id"]][key] = amount

    id_to_state = {s["id"]: s for s in states}
    changed = 0
    for sid, extra in placed.items():
        state = id_to_state[sid]
        text = state["path"].read_text(encoding="utf-8", errors="ignore")
        updated = merge_resources(text, extra)
        if updated != text:
            state["path"].write_text(updated, encoding="utf-8")
            changed += 1

    if STATES_CSV.exists():
        with STATES_CSV.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fields = list(reader.fieldnames or [])
        for key in KEYS:
            if key not in fields:
                fields.append(key)
        by_id = {int(row["state_id"]): row for row in rows if row.get("state_id")}
        for sid, extra in placed.items():
            row = by_id.get(sid)
            if row:
                for key, amount in extra.items():
                    row[key] = amount
        for row in rows:
            for key in KEYS:
                row.setdefault(key, row.get(key) or 0)
        with STATES_CSV.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    print(f"states patched {changed}")
    if missing_tags:
        print("missing tags", ", ".join(missing_tags))
    for key in KEYS:
        rows = []
        for sid, extra in placed.items():
            if key in extra:
                state = id_to_state[sid]
                other = sum(v for name, v in state["resources"].items())
                rows.append((extra[key], state["owner"], sid, state["loc_pretty"], other))
        rows.sort(reverse=True)
        print(f"== {key} {sum(r[0] for r in rows)}")
        for amount, owner, sid, name, other in rows[:12]:
            print(f"  {amount:3} {owner:4} {sid:5} {name} other={other}")


if __name__ == "__main__":
    main()
