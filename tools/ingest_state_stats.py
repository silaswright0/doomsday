#!/usr/bin/env python3
"""Download and freeze cited country-level datasets for the 2026 state pipeline."""
from __future__ import annotations

import argparse
import http.client
import json
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from state_stats_lib import DATA, ROOT, load_all_states, pretty_name_from_file  # noqa: E402

RETRIEVED = date.today().isoformat()
CTX = ssl.create_default_context()

WB_INDICATORS = {
    "NV.IND.MANF.CD": "mva_usd",
    "NV.IND.TOTL.CD": "industry_usd",
    "NV.AGR.TOTL.CD": "agriculture_usd",
    "NV.IND.TOTL.ZS": "industry_pct_gdp",
    "NV.AGR.TOTL.ZS": "agriculture_pct_gdp",
    "NY.GDP.MKTP.CD": "gdp_usd",
    "SP.POP.TOTL": "pop_wb",
    "MS.MIL.XPND.CD": "milex_usd",
    "LP.LPI.INFR.XQ": "lpi_infra",
}


def fetch_json(url: str, timeout: int = 120) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "DoomsdayMod/1.0 (research snapshot)"})
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url: str, timeout: int = 120) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "DoomsdayMod/1.0 (research snapshot)"})
    with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def latest_wb(indicator: str) -> dict[str, dict]:
    """Most recent non-empty World Bank value per ISO3 country."""
    url = (
        "https://api.worldbank.org/v2/country/all/indicator/"
        f"{indicator}?mrnev=1&format=json&per_page=400"
    )
    payload = fetch_json(url)
    if not isinstance(payload, list) or len(payload) < 2:
        raise RuntimeError(f"unexpected World Bank payload for {indicator}")
    out: dict[str, dict] = {}
    for row in payload[1]:
        iso3 = (row.get("countryiso3code") or "").strip()
        val = row.get("value")
        if not iso3 or val is None:
            continue
        # 2011 Venezuela etc. report 0; that is missing, not a real sector.
        if float(val) == 0 and indicator in {
            "NV.IND.MANF.CD",
            "NV.IND.TOTL.CD",
            "NV.AGR.TOTL.CD",
            "NV.IND.TOTL.ZS",
            "NV.AGR.TOTL.ZS",
        }:
            continue
        out[iso3] = {
            "value": float(val),
            "year": int(row["date"]) if str(row.get("date", "")).isdigit() else row.get("date"),
            "country": (row.get("country") or {}).get("value"),
        }
    return out


def fetch_wpp_wikimedia() -> dict[str, int]:
    url = "https://commons.wikimedia.org/wiki/Data:WPP24_2026-07.tab?action=raw"
    payload = fetch_json(url)
    data = payload.get("data") or []
    return {str(name): int(pop) for name, pop in data}


WD_UA = "DoomsdayMod/1.0 (research snapshot; HOI4 mod; https://query.wikidata.org/)"


def load_existing_admin1() -> list[dict]:
    path = DATA / "wikidata_admin1_pop.json"
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    rows = payload.get("rows") if isinstance(payload, dict) else payload
    return [r for r in (rows or []) if isinstance(r, dict) and r.get("iso3") and r.get("pop")]


def sparql_bindings(query: str, timeout: int = 40, attempts: int = 2) -> list[dict]:
    """POST SPARQL. GET + subclass paths 504; large JSON bodies also truncate."""
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            body = urllib.parse.urlencode({"query": query, "format": "json"}).encode()
            req = urllib.request.Request(
                "https://query.wikidata.org/sparql",
                data=body,
                headers={
                    "User-Agent": WD_UA,
                    "Accept": "application/sparql-results+json",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, context=CTX, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            stripped = raw.lstrip()
            if not stripped.startswith("{") and not stripped.startswith("["):
                raise RuntimeError(f"non-JSON SPARQL body: {stripped[:120]!r}")
            payload = json.loads(raw)
            return payload.get("results", {}).get("bindings", [])
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            json.JSONDecodeError,
            RuntimeError,
            http.client.IncompleteRead,
            ConnectionError,
        ) as exc:
            last = exc
            time.sleep(1.2 * (attempt + 1))
    raise RuntimeError(last)


def parse_admin1_bindings(bindings: list[dict]) -> list[dict]:
    best: dict[tuple[str, str], dict] = {}
    for b in bindings:
        try:
            iso3 = b["iso3"]["value"].strip()
            iso2 = (b.get("iso2") or {}).get("value", "").strip()
            name = b["itemLabel"]["value"].strip()
            pop = int(float(b["pop"]["value"]))
            alt = ((b.get("alt") or {}).get("value") or "").strip()
        except (KeyError, TypeError, ValueError):
            continue
        if not iso3 or not name or pop <= 0:
            continue
        key = (iso3, iso2 or name.casefold())
        rec = best.get(key)
        if rec is None:
            rec = {"iso3": iso3, "iso2": iso2, "name": name, "pop": pop, "alts": []}
            best[key] = rec
        if pop > rec["pop"]:
            rec["pop"] = pop
            rec["name"] = name
        if alt and alt.casefold() != name.casefold() and alt not in rec["alts"]:
            rec["alts"].append(alt)
    return sorted(best.values(), key=lambda r: (r["iso3"], r["iso2"], r["name"]))


def fetch_admin1_iso3(iso3: str) -> list[dict]:
    primary = f"""
    SELECT ?iso3 ?iso2 ?itemLabel ?pop WHERE {{
      BIND("{iso3}" AS ?iso3)
      ?item wdt:P17 ?country.
      ?country wdt:P298 ?iso3.
      ?item wdt:P300 ?iso2.
      ?item wdt:P1082 ?pop.
      ?item rdfs:label ?itemLabel.
      FILTER(LANG(?itemLabel) = "en")
    }}
    """
    prefix = f"""
    SELECT ?iso3 ?iso2 ?itemLabel ?pop WHERE {{
      BIND("{iso3}" AS ?iso3)
      ?country wdt:P298 ?iso3.
      ?country wdt:P297 ?cc.
      ?item wdt:P300 ?iso2.
      FILTER(STRSTARTS(?iso2, CONCAT(?cc, "-")))
      ?item wdt:P1082 ?pop.
      ?item rdfs:label ?itemLabel.
      FILTER(LANG(?itemLabel) = "en")
    }}
    """
    try:
        rows = parse_admin1_bindings(sparql_bindings(primary))
    except Exception:
        rows = []
    if rows:
        return rows
    return parse_admin1_bindings(sparql_bindings(prefix))


def wikidata_iso3_list() -> list[str]:
    from state_stats_geo import TAG_META

    owners = {s["owner"] for s in load_all_states()}
    iso3s = {TAG_META[tag]["iso3"] for tag in owners if TAG_META.get(tag, {}).get("iso3")}
    iso3s.update({"HKG", "MAC", "PRI", "TWN", "XKX", "GRL", "ESH", "PSE"})
    return sorted(iso3s)


def fetch_wikidata_admin1() -> list[dict]:
    """ISO 3166-2 (P300) units with truthy P1082. One ISO3 per request so WDQS does not 504."""
    prior = {(r["iso3"], r.get("iso2") or r["name"].casefold()): r for r in load_existing_admin1()}
    iso3s = wikidata_iso3_list()
    print(f"  {len(iso3s)} ISO3 codes, POST per country (P300 + P1082)", flush=True)
    ok = 0
    failed: list[str] = []
    for i, iso3 in enumerate(iso3s, 1):
        try:
            rows = fetch_admin1_iso3(iso3)
        except Exception as exc:
            failed.append(iso3)
            print(f"  [{i}/{len(iso3s)}] {iso3} FAIL {exc}", flush=True)
            time.sleep(0.2)
            continue
        if rows:
            prior = {k: v for k, v in prior.items() if v["iso3"] != iso3}
            for row in rows:
                prior[(row["iso3"], row.get("iso2") or row["name"].casefold())] = row
            ok += 1
            print(f"  [{i}/{len(iso3s)}] {iso3} {len(rows)} (total {len(prior)})", flush=True)
            write_admin1(sorted(prior.values(), key=lambda r: (r["iso3"], r.get("iso2") or "", r["name"])), quiet=True)
        else:
            failed.append(iso3)
            print(f"  [{i}/{len(iso3s)}] {iso3} empty, keeping prior", flush=True)
        time.sleep(0.15)
    if failed:
        print(f"  failed/empty {len(failed)}: {', '.join(failed[:20])}{'...' if len(failed) > 20 else ''}", flush=True)
    print(f"  countries_ok {ok}/{len(iso3s)}", flush=True)
    return sorted(prior.values(), key=lambda r: (r["iso3"], r.get("iso2") or "", r["name"]))


def write_admin1(admin1: list[dict], quiet: bool = False) -> None:
    (DATA / "wikidata_admin1_pop.json").write_text(
        json.dumps(
            {
                "retrieved": RETRIEVED,
                "source": "Wikidata P1082 population on ISO 3166-2 (P300) admin units",
                "via": "https://query.wikidata.org/sparql",
                "query": "POST one ISO3 at a time; truthy P1082. The Q10864048 subclass path 504s on WDQS.",
                "rows": admin1,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if not quiet:
        print(f"  admin1 rows {len(admin1)}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze cited country datasets for the 2026 state pipeline.")
    parser.add_argument("--wikidata-only", action="store_true", help="Refresh ISO 3166-2 admin populations only")
    parser.add_argument("--wb-only", action="store_true", help="Refresh World Bank indicators only")
    args = parser.parse_args()
    DATA.mkdir(parents=True, exist_ok=True)

    if args.wikidata_only:
        print("Wikidata admin-1 populations...")
        write_admin1(fetch_wikidata_admin1())
        print("ingest complete")
        return

    meta = {"retrieved": RETRIEVED, "files": {}}

    print("World Bank indicators...")
    wb: dict[str, dict] = {}
    for code, key in WB_INDICATORS.items():
        try:
            series = latest_wb(code)
        except Exception as exc:
            print(f"  FAIL {code}: {exc}")
            series = {}
        path = DATA / f"worldbank_{key}.json"
        path.write_text(json.dumps({"indicator": code, "retrieved": RETRIEVED, "rows": series}, indent=2), encoding="utf-8")
        meta["files"][path.name] = {"indicator": code, "countries": len(series)}
        print(f"  {code} -> {len(series)} countries")
        for iso3, rec in series.items():
            wb.setdefault(iso3, {})[key] = rec

    (DATA / "worldbank_by_iso3.json").write_text(
        json.dumps({"retrieved": RETRIEVED, "countries": wb}, indent=2), encoding="utf-8"
    )

    if args.wb_only:
        (DATA / "ingest_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        print("ingest complete (World Bank only)")
        return

    print("UN WPP 2026 (Wikimedia snapshot of UN DESA WPP 2024 medium)...")
    try:
        wpp = fetch_wpp_wikimedia()
    except Exception as exc:
        print(f"  FAIL WPP: {exc}")
        wpp = {}
    (DATA / "un_wpp2026.json").write_text(
        json.dumps(
            {
                "retrieved": RETRIEVED,
                "source": "UN DESA World Population Prospects 2024 medium variant, 1 July 2026",
                "via": "https://commons.wikimedia.org/wiki/Data:WPP24_2026-07.tab",
                "official": "https://population.un.org/wpp/",
                "rows": wpp,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"  WPP rows {len(wpp)}")

    print("Wikidata admin-1 populations...")
    try:
        admin1 = fetch_wikidata_admin1()
    except Exception as exc:
        print(f"  FAIL Wikidata: {exc}")
        admin1 = load_existing_admin1()
    write_admin1(admin1)

    print("State inventory...")
    states = load_all_states()
    inv = [
        {
            "id": s["id"],
            "file": s["file"],
            "pretty": s["pretty"],
            "owner": s["owner"],
            "category": s["category"],
            "manpower_old": s["manpower"],
            "province_count": s["province_count"],
            "coastal": s["coastal"],
            "impassable": s["impassable"],
        }
        for s in states
    ]
    (DATA / "state_inventory.json").write_text(
        json.dumps({"retrieved": RETRIEVED, "count": len(inv), "states": inv}, indent=2),
        encoding="utf-8",
    )
    print(f"  states {len(inv)}")
    (DATA / "ingest_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print("ingest complete")


if __name__ == "__main__":
    main()
