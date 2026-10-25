# `xmm_xspec` — official XMM-Newton EPIC spectra with HEASoft/PyXspec

This tool fits the **official XMM-Newton Pipeline Processing System (PPS)**
EPIC spectra of an AGN with **HEASoft/PyXspec**.  It is the repository's X-ray
spectral-fitting branch, separate from the UV/optical/IR emission-line matrix.

The production example is **PDS 456** (ObsID `0721010201`, z = 0.184, PN Large
Window Thin1, 100.4 ks, 341,004 PN counts), using the real PPS source spectra,
background spectra and source ARFs, and the official CCF response matrices.
No response is synthetic.

## What is fitted

The default model, in the observed 0.5–10 keV band, is

```text
constant * tbabs * (zpowerlw + zgauss)
```

* `tbabs` — cold Galactic absorption (`nH`, 10^22 cm^-2).
* `zpowerlw` — redshifted power law (`PhoIndex`, `norm` at 1 keV).
* `zgauss` — Fe Kα line at 6.4 keV **rest frame**, narrow-core width fixed to
  50 eV; the normalization is the total line photon flux.
* `constant` — cross-calibration factor; fixed to 1 for **PN** (reference) and
  free for **MOS1/MOS2**.

The joint fit uses PN, MOS1 and MOS2 simultaneously with all physical
parameters linked and per-instrument constants.  Independent per-instrument
fits are also produced, as are two diagnostics: a free-width Gaussian and a
free-centroid Gaussian.  A blackbody soft-excess baseline
(`tbabs*(zbbody + zpowerlw + zgauss)`) is fitted as a continuum systematic
check.

## Why PPS and not SAS

The PPS spectra are the **official SAS pipeline products**.  Their FITS headers
record the SAS version used (`xmmsas_20241108_1150-21.0.0`).  The tool does
**not** run `epproc`/`especget`/`specgroup`: the SAS Docker image is ~16.5 GB
and the CCF is ~2.9 GB, and the PPS products already contain the official
reduction.  This is stated in `run.json`, `provenance.md` and the repository
docs.  See `SAS_RAW_PATH.md` for the optional raw-ODF path.

## Inputs

```text
inputs/PDS456_z_0.1840/xray/xmm_0721010201/
  download.sh                         # reproducible HEASARC/CCF download
  pps/PN/   *PNS003SRSPEC0001.fits    # source spectrum
            *PNS003BGSPEC0001.fits    # background spectrum
            *PNS003SRCARF0001.fits    # source ARF
  pps/MOS1/ *M1S001...                # same products
  pps/MOS2/ *M2S002...
  responses/epn_e2_lw20_sdY9_v22.0.rmf
  responses/m1_e15_im_pall_c.rmf
  responses/m2_e15_im_pall_c.rmf
```

The PPS MOS spectra are stored in **2400 channels at 5 eV**.  The 15 eV canned
matrices named in the PPS headers have **800 channels**, so the tool rebins the
MOS source and background spectra 3:1 to 15 eV (counts summed, `QUALITY` ORed,
grouping preserved).  The PN spectrum and RMF both have 4096 channels.  The
rebinned spectra are written to `outputs/.../xmm_xspec/prepared/` so the exact
fit inputs are inspectable.

## Build and run

```bash
# 1. download the small PPS products (15 MB total)
bash inputs/PDS456_z_0.1840/xray/xmm_0721010201/download.sh

# 2. build the image (HEASARC conda XSPEC 13.0.0)
bash Pipelines/build_images.sh xmm_xspec

# 3. production fit
bash Pipelines/run_xmm_xspec_docker.sh \
  inputs/PDS456_z_0.1840/xray/xmm_0721010201 \
  outputs/PDS456_z_0.1840/xmm_xspec \
  --source-key PDS456_z_0.1840 --redshift 0.184
```

The image is based on `mambaorg/micromamba:1.5.10`, installs
`xspec=13.0.0=hb0f4dca_2` from
`https://heasarc.gsfc.nasa.gov/FTP/software/conda` plus `astropy`, `scipy` and
`matplotlib` from conda-forge, and sources `headas-init.sh` in its entry point.
`PFILES`, `HOME` and `MPLCONFIGDIR` are writable temporary directories.

## Products

`outputs/<source>/xmm_xspec/`:

| file | content |
|---|---|
| `xmm_spectrum_model_residual.png/pdf` | PN/MOS1/MOS2 data, model and residuals for the joint narrow-line fit |
| `xmm_fe_ka_zoom.png/pdf` | 4–8 keV zoom: data, baseline (no line) and line model, residuals |
| `xmm_fit.csv` | every fit: χ²/dof, N_H, Γ, normalizations, constants, line parameters, Δχ², significance, flux, EW |
| `xmm_lines.csv` | Fe Kα measurements: energy, width, normalization, flux, EW, Δχ², detection/upper limit |
| `xmm_consistency.json` | PN/MOS Γ, N_H and line-flux pulls; cross-calibration constants |
| `run.json` | provenance, input hashes, software versions, config, headline results, runtime, caveats |
| `config.effective.json` | effective configuration and resolved paths |
| `xspec.log` | full XSPEC/PyXspec log from the run |
| `provenance.md` | human-readable PPS/SAS/response provenance |
| `fit_summary.txt` | short human-readable summary |
| `prepared/` | the exact PN and rebinned-MOS spectra used by XSPEC |

## PDS 456 result

The accepted production fit is the joint PN+MOS1+MOS2 narrow-line model.
See `docs/ROADMAP_V2.md` for the full discussion.  In brief (XSPEC 13.0.0,
wilm abundances, 0.5–10 keV):

| quantity | value |
|---|---|
| baseline `tbabs*zpowerlw` | χ²/dof = 879.03/516 = 1.704 |
| Γ | 2.0221 ± 0.0041 |
| N_H | (2.304 ± 0.018) × 10²¹ cm⁻² |
| narrow Fe Kα (σ = 50 eV) | χ²/dof = 862.64/515 = 1.675 |
| Δχ² (1 dof) | 16.39 → **4.05σ** |
| line normalization | (2.32 ± 0.57) × 10⁻⁶ photons cm⁻² s⁻¹ |
| line flux | (2.01 ± 0.50) × 10⁻¹⁴ erg cm⁻² s⁻¹ |
| EW_rest | 25.9 ± 6.4 eV (XSPEC-consistent; corrected (1+z) factor) |
| PN / MOS1 / MOS2 independent | 3.13σ / 1.10σ / 2.45σ |
| MOS/PN constants | 1.0514 ± 0.0038 / 1.0422 ± 0.0037 |

The line normalizations agree within 0.7σ; PN and MOS Γ differ by 2.9σ
(cross-calibration systematic).  A blackbody soft-excess baseline still
requires the narrow line at Δχ² = 17.83 (4.22σ).  The free-width fit prefers a
broad component (σ ≈ 1.16 keV, at the fit bound) with EW_rest ≈ 425 eV; that
broad excess is degenerate with continuum curvature and is **not** claimed as
a resolved line width.  A free-centroid fit (σ fixed) gives
E_rest = 6.179 ± 0.027 keV, i.e. the single-Gaussian centroid is below the
neutral 6.4 keV value, consistent with a redshifted/broad Fe Kα complex.

## What this tool can and cannot measure

**Can measure**

* Absorbed power-law continuum: Γ and a cold N_H (with the caveats below).
* Narrow Fe Kα flux and equivalent width at 6.4 keV rest.
* PN/MOS cross-calibration constants and consistency pulls.
* A model-dependent broad Fe Kα / reflection excess (as a diagnostic).

**Cannot measure**

* The physical origin of the soft excess (blackbody vs warm absorption vs
  reflection) from this band alone.
* A relativistic line profile, black-hole spin, Fe abundance, or inclination.
* A clean intrinsic N_H: it is degenerate with the soft excess and the
  continuum shape.
* X-ray luminosity without a distance and an unabsorbed SED; variability from a
  single epoch.
* Sub-5% cross-calibration systematics.

## Failure modes

* **`RMF FILTER (Medium) is not consistent with spectrum (Thin1)`** — expected;
  the redistribution matrix is filter-independent and the ARF carries the
  filter throughput.
* **MOS channel mismatch** — using the 15 eV RMF with the unrebinned 2400-channel
  PPS spectrum fails.  The tool rebins 3:1 to 800 channels first.
* **`RESPFILE`/`ANCRFILE`/`BACKFILE` pointing to absent files** — PPS headers
  reference archive names.  Prepared spectra set them to `NONE` and the tool
  loads the local response/background explicitly.
* **`tbabs` abundance warning** — the tool sets `Xset.abund = "wilm"`.
* **Poor χ²/dof** — the one-power-law model is not a complete AGN model; the
  line significance is a relative Δχ² and is checked with a soft-excess
  baseline.
* **Line width at a bound** — the broad component is not constrained; use the
  fixed-50 eV narrow-core measurement for the production line flux/EW.

## References

* XSPEC/PyXspec manual: <https://heasarc.gsfc.nasa.gov/xanadu/xspec/>
* XMM-Newton SAS: <https://www.cosmos.esa.int/web/xmm-newton/sas>
* PPS products: <https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0721010201/PPS/>
* CCF response matrices:
  <https://xmm-tools.cosmos.esa.int/external/xmm_ccf/ccf/extras/responses/>
* Wilms, Allen & McCray (2000) for `tbabs`.
