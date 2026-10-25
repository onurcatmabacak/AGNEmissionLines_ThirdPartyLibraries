# Image and upstream provenance

The repository has two levels of provenance:

1. **Source-level provenance** in each `inputs/<source>/source.json` and
   tool `README.md` (URLs, SHA-256, observation IDs, proposals).
2. **Container provenance** in `docs/image_digests.json`.

## Local image digests

After building the images:

```bash
bash Pipelines/build_images.sh
bash Pipelines/record_image_digests.sh
```

`docs/image_digests.json` records, for each of the 25 images:

- image tag,
- local image ID,
- byte size,
- repository digests, if the image was pulled/pushed.

Local image IDs are not a public registry digest.  They make a tested local
build auditable, but they do **not** guarantee bit-for-bit reproduction on
another machine.  For a release, publish images to a registry and replace the
local IDs with immutable `@sha256:` references.

## Upstream pins

The third-party code pins are documented in the per-tool READMEs.  Examples:

- QSOFITMORE: `4c5f6e497b306aaf50b502a8e4b27ed9dfe89421`, package 1.2.2.
- PyQSOFit: source vendored under `Tools/pyqsofit/PyQSOFit`.
- XSPEC: HEASoft conda package 13.0.0 (see `Tools/xmm_xspec/README.md`).
- MaNGA DAP: `sdss-mangadap` 4.5.0.

If you add a tool, record its upstream URL and commit/tag in the tool README
and in the caveat matrix.
