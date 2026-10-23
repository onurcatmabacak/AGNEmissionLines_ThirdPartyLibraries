# `fir_linefit` — FIR line fitter (Docker)

One Gaussian + local continuum per line for PACS/HIFI/SOFIA/ALMA-style FIR
spectra.  Lines: [OI] 63/145, [OIII] 88, [NII] 122, [CII] 158 µm.

## Run

```bash
bash pipeline/build_images.sh fir_linefit
.venv/bin/python pipeline/run_new_tools.py --only NGC253_z_0.0008 --tools fir_linefit --force
.venv/bin/python pipeline/run_new_tools.py --only synthetic_fir_z_0.5000 --tools fir_linefit --force
```

Input can be a single FITS file or a directory.  For a directory the fitter
prefers PACS `.fits.gz` products, combines blue/red segments, and writes
`outputs/<source>/fir_linefit/`.

## Real-data validation

Herschel/PACS HPDP spectra from the ESA HSA:

* **NGC 1068** (`hpacs1342191153...`): [OI] 63 µm detected.
* **NGC 253** (`hpacs1342199414/1342210652...`): [OI] 63, [OIII] 88,
  [OI] 145 and [CII] 158 detected.
* **NGC 4151** (`hpacs1342198305...`): [OIII] 88, [NII] 122, [OI] 145 and
  [CII] 158 detected.

Synthetic PACS-like spectrum (30–300 µm, z=0.5): [OI] 63 is recovered at
~498 (truth 500) after widening the line window; [OIII] 88 and [CII] 158 are
recovered within ~10–20 %.  The remaining low-S/N [NII] 122 bias is
documented, not hidden.

The per-line local-continuum fit is the validated path; a tied-width
experiment was tested and rejected because it did not improve the low-S/N
recovery.

## Remaining limitations

* Local linear continuum; no PDR/AGN decomposition.
* Unresolved lines are fitted near the instrumental resolution.
* Upper limits are the 3σ criterion; no survival analysis.
* PACS spectra are extracted products, not a full beam/aperture model.
