from pathlib import Path

for p in Path("tools").glob("_*.py"):
    t = p.read_text(encoding="utf-8")
    old = 'struct.pack_into("<I", hdr, 20, W * H * 4)'
    new = 'struct.pack_into("<I", hdr, 20, W * H * 4)'
    if old in t:
        p.write_text(t.replace(old, new), encoding="utf-8", newline="\n")
        print("patched", p.name)
