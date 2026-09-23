#!/usr/bin/env python3
"""Alias one national flag onto every Doomsday ideology for each tag.

HOI4 loads TAG_<ruling_ideology>.tga. Switching ideology must not change the
flag art — every ideology suffix for a tag is the same canonical image.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VANILLA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Hearts of Iron IV\gfx\flags")
OUT = ROOT / "gfx" / "flags"

DOOMSDAY_IDEOS = [
    "social_democracy",
    "social_liberalism",
    "liberal_conservatism",
    "progressive_populism",
    "national_populism",
    "sovereign_democracy",
    "military_junta",
    "absolute_monarchy",
    "state_socialism",
    "left_wing_nationalism",
    "islamic_democracy",
    "theocratic_absolutism",
    "jihadist_fundamentalism",
    "democratic_confederalism",
    "fascism",
    "communism",
    "technocracy",
    "anarcho_communism",
]

# Prefer the "normal" national flag, not wartime ideology variants.
VANILLA_PREF = ("democratic", "neutrality", "communism", "fascism")


def pick_canonical(src_dir: Path, dst_dir: Path, tag: str, van_ideos: dict[str, Path]) -> Path | None:
    # Mod bare TAG.tga wins (custom countries / hand overrides).
    bare = dst_dir / f"{tag}.tga"
    if bare.exists() and bare.stat().st_size > 100:
        return bare
    van_bare = src_dir / f"{tag}.tga"
    if van_bare.exists():
        return van_bare
    for key in VANILLA_PREF:
        if key in van_ideos:
            return van_ideos[key]
    if van_ideos:
        return next(iter(van_ideos.values()))
    return None


def main() -> None:
    written = 0
    for size in ("", "medium", "small"):
        src = VANILLA if size == "" else VANILLA / size
        dst = OUT if size == "" else OUT / size
        if not src.is_dir():
            continue
        dst.mkdir(parents=True, exist_ok=True)

        by_tag: dict[str, dict[str, Path]] = {}
        for p in src.glob("*.tga"):
            if "_" not in p.stem:
                continue
            tag, _, ideo = p.stem.partition("_")
            if ideo not in VANILLA_PREF:
                continue
            by_tag.setdefault(tag, {})[ideo] = p

        # Include mod-only tags that only have a bare flag
        for bare in dst.glob("*.tga"):
            if "_" not in bare.stem:
                by_tag.setdefault(bare.stem, {})

        for tag, van_ideos in by_tag.items():
            canon = pick_canonical(src, dst, tag, van_ideos)
            if canon is None:
                continue

            bare_out = dst / f"{tag}.tga"
            if not bare_out.exists():
                shutil.copy2(canon, bare_out)
                written += 1

            for ideo in DOOMSDAY_IDEOS:
                out_p = dst / f"{tag}_{ideo}.tga"
                shutil.copy2(canon, out_p)
                written += 1

    print(f"wrote {written} flag files (same art per tag across all ideologies)")
    print(
        f"mod flags now: large={len(list(OUT.glob('*.tga')))} "
        f"med={len(list((OUT / 'medium').glob('*.tga')))} "
        f"small={len(list((OUT / 'small').glob('*.tga')))}"
    )


if __name__ == "__main__":
    main()
