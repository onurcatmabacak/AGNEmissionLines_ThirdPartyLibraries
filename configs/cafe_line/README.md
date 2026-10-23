# `configs/cafe_line`

Effective CAFE configuration for `Tools/cafe_line`.

```text
configs/cafe_line/
  default/
    inpars.ini          # CAFE input parameters (source: upstream inpars_jwst_miri_AGN.ini)
    default_opt.cafe    # CAFE run options  (source: upstream default_opt.cafe)
  tables/               # CAFE line, PAH, opacity, resolving-power and SED tables
```

Provenance: <https://github.com/GOALS-survey/CAFE> at commit
`39e298bef517030f7828057bb9eeff2927fba77a` (v1.0.1).  The only local changes
are documentation headers; all scientific parameter values are upstream
defaults.

The runner (`Tools/cafe_line/run_cafe.py`) copies `default/inpars.ini` and
`default/default_opt.cafe` into an effective configuration, rewrites
`[PATHS] tabpath` to the effective `tables/` directory, masks any line/PAH
whose observed wavelength falls in a zeroed detector gap, and writes the
result to `outputs/<source>/cafe_line/config_used/`.

The `tables/` directory contains the subset of the upstream CAFE tables used by
this configuration:

* `lines.atomic_AGN.txt`, `lines.molecular_AGN.txt`,
  `lines.H_recombination_AGN.txt`, `pah_template.txt` (plus the alternative
  line/PAH tables shipped upstream);
* `opacity/` (OHMc grain opacities, ice/HAC/CO/CO₂/crystalline-silicate
  features, Gaussian opacities);
* `resolving_power/R_JWST_MIRI_CH*.txt` (all 12 MRS modules);
* `c_abs.*`, `c_ext.*`, `k_abs.*`, `grainsizedf_params.*`;
* `sb99-2myr.txt`, `sb99-10myr.txt`, `sb99-100myr.txt`.

Unused upstream diagnostic images and duplicate upsampled opacity variants
were not copied.  To add a new CAFE configuration, create
`configs/cafe_line/<name>/{inpars.ini,default_opt.cafe}` and run the tool with
`--config /app/config/<name>` (or set `CAFE_CONFIG_DIR` for a host directory
containing `default/`, `<name>/` and `tables/`).
