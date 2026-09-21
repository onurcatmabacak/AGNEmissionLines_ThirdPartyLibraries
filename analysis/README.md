# analysis/

Results of the fit-quality review of the six third-party AGN tools
(BADASS3, Fantasy AGN, GELATO, GLEAM, PyQSOFit, Sculptor) applied to
`../spectrum.fits` (IeRASS J053448.4+212608, z ≈ 0.348).

- `DIAGNOSTICS.md` — the data audit: the wavelength scale of spectrum.fits
  is internally inconsistent (meant for the "confirming results" goal, this
  is the main finding: no standard single-redshift model can fit it).
- `RESULTS.md` — per-tool findings (what each run did wrong) and the tuned
  parameter choices applied to each tool's config in this repo.
- `reference_fit.py`, `region_fits2.py`, `blue_global.py`,
  `data_driven.py`, `noise.py` — the local lmfit experiments that produced
  the measured numbers.  `python ../analysis/<file>.py` needs the venv:
  `../.venv` (py3.12 + numpy/scipy/astropy/matplotlib/lmfit + pyqsofit).

Tool outputs produced during this session:
- `../pyqsofit/main_tuned.py` → `../pyqsofit/result_tuned.pdf`,
  `../pyqsofit/output_tuned.fits`, `../pyqsofit/qsopar_tuned.fits`
  (χ²_ν Hα 17.4 → 2.6; Hβ 13.8 → 3.7).
- GLEAM re-run (fixed stdev/z/line-table/resolution): fits now aligned and
  on-scale; fixed inputs written back to `../Gleam/`.
