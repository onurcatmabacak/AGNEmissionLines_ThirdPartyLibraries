# Vendored upstream sources

| field | value |
|---|---|
| project | PyQSOFitSpec |
| source | https://github.com/yongsukyee/PyQSOFitSpec |
| commit | `aa326ed0b13003b22588a0ad9c8a369d9a2de6dd` ("update README", 2026-03-31) |
| licence | GPL-3.0 (`PyQSOFitSpec/LICENSE`, retained) |
| vendored | 2026-10-23 |

`PyQSOFitSpec/` is a verbatim copy of the upstream files required for a run:

```
PyQSOFitSpec.py fit_linemodel.py main.py fe_uv.txt fe_optical.txt qsopar2.fits
sfddata/README.md LICENSE README.md CHANGELOG.md requirement.txt requirement_old.txt
```

Omitted: `example/` (demo SDSS spectra/PDFs and `pyqsofitspec_out.csv`) and
`archive/` (archived notebooks).  Nothing was modified: the only build-side
patches are in `../patches/` (kapteyn) and `../sfdmap_shim/` (module name),
both outside the upstream tree.

Refresh with:

```bash
git clone https://github.com/yongsukyee/PyQSOFitSpec /tmp/pyqsofitspec
git -C /tmp/pyqsofitspec checkout aa326ed0b13003b22588a0ad9c8a369d9a2de6dd
cp -a /tmp/pyqsofitspec/{PyQSOFitSpec.py,fit_linemodel.py,main.py,fe_uv.txt,\
fe_optical.txt,qsopar2.fits,sfddata,LICENSE,README.md,CHANGELOG.md,\
requirement.txt,requirement_old.txt} Tools/pyqsofitspec_line/third_party/PyQSOFitSpec/
```

and re-check that `python -m py_compile Tools/pyqsofitspec_line/run_pyqsofitspec.py`
still passes, because the driver reads `QSOFit.gauss_result_name`,
`QSOFit.line_result_name`, `QSOFit.line_prop` and `QSOFit.conti_result`.
