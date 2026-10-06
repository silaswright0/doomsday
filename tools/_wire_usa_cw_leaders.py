# -*- coding: utf-8 -*-
"""Wire USA CW leader names + portrait GFX into history/focus/effects/gfx."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

UPDATES = {
    "PTF - Patriot Front.txt": ("Thomas Rousseau", "GFX_portrait_PTF_leader"),
    "SFT - San Francisco.txt": ("Peter Thiel", "GFX_portrait_SFT_leader"),
    "VIR - Virgin Islands.txt": ("David Rockefeller", "GFX_portrait_VIR_leader"),
    "WCL - Pacific Republic.txt": ("Gavin Newsom", "GFX_portrait_WCL_leader"),
    "NYF - New York Finance.txt": ("Finance Board", "GFX_portrait_NYF_leader"),
    "EAS - Eastern Compact.txt": ("Alexandria Ocasio-Cortez", "GFX_portrait_EAS_leader"),
    "RBM - Heartland Compact.txt": ("Marco Rubio", "GFX_portrait_RBM_leader"),
    "VNM - American Mandate.txt": ("JD Vance", "GFX_portrait_VNM_leader"),
}

GFX_ENTRIES = [
    ("PTF", "gfx/leaders/PTF/Portrait_PTF_leader.dds"),
    ("SFT", "gfx/leaders/SFT/Portrait_SFT_leader.dds"),
    ("VIR", "gfx/leaders/VIR/Portrait_VIR_leader.dds"),
    ("WCL", "gfx/leaders/WCL/Portrait_WCL_leader.dds"),
    ("NYF", "gfx/leaders/NYF/Portrait_NYF_leader.dds"),
    ("EAS", "gfx/leaders/EAS/Portrait_EAS_leader.dds"),
    ("RBM", "gfx/leaders/RBM/Portrait_RBM_leader.dds"),
    ("VNM", "gfx/leaders/VNM/Portrait_VNM_leader.dds"),
]


def patch_history() -> None:
    hist = ROOT / "history" / "countries"
    for fname, (name, gfx) in UPDATES.items():
        path = hist / fname
        text = path.read_text(encoding="utf-8")

        def repl(m: re.Match[str]) -> str:
            return (
                "create_country_leader = {\n"
                f'\tname = "{name}"\n'
                f"\tpicture = {gfx}\n"
                f"\tideology = {m.group(1)}\n"
                "}"
            )

        text2, n = re.subn(
            r'create_country_leader = \{\s*name = "[^"]+"\s*picture = GFX_portrait_\w+\s*ideology = (\S+)\s*\}',
            repl,
            text,
            count=1,
        )
        if n != 1:
            raise SystemExit(f"history patch failed for {fname}: {n}")
        path.write_text(text2, encoding="utf-8", newline="\n")
        print("history", fname)


def patch_focus() -> None:
    path = ROOT / "common" / "national_focus" / "usa.txt"
    text = path.read_text(encoding="utf-8")
    repls = [
        (
            'name = "Alexandria Ocasio-Cortez" picture = GFX_portrait_unknown',
            'name = "Alexandria Ocasio-Cortez" picture = GFX_portrait_EAS_leader',
        ),
        (
            'name = "Gavin Newsom" picture = GFX_portrait_unknown',
            'name = "Gavin Newsom" picture = GFX_portrait_WCL_leader',
        ),
        (
            'name = "Marco Rubio" picture = GFX_portrait_unknown',
            'name = "Marco Rubio" picture = GFX_portrait_RBM_leader',
        ),
        (
            'name = "JD Vance" picture = GFX_portrait_unknown',
            'name = "JD Vance" picture = GFX_portrait_VNM_leader',
        ),
    ]
    for old, new in repls:
        c = text.count(old)
        text = text.replace(old, new)
        print("focus", old.split("name = ")[1][:28], "x", c)
    path.write_text(text, encoding="utf-8", newline="\n")


def patch_usa_effect() -> None:
    path = ROOT / "common" / "scripted_effects" / "doomsday_usa.txt"
    text = path.read_text(encoding="utf-8")
    old = (
        "create_country_leader = {\n"
        '\t\t\t\tname = "JD Vance"\n'
        "\t\t\t\tpicture = GFX_portrait_unknown\n"
        '\t\t\t\texpire = "2065.1.1"\n'
        "\t\t\t\tideology = national_populist\n"
        "\t\t\t}"
    )
    new = old.replace("GFX_portrait_unknown", "GFX_portrait_VNM_leader")
    if old not in text:
        raise SystemExit("doomsday_usa Vance block missing")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")
    print("effect Vance portrait")


def patch_gfx() -> None:
    path = ROOT / "interface" / "doomsday_portraits.gfx"
    text = path.read_text(encoding="utf-8")
    block = []
    for tag, tex in GFX_ENTRIES:
        name = f"GFX_portrait_{tag}_leader"
        if name in text:
            print("gfx already", name)
            continue
        block.append(
            "\tspriteType = {\n"
            f'\t\tname = "{name}"\n'
            f'\t\ttexturefile = "{tex}"\n'
            "\t}\n"
        )
    if not block:
        print("gfx nothing to add")
        return
    if not text.rstrip().endswith("}"):
        raise SystemExit("unexpected gfx footer")
    # insert before final closing brace of spriteTypes
    idx = text.rfind("}")
    text = text[:idx] + "".join(block) + text[idx:]
    path.write_text(text, encoding="utf-8", newline="\n")
    print("gfx added", len(block))


def main() -> None:
    patch_history()
    patch_focus()
    patch_usa_effect()
    patch_gfx()


if __name__ == "__main__":
    main()
