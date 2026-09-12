"""Sanity-check history/states and retag buildings.txt after province moves."""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import patch_doomsday_map as p  # noqa: E402

CATS = {
    "wasteland",
    "enclave",
    "small_island",
        "tiny_island",
        "large_island",
        "pastoral",
    "rural",
    "town",
    "large_town",
    "city",
    "large_city",
    "metropolis",
    "megalopolis",
}


def main(retag_provs: set[int] | None = None) -> int:
    states_dir = ROOT / "history" / "states"
    errors: list[str] = []
    id_to_file: dict[int, str] = {}
    id_to_provs: dict[int, list[int]] = {}
    id_to_owner: dict[int, str] = {}
    prov_to_states: dict[int, list[int]] = defaultdict(list)

    for path in states_dir.glob("*.txt"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        mid = re.search(r"id\s*=\s*(\d+)", text)
        if not mid:
            errors.append(f"{path.name}: no id")
            continue
        sid = int(mid.group(1))
        if sid in id_to_file:
            errors.append(f"duplicate state id {sid}: {id_to_file[sid]} and {path.name}")
        id_to_file[sid] = path.name
        mprov = re.search(r"provinces\s*=\s*\{([^}]*)\}", text)
        if not mprov:
            errors.append(f"{path.name} id={sid}: no provinces block")
            provs: list[int] = []
        else:
            provs = [int(x) for x in re.findall(r"\d+", mprov.group(1))]
        if not provs:
            errors.append(f"{path.name} id={sid}: empty provinces")
        id_to_provs[sid] = provs
        for pid in provs:
            prov_to_states[pid].append(sid)
        owner = re.search(r"owner\s*=\s*([A-Z0-9]{3})", text)
        if not owner:
            errors.append(f"{path.name} id={sid}: no owner")
        else:
            id_to_owner[sid] = owner.group(1)
        cat = re.search(r'state_category\s*=\s*"?(\w+)"?', text)
        if not cat:
            errors.append(f"{path.name} id={sid}: no state_category")
        elif cat.group(1) not in CATS:
            errors.append(f"{path.name} id={sid}: invalid state_category {cat.group(1)}")
        if not re.search(r"manpower\s*=", text):
            errors.append(f"{path.name} id={sid}: no manpower")
        pset = set(provs)
        stripped = re.sub(r"#.*", "", text)
        for vm in re.finditer(r"victory_points\s*=\s*\{([^}]*)\}", stripped):
            nums = [int(n) for n in re.findall(r"\d+", vm.group(1))]
            if nums and nums[0] not in pset:
                errors.append(f"{path.name}: VP {nums[0]} not in state {sid}")

    max_id = max(id_to_file)
    missing_ids = [i for i in range(1, max_id + 1) if i not in id_to_file]
    if missing_ids:
        preview = missing_ids[:30]
        extra = f" count={len(missing_ids)}" if len(missing_ids) > 30 else ""
        errors.append(f"missing state ids (HOI4 crash): {preview}{extra}")

    land: set[int] = set()
    sea: set[int] = set()
    all_def: dict[int, str] = {}
    for line in (ROOT / "map" / "definition.csv").read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.split(";")
        if len(parts) < 5:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        kind = parts[4]
        all_def[pid] = kind
        if kind == "land":
            land.add(pid)
        elif kind == "sea":
            sea.add(pid)

    dup_provs = {pid: sids for pid, sids in prov_to_states.items() if len(sids) > 1}
    if dup_provs:
        errors.append(f"duplicate provinces in multiple states count={len(dup_provs)} sample={dict(list(dup_provs.items())[:10])}")
    unknown = [pid for pid in prov_to_states if pid not in all_def]
    if unknown:
        errors.append(f"provinces not in definition.csv: {unknown[:20]} count={len(unknown)}")
    sea_in_state = [pid for pid in prov_to_states if pid in sea]
    if sea_in_state:
        errors.append(f"sea provinces assigned to states: {sea_in_state[:20]} count={len(sea_in_state)}")
    unowned_land = sorted((land - set(prov_to_states)) - {0})
    if unowned_land:
        errors.append(f"land provinces in no state: {unowned_land[:40]} count={len(unowned_land)}")

    print(f"states={len(id_to_file)} max_id={max_id} land={len(land)} assigned_land={len(set(prov_to_states) & land)}")
    print(f"6953 now in states={prov_to_states.get(6953)} kind={all_def.get(6953)}")
    print(f"802 provinces={id_to_provs.get(802)} owner={id_to_owner.get(802)}")
    print(f"108 provinces={id_to_provs.get(108)}")

    print("loading provinces.bmp...")
    im = Image.open(ROOT / "map" / "provinces.bmp")
    px = im.load()
    w, h = im.size
    rgb_to_id, id_to_kind = p.load_definition_maps(ROOT / "map" / "definition.csv")
    prov_to_state = {pid: sids[0] for pid, sids in prov_to_states.items() if len(sids) == 1}

    if retag_provs:
        n = p.retag_buildings_by_province(
            ROOT / "map" / "buildings.txt",
            px,
            h,
            w,
            h,
            rgb_to_id,
            id_to_kind,
            prov_to_state,
            retag_provs,
        )
        print(f"retagged buildings.txt rows on {sorted(retag_provs)}: {n}")

    mismatch = 0
    examples: list[str] = []
    bpath = ROOT / "map" / "buildings.txt"
    lines = bpath.read_text(encoding="utf-8", errors="ignore").splitlines()
    bad_fields = 0
    for i, line in enumerate(lines, 1):
        parts = line.split(";")
        if len(parts) != 7:
            bad_fields += 1
            continue
        try:
            sid = int(parts[0])
        except ValueError:
            errors.append(f"buildings.txt line {i} bad state id")
            continue
        pid = p._province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
        if pid is None or id_to_kind.get(pid) != "land":
            continue
        real_state = prov_to_state.get(pid)
        if real_state is not None and real_state != sid:
            mismatch += 1
            if pid in (retag_provs or set()) or sid in {108, 802}:
                errors.append(
                    f"buildings.txt {parts[1]} on province {pid} tagged state {sid}, belongs to {real_state}"
                )
            elif len(examples) < 5:
                examples.append(f"state {sid} row on prov {pid} (belongs to {real_state}) type={parts[1]}")
    if bad_fields:
        errors.append(f"buildings.txt has {bad_fields} rows with !=7 fields")

    print(f"buildings.txt land-pixel state mismatches (all, vanilla noise included): {mismatch}")
    for e in examples:
        print("  leftover example:", e)

    still = 0
    for line in lines:
        parts = line.split(";")
        if len(parts) < 5:
            continue
        pid = p._province_at(px, parts[2], parts[4], h, rgb_to_id, w, h)
        if pid == 6953:
            still += 1
            print(f"  6953 building now tagged state={parts[0]} type={parts[1]}")
    print(f"building rows on 6953: {still}")

    if errors:
        print("FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("OK: every state has owner, category, manpower, provinces; land provinces unique; no sea-in-state; no id gaps")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(retag_provs={6953}))
