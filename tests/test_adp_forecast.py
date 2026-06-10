"""Tests run fully offline against the committed snapshot.

Focus on the decisions that matter: the change is derived correctly from the
level, the models behave as specified, and the backtest scoring is sound and
look-ahead-free.
"""
import math
import unittest

from adp_forecast import data as data_mod
from adp_forecast.backtest import evaluate, walk_forward
from adp_forecast.models import (HistoricalMean, MovingAverage, NaiveLast,
                                 SeasonalNaive, SimpleExpSmoothing, default_models)


class TestData(unittest.TestCase):
    def test_change_is_first_difference_of_level(self):
        obs = data_mod.get_observations()
        # first row has no change
        self.assertIsNone(obs[0].change)
        # spot check a known published value: May 2026 = +122k
        by_month = {o.month.strftime("%Y-%m"): o for o in obs}
        self.assertEqual(by_month["2026-05"].change, 122000)
        self.assertEqual(by_month["2025-12"].change, 37000)

    def test_change_series_is_in_thousands(self):
        changes = data_mod.change_series()
        self.assertAlmostEqual(changes[-1], 122.0)  # May 2026 in thousands
        self.assertGreater(len(changes), 150)


class TestModels(unittest.TestCase):
    def test_naive_returns_last(self):
        self.assertEqual(NaiveLast().predict([1, 2, 3]), 3)

    def test_moving_average(self):
        self.assertAlmostEqual(MovingAverage(3).predict([0, 30, 60, 90]), 60.0)

    def test_ma_handles_short_history(self):
        self.assertAlmostEqual(MovingAverage(6).predict([10, 20]), 15.0)

    def test_seasonal_naive_uses_t_minus_12(self):
        series = list(range(13))  # 0..12; predicting index 13 -> uses index 1
        self.assertEqual(SeasonalNaive().predict(series), 1)  # changes[-12]

    def test_ses_alpha_one_is_naive(self):
        self.assertAlmostEqual(SimpleExpSmoothing(1.0).predict([5, 9, 2]), 2.0)

    def test_historical_mean(self):
        self.assertAlmostEqual(HistoricalMean().predict([10, 20, 30]), 20.0)


class TestBacktest(unittest.TestCase):
    def test_walk_forward_is_look_ahead_free(self):
        # A spy model records how much history it was shown each step; it must
        # never see the value it's being asked to predict.
        seen_lengths = []

        class Spy:
            name = "spy"
            def predict(self, changes):
                seen_lengths.append(len(changes))
                return changes[-1]

        changes = list(range(40))
        preds, actuals = walk_forward(changes, Spy(), min_train=24)
        self.assertEqual(len(preds), 16)
        # at the first step it sees exactly min_train points, then grows by 1
        self.assertEqual(seen_lengths[0], 24)
        self.assertEqual(seen_lengths[-1], 39)

    def test_evaluate_ranks_and_scores(self):
        changes = data_mod.change_series()
        results = evaluate(changes, default_models(), min_train=24)
        self.assertEqual(len(results), len(default_models()))
        # sorted ascending by MAE
        maes = [r.mae for r in results]
        self.assertEqual(maes, sorted(maes))
        # naive's own MASE must be ~1.0 by construction
        naive = next(r for r in results if r.model == "naive_last")
        self.assertAlmostEqual(naive.mase, 1.0, places=6)
        for r in results:
            self.assertTrue(0.0 <= r.directional_acc <= 1.0)
            self.assertFalse(math.isnan(r.mae))


if __name__ == "__main__":
    unittest.main()
