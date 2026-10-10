"""
solar.py  -  Solar Potential Calculator (SDG 7: Affordable & Clean Energy, SDG 13: Climate Action)
Fetches long-term average sunlight for ANY location from NASA's free POWER API, then
estimates how much electricity a solar system would produce there and how much
generator fuel, money and CO2 it would replace.

Examples:
    python solar.py --lat 9.06 --lon 7.49 --kwp 3                       # Abuja, a 3 kW system
    python solar.py --lat 6.52 --lon 3.38 --need 8                      # Lagos: size a system for 8 kWh/day
    python solar.py --lat 12.0 --lon 8.52 --kwp 2 --fuel-price 1000 --cost 2500000
    python solar.py --offline --kwp 3                                   # no internet: MADE-UP demo sunlight
"""

import argparse                         # command-line options
import json                             # parse the API response
import sys
import urllib.request                   # download (built in)
from pathlib import Path

import calc                             # our maths (calc.py)

ROOT = Path(__file__).parent
CACHE = ROOT / "data"                   # API responses are saved here so repeat runs are instant
API = ("https://power.larc.nasa.gov/api/temporal/climatology/point"
       "?parameters=ALLSKY_SFC_SW_DWN&community=RE&longitude={lon}&latitude={lat}&format=JSON")
# ALLSKY_SFC_SW_DWN = sunlight reaching the ground, cloudy days included, in kWh/m²/day.
# community=RE = the "renewable energy" units. climatology = the long-term average per month.

DEMO_PSH = {"JAN": 5.8, "FEB": 6.1, "MAR": 6.2, "APR": 6.0, "MAY": 5.6, "JUN": 5.0,   # MADE-UP values shaped
            "JUL": 4.5, "AUG": 4.3, "SEP": 4.8, "OCT": 5.4, "NOV": 5.9, "DEC": 5.7}   # like a West African year


def fetch_psh(lat, lon):
    """Return {'JAN': psh, ...} for a location, using the local cache when possible."""
    CACHE.mkdir(exist_ok=True)
    cache_file = CACHE / f"power_{lat:.2f}_{lon:.2f}.json"         # one file per location (2 decimals ≈ 1 km)
    if cache_file.exists():
        payload = json.loads(cache_file.read_text(encoding="utf-8"))
    else:
        url = API.format(lat=lat, lon=lon)
        with urllib.request.urlopen(url, timeout=60) as resp:        # NASA can be slow - allow 60 seconds
            payload = json.loads(resp.read().decode("utf-8"))
        cache_file.write_text(json.dumps(payload), encoding="utf-8")
    values = payload["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]   # dig into the nested JSON
    psh = {m: float(values[m]) for m in calc.MONTHS}                   # keep only the 12 months
    if any(v < 0 for v in psh.values()):                               # NASA uses -999 for "missing"
        raise ValueError("NASA returned missing values for this location")
    return psh


def main():
    p = argparse.ArgumentParser(description="Estimate solar output and generator savings for a location.")
    p.add_argument("--lat", type=float, help="latitude, e.g. 9.06")
    p.add_argument("--lon", type=float, help="longitude, e.g. 7.49")
    p.add_argument("--kwp", type=float, help="system size in kilowatts-peak (kWp)")
    p.add_argument("--need", type=float, help="OR: daily need in kWh - the tool sizes the system for you")
    p.add_argument("--pr", type=float, default=calc.DEFAULT_PERFORMANCE_RATIO, help="performance ratio (default 0.75)")
    p.add_argument("--litres-per-kwh", type=float, default=0.7,
                   help="generator fuel use per kWh (default 0.7 - an assumption, see README)")
    p.add_argument("--fuel-price", type=float, help="petrol price per litre in your currency (today's price)")
    p.add_argument("--cost", type=float, help="installed system cost, for the payback estimate")
    p.add_argument("--offline", action="store_true", help="use made-up demo sunlight (no internet)")
    a = p.parse_args()

    if not a.offline and (a.lat is None or a.lon is None):
        sys.exit("Give --lat and --lon (or use --offline)")
    if (a.kwp is None) == (a.need is None):                          # both given, or neither
        sys.exit("Give exactly one of --kwp or --need")

    try:
        psh = DEMO_PSH if a.offline else fetch_psh(a.lat, a.lon)
    except OSError as err:                                           # no internet, timeout, blocked
        sys.exit(f"Could not reach NASA POWER ({err}). Try again, or use --offline.")

    where = "DEMO location (made-up sunlight)" if a.offline else f"{a.lat}, {a.lon}"
    kwp = a.kwp if a.kwp is not None else calc.size_for_need(a.need, psh, a.pr)
    if a.need is not None:
        print(f"To cover {a.need} kWh/day even in the cloudiest month you need about {kwp:.2f} kWp")

    rows = calc.monthly_table(kwp, psh, a.pr)
    print(f"\nSolar estimate for {where}: {kwp:.2f} kWp, performance ratio {a.pr}")
    print(f"{'Month':<6}{'Sun hrs':>8}{'kWh/day':>9}{'kWh/month':>11}")
    best = max(r[3] for r in rows)                                   # biggest month, for scaling the bars
    for month, sun, per_day, per_month in rows:
        bar = "█" * round(per_month / best * 30)                     # up to 30 blocks wide
        print(f"{month:<6}{sun:>8.2f}{per_day:>9.2f}{per_month:>11.1f}  {bar}")
    annual = sum(r[3] for r in rows)
    print(f"\nYearly output: {annual:,.0f} kWh  (about {annual / 365:.1f} kWh per day on average)")

    gen = calc.generator_comparison(annual, a.litres_per_kwh, a.fuel_price)
    print(f"\nReplacing a petrol generator ({a.litres_per_kwh} L per kWh) would avoid each year:")
    print(f"  {gen['litres_per_year']:,.0f} litres of petrol")
    print(f"  {gen['co2_kg_per_year'] / 1000:,.2f} tonnes of CO2")
    if gen["fuel_cost_per_year"] is not None:
        print(f"  {gen['fuel_cost_per_year']:,.0f} in fuel spending (at {a.fuel_price:,.0f} per litre)")
        if a.cost:
            years = calc.payback_years(a.cost, gen["fuel_cost_per_year"])
            print(f"  Payback on a {a.cost:,.0f} system: about {years:.1f} years (fuel savings only)")
    else:
        print("  (add --fuel-price to see money saved, and --cost for the payback time)")
    if a.offline:
        print("\nNOTE: --offline uses invented sunlight numbers. Use --lat/--lon for real NASA data.")


if __name__ == "__main__":
    main()
