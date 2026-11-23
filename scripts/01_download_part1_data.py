"""Download and clean the Part 1 TQQQ data set.

The script uses Yahoo Finance's chart endpoint for reproducible daily prices.
Raw files are kept unchanged; the processed tables use adjusted ETF prices
and the unadjusted close for the Nasdaq-100 index.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.parse import quote

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
METADATA_DIR = ROOT / "data" / "metadata"

with (ROOT / "config" / "project.yaml").open() as handle:
    PROJECT_CONFIG = yaml.safe_load(handle)

PART1_CONFIG = PROJECT_CONFIG["part1"]
RAW_START = PART1_CONFIG["raw_start_date"]
ANALYSIS_START = PART1_CONFIG["analysis_start_date"]
ANALYSIS_END = PART1_CONFIG["analysis_end_date"]
PRICES_FILE = ROOT / PART1_CONFIG["prices_file"]
RETURNS_FILE = ROOT / PART1_CONFIG["returns_file"]

SYMBOLS = {
    "TQQQ": "TQQQ",
    "QQQ": "QQQ",
    "NDX": "^NDX",
}


def date_to_epoch(date_text: str, inclusive: bool = True) -> int:
    date = pd.Timestamp(date_text)
    if inclusive:
        date = date + pd.Timedelta(days=1)
    return int(date.tz_localize("UTC").timestamp())


def fetch_chart(symbol: str, start: str, end: str) -> tuple[dict, str]:
    params = {
        "period1": date_to_epoch(start, inclusive=False),
        "period2": date_to_epoch(end, inclusive=True),
        "interval": "1d",
        "events": "div,splits",
        "includeAdjustedClose": "true",
        "includePrePost": "false",
    }
    url = "https://query1.finance.yahoo.com/v8/finance/chart/{}?{}".format(
        quote(symbol, safe=""), urlencode(params)
    )
    # Yahoo may return HTTP 429 to repeated Python-library requests. Curl with
    # a browser user-agent is used only as the transport; the endpoint and
    # parsed fields remain unchanged.
    payload = None
    last_error = None
    # A long historical query can be rate-limited even when a smaller query
    # succeeds. Try the secondary Yahoo host before reporting a failure.
    hosts = ["query1.finance.yahoo.com", "query2.finance.yahoo.com"]
    url_candidates = [url.replace("query1.finance.yahoo.com", host) for host in hosts]
    for attempt in range(4):
        candidate_url = url_candidates[attempt % len(url_candidates)]
        try:
            raw_response = subprocess.check_output(
                [
                    "curl",
                    "-sS",
                    "-L",
                    "--max-time",
                    "30",
                    "-A",
                    "Mozilla/5.0",
                    candidate_url,
                ],
                text=True,
            )
            payload = json.loads(raw_response)
            if isinstance(payload, dict) and payload.get("chart", {}).get("result"):
                break
            last_error = RuntimeError(raw_response[:200])
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(2 + attempt)
    if payload is None or not payload.get("chart", {}).get("result"):
        raise RuntimeError(f"Could not download Yahoo data for {symbol}") from last_error
    result = payload.get("chart", {}).get("result")
    if not result:
        error = payload.get("chart", {}).get("error")
        raise RuntimeError(f"No chart data for {symbol}: {error}")
    return result[0], url


def event_value(events: dict, event_name: str, timestamp: int, default):
    values = events.get(event_name, {})
    event = values.get(str(timestamp)) or values.get(timestamp)
    if event is None:
        return default
    return event


def chart_to_frame(result: dict, label: str) -> pd.DataFrame:
    timestamps = result.get("timestamp", [])
    quote = result["indicators"]["quote"][0]
    adjusted = result["indicators"].get("adjclose", [{}])[0].get("adjclose", [])
    events = result.get("events", {})
    rows = []
    for i, timestamp in enumerate(timestamps):
        split = event_value(events, "splits", timestamp, {})
        split_ratio = (
            float(split.get("numerator", 1)) / float(split.get("denominator", 1))
            if split
            else 1.0
        )
        dividend_event = event_value(events, "dividends", timestamp, {})
        rows.append(
            {
                "Date": datetime.fromtimestamp(timestamp, timezone.utc).date().isoformat(),
                "Open": quote.get("open", [None] * len(timestamps))[i],
                "High": quote.get("high", [None] * len(timestamps))[i],
                "Low": quote.get("low", [None] * len(timestamps))[i],
                "Close": quote.get("close", [None] * len(timestamps))[i],
                "Adj Close": adjusted[i] if i < len(adjusted) else None,
                "Volume": quote.get("volume", [None] * len(timestamps))[i],
                "Dividends": float(dividend_event.get("amount", 0.0)),
                "Stock Splits": split_ratio,
            }
        )
    frame = pd.DataFrame(rows)
    frame["Date"] = pd.to_datetime(frame["Date"])
    frame = frame.drop_duplicates("Date").sort_values("Date").reset_index(drop=True)
    frame.insert(0, "Ticker", label)
    return frame


def download_raw() -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    frames: dict[str, pd.DataFrame] = {}
    urls: dict[str, str] = {}
    for label, symbol in SYMBOLS.items():
        # Use sub-year windows so the public endpoint does not reject a large
        # one-shot request. The concatenated file is de-duplicated by date.
        chunks = []
        chunk_start = pd.Timestamp(RAW_START)
        last_url = ""
        while chunk_start <= pd.Timestamp(ANALYSIS_END):
            chunk_end = min(
                chunk_start + pd.Timedelta(days=330), pd.Timestamp(ANALYSIS_END)
            )
            result, last_url = fetch_chart(
                symbol, chunk_start.date().isoformat(), chunk_end.date().isoformat()
            )
            chunks.append(chart_to_frame(result, label))
            chunk_start = chunk_end + pd.Timedelta(days=1)
            time.sleep(0.4)
        frame = (
            pd.concat(chunks, ignore_index=True)
            .drop_duplicates("Date")
            .sort_values("Date")
            .reset_index(drop=True)
        )
        frame.to_csv(RAW_DIR / f"{label}_raw.csv", index=False, date_format="%Y-%m-%d")
        frames[label] = frame
        urls[label] = last_url
        time.sleep(1)
    return frames, urls


def load_existing_raw() -> dict[str, pd.DataFrame]:
    """Load the frozen raw CSV files without making a network request."""
    frames: dict[str, pd.DataFrame] = {}
    for label in SYMBOLS:
        path = RAW_DIR / f"{label}_raw.csv"
        if not path.exists():
            raise FileNotFoundError(f"Missing raw CSV file: {path}")
        frame = pd.read_csv(path, parse_dates=["Date"])
        frame = frame.drop_duplicates("Date").sort_values("Date").reset_index(drop=True)
        frames[label] = frame
    return frames


def make_processed(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    selected = {}
    for label, frame in frames.items():
        frame = frame.copy()
        frame["Date"] = pd.to_datetime(frame["Date"])
        price_col = "Adj Close" if label in {"TQQQ", "QQQ"} else "Close"
        selected[label] = frame[["Date", price_col, "Volume"]].rename(
            columns={price_col: f"{label}_price", "Volume": f"{label}_volume"}
        )

    prices = selected["TQQQ"]
    prices = prices.merge(selected["QQQ"], on="Date", how="inner")
    prices = prices.merge(selected["NDX"], on="Date", how="inner")
    prices = prices.sort_values("Date").drop_duplicates("Date").reset_index(drop=True)
    prices = prices.loc[
        (prices["Date"] >= ANALYSIS_START) & (prices["Date"] <= ANALYSIS_END)
    ].copy()

    price_columns = ["TQQQ_price", "QQQ_price", "NDX_price"]
    if prices[price_columns].isna().any().any():
        raise ValueError("Missing prices remain after the common-date merge")
    if (prices[price_columns] <= 0).any().any():
        raise ValueError("Non-positive prices remain after cleaning")

    returns = prices[["Date"]].copy()
    for label in ["TQQQ", "QQQ", "NDX"]:
        returns[f"{label}_simple_ret"] = prices[f"{label}_price"].pct_change()
        returns[f"{label}_log_ret"] = np.log1p(returns[f"{label}_simple_ret"])
    returns = returns.join(prices.drop(columns="Date").set_index(prices.index))
    returns = returns.iloc[1:].reset_index(drop=True)

    # Flag observations for manual review; genuine crisis observations are kept.
    returns["manual_review_flag"] = (
        returns["TQQQ_simple_ret"].abs() > 0.30
    ) | (returns["QQQ_simple_ret"].abs() > 0.15) | (
        returns["NDX_simple_ret"].abs() > 0.15
    )
    return prices, returns


def write_csv_if_changed(
    frame: pd.DataFrame, path: Path, date_format: str | None = None
) -> bool:
    """Write a CSV only when its tabular values have materially changed."""
    candidate = frame.copy()
    for column in candidate.select_dtypes(include=["datetime", "datetimetz"]):
        candidate[column] = candidate[column].dt.strftime(date_format or "%Y-%m-%d")

    if path.exists():
        existing = pd.read_csv(path)
        same_schema = list(existing.columns) == list(candidate.columns)
        if same_schema and existing.shape == candidate.shape:
            equivalent = True
            for column in candidate.columns:
                left = candidate[column]
                right = existing[column]
                both_numeric = pd.api.types.is_numeric_dtype(
                    left
                ) and pd.api.types.is_numeric_dtype(right)
                if both_numeric:
                    if not np.allclose(
                        left.to_numpy(dtype=float),
                        right.to_numpy(dtype=float),
                        rtol=1e-12,
                        atol=1e-15,
                        equal_nan=True,
                    ):
                        equivalent = False
                        break
                else:
                    left_text = left.fillna("").astype(str).reset_index(drop=True)
                    right_text = right.fillna("").astype(str).reset_index(drop=True)
                    if not left_text.equals(right_text):
                        equivalent = False
                        break
            if equivalent:
                print(f"Unchanged: {path.relative_to(ROOT)}")
                return False

    frame.to_csv(path, index=False, date_format=date_format)
    print(f"Updated: {path.relative_to(ROOT)}")
    return True


def write_quality_table(prices: pd.DataFrame, returns: pd.DataFrame) -> None:
    checks = [
        ("price_rows", len(prices)),
        ("return_rows", len(returns)),
        ("price_start", prices["Date"].min().date().isoformat()),
        ("price_end", prices["Date"].max().date().isoformat()),
        ("duplicate_dates", int(prices["Date"].duplicated().sum())),
        ("missing_price_cells", int(prices.isna().sum().sum())),
        ("manual_review_rows", int(returns["manual_review_flag"].sum())),
    ]
    quality = pd.DataFrame(checks, columns=["check", "value"])
    write_csv_if_changed(quality, METADATA_DIR / "part1_data_quality.csv")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one file without loading it all at once."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_checksum_manifest() -> None:
    """Record checksums for the reviewed Part 1 data and metadata files."""
    paths = sorted(RAW_DIR.glob("*_raw.csv"))
    paths.extend([PRICES_FILE, RETURNS_FILE])
    paths.extend(
        path
        for path in [
            METADATA_DIR / "part1_source_manifest.csv",
            METADATA_DIR / "part1_product_facts.csv",
            METADATA_DIR / "part1_data_dictionary.csv",
            METADATA_DIR / "part1_data_quality.csv",
        ]
        if path.exists()
    )
    rows = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in paths
    ]
    write_csv_if_changed(pd.DataFrame(rows), METADATA_DIR / "part1_checksums.csv")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clean-existing-raw",
        action="store_true",
        help=(
            "rebuild the processed CSV files from the frozen raw CSV files "
            "without downloading data or changing source metadata"
        ),
    )
    args = parser.parse_args()

    for directory in [RAW_DIR, PROCESSED_DIR, METADATA_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    if args.clean_existing_raw:
        frames = load_existing_raw()
        urls = None
    else:
        frames, urls = download_raw()
    prices, returns = make_processed(frames)
    write_csv_if_changed(prices, PRICES_FILE, date_format="%Y-%m-%d")
    write_csv_if_changed(returns, RETURNS_FILE, date_format="%Y-%m-%d")
    write_quality_table(prices, returns)

    if urls is not None:
        downloaded_at = datetime.now(timezone.utc).isoformat()
        manifest = pd.DataFrame(
            [
                {
                    "ticker": label,
                    "source": "Yahoo Finance chart API",
                    "source_url": urls[label],
                    "downloaded_at_utc": downloaded_at,
                    "raw_start_requested": RAW_START,
                    "raw_end_requested": ANALYSIS_END,
                    "analysis_start": ANALYSIS_START,
                    "analysis_end": ANALYSIS_END,
                    "field_used": (
                        "Adj Close" if label in {"TQQQ", "QQQ"} else "Close"
                    ),
                    "adjustment_note": (
                        "Adjusted Close used for ETF total-return series"
                        if label in {"TQQQ", "QQQ"}
                        else "Close used for Nasdaq-100 index series"
                    ),
                }
                for label in SYMBOLS
            ]
        )
        manifest.to_csv(METADATA_DIR / "part1_source_manifest.csv", index=False)
    write_checksum_manifest()
    print(f"Saved {len(prices):,} common price rows and {len(returns):,} return rows")
    print(f"Price range: {prices['Date'].min().date()} to {prices['Date'].max().date()}")
    print(f"Manual-review rows: {int(returns['manual_review_flag'].sum())}")


if __name__ == "__main__":
    main()
