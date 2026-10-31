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
