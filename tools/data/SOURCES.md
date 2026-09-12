# Cited sources for 2026 state manpower and buildings

Retrieved during pipeline ingest unless a file header says otherwise.
Country totals are control totals; subnational rows only allocate.

## Population

| Dataset | Publisher | Year / vintage | What it feeds | URL |
|---|---|---|---|---|
| World Population Prospects 2024, medium variant, 1 July 2026 | UN DESA Population Division | 2024 revision, year 2026 | Country `pop` control totals | https://population.un.org/wpp/ |
| Wikimedia `Data:WPP24_2026-07.tab` | Wikimedia Commons (UN WPP 2024 dump) | 2026-07 | Frozen `un_wpp2026.json` | https://commons.wikimedia.org/wiki/Data:WPP24_2026-07.tab |
| WorldPop unconstrained population | WorldPop | 2020/2025 | Intended zonal gold path | https://www.worldpop.org/ |
| HOI4 `provinces.bmp` pixel counts | Paradox map + this mod | n/a | Area-density fallback when no census match (`state_pixel_area.json`) | `map/provinces.bmp` |
| Wikidata P1082 on ISO 3166-2 (P300) units | Wikidata | latest truthy statement | Subnational pop when no census table match | https://query.wikidata.org/sparql |
| US Census Bureau Vintage 2024 state estimates | US Census Bureau | 2024-07-01 | USA state manpower | https://www.census.gov/programs-surveys/popest.html |
| HOI4 `provinces.bmp` pixel counts | Paradox map + this mod | n/a | Area weight when no census match | `map/provinces.bmp` |

## Industry / buildings

| Dataset | Publisher | Year | What it feeds | URL |
|---|---|---|---|---|
| Industry value added, current US$ (`NV.IND.TOTL.CD`) | World Bank WDI | latest available | Civilian factories (mining, manufacturing, utilities, construction) | https://data.worldbank.org/indicator/NV.IND.TOTL.CD |
| Agriculture value added, current US$ (`NV.AGR.TOTL.CD`) | World Bank WDI | latest available | Civilian factories (added to industry) | https://data.worldbank.org/indicator/NV.AGR.TOTL.CD |
| Industry / agriculture % of GDP (`NV.IND.TOTL.ZS`, `NV.AGR.TOTL.ZS`) | World Bank WDI | latest | Fallback when current USD is missing | https://data.worldbank.org/indicator/NV.IND.TOTL.ZS |
| Manufacturing value added, current US$ (`NV.IND.MANF.CD`) | World Bank WDI | latest available (usually 2023–2024) | Fallback if industry+agri missing, ×1.67 | https://data.worldbank.org/indicator/NV.IND.MANF.CD |
| Military expenditure, current US$ (`MS.MIL.XPND.CD`) | World Bank WDI (SIPRI underlying) | latest | Ammo stockpiles / extra buildings, not mil counts | https://data.worldbank.org/indicator/MS.MIL.XPND.CD |
| SIPRI Military Expenditure Database | SIPRI | 2025 edition | Cross-check only | https://milex.sipri.org/ |
| SIPRI Arms Industry Database (Top 100, 2024) | SIPRI | fact sheet Dec 2025 | DIB scale for listed HQ countries | https://www.sipri.org/sites/default/files/2025-11/fs_2512_top_100_2024.pdf |
| Defense industrial base table | This mod | 2026 | Military factory country totals (`dib_mils.json`); territorial tags only | `tools/data/dib_mils.json` |
| CSIS munitions / industrial-base reports | CSIS | 2023–2025 | Wartime mill placement (RU/UA/US/EU) | https://www.csis.org/ |
| Gardner World Machine-Tool Output | Gardner / Modern Machine Shop | latest survey | Civ concentration DE/JP/CN/US/IT/KR/CH/TW | https://gardnerweb.com/ |
| Statbase ships built by country, 2025 DWT | Statbase (UNCTAD/Clarksons series) | 2025 | Merchant dockyards (`dib_docks.json`) | https://statbase.org/datasets/air-rail-and-water-transportation/merchant-fleet-built/ |
| Review of Maritime Transport 2025 Table II.1 | UNCTAD / Clarksons | 2024 GT shares | Cross-check: China 54.57%, Korea 28.02%, Japan 12.56% | https://unctad.org/publication/review-of-maritime-transport-2025 |
| Clarksons Research shipbuilding summaries | Clarksons | 2024–2025 | Underlying order-book / capacity series UNCTAD publishes | https://www.clarksons.com/home/news-and-insights/ |
| Janes Fighting Ships / IISS Military Balance | Janes; IISS | 2024–2026 programs | Naval construction campuses in `dib_docks.json` | https://www.iiss.org/publications/the-military-balance/ |
| NavBase / Phoenix_jz aggregate displacement | theworldwars.net; Phoenix_jz 1 Jan 2025 | 2025 | Fleet-tonnage cross-check (why USA ≠ 0). Not a dock formula | http://www.theworldwars.net/navbase/ |
| LPI 2023 infrastructure component (`LP.LPI.INFR.XQ`) | World Bank | 2023 | Infrastructure 1–5 | https://lpi.worldbank.org/ |
| Renewable Capacity Statistics 2026 | IRENA | end-2025 | `renewable_park` (1 park / 20 GW) | https://www.irena.org/Publications |
| Energy Institute Statistical Review of World Energy | Energy Institute | 2025 | Oil, coal, electricity context | https://www.energyinst.org/statistical-review |

## Resources

| Dataset | Publisher | Year | What it feeds | URL |
|---|---|---|---|---|
| World Steel in Figures / crude steel production | World Steel Association | 2024 | `steel` nodes | https://worldsteel.org/ |
| Mineral Commodity Summaries | USGS | 2025 | Al, W, Cr, Cu, graphite, Li, Co, REE, iron ore | https://www.usgs.gov/centers/national-minerals-information-center/mineral-commodity-summaries |
| Energy Institute Statistical Review | Energy Institute | 2025 | `oil`, `coal` | https://www.energyinst.org/statistical-review |
| FAO / IRSG rubber | FAOSTAT | latest | `rubber` | https://www.fao.org/faostat/ |

## Scaling (gameplay, documented)

- 1 civilian factory per $35 billion industry+agriculture value added (soft floor $0.5B → 1 civ)
- Military factories: DIB table in `dib_mils.json`. 1 mil = one serial campus or workshop minimum; mega-campuses 2–4. Same campus rule for every tag (USA 45, China 36, Russia 26, world ~419). Hulls are dockyards. Services firms omitted. No wartime×2.5. No vs-USA cap. SIPRI Top 100 2024 is a scale cross-check; PLA/Rostec plants are counted directly.
- 1 dockyard = 2 million dwt merchant output (Statbase 2025; only if ≥0.8M dwt) plus Janes/IISS naval campuses. Philippines merchant leftover is not a dock. Hulls are dockyards, not mils.
- 1 `renewable_park` per 20 GW IRENA renewable nameplate (hydro included; nuclear excluded)
- LPI infrastructure: <2.5→1, <3.0→2, <3.5→3, <4.0→4, else 5, then ±1 intra-country
- Resource units are HOI4 nodes, not tonnes: see constants in `allocate_state_stats.py`

`renewable_park` already grants `local_resources_coal = 1` per level. Fossil `coal` resources are mines/thermal supply only.
