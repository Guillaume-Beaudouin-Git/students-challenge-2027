"""Carbon intensity of sovereign issuers, as the PCAF standard recommends for sovereign debt:
a country's production emissions divided by its GDP at purchasing-power parity.

Descriptive. Emissions: total greenhouse gases excluding land use, Mt CO2e (EDGAR, World Bank
indicator EN.GHG.ALL.MT.CE.AR5). GDP: PPP, current international dollars (World Bank indicator
NY.GDP.MKTP.PP.CD). Year 2024. The last line attributes emissions to a holding the PCAF way:
exposure / PPP-adjusted GDP x the country's emissions.

    python3 sovereign_carbon.py > outputs/sovereign_carbon.txt
"""
import json
import subprocess

YEAR = "2024"
COUNTRIES = {"USA": "United States", "DEU": "Germany", "FRA": "France", "ITA": "Italy", "ESP": "Spain", "NLD": "Netherlands", "EMU": "Euro area"}
TREASURIES_HELD_USD = 45e6      # 55% in bonds at the open, less 10% in supranational green bonds, of $100m


def fetch(indicator: str) -> dict:
    url = f"https://api.worldbank.org/v2/country/{';'.join(COUNTRIES)}/indicator/{indicator}?format=json&date={YEAR}&per_page=100"
    rows = json.loads(subprocess.run(["curl", "-s", "--max-time", "40", url], capture_output=True, text=True).stdout)[1]
    return {r["countryiso3code"] or r["country"]["id"]: r["value"] for r in rows if r["value"] is not None}


ghg, gdp = fetch("EN.GHG.ALL.MT.CE.AR5"), fetch("NY.GDP.MKTP.PP.CD")
print(f"{YEAR}: tonnes of CO2e per $1m of PPP-adjusted GDP")
out = {}
for code, name in COUNTRIES.items():
    key = code if code in ghg else {"EMU": "XC"}.get(code, code)
    intensity = ghg[key] * 1e6 / (gdp[key] / 1e6)
    out[code] = intensity
    print(f"  {name:14s} emissions {ghg[key]:8.1f} Mt | GDP {gdp[key] / 1e9:9.1f} $bn | intensity {intensity:6.1f}")
print("ratio United States / euro area: %.2f" % (out["USA"] / out["EMU"]))
print("emissions attributed to $%.0fm of US Treasuries: %.0f tonnes a year" % (TREASURIES_HELD_USD / 1e6, TREASURIES_HELD_USD / 1e6 * out["USA"]))
