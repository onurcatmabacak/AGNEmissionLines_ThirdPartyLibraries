# `configs/xmm_xspec/default/`

Complete configuration for the production XMM-Newton EPIC fit.  The same file
is mounted at `/app/config` in the `xmm_xspec` image and copied to
`outputs/<source>/xmm_xspec/config.effective.json` after a run.

| key | meaning |
|---|---|
| `redshift` | source redshift; `zpowerlw` and `zgauss` use it.  Overridable with `--redshift`. |
| `band_keV` | observed-frame fit band, default `[0.5, 10.0]`. |
| `statistic` | XSPEC statistic; `chi` (grouped PPS spectra). |
| `fit_iterations` | maximum Levenberg–Marquardt iterations. |
| `xspec_chatter` | XSPEC log verbosity (10 = full fit tables in `xspec.log`). |
| `zoom_keV` | observed-energy range of the Fe Kα zoom figure. |
| `plot_dpi` | PNG resolution. |
| `baseline_model` | documentation of the required baseline (`tbabs*zpowerlw`). |
| `line_model` | `zgauss`. |
| `line_rest_energy_keV` | Fe Kα rest energy, 6.4 keV. |
| `line_sigma_keV` | narrow-core Gaussian sigma, 50 eV rest frame. |
| `line_sigma_free` | production is `false`; a free-width diagnostic is still run. |
| `line_sigma_free_bounds_keV` | bounds used by the broad-component diagnostic. |
| `soft_excess_check` | run the `tbabs*(zbbody+zpowerlw+zgauss)` systematic check. |
| `independent_fits` | instruments also fitted separately for consistency. |
| `mos_rebin_factor` | 3 (5 eV PPS channels → 15 eV for the canned MOS RMF). |
| `cross_calibration` | PN is the reference; MOS constants are free in `[0.5, 1.5]`. |

The effective fit is:

```text
constant * tbabs * (zpowerlw + zgauss)           # joint PN+MOS1+MOS2, 0.5-10 keV
constant_PN = 1 (fixed), constant_MOS1/MOS2 free
zgauss.LineE = 6.4 keV (rest), zgauss.Sigma = 0.05 keV (rest)
```

The production line measurement uses the **fixed-width** Gaussian.  The
free-width and free-centroid fits are diagnostics; their widths/centroids are
reported but not used for the headline EW.

To adapt the config to another XMM AGN, copy this directory to a new variant
and change `redshift`, `source_name`, and (if needed) the `products` override
paths.  Do not change the response/RMF policy without documenting it.
