import csv
import io
from dataclasses import dataclass


@dataclass(frozen=True)
class Report:
    rows: int
    missing: int
    gaps: int
    quality_score: int


def check_quality(csv_text: str, max_gap: float = 10.0) -> Report:
    """Score a measurement file: every missing value costs 1 point, every gap in time costs 5."""
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    missing = sum(1 for row in rows for value in row.values() if value in ("", None))
    times = [float(row["time"]) for row in rows if row.get("time")]
    gaps = sum(1 for a, b in zip(times, times[1:], strict=False) if b - a > max_gap)
    score = max(0, 100 - missing - 5 * gaps)
    return Report(rows=len(rows), missing=missing, gaps=gaps, quality_score=score)
