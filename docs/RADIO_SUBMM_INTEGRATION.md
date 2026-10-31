# Radio and sub-mm integration — verified feasibility

Written after checking each candidate against PyPI, GitHub and its dependency
chain (2026-10-30).  The point of this note is to stop us building images that
cannot be built or shipped, and to record the one that can.

## What the repository has today

Bands covered: SDSS optical spectra (`inputs/*/raw/spec-*.fits`), JWST/MIRI
`x1d` and Spitzer IRS `tbl`, MaNGA LOGCUBE, XMM PPS and RXTE `stdprod`.

**There is no radio or sub-mm data in the tree.**  Every radio/sub-mm tool will
therefore be developed and smoke-tested against synthetic or fetched data, and
cannot produce a science product until we acquire real spectra/cubes.

## Verified status of the proposed tools

| tool | distribution | PyPI? | licence | hard dependency | verdict |
|---|---|---|---|---|---|
| **RadioSED** | `github.com/ekerrison/RadioSED` | no (script collection) | **GPL-3.0** | `bilby`, `george`, `astroquery` | **buildable now** — verified below |
| Qubespec | `github.com/honzascholtz/Qubespec` (395 MB, Jupyter) | no | **none (all rights reserved)** | python | licence blocker: cannot be vendored or shipped; build-time clone only, and only with the author's permission |
| XCLASS | not on GitHub/PyPI; tarball from Uni. Cologne | no | academic, per-download | CASA python API | **feasible now** that casatools is a pip wheel, but the source is still a per-download tarball with its own licence |
| **McFine** | **PyPI `mcfine` 0.4** | **yes** | GPL | `spectral_cube`, `emcee`, `lmfit` — **no CASA** | **buildable now** — verified: `pip download mcfine` succeeds, deps are astropy/corner/emcee/lmfit/numdifftools/numpy/scipy/spectral_cube |
| MoD_AbS | no public repository found | no | — | — | blocked: not publicly distributed |
| Lightning (SED) | not found under that name | **name collision**: PyPI `lightning` is PyTorch Lightning | — | — | blocked: must identify the real project first |
| **pyspeckit** | **PyPI 1.0.4** | **yes** | BSD-3 | astropy, radio_beam, casa-formats-io | **buildable now**: multi-Gaussian, hyperfine, H I/RRL fitting on spectra and cubes |
| spectral-cube / radio-beam | PyPI 0.7.0 / 0.3.10 | yes | BSD-3 | — | cube I/O and beam handling |
| RADEX (`pyradex`) | sdist, needs a Fortran build | partly | GPL | gfortran | non-LTE excitation; build in-image with gfortran |
| Splatalogue | `astroquery.splatalogue` | yes | BSD-3 | astroquery | mandatory line identification before any sub-mm fit |
| CASA 6 | **PyPI `casatools` (82 MB) + `casatasks` (2 MB)** | **yes** | — | — | **much lighter than expected**: the multi-GB NRAO tarball is not needed, so `specfit` and the CASA data path are ~85 MB |

Also note AGNfitter already exists in this repo as `agnfitter_sed`; the
"AGNfitter-RX radio extension" would be a *variant config* of that tool, not a
new image.

## RadioSED: verified build recipe

RadioSED ships no `setup.py`/`pyproject.toml` (the repo is a script collection
plus 200 MB of data), so it is used in place with the repo on `PYTHONPATH`.
Verified end to end in `python:3.12-slim`:

```dockerfile
RUN apt-get install -y git gcc g++
RUN git clone --depth 1 https://github.com/ekerrison/RadioSED /app/radiosed
RUN pip install astropy bilby corner pandas matplotlib scipy emcee dynesty george astroquery
WORKDIR /app/radiosed
CMD ["python", "radiosed.py", "--custom_data_file", "/app/input/radio.csv", \
     "--name", "PDS456", "--write_output"]
```

`python radiosed.py --help` succeeds with that dependency set.  The relevant
flags for an offline pipeline:

* `-c/--custom_data_file` — supply radio flux measurements directly instead of
  querying Vizier/NED, which is what we need inside a container;
* `-f/--file` — list of sources;
* `-o/--overwrite`, `-p/--plot`, `-w/--write_output`.

Bilby emits two `FutureWarning`s about `log_likelihood(parameters)`; harmless
for bilby 2.x, to be revisited if bilby 3 lands.

## Implemented: `radio_line` (pyspeckit)

`Tools/radio_line/` + `pipeline/runners/run_radio_line_docker.sh` +
`configs/radio_line/default` — registered in the tool registry, capabilities,
caveats and `ALL_TOOLS`.  Image builds (1.33 GB, pyspeckit 1.0.4 + spectral-cube
+ radio-beam + astroquery + lmfit).

```bash
bash pipeline/runners/run_radio_line_docker.sh <spectrum.fits> <outdir> \
     --z <z> --ncomp 2 --absorption
```

Writes `radio_lines.csv` (component, centre, velocity, FWHM, integrated flux,
S/N), `radio_model.csv`, `radio_fit.png/pdf` and `run.json`.

### Validation

* **Single component, synthetic H I 21-cm absorption** at 45 km/s: recovered
  centre 1.426359 GHz vs 1.426360 injected, sigma 2.148e-4 GHz = 45.1 km/s,
  amplitude -3.493e-3 vs -3.500e-3 injected — exact.
* **Two blended components** (+240 and -120 km/s, 80 and 45 km/s wide): both
  velocities recovered to 0.2 km/s (240.2 and -119.9), chi2/nu = 0.50, but the
  widths come out biased high (188 and 106 km/s) because two Gaussians on a
  smooth spectrum are partly degenerate.  That bias is recorded in the tool
  caveat; it is not a units problem (the single-component case proves the
  conversion is right).

### Real-data status

No real radio/sub-mm AGN spectrum is committed, and that is a hard blocker
rather than an oversight: the ALMA archive line cubes for NGC 1068 are
**200-700 MB each** (measured via the datalink products; the sub-MB products
are continuum images), and NRAO H I absorption spectra require a CASA
reduction before they are a spectrum at all.  The tool is therefore validated
on the synthetic doublet above and awaits a fetched spectrum; the ALMA route
(`astroquery.alma` -> `get_data_info(member_ous_uid)` -> access_url) is
verified to work up to the download size.

## Implemented: `submm_line` (McFine)

`Tools/submm_line/` + `pipeline/runners/run_submm_line_docker.sh` +
`configs/submm_line/default`, registered in registry/capabilities/caveats/
`ALL_TOOLS`.  Image builds (McFine 0.4, pure pip, no CASA/RADEX).

Fits N components of McFine's optical-depth hyperfine model
(`hyperfine_structure_lte`: T_ex, log tau, v_centre, width per component) plus
one Jy-per-K scale, for `n2hp10` (7 merged hyperfine groups, 93.17 GHz), `co21`
and `hi21cm`.

### Validation (synthetic N2H+ 1-0, two components)

Data generated from McFine's own model so the hyperfine strengths/offsets match
exactly (circular in the radiative transfer, but it tests units, velocity
convention, key handling and the fitter): components at -60 km/s (sigma 35, tau
0.56) and +140 km/s (sigma 55, tau 0.32), plus noise.

| | injected | recovered |
|---|---|---|
| v_centre c1 | -60.0 km/s | **-60.00** |
| v_centre c2 | +140.0 km/s | **+139.96** |
| sigma c1 / c2 | 35 / 55 km/s | **34.9 / 55.3** |
| tau c1 / c2 | 0.56 / 0.32 | **0.59 / 0.28** |
| chi2/dof | ~1 | **0.96** |

T_ex comes out below the injected value (13.6 vs 22 K) because it is
degenerate with the free Jy-per-K scale — recorded as the tool caveat, so T_ex
is reported as indicative only.

Two adapter bugs the test caught: McFine's `strength_lines_dict` only holds the
*merged* hyperfine groups (7 for N2H+ 1-0, not the 15 individual transitions),
and its `line_width` is a Gaussian sigma, so `fwhm_kms` must not be multiplied
by 2.3548 twice.

## Integration order (recommended)

1. **RadioSED** — buildable, GPL-3.0, offline via `--custom_data_file`.  Needs a
   small radio photometry table per source (`inputs/<key>/photometry/radio.csv`).
2. **Fetch real radio photometry** for the existing sources (NED/Vizier at the
   `prepare_inputs` stage, committed as a table) so RadioSED has data.
3. **Qubespec** — only with the author's permission (no licence).  Otherwise
   skip; its function overlaps the nine optical fitters already present.
4. **XCLASS / McFine** — require CASA; a separate multi-GB image, and only
   worth it once ALMA data exist.
5. **MoD_AbS / Lightning** — re-check when a public distribution is identified.

## Wiring these in, once a tool is buildable

The existing pattern applies unchanged:

* `Tools/<tool>/dockerfile` + `run_<tool>.py` adapter;
* `pipeline/runners/run_<tool>_docker.sh`;
* an entry in `pipeline/tool_registry.py` with `wave=("radio",)` or
  `("submm",)`, `kind`, `uncertainty` and the runner path;
* `pipeline/tool_capabilities.py` (threads + description), `configs/caveats.yaml`
  (a scientific caveat), `pipeline/run_new_tools.py::ALL_TOOLS`;
* output standardisation: `run.json`, `*_lines.csv` with
  `line,component,flux,flux_err,fwhm_kms,velocity_kms,snr` so the radio results
  drop into `docs/line_tool_comparison.csv` next to the optical ones;
* `docs/LITERATURE_COVERAGE.md` row, and a `pipeline/build_output_manifest.py`
  regeneration.

`decide_tools.py` already routes by the source's declared `tools` list; adding a
band-aware default only needs the band recorded in `inputs/<key>/source.json`.
