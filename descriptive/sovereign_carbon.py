"""Carbon intensity of sovereign issuers, as the PCAF standard sets it for sovereign debt (Part A,
third edition, December 2025, chapter on sovereign debt): a country's production emissions (its
scope 1) divided by its GDP at purchasing-power parity, reported both excluding and including land
use (LULUCF). A holding is attributed emissions by: exposure / PPP-adjusted GDP x the country's
emissions. Emissions of imports (the country's scopes 2 and 3) are not computed here.

Descriptive. Emissions excluding land use: total greenhouse gases, Mt CO2e (EDGAR, World Bank
indicator EN.GHG.ALL.MT.CE.AR5), year 2024. Land use: World Bank indicator EN.GHG.CO2.LU.MT.CE.AR5,
whose last year is 2023; that flow is added to the 2024 figure. GDP: PPP, current international
dollars (NY.GDP.MKTP.PP.CD), 2024; current dollars (NY.GDP.MKTP.CD) for comparison.

    python3 sovereign_carbon.py > outputs/sovereign_carbon.txt
"""
import json
import subprocess
import time

YEAR, LAND_USE_YEAR = "2024", "2023"
COUNTRIES = {"USA": "United States", "DEU": "Germany", "FRA": "France", "ITA": "Italy", "ESP": "Spain", "NLD": "Netherlands", "EMU": "Euro area"}
TREASURIES_HELD_USD = 45e6       # 55% in bonds at the open, less 10% in supranational green bonds, of $100m
WITHOUT_GREEN_BONDS_USD = 55e6   # the same sleeve if the green bonds are not eligible


def fetch(indicator: str, year: str) -> dict:
    url = f"https://api.worldbank.org/v2/country/{';'.join(COUNTRIES)}/indicator/{indicator}?format=json&date={year}&per_page=100"
    rows = None
    for attempt in range(4):                      # the API sometimes answers with an empty body
        raw = subprocess.run(["curl", "-s", "--max-time", "40", url], capture_output=True, text=True).stdout
        try:
            rows = json.loads(raw)[1]
            break
        except (ValueError, IndexError):
            time.sleep(3)
    if rows is None:
        raise SystemExit(f"no answer from the World Bank API for {indicator}")
    out = {}
    for r in rows:
        if r["value"] is not None:
            code = r["countryiso3code"] or r["country"]["id"]
            out["EMU" if code in ("XC", "EMU") else code] = r["value"]
    return out


ghg, land = fetch("EN.GHG.ALL.MT.CE.AR5", YEAR), fetch("EN.GHG.CO2.LU.MT.CE.AR5", LAND_USE_YEAR)
ppp, usd = fetch("NY.GDP.MKTP.PP.CD", YEAR), fetch("NY.GDP.MKTP.CD", YEAR)
print(f"tonnes of CO2e per $1m of GDP at purchasing-power parity, {YEAR} (land use: {LAND_USE_YEAR} flow)")
ex, inc, cur = {}, {}, {}
for code, name in COUNTRIES.items():
    ex[code] = ghg[code] * 1e6 / (ppp[code] / 1e6)
    inc[code] = (ghg[code] + land[code]) * 1e6 / (ppp[code] / 1e6)
    cur[code] = ghg[code] * 1e6 / (usd[code] / 1e6)
    print(f"  {name:14s} emissions {ghg[code]:8.1f} Mt | land use {land[code]:+8.1f} Mt | PPP GDP {ppp[code] / 1e9:9.1f} $bn | excluding land use {ex[code]:6.1f} | including {inc[code]:6.1f} | at current GDP {cur[code]:6.1f}")
print("ratio United States / euro area: excluding land use %.2f | including %.2f | at current GDP, excluding %.2f" % (ex["USA"] / ex["EMU"], inc["USA"] / inc["EMU"], cur["USA"] / cur["EMU"]))
for label, amount in (("$45m of US Treasuries", TREASURIES_HELD_USD), ("$55m of US Treasuries (no green bonds)", WITHOUT_GREEN_BONDS_USD)):
    print("emissions attributed to %s: %.0f tonnes a year excluding land use, %.0f including" % (label, amount / 1e6 * ex["USA"], amount / 1e6 * inc["USA"]))
