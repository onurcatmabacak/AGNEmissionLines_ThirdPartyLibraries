# `rxte_xspec` - official RXTE/PCA spectra with HEASoft/PyXspec

This tool fits the **official HEASARC RXTE/PCA `stdprod` products** of an AGN
with **HEASoft/PyXspec**.  It is the repository's second X-ray branch, next to
the XMM-Newton EPIC branch, and it is deliberately separate from the
UV/optical/IR emission-line matrix.

The production example is **3C 120** (ObsID `10339-02-01-01`, z = 0.0330,
PCA Standard2, 9808 s, 294,417 net counts).  The fallback example is
**MCG-6-30-15** (ObsID `20310-01-02-00`, z = 0.007749, 5888 s, 77,824 net
counts).  Both use the real HEASARC source spectrum, the real PCA background
model and the real 5-PCU response matrix.  No response is synthetic.

## The data: PPS-equivalent `stdprod`, not a new reduction

The files are the HEASARC **`stdprod`** products:

```text
inputs/3C120_z_0.0330/xray/rxte_10339-02-01-01/
  xp10339020101_s2.pha.gz     # PCA Standard2 source spectrum, 129 channels
  xp10339020101_b2.pha.gz     # PCA background model
  xp10339020101.rsp.gz        # PCA response, 5 PCUs summed
  download.sh                 # reproducible download + SHA256 check
```

`stdprod` is the official reduced PCA product set.  It is the RXTE equivalent
of the XMM-Newton PPS products.  **This tool does not run `pcabackest` or
`saextrct`.**  A raw PCA reduction would require the PCA event files, the
housekeeping/particle-monitor filters, the good-time intervals and the
`pcabackest` model; it would produce a different dataset.  The official
`stdprod` products are the reproducible, archive-level products and are what
this tool fits.

The `b2` file is a **background model**, not a measured background spectrum.
XSPEC subtracts it and propagates its `STAT_ERR`.  The background-model
systematics (the dominant PCA uncertainty) are not included in the chi-square
errors; this is stated again in `run.json`, `provenance.md` and the summary.

## Model

Production fit in the observed 3-20 keV band:

```text
tbabs * (zpowerlw + zgauss)
```

* `tbabs` - cold absorption (`nH` in 10^22 cm^-2), Wilms abundances.
* `zpowerlw` - redshifted power law (`PhoIndex`, `norm` at 1 keV rest frame).
* `zgauss` - Fe K-alpha at **6.4 keV rest frame**, narrow-core width fixed to
  **50 eV**; `norm` is the total line photon flux.
* Everything is fitted with `chi` (grouped PHA, `STAT_ERR` from the official
  products), `Fit.nIterations=500`.

The tool also fits:

| fit | band | purpose |
|---|---|---|
| `baseline_3_20` | 3-20 keV | continuum-only baseline |
| `line_3_20` | 3-20 keV | **production** narrow Fe K-alpha |
| `line_3_20_fixed_nH` | 3-20 keV | conservative: `nH` frozen to the baseline value |
| `baseline_3_10` | 3-10 keV | line-band continuum |
| `line_3_10` | 3-10 keV | line-band cross-check (simple power law is a good description) |
| `line_3_10_free_sigma` | 3-10 keV | diagnostic free width (0.01-1.0 keV) |
| `line_3_10_free_energy` | 3-10 keV | diagnostic free centroid and width |

`Delta chi^2` is measured against the matching baseline in the same band.
The significance is the Gaussian-equivalent one-sided p-value of
`chi2_sf(Delta chi^2, Delta dof)`.  It is a line-at-a-fixed-rest-energy
significance, not a look-elsewhere-corrected discovery significance.

## Build and run

```bash
# 1. download the three small official products and check SHA256
bash inputs/3C120_z_0.0330/xray/rxte_10339-02-01-01/download.sh

# 2. build the thin image on top of the existing xmm_xspec image
#    (XSPEC 13.0.0 / HEASoft 6.37; no second 4.3 GB install)
bash pipeline/runners/build_images.sh rxte_xspec

# 3. production fit
bash pipeline/runners/run_rxte_xspec_docker.sh \
  inputs/3C120_z_0.0330/xray/rxte_10339-02-01-01 \
  outputs/rxte_xspec/3C120_z_0.0330 \
  --source-key 3C120_z_0.0330 --redshift 0.0330 --source-name "3C 120"
```

The image is `FROM xmm_xspec:latest` plus the runner and entry point.  The
entry point sources `headas-init.sh` and uses writable `PFILES`, `HOME` and
`MPLCONFIGDIR` under `/tmp`.  The input is mounted read-only.

## Products

`outputs/rxte_xspec/<source>/`:

| file | content |
|---|---|
| `rxte_spectrum_model_residual.png/pdf` | PCA data, full model, continuum baseline and residuals |
| `rxte_fe_ka_zoom.png/pdf` | 4-8 keV zoom: data, full model, continuum and Fe K-alpha excess |
| `rxte_fit.csv` | every fit: chi2/dof, nH, Gamma, line parameters, Delta chi2, flux, EW |
| `rxte_lines.csv` | Fe K-alpha measurements with significance, flux, EW and 90% upper limits |
| `run.json` | provenance, input hashes, header metadata, software, config, results, caveats |
| `config.effective.json` | effective configuration and resolved paths |
| `xspec.log` | full XSPEC/PyXspec log |
| `run.log` | container stdout/stderr |
| `provenance.md` | human-readable HEASARC/`stdprod`/response provenance |
| `fit_summary.txt` | short human-readable summary |
| `prepared/` | the exact decompressed/sanitised source, background and response used by XSPEC |

## 3C 120 result (XSPEC 13.0.0, chi, 3-20 keV)

| quantity | value |
|---|---|
| baseline `tbabs*zpowerlw` | chi2/dof = 89.85/49 = 1.834 |
| production `tbabs*(zpowerlw+zgauss)` | chi2/dof = **72.02/48 = 1.500** |
| photon index Gamma | **1.8163 +/- 0.0240** |
| N_H | **(3.06 +/- 0.51) x 10^22 cm^-2** |
| narrow Fe K-alpha (sigma = 50 eV) | Delta chi2 = **17.83 (1 dof) -> 4.22 sigma** |
| line normalization | (5.07 +/- 1.18) x 10^-5 photons cm^-2 s^-1 |
| line flux | **(5.03 +/- 1.17) x 10^-13 erg cm^-2 s^-1** |
| EW_rest | **90.3 eV** |
| 3-10 keV line-band cross-check | chi2/dof = 19.90/21 = 0.947; Delta chi2 = 22.22 -> **4.71 sigma**; flux 5.54e-13; EW_rest 102.7 eV |
| conservative (N_H frozen to continuum value) | Delta chi2 = 11.94 -> 3.46 sigma; flux 3.43e-13; EW_rest 59.6 eV |
| diagnostic (N_H frozen at Galactic 0.024e22) | baseline chi2/dof = 198.45/50 = 3.97; line chi2/dof = 109.11/49 = 2.23; Delta chi2 = 89.33 -> 9.45 sigma; flux 8.77e-13; EW_rest 171.6 eV |
| soft-blackbody continuum check | Delta chi2 = 53.91 -> 7.34 sigma; flux 5.21e-13; EW_rest 95.4 eV |
| free width (3-10 keV) | sigma = 0.60 +/- 0.25 keV; Delta chi2 = 24.96 (2 dof) -> 4.62 sigma |
| free centroid (3-10 keV) | E_rest = 6.39 +/- 0.19 keV; sigma = 0.62 +/- 0.28 keV; 4.32 sigma |
| statistic cross-check | `pgstat` Delta = 17.84; `cstat` Delta = 17.84 (chi 17.83) |

The second independent AGN, **MCG-6-30-15**, gives chi2/dof =
**39.41/41 = 0.961**, Gamma = **1.867 +/- 0.048**, N_H =
**(2.40 +/- 1.03) x 10^22 cm^-2**, Delta chi2 = **46.48 -> 6.82 sigma**,
flux **(1.10 +/- 0.15) x 10^-12 erg cm^-2 s^-1**, EW_rest **263.5 eV**.
Its Galactic-`nH` diagnostic gives Delta chi2 = 91.38 (9.56 sigma) on a poor
chi2/dof = 135.98/43 baseline, the same continuum-mismatch behaviour.

The verified-data note's `Delta chi^2 ~ 82` for 3C 120 belongs to the
**fixed-low-N_H family**: freezing `nH` at the Galactic value (0.024e22)
gives Delta chi2 = 89.33, but that baseline has chi2/dof = 3.97 and the line
is absorbing continuum residuals.  It is reported as a diagnostic, not the
production measurement.  The production free-`nH` fit gives 17.83 on a
chi2/dof = 1.83 baseline; a soft-excess continuum reaches 53.91; a fixed
(continuum-value) N_H conservative fit gives 11.94.  The detection is
significant in every variant (3.5-9.6 sigma), but the exact Delta chi2 is
continuum/background-dependent.  The statistic choice is not the explanation:
with the same model and background, `pgstat` gives 17.84 and `cstat` gives
17.84, identical to `chi` within 0.01.  This is the honest PCA systematics
budget, not a statistical error bar.

## What this tool can and cannot measure

**Can measure**

* Absorbed power-law continuum: photon index and a cold `nH` (with caveats).
* Narrow Fe K-alpha flux and equivalent width at 6.4 keV rest.
* A model-dependent broad Fe K-alpha excess (diagnostic only).
* A second independent AGN (MCG-6-30-15) with the same model.

**Cannot measure**

* A relativistic line profile, black-hole spin, Fe abundance or inclination.
* A clean intrinsic `nH`: it is degenerate with the continuum shape and the
  PCA calibration.
* The physical origin of the soft/hard excess from a single power law.
* X-ray luminosity without a distance and an unabsorbed SED; variability from
  a single epoch.
* Background-model systematics, which dominate the PCA error budget.

## Failure modes

* **`cannot read response file`** - XSPEC reads FITS, not `.gz`; the tool
  decompresses the products into `prepared/` first.
* **`RESPFILE`/`BACKFILE` pointing to absent files** - the official PHA headers
  reference archive names.  The prepared copies set these to `NONE` and the
  tool loads the local response/background explicitly.
* **`tbabs` abundance warning** - the tool sets `Xset.abund = "wilm"`.
* **Poor reduced chi-square in 3-20 keV** - a single absorbed power law is not
  a complete PCA continuum model; the 3-10 keV line-band fit is the cleaner
  line measurement.  Do not hide the 3-20 keV residuals.
* **Line width at a bound** - the free-width diagnostic is not a resolved
  velocity measurement.  The production line flux/EW uses the fixed 50 eV
  narrow core.
* **Background systematics** - `b2` is a model.  A 1-2% background
  mis-calibration can change the line significance; always report the
  background-inclusive result and the conservative `nH`-fixed variant.

## References

* XSPEC/PyXspec manual: <https://heasarc.gsfc.nasa.gov/xanadu/xspec/>
* RXTE PCA `stdprod` archive:
  <https://heasarc.gsfc.nasa.gov/FTP/xte/data/archive/>
* RXTE PCA calibration and background: HEASARC RXTE Guest Observer Facility
  documentation.
* Wilms, Allen & McCray (2000) for `tbabs`.
