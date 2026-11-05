#!/usr/bin/env python3
"""Compare PyQSOFit UV/optical line areas with the SDSS ZLINE table.

The point is not to force agreement: the table records broad and narrow
PyQSOFit components separately so a broad C III] complex is not mistaken for a
narrow-line flux.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "Tools"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from pipeline_ir.spectrum import zline_table  # noqa: E402
from pipeline.io_layout import iter_sources, output_dir, source_files  # noqa: E402

MAP = {
    "MgII": ("Mg_II 2799", ("MgII_br", "MgII_na")),
    "CIII": ("C_III] 1908", ("CIII_br", "CIII_na")),
    "CIV": ("C_IV 1549", ("CIV_br", "CIV_na")),
    "Hb": ("H_beta", ("Hb_br", "Hb_na")),
    "OIII5007": ("[O_III] 5007", ("OIII5007w", "OIII5007c")),
}


def read_lines(path: Path):
    out = {}
    if not path.exists():
        return out
    with path.open() as fh:
        for r in csv.DictReader(fh):
            out[(r["line"], r["component"])] = float(r["area_1e17"])
    return out


def main():
    rows = []
    for src in iter_sources():
        if src.get("kind") != "sdss":
            continue
        spec = source_files(src, "spectrum")
        if not spec:
            continue
        zt = zline_table(spec[0])
        lines = read_lines(output_dir(src["key"], "pyqsofit_uv") / "pyqsofit_lines.csv")
        for key, (zname, components) in MAP.items():
            if zname not in zt:
                continue
            zarea = float(zt[zname]["area"])
            broad = lines.get((components[0], "broad"), 0.0)
            narrow = lines.get((components[1], "narrow"), 0.0)
            rows.append({"source": src["key"], "line": key,
                         "zline_area": zarea, "pyq_broad": broad,
                         "pyq_narrow": narrow, "pyq_total": broad + narrow,
                         "total/zline": (broad + narrow) / zarea if zarea else "",
                         "narrow/zline": narrow / zarea if zarea else ""})
    # per-source validation tables stay under the source/tool directory
    for src in iter_sources():
        sub = [r for r in rows if r["source"] == src["key"]]
        if not sub:
            continue
        f = output_dir(src["key"], "pyqsofit_uv") / "zline_comparison.csv"
        f.parent.mkdir(parents=True, exist_ok=True)
        with f.open("w", newline="") as fh:
            w = csv.DictWriter(fh, lineterminator="\n", fieldnames=list(sub[0]))
            w.writeheader(); w.writerows(sub)
    # compact documentation table
    out = ROOT / "docs" / "pyqsofit_zline_comparison.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, lineterminator="\n", fieldnames=list(rows[0]) if rows else ["source"])
        w.writeheader(); w.writerows(rows)
    print(f"wrote per-source tables and {out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
