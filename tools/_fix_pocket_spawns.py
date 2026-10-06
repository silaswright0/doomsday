from pathlib import Path
import re

POCKETS = [
    (261, 6855), (261, 9775), (261, 6890), (261, 6874), (261, 9808),
    (395, 954), (395, 1527), (395, 12365),
    (378, 9814), (378, 6681), (378, 1562), (378, 9713), (378, 6665), (378, 823),
    (377, 853), (377, 3834),
    (376, 4975), (376, 2102),
    (379, 4799), (379, 12399), (379, 4816),
    (382, 1827), (382, 868),
    (366, 1843), (366, 10352), (366, 1572),
    (363, 10051), (363, 7138), (363, 10081),
    (362, 788),
    (375, 12341),
    (368, 12670),
    (386, 1690), (386, 7255),
    (385, 10305), (385, 4347),
    (358, 859),
]


def make_block(name: str, div_name: str, template: str, exp: str, equip: str) -> str:
    lines = [
        f"{name} = {{",
        "\t# Country-scoped. Province is_controlled_by PREV = spawning country.",
    ]
    div = (
        f'name = \\"{div_name}\\" division_template = \\"{template}\\" '
        f"start_experience_factor = {exp} start_equipment_factor = {equip}"
    )
    for sid, pid in POCKETS:
        lines.extend(
            [
                "\tif = {",
                "\t\tlimit = {",
                "\t\t\tcheck_variable = { dd_cw_spawn > 0 }",
                f"\t\t\t{pid} = {{ is_controlled_by = PREV }}",
                "\t\t}",
                f"\t\t{sid} = {{",
                "\t\t\tcreate_unit = {",
                f'\t\t\t\tdivision = "{div}"',
                "\t\t\t\towner = PREV",
                "\t\t\t\tcount = 1",
                f"\t\t\t\tprioritize_location = {pid}",
                "\t\t\t\tallow_spawning_on_enemy_provs = yes",
                "\t\t\t}",
                "\t\t}",
                "\t\tsubtract_from_variable = { dd_cw_spawn = 1 }",
                "\t}",
            ]
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


militia = make_block(
    "dd_usa_cw_spawn_militia_pockets", "Militia", "Militia", "0.2", "0.55"
)
ng = make_block(
    "dd_usa_cw_spawn_ng_pockets",
    "National Guard",
    "National Guard",
    "0.3",
    "0.65",
)

p = Path("common/scripted_effects/doomsday_usa_war.txt")
text = p.read_text(encoding="utf-8")
text2, n1 = re.subn(
    r"dd_usa_cw_spawn_militia_pockets = \{.*?\n\}",
    militia.rstrip(),
    text,
    count=1,
    flags=re.S,
)
text3, n2 = re.subn(
    r"dd_usa_cw_spawn_ng_pockets = \{.*?\n\}",
    ng.rstrip(),
    text2,
    count=1,
    flags=re.S,
)
print("replaced militia", n1, "ng", n2)
assert n1 == 1 and n2 == 1
p.write_text(text3, encoding="utf-8", newline="\n")
print("braces", text3.count("{"), text3.count("}"))
print("bad ROOT refs", "is_controlled_by = ROOT" in text3 or "owner = ROOT" in text3)
