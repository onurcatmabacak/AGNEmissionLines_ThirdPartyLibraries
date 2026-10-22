# fir_linefit — dedicated FIR line fitter (Docker)

The FIR-suite tool: one Gaussian + local continuum per line for
PACS/SOFIA/ALMA-style spectra. Lines: [OI] 63/145, [OIII] 88, [NII] 122,
[CII] 158 µm.

## Build / run

```bash
bash pipeline/build_images.sh fir_linefit
bash run_fir_linefit_docker.sh input_fir/synthetic_fir.fits \
     results_ir/fir_synth_dedicated 0.5
```

Input: a FITS spectrum readable by `pipeline_ir.spectrum.read_spectrum`
(SDSS-style `loglam/flux/ivar` or a generic wavelength/flux/error table).
Output: `<object>.fir_lines.csv`, `.fir_fit.png/pdf`, `.fir_summary.json`.

## Validation (synthetic PACS-like spectrum)

`input_fir/synthetic_fir.fits` — 30–300 µm, z=0.5, injected lines:
[OI] 63 = 500, [OIII] 88 = 1000, [NII] 122 = 300, [CII] 158 = 2000
(1e-17 units, FWHM 400 km/s), S/N≈30, R=2000.

| line | recovered | truth | ratio | S/N |
|---|---:|---:|---:|---:|
| [OI] 63 | 445 | 500 | 0.89 | 6.9 |
| [OIII] 88 | 925 | 1000 | 0.92 | 10.6 |
| [NII] 122 | 229 | 300 | 0.76 | 2.4 (marginal) |
| [CII] 158 | 1563 | 2000 | 0.78 | 10.6 |

The 20–25 % low biases come from the fixed local continuum and the coarse
FIR sampling; the next refinement is a joint continuum + multi-line fit.

**Inspect:** `results_ir/fir_synth_dedicated/spectrum.fir_fit.png` / `.pdf`.

## Real FIR data — next adapter

IRSA TAP exposes `herschel.digit_pacs_fits` (PACS spectra of IRAS galaxies)
and `sofia.observation/plane`, but the `spectrum_fits_u` base URL was not
resolved in this pass, and the named AGN (NGC 1068, Mrk 231, PDS 456) are not
in that digitized sample. The real-data adapter (Herschel/ALMA/SOFIA) is the
next step; the synthetic PACS-like spectrum is the current validation.

## Caveats

- Local linear continuum; no PDR/AGN decomposition.
- Unresolved lines are fitted with a width near the instrumental resolution.
- No upper-limit survival analysis beyond the 3σ criterion.
