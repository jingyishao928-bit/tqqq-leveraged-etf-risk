import subprocess
import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def tracked_csv_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in sorted(result.stdout.splitlines()) if line]


class StataExportTests(unittest.TestCase):
    def test_every_tracked_csv_has_readable_same_folder_dta(self):
        csv_files = tracked_csv_files()
        self.assertTrue(csv_files)
        for csv_path in csv_files:
            with self.subTest(csv=csv_path.relative_to(ROOT)):
                dta_path = csv_path.with_suffix(".dta")
                self.assertTrue(dta_path.exists())
                csv_frame = pd.read_csv(csv_path)
                dta_frame = pd.read_stata(dta_path, convert_categoricals=False)
                self.assertEqual(dta_frame.shape, csv_frame.shape)

    def test_analysis_dates_are_stata_dates(self):
        path = ROOT / "data" / "processed" / "part1_clean_returns.dta"
        frame = pd.read_stata(path, convert_categoricals=False)
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(frame["Date"]))
        self.assertEqual(frame["Date"].min().date().isoformat(), "2019-01-03")
        self.assertEqual(frame["Date"].max().date().isoformat(), "2026-11-20")


if __name__ == "__main__":
    unittest.main()
