"""Orchestrator: collectors -> builder -> renderer, in one pass.

    python3 refresh.py            # sample data for every dataset
    python3 refresh.py --live     # live where a connector exists (repo_security), last-good elsewhere

In GitHub Actions the workflow then runs check_freshness.py and deploys site/.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "collectors"))

# Order matters: evidence links to control IDs, so controls run first.
COLLECTORS = ["controls", "evidence", "findings", "risks", "policies", "training", "changes", "access_reviews", "repo_security"]


def main():
    live = "--live" in sys.argv
    for name in COLLECTORS:
        mod = importlib.import_module(name)
        n = mod.main(live)
        print(f"  ✓ {name:<15} {n} rows")
    import build_register
    import gen_html
    build_register.main()
    gen_html.main()


if __name__ == "__main__":
    main()
