"""
calc.py  -  Solar maths, kept separate from the internet code so it can be unit-tested.

Key idea: "peak sun hours" (PSH). NASA reports average daily sunlight as kWh per m²
per day. 1 kWh/m²/day is the same as 1 hour of full-strength (1,000 W/m²) sun, so the
number doubles as "how many hours a panel effectively runs at its rated power".
"""

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]   # ignoring leap years

# Share of the panel's ideal output you actually get after heat, dust, wiring and
# inverter losses. 0.75 is a common rule-of-thumb assumption - change it if you know better.
DEFAULT_PERFORMANCE_RATIO = 0.75

PETROL_KG_CO2_PER_LITRE = 2.35        # approx. US EPA: 8,887 g CO2 per US gallon / 3.785 L


def daily_kwh(kwp, psh, performance_ratio=DEFAULT_PERFORMANCE_RATIO):
    """Energy a system of `kwp` kilowatts-peak makes on an average day with `psh` peak sun hours."""
    return kwp * psh * performance_ratio          # kW x hours = kWh, then remove losses


def monthly_table(kwp, psh_by_month, performance_ratio=DEFAULT_PERFORMANCE_RATIO):
    """List of (month, psh, kWh per day, kWh per month) for all 12 months."""
    rows = []
    for month, days in zip(MONTHS, DAYS_IN_MONTH):        # zip walks both lists together
        psh = psh_by_month[month]
        per_day = daily_kwh(kwp, psh, performance_ratio)
        rows.append((month, psh, per_day, per_day * days))
    return rows


def size_for_need(daily_need_kwh, psh_by_month, performance_ratio=DEFAULT_PERFORMANCE_RATIO):
    """
    Smallest system (kWp) that covers the daily need even in the darkest month.
    Sizing for the worst month means the lights stay on in the rainy season too.
    """
    worst_psh = min(psh_by_month[m] for m in MONTHS)      # the cloudiest month
    return daily_need_kwh / (worst_psh * performance_ratio)


def generator_comparison(annual_kwh, litres_per_kwh, fuel_price=None):
    """
    What the same energy would cost from a petrol generator.
    litres_per_kwh: how thirsty the generator is (an assumption - see README).
    Returns a dict; money values are None when no fuel price is given.
    """
    litres = annual_kwh * litres_per_kwh
    return {
        "litres_per_year": litres,
        "co2_kg_per_year": litres * PETROL_KG_CO2_PER_LITRE,
        "fuel_cost_per_year": None if fuel_price is None else litres * fuel_price,
    }


def payback_years(system_cost, yearly_saving):
    """Years until fuel savings repay the system. None if there is no saving."""
    if not yearly_saving or yearly_saving <= 0:           # 'not x' is True for None and 0
        return None
    return system_cost / yearly_saving
