# z > 0.5 SDSS DR18 test dataset

Five eFEDS/BOSS QSO spectra downloaded from the SDSS DR18 SAS
(`https://dr18.sdss.org/sas/dr18/spectro/boss/redux/eFEDS`), one per redshift
bin, selected with `pipeline/fetch_efeds.py` (CLASS=QSO, ZWARNING=0, S/N≥20):

| file | z | class | median S/N | purpose |
|---|---:|---|---:|---|
| spec-00000-59345-04592649654.fits | 0.5874 | QSO BROADLINE | 51 | Hα at the optical edge; Hβ/[O III] |
| spec-00000-59345-04592933676.fits | 0.6506 | QSO BROADLINE | 65 | Hβ/[O III]; Hα out of optical |
| spec-00000-59345-04570952937.fits | 0.9901 | QSO BROADLINE | 51 | Hβ/[O III] at the red edge |
| spec-00000-59345-04545014975.fits | 1.1289 | QSO BROADLINE | 60 | rest-frame UV (Mg II, C III]) |
| spec-00000-59345-04592566733.fits | 1.8297 | QSO BROADLINE | 70 | rest-frame UV (C IV, C III], Mg II) |

`dataset.csv` has the catalog IDs, redshifts, classes and median S/N.

Reproduce/download:

```bash
python pipeline/fetch_efeds.py --z-min 0.50 --z-max 0.60 --min-sn 20 --n 1
python pipeline/fetch_efeds.py --z-min 0.60 --z-max 0.80 --min-sn 20 --n 1
python pipeline/fetch_efeds.py --z-min 0.80 --z-max 1.00 --min-sn 20 --n 1
python pipeline/fetch_efeds.py --z-min 1.00 --z-max 1.50 --min-sn 20 --n 1
python pipeline/fetch_efeds.py --z-min 1.50 --z-max 2.50 --min-sn 20 --n 1
```

Run the IR slice:

```bash
bash run_ir.sh --input-dir input_zgt05 --out results_ir/zgt05
```
