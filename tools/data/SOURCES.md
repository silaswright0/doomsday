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
| LPI 2023 infrastructure component (`LP.LPI.INFR.XQ`) | World Bank | 2023 report (API year 2022) | Retired as a live path. Country stamp made Corsica = Île-de-France | https://lpi.worldbank.org/ |
| GLocal GID-1 area-weighted VIIRS (`viirs`, 2021) | Morales-Arilla & Gadgin Matha, Harvard Dataverse | GLocal v3, year 2021 (2022–23 empty) | State infrastructure 1–5. Names via FAO GADM 3.6. Frozen `admin1_ntl.json` | https://doi.org/10.7910/DVN/6TUCTE |
| eoatlas / geoBoundaries ADM1 night lights | eoatlas | 2012–2024 monthly | Alternate ingest; per-unit CSVs, not used live | https://github.com/eoatlas/nightlight |
| GRIP / OSM road length in GLocal | GRIP + OSM | 2018 only, incomplete | Infra cross-check, not live (coverage holes) | GLocal `road_length_*` |
| Services value added, current US$ (`NV.SRV.TOTL.CD`) | World Bank WDI | latest | `services_building` country control (1 per $250B; floor $20B) | https://data.worldbank.org/indicator/NV.SRV.TOTL.CD |
| Global Financial Centres Index 38 | Z/Yen and CDI | 25 Sep 2025 | `finance_center` campuses (`dib_finance.json`) | https://www.longfinance.net/programmes/financial-centre-futures/global-financial-centres-index/ |
| OGJ Worldwide Refining Survey / EIA-820 | Oil & Gas Journal; EIA | latest CDU | `synthetic_refinery` as crude/CTL campuses (`dib_refineries.json`) | https://www.eia.gov/petroleum/refinerycapacity/ |
| US SPR sites; IEA 90-day stocks; CNPR / JOGMEC / KNOC / ISPRL | DOE; IEA; national SPR agencies | 2024–2026 | `fuel_silo` cavern/tank-farm campuses (`dib_fuel_silos.json`) | https://www.energy.gov/ceser/strategic-petroleum-reserve |
| ISO/RTO / ENTSO-E / State Grid regional cores | FERC; ENTSO-E; national TSOs | 2026 footprints | `energy_infrastructure` keystone hubs (`dib_grid.json`), 1/state | https://www.entsoe.eu/ |
| Renewable Capacity Statistics 2026 | IRENA | end-2025 | `renewable_park` (1 park / 20 GW). Hydro included; nuclear excluded | https://www.irena.org/Publications |
| Energy Institute Statistical Review of World Energy | Energy Institute | 2025 | `oil` and `coal` resource nodes only. Not energy buildings | https://www.energyinst.org/statistical-review |

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
- State infrastructure: GLocal 2021 area-weighted VIIRS mean radiance (nW/cm²/sr). Breaks 0.08 / 0.35 / 1.20 / 4.00 → HOI4 1–5. No country LPI offset. Unmatched states use category fallback. Impassable capped at 2.
- 1 `finance_center` = one GFCI 38 centre in that HOI4 state (ranks 1–4 → 3, 5–10 → 2, 11–40 → 1)
- 1 `services_building` per $250 billion services value added (`NV.SRV.TOTL.CD`; else GDP − industry − agriculture). Floor $20B → 1. Allocated to urban states by population.
- 1 `synthetic_refinery` ≈ 400 kb/d CDU (min ~350; mega 2–3; `state_max` 3)
- 1 `fuel_silo` = one SPR cavern or export tank-farm campus
- 1 `energy_infrastructure` = one ISO/TSO / national-grid core (`state_max` 1; exclusive with `industrial_infrastructure`)
- Resource units are HOI4 nodes, not tonnes: see constants in `allocate_state_stats.py`

`renewable_park` already grants `local_resources_coal = 1` per level. Fossil `coal` resources are mines/thermal supply only.

Energy buildings on the map: `renewable_park` (IRENA), `energy_infrastructure` (TSO hubs in `dib_grid.json`). Not placed: `industrial_infrastructure` (exclusive keystone; mining-state rule not used), `nuclear_reactor` (IAEA PRIS would be the campus table), dams (leftover vanilla, not ICOLD). Do not treat Energy Institute TWh as if it placed those.
