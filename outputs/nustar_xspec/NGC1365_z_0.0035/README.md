# NGC 1365 — NuSTAR 3–79 keV (`nustar_xspec`)

First real NuSTAR product in the repository.  It is a **reduction and response
proof**, not yet a publication-grade flux measurement: the RMF is built from
the local CALDB, but the ARF is still the canned whole-FPM response.

## Observation

| item | value |
|---|---|
| source | NGC 1365 (RA 53.4016, Dec -36.1404) |
| ObsID | `60002046002` (full-frame; the configured `60002046001` is subframe) |
| date | 2012-07-25 |
| focal plane | FPMA (FPMB not yet reduced) |
| extraction | 60" circle, no background |
| spectrum | `nu60002046002A01_sr.pha`, **12,603 counts** |
| RMF | `numkrmf` from CALDB (`nuAcutdet0..3` + `nuAcutgrprmf`), 66 MB |
| ARF | CALDB `nuA20100101v001.arf` (whole FPM — **not** source-region matched) |

## Result

PyXspec 13 / C-statistic, 3–79 keV, `tbabs*cutoffpl`:

| quantity | value |
|---|---|
| C-stat/dof | **1861.8 / 1895 = 0.982** |
| nH | ~4.0 x 10^23 cm^-2 |
| Gamma | 1.49 |
| E_cut | 22 keV |
| `tbabs*(cutoffpl+pexrav)` | C-stat/dof 1845.9 / 1891 = 0.976 |

The Compton-thick shape is plausible for NGC 1365, but **do not quote the flux
or normalization**: the ARF is the whole-focal-plane curve, and the 60" source
region is not folded into it.  The spectral shape is what this product
establishes.

## What was actually blocking the tool

Two issues, neither of them the archive:

1. **`CALDBCONFIG` format.**  The runner wrote `CALDB = /opt/caldb`.  HEASoft's
   CALDB library wants a mission/instrument table:
   `NUSTAR FPMA CALDB data/nustar/fpm caldb.indx CALDB data/nustar/fpm`.
   With the one-line form every query fails with
   `Problem reading CALDB config file` / `Operation not permitted`.
   `Tools/nustar_xspec/run_nustar_xspec.py` now writes the table.
2. **Subframe coordinates.**  The configured ObsID `60002046001` is a 32x32
   subframe exposure with `X/Y = -1` in the event file, so `numkrmf` cannot
   select detector pixels.  Use the full-frame `60002046002` (or compute `X/Y`
   with `nucoord`, which needs the mast-aspect and PIXPOS/ALIGN products).

With the table and a local CALDB tree, `numkrmf` succeeds on a **read-only**
mount; the earlier `EPERM` was a symptom of the bad config, not the mount.

## Reproduce

```bash
# observation: event_cl + auxil from HEASARC
curl -sL https://heasarc.gsfc.nasa.gov/FTP/nustar/data/obs/00/6/60002046002/event_cl/...
# CALDB: caldb.indx, nuAcutdet0..3*, nuAcutgrprmf*, nuA20100101v001.arf/.teldef
# then, in the nustar_xspec image:
numkrmf infile=nu60002046002A01_cl.evt \
        srcregionfile=nu60002046002A01_src.reg \
        outfile=nu60002046002A01_sr.rmf clobber=yes
# nuproducts with srcregionfile=sky.reg, runmkarf=no, runmkrmf=no
# fit with PyXspec tbabs*cutoffpl
```

The working scripts are in `~/nustar_work/` on the `acer` host:
`test_numkrmf.sh`, `test_nuprod_cmd.sh`, `fit_nustar.py`.

## Remaining work

- Generate the source-region ARF with `numkarf` (needs the CALDB SPECRESP/PSF
  products) — then the flux/normalization become quotable.
- Reduce FPMB and fit FPMA+FPMB jointly.
- Extract a background spectrum and set `BACKSCAL`.
- Register `nustar_xspec` in `pipeline/tool_registry.py` and add the product to
  `docs/RESULTS.md` once the ARF is real.
