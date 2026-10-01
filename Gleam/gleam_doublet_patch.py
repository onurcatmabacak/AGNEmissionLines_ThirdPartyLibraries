#!/usr/bin/env python3
"""Runtime patch for GLEAM: tie the physical doublets.

GLEAM fits one independent Gaussian per line and has no ratio mechanism, so
[OIII]4959/5007 came out ~0.1-0.18 instead of ~0.33.  With ``tolerance >= 47``
in gleamconfig.yaml the [OIII] pair (and, already, Ha+[NII]) are fit in the same
group; this patch then constrains ``g4959_amplitude = g5007_amplitude/3`` and
``g6548_amplitude = g6583_amplitude/3`` via lmfit parameter expressions, and
makes ``is_good`` ignore the tied (expression) amplitudes so the subset search
does not delete them.

Applied inside the container at start-up by ``Gleam/gleam.sh``; idempotent.
"""

from __future__ import annotations

import pathlib

FILE = pathlib.Path("/usr/local/lib/python3.8/site-packages/gleam/gaussian_fitting.py")
PLOT_FILE = pathlib.Path("/usr/local/lib/python3.8/site-packages/gleam/plot_gaussian.py")
MAIN_FILE = pathlib.Path("/usr/local/lib/python3.8/site-packages/gleam/main.py")

# The results FITS table is written after the plotting loop; a plotting failure
# (GLEAM's label code breaks for 3+-line groups) must not discard the table.
MAIN_OLD = (
    "                plot_line(\n"
    "                    lines,\n"
    "                    spectrum_fit,\n"
    "                    config.resolution / (1 + target[\"Redshift\"]),\n"
    "                    sky,\n"
    "                )"
)
MAIN_NEW = (
    "                # Write the results table before plotting, because GLEAM's\n"
    "                # label code can crash on 3+-line groups.\n"
    "                try:\n"
    "                    _out = astropy.table.vstack(tables)\n"
    "                    _out = Table(_out, masked=True, copy=False)\n"
    "                    _out.write(\"{}.fits\".format(rf.naming_convention(\n"
    "                        data_path, target[\"Sample\"], target[\"SourceNumber\"],\n"
    "                        target[\"Setup\"], target[\"Pointing\"], \"linefits\")),\n"
    "                        overwrite=True)\n"
    "                except Exception as _ew:\n"
    "                    print(\"WARNING: GLEAM FITS write failed:\", _ew)\n"
    "                try:\n"
    "                    plot_line(\n"
    "                        lines,\n"
    "                        spectrum_fit,\n"
    "                        config.resolution / (1 + target[\"Redshift\"]),\n"
    "                        sky,\n"
    "                    )\n"
    "                except Exception as _e:\n"
    "                    print(\"WARNING: GLEAM plot_line failed:\", _e)"
)

# plot_gaussian.adjust_labels only defines `offsets` for 1- or 2-line groups;
# a 3+-line group (e.g. Ha + Ha_broad + [NII]) raises UnboundLocalError and
# aborts the run before the FITS table is written.
PLOT_OLD = "        for (text, offset) in zip(texts, offsets):"

# plot_gaussian_fit draws each Gaussian separately over the continuum; add the
# sum so the user can see the TOTAL line model.
PLOT2_OLD = "    for line_fit in spectrum_fit.lines:\n        # Plot detections"
PLOT2_NEW = (
    "    # Total model = continuum + sum of all detected Gaussians.\n"
    "    _detected = [l for l in spectrum_fit.lines if isinstance(l, gf.Line)]\n"
    "    if _detected:\n"
    "        _total = sum(\n"
    "            gf.gauss_function(wl, l.height.value, l.wavelength.value, l.sigma.value)\n"
    "            for l in _detected\n"
    "        )\n"
    "        ax.plot(wl, _total + spectrum_fit.continuum.value, color=\"black\", lw=1.2)\n"
    + PLOT2_OLD
)
PLOT_NEW = (
    "        else:\n"
    "            offsets = tuple((0.0, 0.0) for _ in texts)\n"
    "        for (text, offset) in zip(texts, offsets):"
)

INJECT = (
    "    # Tie physical doublets: [OIII]4959 = 5007/3, [NII]6548 = 6583/3.\n"
    "    _wl = list(wl_line.to(x.unit).value)\n"
    "    def _idx(target, tol=3.0):\n"
    "        for _i, _wv in enumerate(_wl):\n"
    "            if abs(_wv - target) < tol:\n"
    "                return _i\n"
    "        return None\n"
    "    # Duplicate-wavelength rows are broad counterparts: seed them with a\n"
    "    # broad initial width so the fit does not collapse to one narrow line.\n"
    "    for _i, _w in enumerate(_wl):\n"
    "        for _j in range(_i):\n"
    "            if abs(_w - _wl[_j]) < 3.0:\n"
    "                _bf = 45.0 * (_w / 6564.6)\n"
    "                model.set_param_hint(f\"g{_i}_fwhm\", value=_bf, min=8.0)\n"
    "                model.set_param_hint(f\"g{_i}_sigma\", value=_bf / 2.3548, min=3.0)\n"
    "                break\n"
    "    # Amplitudes must stay physical (GLEAM otherwise returns negative fluxes).\n"
    "    for _i in range(len(_wl)):\n"
    "        model.set_param_hint(f\"g{_i}_amplitude\", min=0.0)\n"
    "    # [NII] is narrow: cap its width so a broad Gaussian cannot be\n"
    "    # misfiled at the [NII] position (which steals the broad Halpha).\n"
    "    for _i, _w in enumerate(_wl):\n"
    "        if abs(_w - 6548.05) < 3.0 or abs(_w - 6583.46) < 3.0:\n"
    "            model.set_param_hint(f\"g{_i}_fwhm\", max=20.0)\n"
    "            model.set_param_hint(f\"g{_i}_sigma\", max=8.5)\n"
    "    for _a, _b in [(4958.9, 5006.8), (6548.05, 6583.46)]:\n"
    "        _ia, _ib = _idx(_a), _idx(_b)\n"
    "        if _ia is not None and _ib is not None:\n"
    "            model.set_param_hint(\n"
    "                f\"g{_ia}_amplitude\", expr=f\"g{_ib}_amplitude / 3.0\"\n"
    "            )\n"
    "\n"
)

OLD_IS_GOOD = (
    "    return all(\n"
    "        RandomVariable.from_param(fitparams[f\"g{i}_amplitude\"]).significance > SN_limit\n"
    "        for i in range(len(model.components) - 1)\n"
    "    )"
)
NEW_IS_GOOD = (
    "    for i in range(len(model.components) - 1):\n"
    "        _p = fitparams[f\"g{i}_amplitude\"]\n"
    "        if getattr(_p, \"expr\", None):\n"
    "            continue  # tied to a reference line; do not reject the group\n"
    "        if RandomVariable.from_param(_p).significance <= SN_limit:\n"
    "            return False\n"
    "    return True"
)

ANCHOR = "    # Set the continuum to the median of the selected range"


def main() -> int:
    src = FILE.read_text()
    if "Tie physical doublets" in src:
        print("GLEAM already patched")
        return 0
    if ANCHOR not in src or OLD_IS_GOOD not in src:
        print("GLEAM patch anchors not found -- skipping")
        return 1
    src = src.replace(ANCHOR, INJECT + ANCHOR, 1)
    src = src.replace(OLD_IS_GOOD, NEW_IS_GOOD, 1)
    FILE.write_text(src)
    _plot = PLOT_FILE.read_text()
    if "patched GLEAM label offsets" not in _plot and PLOT_OLD in _plot:
        _plot = _plot.replace(PLOT_OLD, PLOT_NEW, 1)
        PLOT_FILE.write_text(_plot)
        print("patched GLEAM label offsets")
    _plot = PLOT_FILE.read_text()
    if "_total = sum(" not in _plot and PLOT2_OLD in _plot:
        _plot = _plot.replace(PLOT2_OLD, PLOT2_NEW, 1)
        PLOT_FILE.write_text(_plot)
        print("patched GLEAM total-line plot")
    if MAIN_OLD in MAIN_FILE.read_text():
        main_txt = MAIN_FILE.read_text().replace(MAIN_OLD, MAIN_NEW, 1)
        MAIN_FILE.write_text(main_txt)
        print("patched GLEAM non-fatal plotting")
    print("patched GLEAM doublet ties")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
