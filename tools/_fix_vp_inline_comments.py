# -*- coding: utf-8 -*-
"""Fix USA victory_points to match vanilla/working Clausewitz format.

error.log evidence:
  set victory points takes 2 parameters: victory_points
on every 2nd+ VP block in USA states.

Working format (vanilla CA, mod Vaasa): numbers alone on their line;
comments only on the opening brace line, never after the province/value pair.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "history" / "states"

# Same USA scope as audit
CW_TAGS = {
    "USA", "WCL", "EAS", "RBL", "ACA", "ASK", "FVA", "EME", "NFA",
    "RBM", "VNM", "TEX", "CSA", "CAL", "NEV", "FLG", "APC",
}
OWNER = re.compile(r"^\s*owner\s*=\s*(\S+)", re.M)
VP_BLOCK = re.compile(
    r"(victory_points\s*=\s*\{)([^}]*)(\})",
    re.S,
)
PAIR = re.compile(r"(\d+)\s+(\d+)(?:\s*#[^\n]*)?")


def fix_text(text: str) -> tuple[str, int]:
    n = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal n
        body = m.group(2)
        pairs = PAIR.findall(body)
        if not pairs:
            return m.group(0)
        # Prefer existing comment text if present after numbers
        comment = ""
        cm = re.search(r"#\s*([^\n]+)", body)
        if cm:
            comment = cm.group(1).strip()
        # Also check brace-line comment already in group1 — leave structure clean
        pid, vp = pairs[0]
        n += 1
        if comment:
            return f"victory_points = {{ # {comment}\n\t\t\t{pid} {vp}\n\t\t}}"
        return f"victory_points = {{\n\t\t\t{pid} {vp}\n\t\t}}"

    return VP_BLOCK.sub(repl, text), n


def main() -> None:
    changed_files = 0
    total_blocks = 0
    for path in sorted(STATES.glob("*.txt")):
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        owners = set(OWNER.findall(text))
        if not (owners & CW_TAGS or "add_core_of = USA" in text):
            continue
        if "victory_points" not in text:
            continue
        # Only rewrite blocks that have inline comments after numbers
        if not re.search(r"victory_points\s*=\s*\{[^}]*\d+\s+\d+\s*#", text, re.S):
            continue
        new_text, n = fix_text(text)
        if new_text == text:
            continue
        # Preserve original newline style
        if b"\r\n" in raw:
            out = new_text.replace("\n", "\r\n").encode("utf-8")
            # avoid double-converting if already mixed — normalize from decoded \n
            out = new_text.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-8")
        else:
            out = new_text.encode("utf-8")
        path.write_bytes(out)
        changed_files += 1
        total_blocks += n
        print(f"fixed {path.name}: {n} blocks")
    print(f"done files={changed_files} blocks={total_blocks}")


if __name__ == "__main__":
    main()
