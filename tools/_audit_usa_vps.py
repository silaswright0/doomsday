# -*- coding: utf-8 -*-
"""Audit USA victory points vs localisation. Evidence only."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "history" / "states"
LOCS = [
    ROOT / "localisation" / "english" / "doomsday_usa_cities_l_english.yml",
    ROOT / "localisation" / "english" / "replace" / "doomsday_usa_cities_l_english.yml",
    ROOT / "localisation" / "replace" / "doomsday_usa_cities_l_english.yml",
    ROOT / "localisation" / "replace" / "doomsday_overrides_l_english.yml",
]

VP_BLOCK = re.compile(r"victory_points\s*=\s*\{([^}]*)\}", re.S)
PAIR = re.compile(r"(\d+)\s+(\d+)(?:\s*#\s*([^\n]*))?")
PROV_BLOCK = re.compile(r"provinces\s*=\s*\{([^}]*)\}", re.S)
OWNER = re.compile(r"^\s*owner\s*=\s*(\S+)", re.M)


def has_bom(path: Path) -> bool:
    return path.read_bytes()[:3] == b"\xef\xbb\xbf"


def load_loc_keys(path: Path) -> dict[int, str]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8-sig")
    out: dict[int, str] = {}
    for m in re.finditer(r'VICTORY_POINTS_(\d+)\s*:\d*\s*"(.*)"\s*$', text, re.M):
        out[int(m.group(1))] = m.group(2)
    return out


def main() -> None:
    print("=== LOC FILES ===")
    all_loc: dict[int, str] = {}
    for p in LOCS:
        if not p.exists():
            print(f"MISSING {p.relative_to(ROOT)}")
            continue
        raw = p.read_bytes()
        keys = load_loc_keys(p)
        lines = raw.decode("utf-8-sig").splitlines()
        bad = []
        for i, line in enumerate(lines, 1):
            s = line.strip()
            if not s or s.startswith("l_english") or s.startswith("#"):
                continue
            if "VICTORY_POINTS_" in s:
                if not re.match(r'^VICTORY_POINTS_\d+:\d*\s+".*"\s*$', s):
                    bad.append((i, s[:100]))
        print(
            f"{p.relative_to(ROOT)}: size={len(raw)} bom={has_bom(p)} "
            f"header={lines[0]!r} keys={len(keys)} bad={len(bad)}"
        )
        for b in bad[:8]:
            print(f"  BAD line {b[0]}: {b[1]!r}")
        all_loc.update(keys)

    # USA states: owner USA or known CW tags, or add_core_of USA
    cw_tags = {
        "USA", "WCL", "EAS", "RBL", "ACA", "ASK", "FVA", "EME", "NFA",
        "RBM", "VNM", "TEX", "CSA", "CAL", "NEV", "FLG", "APC",
    }
    usa_files: list[Path] = []
    for p in sorted(STATES.glob("*.txt")):
        t = p.read_text(encoding="utf-8", errors="replace")
        owners = set(OWNER.findall(t))
        if owners & cw_tags or "add_core_of = USA" in t:
            usa_files.append(p)

    print(f"\n=== USA STATE FILES ({len(usa_files)}) ===")
    multi = []
    missing_prov = []
    vp_entries = []  # file, pid, vp, comment, in_provs, owner
    for p in usa_files:
        t = p.read_text(encoding="utf-8", errors="replace")
        owners = OWNER.findall(t)
        owner = owners[0] if owners else "?"
        pm = PROV_BLOCK.search(t)
        provs = set(int(x) for x in re.findall(r"\d+", pm.group(1))) if pm else set()
        for m in VP_BLOCK.finditer(t):
            body = m.group(1)
            pairs = PAIR.findall(body)
            if len(pairs) > 1:
                multi.append((p.name, [(int(a), int(b)) for a, b, _ in pairs]))
            for pid_s, vp_s, name in pairs:
                pid, vp = int(pid_s), int(vp_s)
                entry = (p.name, pid, vp, (name or "").strip(), pid in provs, owner)
                vp_entries.append(entry)
                if pid not in provs:
                    missing_prov.append(entry)

    print(f"VP entries: {len(vp_entries)}")
    print(f"Multi-province blocks: {len(multi)}")
    for m in multi:
        print(f"  MULTI {m[0]}: {m[1]}")
    print(f"VP province not in state provinces=: {len(missing_prov)}")
    for e in missing_prov[:40]:
        print(f"  {e[0]} owner={e[5]} pid={e[1]} vp={e[2]} comment={e[3]!r}")

    vp_pids = {e[1] for e in vp_entries}
    no_loc = sorted(vp_pids - set(all_loc))
    print(f"\n=== CROSS CHECK ===")
    print(f"Unique VP provinces: {len(vp_pids)}")
    print(f"Union loc keys: {len(all_loc)}")
    print(f"VP without any loc key: {len(no_loc)}")
    for pid in no_loc[:50]:
        hits = [e for e in vp_entries if e[1] == pid]
        print(f"  {pid}: {hits[0][0]} comment={hits[0][3]!r} owner={hits[0][5]}")

    # Sample California / Alabama / Maryland specifically
    samples = {
        "California": "378-California.txt",
        "Alabama": "367-Alabama.txt",
        "Maryland": "361-Maryland.txt",
        "SanFran": "1124-San Francisco.txt",
    }
    print("\n=== SAMPLE STATE VP BLOCKS ===")
    for label, name in samples.items():
        p = STATES / name
        if not p.exists():
            print(f"{label}: MISSING FILE {name}")
            continue
        t = p.read_text(encoding="utf-8", errors="replace")
        blocks = VP_BLOCK.findall(t)
        print(f"{label} ({name}): {len(blocks)} blocks")
        for body in blocks:
            pairs = PAIR.findall(body)
            for pid_s, vp_s, cmt in pairs:
                pid = int(pid_s)
                print(
                    f"  pid={pid} vp={vp_s} comment={(cmt or '').strip()!r} "
                    f"loc={all_loc.get(pid, 'MISSING')!r}"
                )

    # Check descriptor / replace_path
    desc = ROOT / "descriptor.mod"
    if desc.exists():
        print("\n=== descriptor.mod ===")
        print(desc.read_text(encoding="utf-8", errors="replace")[:800])

    # Documents/localisation nudger overrides
    nudge = Path(r"c:\Users\siwri\Documents\Paradox Interactive\Hearts of Iron IV\localisation")
    print(f"\n=== Documents localisation folder exists={nudge.exists()} ===")
    if nudge.exists():
        files = list(nudge.rglob("*.yml"))
        print(f"yml files: {len(files)}")
        for f in files[:30]:
            print(f"  {f}")


if __name__ == "__main__":
    main()
