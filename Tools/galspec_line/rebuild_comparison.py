#!/usr/bin/env python3
"""Rebuild the cross-tool comparison for a finished GalSpec product.

A GalSpec run compares its H-beta/[O III] 5007 fluxes with the sibling tool
products for the same source.  When the chain is produced in scratch space
(``work/<run>/``) those siblings are not visible, so this utility re-runs only
the comparison step against a committed reference root:

    python rebuild_comparison.py outputs/galspec_line/04592649654_z_0.5874 \
        --reference-root outputs --update-run-json

It rewrites ``galspec_comparison.csv`` and (with ``--update-run-json``) the
``reference_runtimes`` block of ``run.json``.  It never touches the fit, the
chain or the line measurements.

Run it inside the ``galspec_line`` image, e.g.:

    docker run --rm --user "$(id -u):$(id -g)" \
      -v "$PWD/outputs:/app/outputs:ro" -v "<product>:/app/product" \
      -w /app/galspec_line --entrypoint python galspec_line \
      rebuild_comparison.py /app/product --reference-root /app/outputs
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import galspec_full as gf  # noqa: E402
import run_galspec as gr  # noqa: E402


def load_rows(product: Path) -> list[dict]:
    """Read galspec_lines.csv back into the row dicts the writer produced."""
    rows = []
    with (product / "galspec_lines.csv").open(newline="") as fh:
        for row in csv.DictReader(fh):
            out = dict(row)
            for key in ("flux_1e17", "flux_err_1e17", "fwhm_kms", "fwhm_err_kms",
                        "velocity_kms", "velocity_err_kms", "snr", "flux", "flux_err",
                        "lambda_rest"):
                if key in out:
                    out[key] = gr._num(out[key])
            rows.append(out)
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("product", type=Path,
                    help="finished product directory, e.g. outputs/galspec_line/<source>")
    ap.add_argument("--reference-root", type=Path, default=Path("/app/outputs"),
                    help="root holding the sibling outputs/<tool>/<source>/ trees")
    ap.add_argument("--update-run-json", action="store_true",
                    help="also rewrite run.json's reference_runtimes block")
    args = ap.parse_args(argv)

    product = args.product
    if not (product / "galspec_lines.csv").exists():
        raise SystemExit(f"no galspec_lines.csv in {product}")
    cfg_path = product / "config.effective.json"
    cfg = json.loads(cfg_path.read_text()) if cfg_path.exists() else {}
    # The container mount name is arbitrary; take the source key from the
    # effective config so reference lookup never depends on the mount point.
    source_key = (cfg.get("_effective") or {}).get("object") or product.name

    rows = load_rows(product)
    comparison = gf.extended_comparison(product, rows, cfg, args.reference_root)
    pd.DataFrame(comparison).to_csv(product / "galspec_comparison.csv", index=False)
    print(f"wrote {product / 'galspec_comparison.csv'} ({len(comparison)} rows)")

    if args.update_run_json:
        run_path = product / "run.json"
        if run_path.exists():
            run = json.loads(run_path.read_text())
            root = args.reference_root
            run["reference_runtimes"] = {
                tool: gr._reference_runtime(gr._reference_dir(root, tool, source_key))
                for tool in ("pyqsofit_uv", "pyqsofitspec_line", "gandalf_line",
                             "s3fit_line", "qgfit", "sheap_line")
            }
            run_path.write_text(json.dumps(run, indent=2) + "\n")
            print(f"updated {run_path} reference_runtimes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
