"""Unit tests for calc.py. Run:  python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import calc  # noqa: E402

FLAT = {m: 5.0 for m in calc.MONTHS}                     # 5 peak sun hours every month


class CalcTests(unittest.TestCase):
    def test_daily_kwh(self):
        self.assertAlmostEqual(calc.daily_kwh(2, 5, 0.8), 8.0)    # 2 kW x 5 h x 0.8 = 8 kWh

    def test_year_has_365_days(self):
        rows = calc.monthly_table(1, FLAT, 1.0)                     # 1 kW, no losses
        self.assertAlmostEqual(sum(r[3] for r in rows), 5 * 365)

    def test_sizing_uses_worst_month(self):
        psh = dict(FLAT, AUG=4.0)                                   # August is cloudier
        self.assertAlmostEqual(calc.size_for_need(8, psh, 1.0), 2.0)   # 8 kWh / 4 h = 2 kW

    def test_generator_comparison(self):
        gen = calc.generator_comparison(1000, 0.5, fuel_price=100)
        self.assertEqual(gen["litres_per_year"], 500)
        self.assertEqual(gen["fuel_cost_per_year"], 50000)
        self.assertAlmostEqual(gen["co2_kg_per_year"], 1175)

    def test_payback(self):
        self.assertEqual(calc.payback_years(100, 25), 4)
        self.assertIsNone(calc.payback_years(100, None))


if __name__ == "__main__":
    unittest.main()
