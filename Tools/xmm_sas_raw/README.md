# `xmm_sas_raw` — raw XMM-Newton SAS 22.1.0 image (experimental)

This image contains the official ESA **SAS 22.1.0** plus the existing
HEASoft/XSPEC base.  It is for raw ODF reduction (`odfingest`, `cifbuild`,
`epproc`, `evselect`, `especget`), not for the production PPS fit.

It is **not registered as a science tool** and is not part of
`pipeline/runners/build_images.sh`, because the raw ODF/CCF products are large and
must not be committed.

## Build

```bash
docker build -f Tools/xmm_sas_raw/dockerfile -t xmm_sas_raw .
```

The SAS package (1.46 GB compressed) is downloaded during the build; the
resulting image is ~5–6 GB.  Do not push it to GitHub.

## Inputs

- ODF tar from the XMM-Newton Science Archive (`download_data(..., level='ODF')`)
- CCF `valid/` directory (about 2.8 GB) for the observation epoch
- `SAS_ODF` summary file produced by `odfingest`
- `SAS_CCF` CIF produced by `cifbuild`

The `Tools/xmm_sas_raw/README` path is deliberately outside the canonical
input contract until a raw result is validated.

## Reproducible experiment

```bash
docker run --rm -it \
  -v /path/to/odf:/odf:ro \
  -v /path/to/ccf:/ccf:ro \
  -v /path/to/output:/out \
  xmm_sas_raw bash
```

Inside the container:

```bash
export SAS_CCFPATH=/ccf
odfingest odfdir=/odf withodfdir=yes outdir=/out \
  findinstrumentmodes=no usehousekeeping=no
export SAS_ODF=/out/*SUM.SAS
cifbuild calindexset=/out/ccf.cif withccfpath=yes ccfpath=/ccf
export SAS_CCF=/out/ccf.cif
epproc instexpids=PNS003
```

A full uncapped `epproc instexpids=PNS003` run completed with exit 0.  Use the
final `*_ImagingEvts.ds`; the intermediate `*_Evts.ds` has an unfinalized
exposure structure and makes `evselect` write `EXPOSURE=inf`.  The tested
`especget` command uses the final event list, a 20″ source region and a
40–60″ background annulus.  See `docs/XMM_RAW_SAS_RESULT.md` for the result.
The raw reduction is a PN-only cross-check; joint PPS remains the production
path.
