"""Export every tracked CSV table to a same-folder Stata data file.

The CSV files remain the source of truth. This script creates Stata 14+
format files (version 118), normalizes column names to Stata's rules, and
verifies every export by reading it back.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATE_COLUMNS = {
    "date",
    "accessed_on",
    "raw_start_requested",
    "raw_end_requested",
    "analysis_start",
    "analysis_end",
}
DATETIME_COLUMNS = {"downloaded_at_utc"}
STATA_RESERVED_WORDS = {
    "aggregate", "array", "boolean", "break", "byte", "case", "catch",
    "class", "colvector", "complex", "const", "continue", "default",
    "delegate", "delete", "do", "double", "else", "eltypedef", "end",
    "enum", "explicit", "export", "external", "float", "for", "friend",
    "function", "global", "goto", "if", "inline", "int", "local", "long",
    "NULL", "pragma", "protected", "quad", "rowvector", "short", "typedef",
    "typename", "virtual", "_all", "_N", "_skip", "_b", "_pi", "str#",
    "in", "_pred", "strL", "_coef", "_rc", "using", "_cons", "_se",
    "with", "_n",
}


def tracked_csv_files() -> list[Path]:
    """Return tracked CSV files in stable repository-relative order."""
    result = subprocess.run(
        ["git", "ls-files", "*.csv"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in sorted(result.stdout.splitlines()) if line]


def stata_name(original: object, used: set[str]) -> str:
    """Return one unique Stata-compatible variable name."""
    name = re.sub(r"[^A-Za-z0-9_]", "_", str(original))
    name = re.sub(r"_+", "_", name).strip("_") or "variable"
    if name[0].isdigit():
        name = f"v_{name}"
    if name in STATA_RESERVED_WORDS:
        name = f"v_{name}"
    name = name[:32]

    candidate = name
    suffix_number = 2
    while candidate in used:
        suffix = f"_{suffix_number}"
        candidate = f"{name[: 32 - len(suffix)]}{suffix}"
        suffix_number += 1
    used.add(candidate)
    return candidate


def prepare_frame(csv_path: Path) -> tuple[pd.DataFrame, dict[str, str], dict[str, str]]:
    """Load a CSV and prepare its values, names, and Stata date formats."""
    frame = pd.read_csv(csv_path)
    original_columns = list(frame.columns)
    used: set[str] = set()
    name_map = {column: stata_name(column, used) for column in original_columns}
    frame = frame.rename(columns=name_map)

    date_formats: dict[str, str] = {}
    for original, converted in name_map.items():
        normalized = str(original).lower()
        if normalized in DATE_COLUMNS:
            frame[converted] = pd.to_datetime(frame[converted], errors="raise").dt.normalize()
            date_formats[converted] = "td"
        elif normalized in DATETIME_COLUMNS:
            # Stata %tc has millisecond precision and does not store a timezone.
            frame[converted] = (
                pd.to_datetime(frame[converted], errors="raise", utc=True)
                .dt.tz_localize(None)
                .dt.floor("ms")
            )
            date_formats[converted] = "tc"
        elif pd.api.types.is_bool_dtype(frame[converted]):
            frame[converted] = frame[converted].astype("int8")
        elif pd.api.types.is_object_dtype(frame[converted]):
            frame[converted] = frame[converted].where(frame[converted].notna(), None)

    labels = {name_map[column]: str(column)[:80] for column in original_columns}
    return frame, labels, date_formats


def verify_round_trip(expected: pd.DataFrame, dta_path: Path) -> None:
    """Read one DTA back and compare its schema and values with the export frame."""
    actual = pd.read_stata(dta_path, convert_categoricals=False)
    if list(actual.columns) != list(expected.columns):
        raise AssertionError(f"Column mismatch in {dta_path}")
    if actual.shape != expected.shape:
        raise AssertionError(
            f"Shape mismatch in {dta_path}: expected {expected.shape}, got {actual.shape}"
        )

    for column in expected.columns:
        left = expected[column]
        right = actual[column]
        if pd.api.types.is_datetime64_any_dtype(left):
            pd.testing.assert_series_equal(
                pd.to_datetime(right), left, check_names=False, check_dtype=False
            )
        elif pd.api.types.is_numeric_dtype(left):
            np.testing.assert_allclose(
                pd.to_numeric(right),
                pd.to_numeric(left),
                rtol=1e-12,
                atol=1e-12,
                equal_nan=True,
                err_msg=f"Numeric mismatch in {dta_path}:{column}",
            )
        else:
            left_text = left.fillna("").astype(str).reset_index(drop=True)
            right_text = right.fillna("").astype(str).reset_index(drop=True)
            pd.testing.assert_series_equal(
                right_text, left_text, check_names=False, check_dtype=False
            )


def export_one(csv_path: Path, check_only: bool = False) -> tuple[Path, int, int]:
    """Create or verify the DTA corresponding to one CSV file."""
    frame, labels, date_formats = prepare_frame(csv_path)
    dta_path = csv_path.with_suffix(".dta")
    if not check_only:
        frame.to_stata(
            dta_path,
            version=118,
            write_index=False,
            convert_dates=date_formats,
            variable_labels=labels,
            data_label=f"Exported from {csv_path.name}"[:80],
        )
    if not dta_path.exists():
        raise FileNotFoundError(f"Missing Stata export: {dta_path}")
    verify_round_trip(frame, dta_path)
    return dta_path, len(frame), len(frame.columns)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="verify existing DTA files without rewriting them",
    )
    args = parser.parse_args()

    csv_files = tracked_csv_files()
    if not csv_files:
        raise RuntimeError("No tracked CSV files were found")

    for csv_path in csv_files:
        dta_path, rows, columns = export_one(csv_path, check_only=args.check_only)
        action = "verified" if args.check_only else "exported"
        print(f"{action}: {dta_path.relative_to(ROOT)} ({rows} rows, {columns} columns)")
    print(f"Completed {len(csv_files)} Stata exports.")


if __name__ == "__main__":
    main()
