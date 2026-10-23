# `fir_linefit` — FIR line fitter (Docker)

One Gaussian + local continuum per line for PACS/HIFI/SOFIA/ALMA-style FIR
spectra.  Lines: [OI] 63/145, [OIII] 88, [NII] 122, [CII] 158 µm.

## Run

```bash
bash Pipelines/build_images.sh fir_linefit
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

Synthetic PACS-like spectrum (30–300 µm, z=0.5), after using the local
pixel spacing and a two-pass velocity-width tie for low-S/N lines:
[OI] 63 498/500, [OIII] 88 911/1000, [NII] 122 347±67/300, [CII] 158
1942±153/2000; median recovered/truth 0.983 (bootstrap 0.941–1.064).

The per-line local-continuum fit with local spacing is the validated path.
The second pass uses an S/N-weighted velocity width only for S/N<5 lines; real
PACS detections (S/N>25) are unchanged.

## Remaining limitations

* Local linear continuum; no PDR/AGN decomposition.
* Unresolved lines are fitted near the instrumental resolution.
* Upper limits are the 3σ criterion; no survival analysis.
* PACS spectra are extracted products, not a full beam/aperture model.
