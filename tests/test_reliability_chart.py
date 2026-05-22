import unittest

from sentinel_eval.domain.suite_metrics import CalibrationMetrics, ReliabilityBin
from sentinel_eval.reporting.reliability_chart import reliability_diagram_svg, write_reliability_chart


class TestReliabilityChart(unittest.TestCase):
    def test_svg_contains_bins(self):
        bins = [
            ReliabilityBin(
                bin=0,
                bin_lo=0.0,
                bin_hi=0.1,
                mean_predicted=0.05,
                mean_actual=0.0,
                count=2,
            ),
            ReliabilityBin(
                bin=9,
                bin_lo=0.9,
                bin_hi=1.0,
                mean_predicted=0.92,
                mean_actual=1.0,
                count=3,
            ),
        ]
        svg = reliability_diagram_svg(bins)
        self.assertIn("<svg", svg)
        self.assertIn("n=3", svg)

    def test_write_chart(self):
        import tempfile
        from pathlib import Path

        cal = CalibrationMetrics(
            reliability_diagram=[
                ReliabilityBin(
                    bin=0,
                    mean_predicted=0.2,
                    mean_actual=0.1,
                    count=1,
                ),
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = write_reliability_chart(cal, Path(tmp) / "rel.svg")
            self.assertIsNotNone(path)
            assert path is not None
            self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
