"""Builder: join every data/<dataset>.json into one queryable SQLite register.

Outputs
  data/register.db        one table per dataset + a `summary` view
  exports/<dataset>.csv   for people who live in Excel
  data/history.json       one row of headline stats per run (trend charts)

Design rules (mirrors the production register):
  * link, never duplicate -- rows hold IDs and URLs back to the system of record
  * the builder is tool-agnostic; only collectors know about specific systems
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "collectors"))
from _common import AS_OF, DATA, atomic_write, rng  # noqa: E402

ROOT = Path(__file__).parent
DATASETS = ["controls", "evidence", "findings", "risks", "policies", "training", "changes", "access_reviews", "repo_security"]


def load(name):
    p = DATA / f"{name}.json"
    if not p.exists():
        raise SystemExit(f"missing data/{name}.json -- run refresh.py first")
    return json.loads(p.read_text())["rows"]


def headline(rows_by):
    c = rows_by["controls"]
    f = [x for x in rows_by["findings"] if x["status"] != "Closed"]
    return {
        "controls": len(c),
        "strict_effective": sum(x["strict_status"] == "Effective" for x in c),
        "audit_effective": sum(x["audit_status"] == "Effective" for x in c),
        "automated": sum(x["automation"] == "Automated" for x in c),
        "open_findings": len(f), "overdue_findings": sum(x["overdue"] for x in f),
        "stale_evidence": sum(x["stale"] for x in rows_by["evidence"]),
        "change_sla_pct": round(100 * sum(x["within_sla"] for x in rows_by["changes"]) / len(rows_by["changes"]), 1),
    }


def seed_history(h):
    """Fabricate 11 prior weekly points so the demo trend chart has a shape."""
    r = rng("history")
    out, s, a = [], max(h["strict_effective"] - 22, 10), max(h["audit_effective"] - 9, 10)
    import datetime as dt
    for w in range(11, 0, -1):
        s, a = min(h["strict_effective"], s + r.randint(0, 4)), min(h["audit_effective"], a + r.randint(0, 2))
        out.append({"week": (AS_OF - dt.timedelta(weeks=w)).isoformat(), "strict_effective": s, "audit_effective": a,
                    "open_findings": h["open_findings"] + r.randint(0, 5), "controls": h["controls"]})
    return out


def main():
    rows_by = {n: load(n) for n in DATASETS}
    db_path = DATA / "register.db"
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    (ROOT / "exports").mkdir(exist_ok=True)
    for name, rows in rows_by.items():
        cols = list(rows[0].keys())
        quoted = ", ".join('"' + c + '"' for c in cols)
        con.execute(f"CREATE TABLE {name} ({quoted})")
        con.executemany(f"INSERT INTO {name} VALUES ({', '.join('?' * len(cols))})",
                        [[json.dumps(r[c]) if isinstance(r[c], (list, dict)) else r[c] for c in cols] for r in rows])
        with open(ROOT / "exports" / f"{name}.csv", "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
    con.execute("""CREATE VIEW control_coverage AS
        SELECT c.control_id, c.title, c.domain, c.strict_status, c.audit_status,
               COUNT(e.evidence_id) AS linked_evidence, SUM(e.stale) AS stale_evidence
        FROM controls c LEFT JOIN evidence e ON e.control_id = c.control_id GROUP BY c.control_id""")
    con.commit()
    con.close()

    h = headline(rows_by)
    hist_path = DATA / "history.json"
    hist = json.loads(hist_path.read_text()) if hist_path.exists() else seed_history(h)
    hist = [x for x in hist if x["week"] != AS_OF.isoformat()] + [{"week": AS_OF.isoformat(), **{k: h[k] for k in ("strict_effective", "audit_effective", "open_findings", "controls")}}]
    atomic_write(hist_path, hist[-26:])
    atomic_write(DATA / "summary.json", h)
    print(f"register built: {sum(len(v) for v in rows_by.values())} rows across {len(rows_by)} datasets")
    return h


if __name__ == "__main__":
    main()
