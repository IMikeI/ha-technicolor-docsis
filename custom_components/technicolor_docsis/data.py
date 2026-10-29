"""Pure parsing and stable row identities for router measurements."""

from __future__ import annotations

import math
import re
from typing import Any

CHANNEL_TABLES = ("DSTbl", "exDSTbl", "USTbl", "exUSTbl")
TABLE_NAMES = {
    "DSTbl": "Downstream SC-QAM",
    "exDSTbl": "Downstream OFDM",
    "USTbl": "Upstream SC-QAM",
    "exUSTbl": "Upstream OFDMA",
    "ErrTbl": "Error statistics slot",
}


def row_identity(table: str, row: dict[str, Any]) -> str | None:
    """Keep channels stable across sorting; error slots have no known channel ID."""
    value = row.get("__id") if table == "ErrTbl" else row.get("ChannelID")
    return str(value) if value is not None and str(value) else None


def find_row(data: dict[str, Any], table: str, identity: str) -> dict[str, Any] | None:
    """Return None rather than a zero-valued replacement for absent channels."""
    return next(
        (row for row in data["modem"].get(table, []) if row_identity(table, row) == identity),
        None,
    )


def number(value: Any, unit: str | None = None) -> int | float | None:
    """Parse complete values, preserving integer counters and validating units."""
    if value is None or isinstance(value, bool):
        return None
    match = re.fullmatch(r"\s*([+-]?\d+(?:\.\d+)?)\s*([^\d\s]*)\s*", str(value))
    if not match:
        return None
    numeric, suffix = match.groups()
    if unit == "MHz" and suffix in ("Hz", "kHz", "MHz", "GHz"):
        result = float(numeric) * {"Hz": 0.000001, "kHz": 0.001, "MHz": 1, "GHz": 1000}[suffix]
    elif suffix and suffix != unit:
        return None
    else:
        result = float(numeric) if "." in numeric else int(numeric)
    return result if isinstance(result, int) or math.isfinite(result) else None
