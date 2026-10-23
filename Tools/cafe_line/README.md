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
| `read_jwst_x1d.py` | JWST `x1d` reader/combiner and CAFE 3-column text writer. |
| `../../configs/cafe_line/default/` | Effective `inpars.ini` and `default_opt.cafe` (upstream `inpars_jwst_miri_AGN.ini` / `default_opt.cafe`, provenance headers added). |
| `../../configs/cafe_line/tables/` | CAFE line/PAH/opacity/resolving-power/SED tables read by the configuration. |
| `../../Pipelines/run_cafe_line_docker.sh` | Host entry point. |

## Build

```bash
bash Pipelines/build_images.sh cafe_line
# or directly:
docker build -f Tools/cafe_line/dockerfile -t cafe_line .
```

Measured on the development machine: build **2 m 4 s**, image **1.04 GB**
(`docker image inspect cafe_line`).  The image is large because CAFE requires
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
  outputs/PDS456_z_0.1840/cafe_line \
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

The runner writes the prepared 3-column CAFE spectrum and all scratch files
under `work/prepared/<source>/cafe_line/`, never under `outputs/`.

Useful options:

| option | default | meaning |
| --- | --- | --- |
| `--config DIR` | `/app/config/default` | directory containing `inpars.ini` + `default_opt.cafe` |
| `--tables DIR` | `../tables` next to `--config` | CAFE table directory |
| `--segment {both,short,long}` | `both` | select MIRI short/long x1d files |
| `--dq-policy {good,all}` | `good` | `good` keeps DQ==0 only |
| `--error-floor F` | `0.01` | `err = max(err, F*|flux|)` in the adapter |
| `--max-wave UM` | none | observed-frame red cut |
| `--bin-kms V` | `0` | optional constant-velocity binning (off: CAFE line widths assume instrument resolution) |
| `--edge-trim N` | `2` | pixels removed at each contiguous-segment edge |
| `--no-coverage-mask` | off | do not mask lines/PAHs outside contiguous coverage |
| `--force-all-lines` | on | keep all in-coverage lines in the fit even if CAFE's guesser rejects them |
| `--max-loops N` | `5` | CAFE parameter-check/refit loops |
| `--mc-samples N` | `200` | post-fit covariance samples (`0` disables) |
| `--no-mc` | off | disable the uncertainty Monte Carlo |
| `--outlier-sigma` | `5.0` | MAD threshold for the optional clipping pass |
| `--outlier-rel-threshold` | `0.10` | clipping also requires >10 % relative residual |

`CAFE_CONFIG_DIR` (host) and `CAFE_WORK_DIR` (host) override the mounted config
and work directories.

## Inputs and adapter

`read_jwst_x1d.py` reads the canonical `inputs/<source>/raw/*_x1d.fits`
`EXTRACT1D` table:

* `WAVELENGTH` (µm), `FLUX` (Jy), `FLUX_ERROR` (Jy); a `SURF_BRIGHT` fallback
  is supported when `--sb-aperture-arcsec2` is supplied.
* `DQ == 0` by default.  In the PDS 456 x1d products the `DQ=1` rows are
  exactly the blanked rows with `FLUX=0` and `FLUX_ERROR=0`; they correspond to
  the MRS sub-bands that were not extracted.
* The short and long files are concatenated, sorted, and inverse-variance
  combined for duplicate wavelengths.
* Contiguous coverage segments are detected; lines/PAHs whose observed
  wavelength lies in a zeroed gap are masked in the effective line tables and
  reported as `not_covered` (never fitted by interpolating across the gap).
* A 1 % fractional error floor is applied.  CAFE v1.0.1 reads `ErrSpec` from
  `default_opt.cafe` but **does not apply it anywhere in the released code**
  (verified by searching the pinned source), so the floor is applied by the
  adapter instead.

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
   profiles, applying the fitted extinction at each feature;
5. writes `cafe_uncertainties.csv`, `cafe_mc_samples.csv` and
   `cafe_uncertainty.png`.

The method string in the outputs is `lmfit_covariance_multivariate_normal`.
If the covariance is unavailable, the driver falls back to a diagonal
`lmfit_stderr_diagonal_normal` draw and says so.  If neither covariance nor
complete stderr is available, the outputs contain NaN with a clear
`uncertainty.method = "unavailable"` flag and the figure states the reason.
This is a local, Gaussian approximation around the best fit, not a posterior
exploration; it cannot capture multimodality or parameter-bound pile-ups.

## Committed PDS 456 result

Command (above): `--max-wave 27.8 --no-outlier-clip --mc-samples 200`.

| quantity | value |
| --- | --- |
| status | `ok`, stable |
| pixels used | 3361 (from 3437 after the 27.8 µm cut) |
| coverage (observed) | 6.531–7.658, 10.005–11.697, 15.414–17.985, 24.407–27.773 µm |
| fit runtime | 35.1 s (CAFE/lmfit; 34–66 s across repeated runs on this host) |
| wall time | 59.8 s including adapter, tables, MC and figures |
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
| PAH 6.2 | 6.22 | 7.364 | (3.798 ± 0.271)e-16 | 14.0 | (3.339/3.489/3.630)e-16 | detected; EQW 0.0170 µm |
| PAH 8.6 | 8.61 | 10.194 | (7.289 ± 2.449)e-17 | 2.98 | (0.454/0.618/0.830)e-16 | marginal (3σ UL 7.35e-17) |
| PAH 13.5 | 13.50 | 15.984 | (1.750 ± 0.155)e-16 | 11.3 | (1.457/1.588/1.729)e-16 | detected; EQW 0.0206 µm |
| PAH 14.2 | 14.19 | 16.801 | (6.534 ± 1.116)e-17 | 5.86 | (4.750/5.745/6.776)e-17 | detected |
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
(MC 0.127/0.177/0.240; S/N 2.9, marginal).

Continuum decomposition (integrated over the covered rest-frame windows):
COO 20.4 K, 25 % of the continuum; WRM 92.0 K, 43 %; HOT 649 K, 15 %;
STB 9 %; DSK 8 %; PAH continuum 0.7 %.  The "STB" component is freely fitted
by the upstream AGN configuration and should not be read as a star-formation
measurement.

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

and in `inputs/PDS456_z_0.1840/source.json` add `"cafe_line"` to `tools` plus

```json
"cafe_args": ["--max-wave", "27.8", "--no-outlier-clip",
              "--mc-samples", "200", "--mc-seed", "20250101"]
```

`Pipelines/build_images.sh` already includes `cafe_line` in its tool lists.

## Validation commands

```bash
python -m py_compile Tools/cafe_line/run_cafe.py Tools/cafe_line/read_jwst_x1d.py
bash -n Pipelines/run_cafe_line_docker.sh
bash Pipelines/build_images.sh cafe_line
docker run --rm cafe_line --help
bash Pipelines/run_cafe_line_docker.sh inputs/PDS456_z_0.1840/raw \
  outputs/PDS456_z_0.1840/cafe_line 0.184 \
  --max-wave 27.8 --no-outlier-clip --mc-samples 200 --mc-seed 20250101
```

## Limitations

* The uncertainty product is a local Gaussian covariance MC, not an MCMC.
* CAFE's `ErrSpec` is a no-op in v1.0.1; the 1 % floor is applied externally.
* The x1d gaps prevent [Ne II], [Ne III], [S III] 18.7 and PAH 7.7/11.3/12.7/17.
* The [Ne V] 14.32 detection is marginal and its broad component sits at the
  ±500 km/s and 2000 km/s width bounds; treat it as tentative.
* The PAH 8.6 feature is marginal (S/N 2.98).
* H₂ S(3) is not detected; its 3σ limit is 7.57e-19 W m⁻².
* The red-edge cut at 27.8 µm is a data-quality choice, not a physical model
  boundary; without it the fit is pulled by 28 µm outliers.
* CAFE's derived "STB" continuum component is freely fitted and is not a
  star-formation rate.
