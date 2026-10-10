# Solar Potential Calculator (SDG 7 + SDG 13)

Millions of homes and businesses in Nigeria run petrol generators every day. Give this tool a location and it fetches **NASA's long-term sunlight data** for that spot, then estimates:
- how much electricity a solar system would produce there, month by month
- what system size you'd need for a given daily usage, sized for the **cloudiest** month
- how many litres of petrol, tonnes of CO₂ and how much money it would save compared with a generator, and the payback time

**SDG targets covered:** 7.1 (access to energy), 7.2 (more renewables) and 13.2 (cut emissions).

## Run it
```bash
python solar.py --lat 9.06 --lon 7.49 --kwp 3                               # Abuja, a 3 kW system
python solar.py --lat 6.52 --lon 3.38 --need 8                              # Lagos: size a system for 8 kWh/day
python solar.py --lat 12.00 --lon 8.52 --kwp 2 --fuel-price <today's price> --cost <system price>
python solar.py --offline --kwp 3                                           # no internet: made-up demo sunlight
python -m unittest discover tests
```
Everything uses the Python standard library. NASA POWER is free and needs no API key. Responses are cached in `data/` so repeat runs are instant.

## How the maths works (`calc.py`)
- **Peak sun hours:** NASA's `ALLSKY_SFC_SW_DWN` value, in kWh/m²/day, equals the number of hours of full-strength sun per day.
- **Daily output** = system size (kWp) × peak sun hours × performance ratio (default 0.75, to cover heat, dust, wiring and inverter losses).
- **Sizing:** kWp = daily need ÷ (peak sun hours in the worst month × performance ratio).
- **Generator comparison:** litres = kWh × litres-per-kWh. CO₂ = litres × 2.35 kg (approximate, from US EPA).
- **Payback** = system cost ÷ yearly fuel saving.

## Assumptions to state honestly
- **`--litres-per-kwh 0.7`** is a rough figure for a small petrol generator. Real values vary a lot with size and load, so measure yours if you can.
- **Fuel price and system cost** have no defaults, because prices change too fast to hard-code. Enter today's numbers.
- The savings assume *every* kWh the panels make replaces a generator kWh. Without batteries, night-time use still needs another source, and batteries add cost. Treat the payback figure as a best case.

## Ideas to extend it
- Add battery sizing for night-time load
- Compare several cities in one run and write a CSV
- Add a matplotlib chart of the monthly output

## Data source
NASA Langley Research Center (LaRC) POWER Project, funded through the NASA Earth Science/Applied Science Program. The `--offline` demo values are **invented**.
