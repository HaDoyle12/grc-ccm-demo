"""Collector: security awareness training  (systems of record: HRIS roster + LMS completions).

Join key is the employee ID, never the name. People in the roster with no LMS
record are reported as "no record" rather than silently dropped -- that is the
population an auditor samples from. Live pull is an HRIS report export + the
LMS completions API; both land in data/ as thin CSV slices.
"""
from __future__ import annotations

import sys

from _common import rng, run


def sample():
    r = rng("training")
    rows = []
    for cohort, n in [("Employees", 1240), ("Contractors", 310), ("New hires (30-day window)", 64)]:
        done = int(n * r.uniform(0.82, 0.97))
        overdue = int((n - done) * r.uniform(0.4, 0.7))
        rows.append({"cohort": cohort, "population": n, "completed": done, "overdue": overdue,
                     "no_record": n - done - overdue, "pct": round(100 * done / n, 1)})
    return rows


def main(live: bool = False) -> int:
    return run("training", "HRIS roster + LMS completions", sample, live=live)


if __name__ == "__main__":
    print(main("--live" in sys.argv))
