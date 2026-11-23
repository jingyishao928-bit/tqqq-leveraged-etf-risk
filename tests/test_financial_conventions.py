import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from leveraged_etf_risk.mechanics import (  # noqa: E402
    compound_wealth,
    leveraged_simple_return,
    log_to_simple_return,
    long_loss_from_terminal_wealth,
    short_loss_from_terminal_wealth,
)
from leveraged_etf_risk.risk import expected_shortfall, value_at_risk  # noqa: E402


class FinancialConventionTests(unittest.TestCase):
    def test_log_return_is_converted_before_leverage(self):
        log_return = math.log(1.10)
        simple_return = log_to_simple_return(log_return)
        self.assertAlmostEqual(simple_return, 0.10)
        self.assertAlmostEqual(leveraged_simple_return(simple_return, 3.0), 0.30)

    def test_path_dependence_two_day_example(self):
        underlying = [0.10, -1.0 / 11.0]
        leveraged = [leveraged_simple_return(value, 3.0) for value in underlying]
        self.assertAlmostEqual(compound_wealth(underlying), 1.0)
        self.assertAlmostEqual(compound_wealth(leveraged), 0.9454545454545454)

    def test_nav_floor_prevents_negative_wealth(self):
        self.assertEqual(compound_wealth([-1.5], nav_floor=0.0), 0.0)

    def test_short_loss_is_not_capped_at_one_hundred_percent(self):
        self.assertEqual(short_loss_from_terminal_wealth(2.5), 1.5)
        self.assertEqual(long_loss_from_terminal_wealth(0.0), 1.0)

    def test_var_and_es_use_positive_losses(self):
        losses = [-0.20, -0.05, 0.00, 0.10, 0.40]
        self.assertEqual(value_at_risk(losses, 0.80), 0.10)
        self.assertAlmostEqual(expected_shortfall(losses, 0.80), 0.25)


if __name__ == "__main__":
    unittest.main()

