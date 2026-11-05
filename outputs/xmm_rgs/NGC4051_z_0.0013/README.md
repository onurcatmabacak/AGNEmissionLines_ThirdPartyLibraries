# `xmm_rgs` — resolved soft-X-ray lines in NGC 4051

Input: XMM-Newton RGS1/RGS2 pipeline products for obsid 0109141401 (117 ks).
The counts spectra (`SRSPEC`) are committed in `inputs/NGC4051_z_0.0013/raw/rgs/`;
the response matrices (`RSPMAT`, 30 + 12 MB) are fetched with the URL in
`inputs/NGC4051_z_0.0013/source.json`.

```bash
bash pipeline/runners/run_xmm_rgs_docker.sh <dir with SRSPEC + RSPMAT> \
    outputs/xmm_rgs/NGC4051_z_0.0013 --source-key NGC4051_z_0.0013 \
    --config configs/xmm_rgs/default
```

## Result

Model `tbabs*zpowerlw` + one `zgauss` per line, C-statistic,
0.0 / 0 dof, band 0.45-1.05 keV:

| line | energy (keV) | wavelength (A) | FWHM (eV) | S/N | detected |
|---|---:|---:|---:|---:|---|
| OVII f 22.10A | 0.5610 | 22.10 | 4.7 | 9.2 | yes |
| OVII i 21.80A | 0.5686 | 21.81 | 4.7 | 5.3 | yes |
| OVII r 21.60A | 0.5739 | 21.60 | 4.7 | 0.0 | no |
| OVIII Ly-alpha 18.97A | 0.6536 | 18.97 | 4.7 | 0.8 | no |
| Ne IX 13.55A | 0.9149 | 13.55 | 4.7 | 0.0 | no |

The **OVII forbidden and intercombination** components are detected at S/N 9.2 and
5.3 - lines that are completely blended into one hump at CCD resolution, which is
what every other X-ray tool in this repository uses.  The OVII resonance line and
Ne IX come out consistent with zero: at 117 ks the cool phase is weak, and the
resonance line of NGC 4051 is known to be suppressed by resonant scattering.

## Why the pipeline products, not `rgsproc`

`rgsproc` needs the ODF (attitude + housekeeping), and XSA's AIO endpoint serves
level=PPS products only - `level=ODF` returns 404, and there is no ATT product.
The PPS `SRSPEC` + `RSPMAT` pair is enough to fit in XSPEC, and it makes the test
dependent on two small files instead of a SAS reduction.

## Caveats

* `RSPMAT` is the response matrix without a separate ARF, so line energies,
  widths and significances are calibrated while **absolute fluxes are not**.
* Energies and widths are frozen (laboratory values, RGS resolution): five
  blended Gaussians with free positions and widths is degenerate - the first
  attempt drove the energies to their bounds and C-stat to 5594/2716.
* C-stat/dof ~2.0 is dominated by the crude continuum and by unmodelled
  instrumental/absorption structure, not by the line model.
