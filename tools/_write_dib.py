"""One-shot rewrite of dib_mils.json under campus-unbundle rules. Not a pipeline step."""
from __future__ import annotations

import json
from pathlib import Path

# Sector scores stay 0/1/2. mils is the campus count.
# 1 mil = one serial campus or workshop minimum. Mega-lines 2–4.
# Hulls are dockyards. Services firms omitted. No wartime×2.5. No vs-USA cap.

TAGS = {
    "USA": (45, 2, 2, 2, 2, 2, 2, "Unbundled US campuses (air 11, missiles 11, land 6, ammo/small arms 7, electronics 5, naval weapons 2). SIPRI 39 firms $334B; services omitted. Not dollar-parity 80."),
    "CHI": (36, 2, 2, 2, 2, 2, 2, "Same campus rule as USA. AVIC Chengdu/Shenyang/Xi'an, NORINCO land/ammo, CASC/CASIC missiles, CETC, CSGC ammo. SIPRI 8 firms $88.3B undercounts PLA plants. CSSC hulls are dockyards."),
    "SOV": (26, 2, 2, 1, 2, 1, 2, "UVZ/Omsk/Kurgan armor, ammo plants (2024 ~1.3M 152mm shells), Almaz-Antey/KTRV, Kalashnikov, UAC sanction-thin. Rostec $27.1B is a holding proxy; count plants not the holding."),
    "GER": (13, 2, 2, 1, 2, 2, 1, "Rheinmetall $8.2B ammo/vehicles (Unterlüß and others), KNDS/KMW, Diehl IRIS-T, Hensoldt, Airbus Manching share, HK. 36% Top 100 growth is extra shifts on these campuses."),
    "KOR": (12, 1, 2, 2, 2, 2, 1, "Hanwha $8.0B Changwon tracked, Rotem K2, KAI Sacheon, LIG Nex1, Poongsan ammo. Export boom is these plants, not overtime on 4 mils."),
    "FRA": (12, 1, 2, 2, 2, 2, 1, "Dassault, Thales $11.8B, Safran, Nexter/KNDS Roanne, MBDA France, Naval Group weapons (hulls=docks). Airbus share is territorial plants."),
    "TUR": (12, 2, 2, 1, 2, 2, 1, "Five Top 100 firms $10.1B: ASELSAN, TAI, Baykar, Roketsan, MKE. Plus BMC/FNSS/Otokar. UAV/armor/ammo serial."),
    "RAJ": (12, 2, 1, 2, 2, 2, 1, "HAL several campuses, Munitions India/OFB complexes, BEL, BDL missiles, Avadi HVF. Mazagon is docks. Tejas rate low; the plants still exist."),
    "ENG": (11, 1, 1, 2, 2, 2, 2, "BAE $33.8B includes US work — count UK plants: Warton, munitions, land, RR military, MBDA Stevenage, Babcock/Thales UK. Not the US subsidiary."),
    "JAP": (11, 1, 1, 2, 2, 2, 2, "Five firms $13.3B (+40% 2024): MHI aircraft/missiles, Kawasaki, MELCO, Fujitsu, NEC. Missile buildup is extra lines on these campuses."),
    "ITA": (9, 1, 1, 2, 1, 2, 2, "Leonardo $13.8B (aircraft, helos, electronics), Cameri F-35 FACO, CIO/Iveco, MBDA Italy, Beretta. Fincantieri hulls=docks."),
    "ISR": (9, 1, 1, 1, 2, 2, 1, "Elbit $6.3B, IAI $5.2B, Rafael $4.7B — three large OEMs, several campuses. Peacetime plants; Gaza war is overtime on these sites."),
    "UKR": (9, 2, 1, 0, 2, 1, 0, "UDI $3.0B plus 2026 drone clusters and west-Ukraine artillery/ammo sites that exist on the start map. Not a pre-2022 complete DIB."),
    "DPK": (9, 2, 2, 1, 2, 1, 1, "UN Panel: missile series, artillery/ammo, armor, small arms. Hidden multi-plant DIB. SIPRI milex is not the industry."),
    "PER": (8, 2, 1, 1, 2, 1, 1, "DIO ammo/arms, aerospace (Shahed, ballistic) several sites, HESA limited, licensed armor."),
    "PAK": (8, 2, 2, 1, 2, 1, 1, "HIT Taxila, PAC Kamra, NESCOM, POF Wah. KSEW is docks. Al-Khalid and munitions are serial."),
    "POL": (6, 1, 2, 0, 1, 1, 0, "PGZ $3.04B: HSW Krab, Rosomak, Mesko ammo, PZL. Korean kit assembled here is extra lines, not Korean mils."),
    "SWE": (5, 1, 1, 2, 2, 2, 1, "Saab $5.55B Linköping + missiles, Bofors, Kockums combat systems. One firm, several campuses."),
    "FOR": (5, 1, 0, 1, 2, 2, 1, "NCSIST $3.11B missiles, AIDC fighter. CSBC is docks. One-island tag still has several plants."),
    "SPR": (5, 1, 1, 1, 0, 1, 2, "Airbus Spain (Seville), Santa Bárbara, EXPAL ammo, Navantia weapons. Hulls=docks."),
    "BRA": (5, 2, 1, 2, 1, 0, 1, "Embraer Gavião Peixoto, Avibras, IMBEL, Taurus, Helibras."),
    "CZE": (4, 2, 1, 0, 0, 0, 0, "CSG $3.63B (+193%): ammo initiative for Ukraine, Tatra, Excalibur. Several plants, not one mil."),
    "CAN": (4, 1, 2, 0, 0, 1, 1, "GDLS London LAV serial (major IFV line), Colt Canada, Magellan, CAE $1.46B. Irving hulls=docks."),
    "AST": (4, 1, 1, 0, 0, 1, 1, "Rheinmetall Military Vehicle Centre QLD, Thales Bushmaster, Mulwala/Benalla munitions. ASC=docks."),
    "UAE": (4, 1, 1, 0, 1, 1, 1, "EDGE $4.66B conglomerate: NIMR, Halcon, ADASI, Caracal. Not a single mil."),
    "EGY": (4, 2, 1, 1, 0, 0, 0, "AOI multiple factories: vehicles, licensed aircraft work, ammo. Not one arsenal."),
    "INS": (4, 2, 1, 1, 1, 1, 1, "DEFEND ID $1.14B Top 100: Pindad, PTDI, munitions. PAL=docks."),
    "SER": (4, 2, 1, 0, 1, 0, 0, "Zastava, Yugoimport, Krušik, Sloboda. Real export DIB."),
    "HOL": (3, 0, 1, 0, 0, 2, 2, "Thales Nederland radars/naval combat systems, Damen weapons. Hulls=docks."),
    "SNG": (3, 1, 1, 0, 0, 2, 1, "ST Engineering $2.62B vehicles, electronics, munitions."),
    "VIN": (3, 2, 1, 0, 1, 1, 0, "Z-series arsenals, Viettel. Growing serial, not Top 100."),
    "SAF": (3, 1, 1, 1, 1, 1, 0, "Denel remnant plus Rheinmetall Denel Munition and Paramount. Collapsed OEM, remaining plants still 3."),
    "NOR": (3, 0, 0, 0, 2, 2, 2, "Kongsberg $1.78B NSM/NASAMS plus related plants."),
    "FIN": (3, 1, 2, 0, 0, 1, 0, "Patria AMV serial, Nammo share, Sako."),
    "SWI": (3, 1, 2, 0, 0, 1, 0, "Mowag Piranha/Eagle, RUAG ammo, B&T."),
    "BLR": (3, 1, 1, 0, 0, 2, 0, "MZKT, Peleng, 558 repair, ammo remnant."),
    "BRM": (3, 2, 1, 0, 0, 0, 0, "KaPaSa several Directorate of Defence Industries plants."),
    "BEL": (3, 2, 1, 0, 0, 0, 0, "FN Herstal, John Cockerill, Mecar ammo."),
    "AUS": (3, 2, 1, 0, 0, 0, 0, "Glock, Steyr, GDELS Vienna. Small-arms plus vehicles."),
    "BUL": (3, 2, 0, 0, 0, 0, 0, "Arsenal Kazanlak, VMZ Sopot. Major ammo exporters."),
    "ROM": (3, 2, 1, 1, 0, 0, 0, "ROMARM, Aerostar, IAR Brașov."),
    "SAU": (2, 1, 0, 0, 1, 1, 0, "SAMI/GAMI nascent munitions cluster. Still mostly imports; 2 not 1."),
    "HUN": (2, 1, 2, 0, 0, 0, 0, "Rheinmetall Lynx Zalaegerszeg plus Hungarian ammo."),
    "GRE": (2, 1, 1, 0, 0, 1, 1, "EAS / Hellenic Defence munitions and vehicles."),
    "DEN": (2, 0, 0, 0, 1, 2, 1, "Terma radars plus limited munitions."),
    "SLO": (2, 1, 1, 0, 0, 0, 0, "DMD / ZTS / Konštrukta Zuzana SPH serial."),
    "CRO": (2, 2, 0, 0, 0, 0, 0, "HS Produkt plus limited vehicles."),
    "BOS": (2, 2, 0, 0, 0, 0, 0, "Igman / UNIS ammo export."),
    "ARG": (2, 1, 1, 1, 0, 0, 0, "FAdeA, DGFM, FM. Residual aircraft/vehicle/ammo."),
    "COL": (2, 2, 0, 0, 0, 0, 0, "INDUMIL several sites: small arms and munitions."),
    "ALG": (2, 2, 1, 0, 0, 0, 0, "Khenchela ammo plus licensed vehicle plants."),
    "ETH": (2, 2, 1, 0, 0, 0, 0, "Gafat and Homicho."),
    "SIA": (2, 2, 1, 0, 0, 0, 0, "RTA arsenals, Chaiseri, Panus."),
    "MAL": (2, 1, 1, 0, 0, 0, 0, "DEFTECH plus SME ordnance."),
    "BAN": (2, 2, 0, 0, 0, 0, 0, "Bangladesh Ordnance Factories complex."),
    "KAZ": (2, 1, 1, 0, 0, 0, 0, "Petropavl plus Kazakhstan Paramount."),
    "AZR": (2, 2, 1, 0, 0, 0, 0, "MODAR munitions and vehicle assembly."),
    "JOR": (2, 1, 1, 0, 0, 0, 0, "KADDB vehicles and munitions."),
    "SUD": (2, 2, 0, 0, 1, 0, 0, "Yarmouk Industrial Complex: ammo plus Iranian-linked missile work."),
    "HOU": (2, 1, 0, 0, 2, 1, 0, "Houthi missile/drone conversion. Largest non-state producer."),
}

ONES = {
    "CHL": (2, 0, 0, 0, 0, 0, "FAMAE small arms/munitions. ASMAR=docks."),
    "MEX": (2, 1, 0, 0, 0, 0, "SEDENA national arsenal."),
    "VEN": (2, 0, 0, 0, 0, 0, "CAVIM degraded but a plant."),
    "PRU": (2, 0, 0, 0, 0, 0, "FAME. SIMA=docks."),
    "CUB": (2, 0, 0, 0, 0, 0, "Unión de la Industria Militar."),
    "NGA": (2, 0, 0, 0, 0, 0, "DICON."),
    "KEN": (2, 0, 0, 0, 0, 0, "Kenya Ordnance Factories."),
    "ZIM": (2, 0, 0, 0, 0, 0, "Zimbabwe Defence Industries."),
    "GHA": (1, 0, 0, 0, 0, 0, "DIHC limited serial small arms."),
    "PHI": (2, 0, 0, 0, 0, 0, "Government Arsenal."),
    "SRL": (1, 0, 0, 0, 0, 0, "Army ordnance."),
    "UZB": (1, 1, 0, 0, 0, 0, "Chirchiq remnant."),
    "GEO": (2, 0, 0, 0, 1, 0, "STC Delta."),
    "ARM": (1, 0, 0, 0, 0, 0, "National small-arms/ammo."),
    "MOR": (1, 0, 0, 0, 0, 0, "Licensed assembly."),
    "TUN": (1, 0, 0, 0, 0, 0, "Limited national arsenal."),
    "IRQ": (1, 0, 0, 0, 0, 0, "Al-Zawraa reconstituting. Not pre-2003."),
    "POR": (1, 0, 0, 0, 0, 0, "idD / OGMA limited production."),
}

WORKSHOPS = {
    "HEZ": (1, 0, 0, 2, 1, 0, "Hezbollah rocket/UAV workshops."),
    "HAM": (1, 0, 0, 1, 0, 0, "Hamas rocket/tunnel workshops."),
    "PAL": (1, 0, 0, 0, 0, 0, "West Bank workshop assembly."),
    "ROJ": (1, 0, 0, 0, 0, 0, "SDF/Rojava workshops."),
    "SYR": (1, 0, 0, 0, 0, 0, "Damascus/Aleppo remnant workshops."),
    "SNA": (1, 0, 0, 0, 0, 0, "SNA workshops."),
    "DRZ": (1, 0, 0, 0, 0, 0, "Suwayda workshops."),
    "YEM": (1, 0, 0, 0, 0, 0, "PLC remnant assembly."),
    "STC": (1, 0, 0, 0, 0, 0, "Aden workshop assembly."),
    "YNR": (1, 0, 0, 0, 0, 0, "Mocha workshop assembly."),
    "NUG": (1, 0, 0, 0, 0, 0, "NUG/PDF cottage production."),
    "M23": (1, 0, 0, 0, 0, 0, "M23 field workshops."),
    "RSF": (1, 0, 0, 0, 0, 0, "RSF workshops."),
    "AZA": (1, 0, 0, 0, 0, 0, "Azawad workshops."),
    "SHB": (1, 0, 0, 0, 0, 0, "Al-Shabaab IED/small-arms workshops."),
    "JUB": (1, 0, 0, 0, 0, 0, "Jubaland workshops."),
    "SOM": (1, 0, 0, 0, 0, 0, "Somali government workshops."),
    "SML": (1, 0, 0, 0, 0, 0, "Somaliland workshops."),
    "PNT": (1, 0, 0, 0, 0, 0, "Puntland workshops."),
    "SSD": (1, 0, 0, 0, 0, 0, "South Sudan workshops."),
    "SIO": (1, 0, 0, 0, 0, 0, "SPLM-IO workshops."),
    "LNA": (1, 0, 0, 0, 0, 0, "LNA workshops."),
    "LBA": (1, 0, 0, 0, 0, 0, "Tripoli-side workshops."),
    "NRF": (1, 0, 0, 0, 0, 0, "NRF Panjshir workshops."),
    "PMR": (1, 1, 0, 0, 0, 0, "Transnistria leftover Soviet plants."),
    "ABK": (1, 0, 0, 0, 0, 0, "Abkhaz workshops."),
    "SOE": (1, 0, 0, 0, 0, 0, "South Ossetia workshops."),
    "CAR": (1, 0, 0, 0, 0, 0, "CAR allied workshops."),
}


def rec(mils, sa, ar, ac, mi, el, nw, source):
    return {
        "mils": mils,
        "small_arms": sa,
        "armor": ar,
        "aircraft": ac,
        "missiles": mi,
        "electronics": el,
        "naval_weapons": nw,
        "source": source,
    }


def main() -> None:
    tags = {}
    for tag, t in TAGS.items():
        tags[tag] = rec(*t)
    for tag, t in ONES.items():
        sa, ar, ac, mi, el, nw, source = t
        tags[tag] = rec(1, sa, ar, ac, mi, el, nw, source)
    for tag, t in WORKSHOPS.items():
        sa, ar, ac, mi, el, nw, source = t
        tags[tag] = rec(1, sa, ar, ac, mi, el, nw, source)
    payload = {
        "note": "Campus-unbundle DIB. 1 mil = one serial production campus, or the HOI4 workshop minimum. Mega-campuses with parallel halls are 2–4. Same rule for every tag: do not bundle China/Korea/Germany while the US is unbundled. Hulls are dockyards. Services firms omitted. No wartime×2.5. No vs-Germany/USA cap. Do not use fighter unit counts (airframe IC is still near vanilla). SIPRI Top 100 2024 is a scale cross-check; PLA/Rostec plants are undercounted there so campuses are counted directly.",
        "sources": [
            "SIPRI Top 100 Arms-producing and Military Services Companies, 2024 (fact sheet Dec 2025)",
            "SIPRI Arms Transfers Database",
            "IISS The Military Balance (production, not inventory)",
            "CSIS munitions / industrial-base reporting 2023–2025",
            "UN Panel of Experts on DPRK; HIT/PAC/NESCOM; AOI; Denel; Embraer Defense; KaPaSa",
        ],
        "ic_note": "Inf kit 2.5–4.0 so a 1-mil arsenal is a kit line. Small-plane airframe_4 is still ~10 IC; do not set mils from fighter deliveries. Tanks 10–28; missiles 36–74.",
        "tags": tags,
    }
    path = Path(__file__).resolve().parent / "data" / "dib_mils.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total = sum(r["mils"] for r in tags.values())
    print(f"wrote {path} tags={len(tags)} mils={total}")


if __name__ == "__main__":
    main()
