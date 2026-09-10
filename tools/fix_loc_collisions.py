"""Move colliding loc keys: identical dupes out, real overrides into localisation/replace/."""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = Path(r"C:\Users\siwri\Documents\Paradox Interactive\Hearts of Iron IV\logs\text.log")

MOD_FILES = [
    ROOT / "localisation" / "english" / "doomsday_l_english.yml",
    ROOT / "localisation" / "english" / "doomsday_economy_l_english.yml",
    ROOT / "localisation" / "english" / "doomsday_warfare_l_english.yml",
]


def key_of(line: str) -> str | None:
    s = line.strip()
    if not s or s.startswith("#") or s.startswith("l_english"):
        return None
    m = re.match(r"^([A-Za-z0-9_]+):", s)
    return m.group(1) if m else None


def main() -> None:
    collisions: dict[str, dict[str, str | None]] = defaultdict(
        lambda: {"mod": None, "vanilla": None}
    )
    pat = re.compile(r"key: ([^,]+), file: ([^,]+), value: (.*)$")
    for line in LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.search(line)
        if not m:
            continue
        key, f, val = m.group(1), m.group(2).replace("\\", "/"), m.group(3)
        if "doomsday" in f:
            collisions[key]["mod"] = val
        else:
            collisions[key]["vanilla"] = val

    existing_replace = ROOT / "localisation" / "replace" / "doomsday_overrides_l_english.yml"
    overrides: dict[str, str] = {}
    if existing_replace.exists():
        for line in existing_replace.read_text(encoding="utf-8-sig").splitlines(True):
            k = key_of(line)
            if k:
                raw = line if line.endswith("\n") else line + "\n"
                overrides[k] = raw if raw[:1].isspace() else " " + raw.lstrip()

    dropped = 0
    moved = 0
    for path in MOD_FILES:
        text = path.read_text(encoding="utf-8-sig")
        kept: list[str] = []
        for line in text.splitlines(True):
            k = key_of(line)
            if k is None or k not in collisions:
                kept.append(line)
                continue
            ours = collisions[k]["mod"]
            van = collisions[k]["vanilla"]
            if ours is not None and van is not None and ours == van:
                dropped += 1
                continue
            raw = line if line.endswith("\n") else line + "\n"
            if not raw[:1].isspace():
                raw = " " + raw.lstrip()
            overrides[k] = raw
            moved += 1
        path.write_bytes(b"\xef\xbb\xbf" + "".join(kept).encode("utf-8"))

    replace_dir = ROOT / "localisation" / "replace"
    replace_dir.mkdir(parents=True, exist_ok=True)
    body = "l_english:\n" + "".join(overrides[k] for k in sorted(overrides))
    if not body.endswith("\n"):
        body += "\n"
    (replace_dir / "doomsday_overrides_l_english.yml").write_bytes(
        b"\xef\xbb\xbf" + body.encode("utf-8")
    )
    print(f"log collisions: {len(collisions)}")
    print(f"dropped identical: {dropped}")
    print(f"moved this run: {moved}")
    print(f"override keys ({len(overrides)}): {', '.join(sorted(overrides))}")


if __name__ == "__main__":
    main()
