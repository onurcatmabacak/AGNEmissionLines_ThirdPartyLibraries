# `spSpec-51908-0277-120_z_0.0859`

Low-z SDSS galaxy from the public **GANDALF v1.5** release
(`SDSS_example/spSpec-51908-0277-120.fit`).  It is the production validation
object for `gandalf_line` because H-alpha, [N II], [S II] and H-beta are all
inside the observed range.

## Provenance

* SDSS legacy `spSpec` file, `VERSION=v3_23_2`, `VERS_1D=v5_9_4`.
* Plate 277, MJD 51908, fiber 120; observed 2000-12-30 with 12 x 2700 s
  exposures; `QUALITY=excellent`, `OBJTYPE=GALAXY`.
* RA = 166.01292 deg, Dec = -0.15715033 deg, z = 0.0858772 +/- 0.0000415.
* MD5 `db9336122ecaa4787f7b2d677d3f8376`, 167040 bytes.
* The raw file is the unmodified copy from the GANDALF v1.5 release; the
  `spSpec` primary image (row 0 flux, row 1 continuum, row 2 noise, row 3
  mask) is read directly.  `pipeline/prepare_inputs.py` converts it to the
  repository's PyQSOFit/`spectrum.fits` layout for the pipeline without
  changing the measured flux/error values; `work/prepared/<key>/` is generated.

## Coverage

Observed 3824-9185 A, rest-frame 3523-8458 A.  The relevant lines are:

| line | rest (A) | observed (A) |
|---|---:|---:|
| H-beta | 4861.3 | 5278.9 |
| [O III] 4959/5007 | 4958.8/5006.8 | 5384.2/5436.4 |
| H-alpha | 6562.8 | 7126.4 |
| [N II] 6548/6584 | 6548.0/6583.3 | 7110.3/7148.6 |
| [S II] 6716/6730 | 6716.3/6730.7 | 7293.1/7308.8 |
