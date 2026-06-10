"""Data access for the ADP National Employment Report series.

Design decisions (defend these):
- Source is FRED series ADPMNUSNERSA, the official ADP NER carried by the
  St. Louis Fed. FRED exposes a no-auth CSV endpoint, so we avoid scraping the
  ADP site or parsing press-release PDFs -- a far more robust ingestion path.
- FRED carries the *level* of total private employment (persons). The headline
  number everyone quotes ("+122K in May") is the month-over-month CHANGE, so we
  derive it by first-differencing the level. (Verified against ADP press
  releases: May 2026 = 132,624 - 132,502 = +122K.)
- A committed CSV snapshot under data/ means `clone and run` works with zero
  network. `refresh()` re-pulls the live series and overwrites the snapshot.
"""
from __future__ import annotations

import csv
import os
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

FRED_SERIES_ID = "ADPMNUSNERSA"
FRED_CSV_URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={FRED_SERIES_ID}"

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CACHE = os.path.join(_HERE, "..", "data", "adp_ner_level.csv")


@dataclass(frozen=True)
class Observation:
    """One month: the report month, the SA private-employment level, and the
    month-over-month change (the headline number), both in persons."""
    month: date
    level: int
    change: Optional[int]  # None for the first row (no prior month)

    @property
    def change_thousands(self) -> Optional[float]:
        return None if self.change is None else self.change / 1000.0


def _parse_csv(text: str) -> List[tuple]:
    rows = []
    reader = csv.reader(text.splitlines())
    header = next(reader, None)
    for row in reader:
        if len(row) < 2 or not row[1].strip() or row[1].strip() == ".":
            continue  # FRED uses "." for missing
        y, m, d = (int(x) for x in row[0].split("-"))
        rows.append((date(y, m, d), int(float(row[1]))))
    return rows


def load_levels(cache_path: str = DEFAULT_CACHE) -> List[tuple]:
    with open(cache_path, encoding="utf-8") as fh:
        return _parse_csv(fh.read())


def refresh(cache_path: str = DEFAULT_CACHE, timeout: int = 30) -> int:
    """Pull the live series from FRED and overwrite the local snapshot.
    Returns the number of observations written. Network required."""
    with urllib.request.urlopen(FRED_CSV_URL, timeout=timeout) as resp:
        text = resp.read().decode("utf-8")
    levels = _parse_csv(text)
    if not levels:
        raise RuntimeError("FRED returned no parseable observations")
    with open(cache_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["DATE", "VALUE"])
        for d, v in levels:
            w.writerow([d.isoformat(), v])
    return len(levels)


def get_observations(cache_path: str = DEFAULT_CACHE) -> List[Observation]:
    """Levels -> Observations with the derived monthly change."""
    levels = load_levels(cache_path)
    obs: List[Observation] = []
    prev = None
    for d, lvl in levels:
        change = None if prev is None else lvl - prev
        obs.append(Observation(month=d, level=lvl, change=change))
        prev = lvl
    return obs


def change_series(cache_path: str = DEFAULT_CACHE) -> List[float]:
    """The monthly change series in *thousands of jobs* -- the modeling target."""
    return [o.change_thousands for o in get_observations(cache_path) if o.change is not None]
