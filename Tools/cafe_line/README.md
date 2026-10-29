# `cafe_line` — CAFE spectral decomposition (Docker)

Production wrapper around the public **CAFE** (Continuum And Feature Extraction)
fitter for JWST/MIRI MRS spectra.  CAFE models the continuum with reprocessed
and direct-light dust/stellar/AGN components, Drude-profile PAHs, Gaussian
atomic/molecular/hydrogen lines, and optional absorption templates.

* Upstream: <https://github.com/GOALS-survey/CAFE>
* Pinned commit: `39e298bef517030f7828057bb9eeff2927fba77a` (v1.0.1)
* CAFE paper: Diaz-Santos et al. (2025), ascl:2501.001

The upstream git tree is **not** vendored.  The image installs CAFE from the
pinned commit and mounts the effective configuration/tables from this repo.

## Contents

| file | purpose |
| --- | --- |
| `dockerfile` | Python 3.11 image with pinned NumPy/SciPy/Astropy/lmfit/specutils/asdf and CAFE at the pinned commit. Build context is the repo root. |
| `run_cafe.py` | Production driver: adapter → effective config → CAFE fit → native products → harmonised tables → post-fit covariance Monte Carlo. |
| `read_jwst_x1d.py` | JWST `x1d` and MIRI/PAHFIT `s1d` reader/combiner and CAFE 3-column text writer. |
| `../../configs/cafe_line/default/` | Effective `inpars.ini` and `default_opt.cafe` (upstream `inpars_jwst_miri_AGN.ini` / `default_opt.cafe`, provenance headers added). |
| `../../configs/cafe_line/vv114_agn_sb/` | MIRI-only SB+AGN configuration used for the full-coverage VV114 production fit (`inpars_jwst_nirspec-miri_SB_and_AGN.ini`, NIRSpec removed, broad-line width/wave fixed). |
| `../../configs/cafe_line/tables/` | CAFE line/PAH/opacity/resolving-power/SED tables read by the configuration. |
| `../../Pipelines/run_cafe_line_docker.sh` | Host entry point. |

## Build

```bash
bash Pipelines/build_images.sh cafe_line
# or directly:
docker build -f Tools/cafe_line/dockerfile -t cafe_line .
```

Measured on the development machine: clean build **2 m 4 s**, cached rebuild
after a source edit **1–90 s**, image **1.04 GB** (1,039,588,409 bytes;
`docker image inspect cafe_line`).  The image is large because CAFE requires
Astropy, SciPy, pandas, matplotlib, specutils and asdf.

## Run

Generic form:

```bash
bash Pipelines/run_cafe_line_docker.sh <input-dir> <output-dir> <z> [extra args...]
```

The committed PDS 456 test (real JWST/MIRI MRS short+long `x1d`):

```bash
bash Pipelines/run_cafe_line_docker.sh \
  inputs/PDS456_z_0.1840/raw \
  outputs/cafe_line/PDS456_z_0.1840 \
  0.184 \
  --max-wave 27.8 --no-outlier-clip \
  --mc-samples 200 --mc-seed 20250101
```

`--max-wave 27.8` trims the noisy red edge of MIRI CH4L (the last ~0.8 µm of
the long x1d file; the source manifest's PAHFIT recipes use a similar 28.0 µm
cut).  Without it the fit is pulled by a handful of 28 µm outliers.  The
auto-clipping pass (`--outlier-sigma 5 --outlier-rel-threshold 0.10`) is
available and on by default, but for this dataset the conservative
`--no-outlier-clip` run is the reference solution: a clipped refit can fall
into a different local minimum with fewer PAHs.

The committed full-coverage VV114 production fit (all 12 MIRI `s1d`
channels, 5–28 µm, SB+AGN configuration, reduced/documented line set):

```bash
bash Pipelines/run_cafe_line_docker.sh \
  inputs/VV114_z_0.0200/raw \
  outputs/cafe_line/VV114_z_0.0200 \
  0.02 \
  --config /app/config/vv114_agn_sb --tables /app/config/tables \
  --min-wave 5 --max-wave 28 --bin-kms 100 --error-floor 0.05 \
  --no-outlier-clip --max-loops 2 --ftol 1e-3 --mc-samples 200 \
  --keep-line-waves "6.98527,7.6524,8.99138,9.6649,10.5105,12.279,12.81355,14.3217,15.5551,17.035,17.93595,18.713,22.925,24.3175,25.89" \
  --keep-pah-complexes "PAH62,PAH77_C,PAH83,PAH86,PAH113_C,PAH120,PAH126_C,PAH136,PAH142,PAH170_C"
```

The same arguments are recorded in `inputs/VV114_z_0.0200/source.json` as
`cafe_args`.  The prepared spectrum is 5162 pixels after 100 km/s binning
and covers 5.003–27.985 µm with no gaps.  The 5 % error floor is a deliberate
MIRI systematic floor; at 1 % the reduced χ² is dominated by residual fringes
and channel-to-channel calibration structure.

**CAFE performance failure.**  Forcing every in-coverage line and all 27 PAH
components (49 table lines, 17 with double components, plus 42 continuum
parameters) makes the finite-difference Jacobian prohibitively expensive on
this 8367-pixel spectrum.  Two attempts exceeded **35 min without completing
the first fit pass** and were killed.  The production run therefore uses the
documented reduced set above.  It is not a claim that the omitted features
are absent; they were masked, not measured.

The runner writes the prepared 3-column CAFE spectrum and all scratch files
under `work/prepared/<source>/cafe_line/`, never under `outputs/`.

Useful options:

| option | default | meaning |
| --- | --- | --- |
| `--config DIR` | `/app/config/default` | directory containing `inpars.ini` + `default_opt.cafe` |
| `--tables DIR` | `../tables` next to `--config` | CAFE table directory |
| `--segment {both,short,long}` | `both` | select MIRI short/long files; for `s1d`, short=ch1+ch2, long=ch3+ch4 |
| `--dq-policy {good,all}` | `good` | `good` keeps DQ==0 only |
| `--overlap-policy {trim,keep}` | `trim` | cut redundant adjacent-channel overlaps at their midpoint |
| `--sb-aperture-arcsec2 A` | none | aperture for `MJy/sr` (or `SURF_BRIGHT`) input; required for surface brightness |
| `--error-floor F` | `0.01` | `err = max(err, F*|flux|)` in the adapter |
| `--max-wave UM` | none | observed-frame red cut |
| `--bin-kms V` | `0` | optional constant-velocity binning (off: CAFE line widths assume instrument resolution) |
| `--edge-trim N` | `2` | pixels removed at each contiguous-segment edge |
| `--no-coverage-mask` | off | do not mask lines/PAHs outside contiguous coverage |
| `--force-all-lines` | on | keep all selected lines in the fit even if CAFE's guesser rejects them |
| `--keep-line-waves W1,W2,...` | none | rest-frame µm whitelist; all other line-table rows are masked and recorded in `run.json` |
| `--keep-pah-complexes C1,C2,...` | none | CAFE PAH-complex whitelist; all other template rows are trimmed |
| `--max-loops N` | `5` | CAFE parameter-check/refit loops |
| `--ftol F` | `1e-5` | lmfit relative tolerance |
| `--mc-samples N` | `200` | post-fit covariance samples (`0` disables) |
| `--no-mc` | off | disable the uncertainty Monte Carlo |
| `--outlier-sigma` | `5.0` | MAD threshold for the optional clipping pass |
| `--outlier-rel-threshold` | `0.10` | clipping also requires >10 % relative residual |

`CAFE_CONFIG_DIR` (host) and `CAFE_WORK_DIR` (host) override the mounted config
and work directories.

## Inputs and adapter

`read_jwst_x1d.py` reads both input families found in this repo:

* **`x1d`** (PDS 456): the canonical `EXTRACT1D` table with `WAVELENGTH` (µm),
  `FLUX` (Jy), `FLUX_ERROR` (Jy), `DQ`, `NPIXELS`.  A `SURF_BRIGHT` fallback is
  supported when `--sb-aperture-arcsec2` is supplied.
* **`s1d`** (VV114, 12 MIRI channel files): a table with `wavelength` (µm),
  `flux` (MJy) and `uncertainty` (MJy).  The FITS column unit is literally
  `MJy` (not `MJy/sr`), so it is converted with `1 MJy = 1e6 Jy`.  A
  surface-brightness `MJy/sr` input is also accepted, but only with an
  explicit aperture.

Common behaviour:

* `DQ == 0` by default.  In the PDS 456 x1d products the `DQ=1` rows are
  exactly the blanked rows with `FLUX=0` and `FLUX_ERROR=0`; they correspond to
  the MRS sub-bands that were not extracted.  `s1d` files have no DQ column.
* All inputs are sorted and combined.  Exact duplicate wavelengths are
  inverse-variance averaged.
* Adjacent MIRI channels overlap by ~1–3 %.  With `--overlap-policy trim`
  (default) each overlap is cut at its midpoint, so no spectral region is
  counted twice; the VV114 run removes 724 such samples.  `keep` retains both.
* Contiguous coverage segments are detected; lines/PAHs whose observed
  wavelength lies in a zeroed gap are masked in the effective line tables and
  reported as `not_covered` (never fitted by interpolating across the gap).
* A fractional error floor is applied (1 % default; VV114 uses 5 %).  CAFE
  v1.0.1 reads `ErrSpec` from `default_opt.cafe` but **does not apply it
  anywhere in the released code** (verified by searching the pinned source),
  so the floor is applied by the adapter instead.

The text spectrum is written with the header
`# wave_um flux_Jy flux_unc_Jy`; CAFE's `specmod.read_spec` reads it through
`astropy.table.Table.read(..., names=['wave','flux','flux_unc'])`.

## Fitting

`run_cafe.py` drives the upstream CAFE functions directly (`specmod`,
`CAFE_param_generator`, `CAFE_prof_generator`, `cafe_grinder`,
`CAFE_cube_generator`, `cafe_io.line_table`/`pah_table`) rather than calling
`specmod.fit_spec`.  This is necessary to retain the `lmfit.MinimizerResult`
and therefore `result.covar`, which `fit_spec` does not expose.  The fit itself
is unchanged CAFE: `lmfit` least squares with the trust-region reflective
method, CAFE's parameter checks and refit loops.

The effective configuration is written to `outputs/.../cafe_line/config_used/`
(ini, opt, masked line tables, trimmed PAH table, table manifest).  The runner
never falls back silently to CAFE's installed tables.

Line/PAH coverage masking follows the table names actually referenced by the
selected `inpars.ini` (`lines.*_AGN.txt` for the default AGN config,
`lines.*_SB_and_AGN.txt` for `vv114_agn_sb`), so an SB+AGN run cannot silently
leave uncovered features active.  `--keep-line-waves` and
`--keep-pah-complexes` apply a second, documented science mask; the requested
and retained sets are recorded in `run.json` under `config.line_subset` and in
`config_used/tables_manifest.json`.

## Outputs

`outputs/<source>_z_<z>/cafe_line/`:

| file | contents |
| --- | --- |
| `cafe_fit.png` | native CAFE fit figure (copied from `cafe_native/...`) |
| `cafe_fit_residuals.png` | observed-frame data/model/component plot + residual panel with gaps shaded |
| `cafe_uncertainty.png` | covariance-MC histograms, traces, and corner-style panels |
| `cafe_lines.csv` | every CAFE Gaussian component (narrow/broad), rest/observed wavelength, intrinsic/observed flux in W m⁻² and erg s⁻¹ cm⁻², FWHM, S/N, status |
| `cafe_key_lines.csv` | the science key lines/PAHs and ratios, including `not_covered` rows and 3σ upper limits |
| `cafe_pah.csv` | PAH complexes (Drude sums), EQW, S/N, status |
| `cafe_components.csv` | continuum components: reference flux, integrated flux, fractions, component parameters |
| `cafe_fit_parameters.csv` | all lmfit parameters (value, stderr, vary, bounds, expression) |
| `cafe_uncertainties.csv` | MC summary (best, mean, std, p16/p50/p84, n_valid, method) for key lines/PAHs/ratios and selected continuum parameters |
| `cafe_mc_samples.csv` | raw MC samples for the same quantities |
| `run.json` | status, hashes, configuration, coverage, fit statistics, detections, ratios, warnings/limitations |
| `cafe_run.log` | full stdout/stderr |
| `cafe_native/` | native CAFE products: `*_parcube.fits`, `*_contcube.fits`, `*_fitpars.ini`, `*_cafefit.asdf`, `*_fitfigure.png`, `*_linetable.ecsv`, `*_pahtable.ecsv` |
| `config_used/` | effective config and derived line/PAH tables |

Flux units follow CAFE's native convention: integrated line/PAH `strength` is
in W m⁻²; `1 W m⁻² = 1000 erg s⁻¹ cm⁻²`.  The tables also give the erg/s/cm²
values directly.

## Uncertainty method (honest label: not MCMC)

CAFE is a least-squares (`lmfit`) fit.  The tool therefore does **not** run an
MCMC.  After the fit it:

1. reads the free-parameter covariance `result.covar` (46×46 for the PDS fit);
2. regularises it if needed (symmetrise + clip negative eigenvalues) and draws
   `N` samples from the multivariate normal (`--mc-samples`, default 200);
3. holds fixed parameters at their best-fit values and clips samples to the
   lmfit bounds;
4. recomputes each line flux from the Gaussian coefficients
   (`peak`, `gamma`, `wave`) and each PAH complex from the summed Drude
   profiles.  These are **intrinsic** (extinction-corrected) fluxes,
   matching the native `*_strength_int` columns; the observed fluxes are
   computed separately by the native CAFE tables and are not mixed into the
   MC percentiles;
5. writes `cafe_uncertainties.csv`, `cafe_mc_samples.csv` and
   `cafe_uncertainty.png`.

The method string in the outputs is `lmfit_covariance_multivariate_normal`.
If the covariance is unavailable, the driver falls back to a diagonal
`lmfit_stderr_diagonal_normal` draw and says so.  If neither covariance nor
complete stderr is available, the outputs contain NaN with a clear
`uncertainty.method = "unavailable"` flag and the figure states the reason.
This is a local, Gaussian approximation around the best fit, not a posterior
exploration; it cannot capture multimodality or parameter-bound pile-ups.

## Committed VV114 full-coverage result

Command above (recorded in `inputs/VV114_z_0.0200/source.json`).  This is the
production full-coverage test; the PDS 456 run remains the sparse-coverage
regression.

| quantity | value |
| --- | --- |
| status | `ok`, stable |
| inputs | 12 MIRI `s1d` channel files, ch1–ch4 S/M/L |
| coverage (observed) | **5.003–27.985 µm**, one contiguous segment |
| pixels used | 5162 after 100 km/s binning (8467 native, 724 overlap samples trimmed) |
| configuration | `vv114_agn_sb` (SB+AGN, MIRI only), broad-line wave/width fixed |
| error floor | 5 % (MIRI systematic) |
| fit runtime | **20.3 s** CAFE/lmfit |
| wall time | **38.5 s** including adapter, tables, MC and figures |
| MC runtime | 2.8 s for 200 samples |
| χ² / dof | 13709.67 / 5121 |
| reduced χ² | **2.677** |
| rms (relative, global) | 0.143 |
| median \|residual\|/flux | 0.034 |
| 95th percentile \|residual\|/flux | 0.267 |
| covariance | 41×41, errorbars returned, 0 negative eigenvalues |

The reduced χ² is above unity because the 5 % floor is still smaller than the
residual channel-to-channel calibration structure and the narrow-line
spikes; it is a real fit, not a failed one.  The model follows the 5–28 µm
continuum and all ten fitted PAH complexes.

### Exact fitted line/PAH subset

`--keep-line-waves` requested 15 rest wavelengths.  The SB+AGN line tables
contain 11 of them; the other four ([Ne V] 14.32, [Ne V] 24.32, [Fe II]
17.94, [Fe III] 22.93) are not in `lines.*_SB_and_AGN.txt` and are reported
as `not_in_model`.  The 11 fitted lines are:

| line | rest µm | status | flux (W m⁻²) | S/N | MC p16/p50/p84 (W m⁻²) |
| --- | ---: | --- | ---: | ---: | --- |
| [Ar II] | 6.9853 | detected | (1.122 ± 0.113)e-16 | 10.0 | (1.020/1.127/1.233)e-16 |
| [Ne VI] | 7.6524 | not detected | (0.094 ± 0.642)e-17 | 0.15 | (0/0.066/0.622)e-17 |
| [Ar III] | 8.9914 | detected | (1.047 ± 0.229)e-17 | 4.57 | (0.845/1.066/1.310)e-17 |
| H₂ S(3) | 9.6649 | not detected | (0.338 ± 1.011)e-18 | 0.33 | (0/0.454/1.393)e-18 |
| [S IV] | 10.5105 | detected | (1.293 ± 0.261)e-17 | 4.96 | (1.048/1.287/1.520)e-17 |
| H₂ S(2) | 12.279 | detected | (1.872 ± 0.459)e-17 | 4.08 | (1.415/1.916/2.417)e-17 |
| [Ne II] | 12.8136 | detected | (3.634 ± 0.292)e-16 | 12.4 | (3.333/3.659/3.895)e-16 |
| [Ne III] | 15.5551 | detected | (4.204 ± 0.639)e-17 | 6.58 | (3.573/4.228/4.844)e-17 |
| H₂ S(1) | 17.035 | fixed at zero | 0 | — | (0/0.040/0.514)e-17 |
| [S III] | 18.713 | detected | (1.029 ± 0.109)e-16 | 9.42 | (0.929/1.037/1.135)e-16 |
| [O IV] | 25.8903 | not detected | (0.496 ± 0.891)e-17 | 0.56 | (0/0.350/1.400)e-17 |

Ratios: [Ne III]/[Ne II] = 0.1157 ± 0.0199 (MC 0.0980/0.1169/0.1363);
[Ne III]/[Ne II] is thus not elevated.  The 10 fitted PAH complexes are all
detected:

| PAH | rest µm | flux (W m⁻²) | S/N | EQW (µm) |
| --- | ---: | ---: | ---: | ---: |
| 6.2 | 6.22 | (3.659 ± 0.141)e-15 | 26.0 | 1.97 |
| 7.7 | 7.60 | (1.473 ± 0.043)e-14 | 34.4 | 10.7 |
| 8.3 | 8.33 | (2.907 ± 0.172)e-15 | 16.9 | 3.55 |
| 8.6 | 8.61 | (2.801 ± 0.150)e-15 | 18.7 | 4.67 |
| 11.3 | 11.30 | (3.149 ± 0.097)e-15 | 32.6 | 7.67 |
| 12.0 | 11.99 | (1.947 ± 0.103)e-15 | 18.9 | 3.23 |
| 12.7 | 12.65 | (6.261 ± 0.255)e-15 | 24.5 | 6.30 |
| 13.5 | 13.50 | (2.120 ± 0.096)e-15 | 22.0 | 1.50 |
| 14.2 | 14.19 | (1.103 ± 0.067)e-15 | 16.6 | 0.665 |
| 17.0 | 17.00 | (3.388 ± 0.186)e-15 | 18.2 | 3.11 |

PAH ratios: 6.2/11.3 = 1.162 ± 0.057; 7.7/6.2 = 4.025 ± 0.194;
8.6/6.2 = 0.765 ± 0.050.  The intrinsic PAH fluxes are large because the
fitted screen extinction is substantial; the observed (attenuated) fluxes
are also in `cafe_pah.csv`.

Continuum decomposition over the covered rest-frame window: cool dust 46.6 %,
warm dust 35.2 %, hot dust 17.4 %, PAH continuum 28.8 % of the continuum
budget (fractions are not additive because the PAH continuum is reported
against the same `fCON` denominator), AGN disk 0.9 %, SB99 starburst 0.0 %.
The fitted SB/AGN labels describe the template set, not a physical
star-formation rate.

## Committed PDS 456 result

Command (above): `--max-wave 27.8 --no-outlier-clip --mc-samples 200`.

| quantity | value |
| --- | --- |
| status | `ok`, stable |
| pixels used | 3361 (from 3437 after the 27.8 µm cut) |
| coverage (observed) | 6.531–7.658, 10.005–11.697, 15.414–17.985, 24.407–27.773 µm |
| fit runtime | 159.2 s in the audit rerun (43 s for the identical fit on an unloaded host; 34–159 s observed) |
| wall time | 177.5 s in the audit rerun (59.8 s unloaded) |
| MC runtime | 4.8 s for 200 samples |
| χ² / dof | 4211.39 / 3315 |
| reduced χ² | **1.270** |
| rms (relative, global) | 0.0378 |
| median |residual|/flux | 0.0061 |
| 95th percentile |residual|/flux | 0.0745 |
| covariance | 46×46, errorbars returned, 0 negative eigenvalues |

The 1 % error floor gives a reduced χ² near unity; the residual panel is
dominated by 1–3 % systematics and the 28 µm edge, not by photon noise.

### Detections and limits

All fluxes are intrinsic (extinction-corrected) W m⁻²; multiply by 1000 for
erg s⁻¹ cm⁻².  `mc` values are the 16/50/84 percentiles from the covariance MC.

| feature | rest µm | obs µm | flux (W m⁻²) | S/N | MC p16/p50/p84 | status |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| [Ne V] 14.32 (broad) | 14.3217 | 16.957 | (1.038 ± 0.344)e-17 | 3.01 | (0.759/0.965/1.178)e-17 | detected, **tentative** (broad component at ±500 km/s and 2000 km/s width bounds) |
| PAH 6.2 | 6.22 | 7.364 | (3.798 ± 0.271)e-16 | 14.0 | (3.544/3.793/4.049)e-16 | detected; EQW 0.0170 µm |
| PAH 8.6 | 8.61 | 10.194 | (7.289 ± 2.449)e-17 | 2.98 | (0.513/0.700/0.940)e-16 | marginal (3σ UL 7.35e-17) |
| PAH 13.5 | 13.50 | 15.984 | (1.750 ± 0.155)e-16 | 11.3 | (1.580/1.733/1.896)e-16 | detected; EQW 0.0206 µm |
| PAH 14.2 | 14.19 | 16.801 | (6.534 ± 1.116)e-17 | 5.86 | (5.090/6.258/7.346)e-17 | detected |
| [Ne II] 12.81 | 12.8136 | 15.171 | — | — | — | **not covered** (zeroed gap) |
| [Ne III] 15.56 | 15.5551 | 18.417 | — | — | — | **not covered** (zeroed gap) |
| [S III] 18.71 | 18.713 | 22.156 | — | — | — | **not covered** (zeroed gap) |
| [S III] 33.48 | 33.481 | 39.642 | — | — | — | **not covered** (out of range) |
| H₂ S(3) 9.66 | 9.6649 | 11.443 | 0 (fixed) | — | 3σ UL 7.57e-19 | not detected |
| H₂ S(1) 17.03 | 17.035 | 20.169 | — | — | — | not covered |
| H₂ S(2) 12.28 | 12.279 | 14.538 | — | — | — | not covered |
| [Ar III] 8.99 | 8.9914 | 10.646 | (2.16 ± 6.26)e-19 | 0.35 | — | not detected; 3σ UL 1.88e-18 |
| [Ar V] 13.10 | 13.1022 | 15.513 | (2.73 ± 3.78)e-19 | 0.72 | — | not detected; 3σ UL 1.13e-18 |
| [Fe III] 22.93 | 22.925 | 27.143 | (3.65 ± 2.00)e-18 | 1.82 | — | not detected; 3σ UL 6.01e-18 |

PAH complexes not covered: 7.7 (obs 9.00), 11.3 (13.38), 12.7 (14.98),
17.0 (20.13).  Consequently the [Ne III]/[Ne II], [S III] and PAH 6.2/11.3
ratios are undefined.  The PAH 8.6/6.2 ratio is 0.192 ± 0.066
(MC 0.132/0.185/0.249; S/N 2.9, marginal).  The MC percentiles in this table
are now drawn from the intrinsic PAH fluxes, matching `pah_strength_int`
(the earlier committed run accidentally used the observed, attenuated PAH
fluxes in the MC).

Continuum decomposition (integrated over the covered rest-frame windows):
COO 25.2 % of the continuum, WRM 42.6 %, HOT 15.1 %, STB 9.4 %, DSK 7.7 %,
PAH continuum 0.7 %.  The "STB" component is freely fitted by the upstream
AGN configuration and should not be read as a star-formation measurement.

### Why [Ne II]/[Ne III]/[S III] are missing

The canonical PDS 456 x1d files contain only the MRS **L** sub-bands:
short `6.53–7.66` and `10.00–11.70` µm; long `15.41–17.99` and `24.39–28.63` µm
before the 27.8 µm cut.  All other rows are `DQ=1` with `FLUX=0`,
`FLUX_ERROR=0`.  The observed wavelengths of [Ne II] 12.81 (15.17 µm),
[Ne III] 15.56 (18.42 µm) and [S III] 18.71 (22.16 µm) fall inside those
blanked gaps.  CAFE cannot fit them from this x1d product; they are reported
as `not_covered`, not as non-detections.  Recovering them requires the
unblanked MRS channels from the `s3d` cubes or a different extraction, which
are not part of the canonical `inputs/` set.

## Integration with `pipeline/run_new_tools.py` (not applied)

The shared orchestrator was left unchanged, as requested.  To run `cafe_line`
from the matrix, these edits would be needed:

```python
# pipeline/run_new_tools.py
ALL_TOOLS = (..., "cafe_line")

def tool_cafe_line(src: dict, out: Path, logp: Path) -> int:
    raw = Path(src["_path"]) / "raw"
    args = list(src.get("cafe_args", []))
    return run([str(ROOT / "Pipelines" / "run_cafe_line_docker.sh"),
                str(raw), str(out), str(src["z"]), *args], logp)

# dispatch dict:
"cafe_line": lambda: tool_cafe_line(src, out, logp),
```

Both source manifests now carry the tool entry:
`inputs/PDS456_z_0.1840/source.json` has `"cafe_line"` plus the sparse
`cafe_args`, and `inputs/VV114_z_0.0200/source.json` has `"cafe_line"` plus
the full-coverage `cafe_args` listed above.  `Pipelines/build_images.sh`
already includes `cafe_line` in its tool lists.

## Validation commands

```bash
python -m py_compile Tools/cafe_line/run_cafe.py Tools/cafe_line/read_jwst_x1d.py
bash -n Pipelines/run_cafe_line_docker.sh
bash Pipelines/build_images.sh cafe_line
docker run --rm cafe_line --help
bash Pipelines/run_cafe_line_docker.sh inputs/PDS456_z_0.1840/raw \
  outputs/cafe_line/PDS456_z_0.1840 0.184 \
  --max-wave 27.8 --no-outlier-clip --mc-samples 200 --mc-seed 20250101
# VV114 production (args are also in inputs/VV114_z_0.0200/source.json):
# see the full command in the Run section above
```

## Limitations

* The uncertainty product is a local Gaussian covariance MC, not an MCMC.
* CAFE's `ErrSpec` is a no-op in v1.0.1; the error floor is applied externally
  (1 % for PDS 456, 5 % for VV114).
* **VV114 performance:** the full all-line/all-PAH fit (49 lines, 17 double
  components, 27 PAHs, 42 continuum parameters) did not complete its first
  fit pass within 35 min and was killed.  The production result uses the
  documented 11-line/10-PAH-complex subset; omitted features are masked, not
  measured.  This is a CAFE/lmfit scaling limitation, not a data limitation.
* VV114 lines [Ne V] 14.32, [Ne V] 24.32, [Fe II] 17.94 and [Fe III] 22.93
  are absent from the `lines.*_SB_and_AGN.txt` tables, so they are
  `not_in_model`; use the default AGN tables if those lines are required.
* VV114 is binned to 100 km/s.  This is finer than MIRI resolution over most
  of the band but coarser at the red end; narrow-line fluxes there are
  conservative.
* The VV114 5 % floor still leaves reduced χ² = 2.68 because residual
  channel-to-channel structure and narrow-line spikes exceed the formal
  errors.
* The PDS 456 x1d gaps prevent [Ne II], [Ne III], [S III] 18.7 and PAH
  7.7/11.3/12.7/17; they are `not_covered`, not non-detections.
* The PDS [Ne V] 14.32 detection is marginal and its broad component sits at
  the ±500 km/s and 2000 km/s width bounds; treat it as tentative.
* The PDS PAH 8.6 feature is marginal (S/N 2.98).
* PDS H₂ S(3) is not detected; its 3σ limit is 7.57e-19 W m⁻².
* The PDS red-edge cut at 27.8 µm is a data-quality choice, not a physical
  model boundary; without it the fit is pulled by 28 µm outliers.
* CAFE's derived "STB" continuum component is freely fitted and is not a
  star-formation rate.
