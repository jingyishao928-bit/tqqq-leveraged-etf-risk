"""Canonical data schema and validation helpers."""

REQUIRED_COLUMNS = (
    "date",
    "qqq_adj_close",
    "tqqq_adj_close",
    "sqqq_adj_close",
    "qqq_simple_return",
    "qqq_log_return",
    "tqqq_simple_return",
    "sqqq_simple_return",
)


def validate_columns(columns: list[str]) -> None:
    """Raise when the canonical processed-data columns are missing."""
    missing = [column for column in REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")

