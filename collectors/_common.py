"""Shared helpers for every collector.

Every collector follows the same contract:
  1. authenticate to ONE system of record
  2. pull a thin slice (IDs, states, dates, links -- never the raw evidence)
  3. write a fixed-schema JSON file to data/<name>.json

If a live pull fails, the collector keeps the last-good file and records the
failed attempt in data/_freshness.json, so the dashboard keeps publishing while
the freshness gate (check_freshness.py) makes the staleness visible.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FRESHNESS = DATA / "_freshness.json"

# Every number in this demo is fictional. The seed keeps runs reproducible so
# diffs between weekly refreshes show "real" movement rather than noise.
AS_OF = dt.date(2026, 10, 26)
DEMO_URL = "https://github.com/HaDoyle12/grc-ccm-demo"


def rng(name: str) -> random.Random:
    return random.Random(f"northwind-{name}")


def days_ago(n: int) -> str:
    return (AS_OF - dt.timedelta(days=n)).isoformat()


def days_ahead(n: int) -> str:
    return (AS_OF + dt.timedelta(days=n)).isoformat()


def atomic_write(path: Path, payload) -> None:
    """Write via temp file + rename so a crash never leaves half a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False)
        fh.write("\n")
    os.replace(tmp, path)


def record_freshness(name: str, *, ok: bool, mode: str, rows: int, source: str, error: str = "") -> None:
    state = json.loads(FRESHNESS.read_text()) if FRESHNESS.exists() else {}
    prev = state.get(name, {})
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    state[name] = {
        "source": source,
        "mode": mode,
        "last_attempt": now,
        "last_success": now if ok else prev.get("last_success"),
        "rows": rows if ok else prev.get("rows", 0),
        "status": "ok" if ok else "stale",
        "error": error,
    }
    atomic_write(FRESHNESS, state)


def publish(name: str, rows: list[dict], *, source: str, mode: str = "sample") -> int:
    if not rows:
        # A collector that returns nothing is treated as a failure, not "all clear".
        raise RuntimeError(f"{name}: collector returned 0 rows")
    atomic_write(DATA / f"{name}.json", {"dataset": name, "source": source, "mode": mode,
                                         "as_of": AS_OF.isoformat(), "rows": rows})
    record_freshness(name, ok=True, mode=mode, rows=len(rows), source=source)
    return len(rows)


def run(name: str, source: str, sample_fn, live_fn=None, live: bool = False) -> int:
    """Run live if asked and possible; on any live failure keep last-good data."""
    if live and live_fn is not None:
        try:
            return publish(name, live_fn(), source=source, mode="live")
        except Exception as exc:  # noqa: BLE001 - every failure must be recorded
            record_freshness(name, ok=False, mode="live", rows=0, source=source, error=str(exc)[:300])
            if (DATA / f"{name}.json").exists():
                print(f"  ! {name}: live pull failed ({exc}); kept last-good data")
                return 0
    return publish(name, sample_fn(), source=source, mode="sample")
