import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "collectors"))

import check_freshness  # noqa: E402
import _common  # noqa: E402


class FreshnessGate(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.orig = check_freshness.DATA
        check_freshness.DATA = self.tmp

    def tearDown(self):
        check_freshness.DATA = self.orig

    def write(self, state):
        (self.tmp / "_freshness.json").write_text(json.dumps(state))

    def test_fails_when_nothing_checked(self):
        self.write({})
        self.assertEqual(check_freshness.main([]), 1)

    def test_fails_on_stale_dataset(self):
        ok = {"status": "ok", "last_success": "2020-01-01T00:00:00+00:00"}
        self.write({n: ok for n in check_freshness.EXPECTED})
        self.assertEqual(check_freshness.main(["--max-age-days", "8"]), 1)

    def test_fails_on_failed_last_attempt(self):
        import datetime as dt
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        state = {n: {"status": "ok", "last_success": now} for n in check_freshness.EXPECTED}
        state["controls"]["status"] = "stale"
        self.write(state)
        self.assertEqual(check_freshness.main([]), 1)


class Collectors(unittest.TestCase):
    def test_zero_rows_is_a_failure(self):
        with self.assertRaises(RuntimeError):
            _common.publish("empty_probe", [], source="test")


class Dashboard(unittest.TestCase):
    def test_injected_markup_is_not_rendered_raw(self):
        html = (ROOT / "site" / "index.html").read_text()
        payload = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S).group(1)
        self.assertNotIn("</script", payload.lower())
        self.assertIn("const esc", html)

    def test_strict_is_never_kinder_than_audit(self):
        rows = json.loads((ROOT / "data" / "controls.json").read_text())["rows"]
        strict = sum(r["strict_status"] == "Effective" for r in rows)
        audit = sum(r["audit_status"] == "Effective" for r in rows)
        self.assertLessEqual(strict, audit)


if __name__ == "__main__":
    unittest.main()
