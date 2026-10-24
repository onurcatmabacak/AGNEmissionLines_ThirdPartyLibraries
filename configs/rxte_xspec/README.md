# `configs/rxte_xspec/`

Complete configuration for the official RXTE/PCA spectral fits.

| variant | source | use |
|---|---|---|
| `default/` | 3C 120, ObsID `10339-02-01-01`, z = 0.0330 | production Stage 4 result |
| `mcg6-30-15/` | MCG-6-30-15, ObsID `20310-01-02-00`, z = 0.007749 | second independent AGN |

## Keys

| key | meaning |
|---|---|
| `source_name`, `obs_id`, `redshift` | source identity and redshift used by `zpowerlw`/`zgauss`; overridable on the command line |
| `archive_url` | HEASARC `stdprod` base URL recorded in `run.json`/`provenance.md` |
| `band_keV` | production band, observed frame; default `[3.0, 20.0]` |
| `line_band_keV` | line-band cross-check, default `[3.0, 10.0]` |
| `statistic` | XSPEC statistic; `chi` for the grouped PCA spectrum |
| `abund` | `wilm` (Wilms et al. 2000) for `tbabs` |
| `fit_iterations`, `xspec_chatter`, `log_chatter` | XSPEC controls and full-log verbosity |
| `zoom_keV`, `plot_dpi` | Fe K-alpha zoom figure range and PNG resolution |
| `baseline_model`, `line_model` | documentation of `tbabs*zpowerlw` and `zgauss` |
| `line_rest_energy_keV` | Fe K-alpha rest energy, 6.4 keV |
| `line_sigma_keV` | narrow-core Gaussian sigma, 50 eV rest frame |
| `line_sigma_free` | run the free-width diagnostic |
| `line_sigma_free_bounds_keV` | free-width bounds, `[0.01, 1.0]` |
| `line_energy_free` | run the free-centroid diagnostic |
| `line_energy_free_bounds_keV` | free-centroid bounds, `[5.0, 8.0]` |
| `soft_excess_check` | run the `tbabs*(zpowerlw+zbbody+zgauss)` continuum-systematic check |
| seed values | initial `nH`, Gamma, power-law normalization, line normalization and width |

The effective production model is:

```text
tbabs * (zpowerlw + zgauss)                  # 3-20 keV observed, chi
zgauss.LineE = 6.4 keV (rest), Sigma = 0.05 keV (rest, frozen)
```

The 3-10 keV fit is the line-band cross-check (the simple power law describes
that band well).  The free-width/free-centroid fits are diagnostics, not
resolved line-width measurements.  The `nH`-frozen and soft-blackbody fits are
systematic checks.

To adapt the configuration to another RXTE/PCA AGN, copy `default/` to a new
variant and change `source_name`, `obs_id`, `redshift`, `archive_url` and the
source manifest's `rxte_config` pointer.  Keep the `stdprod` product policy and
the `b2` background-model caveat.
