#!/usr/bin/env python3
"""Render the machine-readable caveat matrix into docs/."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "configs" / "caveats.yaml"
OUT_MD = ROOT / "docs" / "CAVEAT_MATRIX.md"
OUT_JSON = ROOT / "docs" / "caveat_matrix.json"
OUT_CSV = ROOT / "docs" / "caveat_matrix.csv"


def main() -> int:
    data = yaml.safe_load(SRC.read_text())
    tools = data["tools"]
    excluded = data.get("excluded", [])
    OUT_JSON.write_text(json.dumps(data, indent=2) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["tool", "kind", "wave", "status", "severity", "caveat", "evidence", "mitigation"])
        for t in tools:
            w.writerow([t["tool"], t["kind"], t["wave"], t["status"], t["severity"],
                        t["caveat"], t["evidence"], t["mitigation"]])
    lines = [
        "# Caveat matrix",
        "",
        "Generated from `configs/caveats.yaml` by `pipeline/build_caveat_matrix.py`.",
        "`status` is what the repository actually validated; `severity` is the",
        "scientific impact if the caveat is ignored.",
        "",
        "| tool | kind | wave | status | severity | caveat | evidence / mitigation |",
        "|---|---|---|---|---|---|---|",
    ]
    for t in tools:
        lines.append(
            f"| `{t['tool']}` | {t['kind']} | {t['wave']} | **{t['status']}** | {t['severity']} | "
            f"{t['caveat']} | {t['evidence']}<br>*Mitigation:* {t['mitigation']} |"
        )
    lines += ["", "## Excluded or intentionally not run", "",
              "| code/path | reason | evidence |", "|---|---|---|"]
    for e in excluded:
        lines.append(f"| `{e['name']}` | {e['reason']} | {e['evidence']} |")
    lines += [
        "",
        "## Decision-engine transparency",
        "",
        "`pipeline/decide_tools.py` returns both a tool list and the reasons for",
        "each selection.  Run:",
        "",
        "```bash",
        ".venv/bin/python pipeline/decide_tools.py --goal lines --z 0.59 --wave-min 3800 --wave-max 9200 --angstrom",
        ".venv/bin/python pipeline/decide_tools.py --goal xray --z 0.033 --wave-min 3 --wave-max 20",
        "```",
        "",
        "The output is advisory: the source manifest's `tools` list is the final",
        "routing decision.  SED codes (`cigale_sed`, `agnfitter_sed`) are never",
        "returned as line fitters.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines))
    print(f"wrote {OUT_MD.relative_to(ROOT)} ({len(tools)} tools, {len(excluded)} exclusions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
