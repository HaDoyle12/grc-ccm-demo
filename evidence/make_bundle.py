"""Package the current datasets as an evidence bundle with a manifest.

The manifest records WHAT was collected, HOW (exact command), BY WHOM (actor +
token identity), WHEN (UTC) and a SHA-256 per file. The workflow then signs
every file with a build-provenance attestation, so the bundle is verifiable
with `gh attestation verify` long after the run logs expire.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "bundle"
FILES = ["repo_security.json", "controls.json", "findings.json", "_freshness.json"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-url", default="local run")
    ap.add_argument("--actor", default="local")
    a = ap.parse_args()
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir()
    rows = []
    for f in FILES:
        src = ROOT / "data" / f
        dst = OUT / f.lstrip("_")
        shutil.copy2(src, dst)
        rows.append((dst.name, hashlib.sha256(dst.read_bytes()).hexdigest()))
    try:
        ident = subprocess.run(["gh", "auth", "status", "--json", "hosts"], capture_output=True, text=True, timeout=30).stdout.strip() or "n/a"
    except Exception:  # noqa: BLE001
        ident = "n/a"
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    md = [f"# Evidence bundle — {now}", "",
          "> Demo: Northwind Cloud is fictional. `repo_security.json` is LIVE data for this demo repository only.", "",
          f"- **Run:** {a.run_url}", f"- **Triggered by:** {a.actor}", "- **Command:** `python3 refresh.py --live && python3 evidence/make_bundle.py`", "",
          "| File | SHA-256 |", "|---|---|", *[f"| `{n}` | `{h}` |" for n, h in rows], "",
          "## Verify", "```bash", "gh release download <this-tag> --repo <owner/repo>",
          "sha256sum -c <(awk -F'`' '/^\\| `/{print $4\"  \"$2}' MANIFEST.md)",
          "gh attestation verify repo_security.json --repo <owner/repo>", "```", "",
          "<details><summary>Collecting identity (gh auth status --json)</summary>", "", "```json",
          _redact(ident), "```", "</details>"]
    (OUT / "MANIFEST.md").write_text("\n".join(md) + "\n")
    print(f"bundle: {len(rows)} files + MANIFEST.md")


def _redact(text: str) -> str:
    try:
        data = json.loads(text)
    except ValueError:
        return text
    for host in (data.get("hosts") or {}).values():
        for acct in host if isinstance(host, list) else []:
            acct.pop("token", None)
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    main()
