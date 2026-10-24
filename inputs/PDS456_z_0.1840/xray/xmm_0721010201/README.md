# PDS 456 — XMM-Newton ObsID 0721010201 (PPS products)

This directory contains the small official XMM-Newton products used by the
`xmm_xspec` tool.  Everything is downloaded by `download.sh`; the archive
serves gzip-compressed FITS (`.FTZ`), which the script decompresses to
`.fits`.  The total committed size is ~15 MB.

## Observation

| | |
|---|---|
| target | PDS 456 (z = 0.184) |
| ObsID | 0721010201 |
| instruments | PN, MOS1, MOS2 |
| PN mode/filter | Large Window, Thin1 |
| PN exposure | 100.4 ks |
| PN counts | 341,004 |
| MOS1 exposure / counts | 108.1 ks / 123,867 |
| MOS2 exposure / counts | 108.3 ks / 127,738 |
| PPS SAS version | `xmmsas_20241108_1150-21.0.0` |
| reduction | **official PPS products**; SAS `epproc`/`especget`/`specgroup` not run |

## Files

```text
pps/PN/
  P0721010201PNS003SRSPEC0001.fits  146,880 B (19,543 B .FTZ)  source spectrum (4096 x 5 eV)
  P0721010201PNS003BGSPEC0001.fits  126,720 B (17,087 B .FTZ)  background spectrum
  P0721010201PNS003SRCARF0001.fits   43,200 B (18,144 B .FTZ)  source ARF
pps/MOS1/
  P0721010201M1S001SRSPEC0001.fits   86,400 B (~13 kB .FTZ)   source spectrum (2400 x 5 eV)
  P0721010201M1S001BGSPEC0001.fits   74,880 B (~12 kB .FTZ)   background spectrum
  P0721010201M1S001SRCARF0001.fits   46,080 B (~19 kB .FTZ)   source ARF
pps/MOS2/
  P0721010201M2S002SRSPEC0001.fits   97,920 B (~20 kB .FTZ)   source spectrum
  P0721010201M2S002BGSPEC0001.fits   86,400 B (~14 kB .FTZ)   background spectrum
  P0721010201M2S002SRCARF0001.fits   46,080 B (~19 kB .FTZ)   source ARF
responses/
  epn_e2_lw20_sdY9_v22.0.rmf        3,795,840 B  PN CCF v22.0 RMF
  m1_e15_im_pall_c.rmf              5,198,400 B  MOS1 15 eV canned RMF
  m2_e15_im_pall_c.rmf              5,198,400 B  MOS2 15 eV canned RMF
MANIFEST.sha256                     SHA-256 of every product
```

The PPS `SRSPEC` file contains the spectra of all detected sources in the
field; `0001` is the target (PDS 456).  Higher source numbers are not used.

## Why the MOS spectra are rebinned

The PPS MOS spectra have **2400 channels at 5 eV**.  The 15 eV canned response
matrices (the matrices named in the PPS `RESPFILE` header) have **800
channels**.  The tool therefore rebins the MOS source and background spectra
3:1 to 15 eV before fitting: counts are summed, `QUALITY` is the bitwise OR,
and grouping starts are preserved.  This is a standard channel rebin, not a
loss of spectral resolution beyond the 15 eV response binning.  The PN
spectrum and the PN RMF both have 4096 channels and are used directly.

The RMF `FILTER` keyword is `Medium` while the observation used `Thin1`.
The redistribution matrix is filter-independent and the ARF carries the filter
throughput; XSPEC emits a warning, which is expected.

## Reproduce the download

```bash
bash inputs/PDS456_z_0.1840/xray/xmm_0721010201/download.sh
sha256sum -c inputs/PDS456_z_0.1840/xray/xmm_0721010201/MANIFEST.sha256
```

URLs:

* PPS base:
  `https://heasarc.gsfc.nasa.gov/FTP/xmm/data/rev0/0721010201/PPS/`
* PN RMF:
  `https://xmm-tools.cosmos.esa.int/external/xmm_ccf/ccf/extras/responses/PN/epn_e2_lw20_sdY9_v22.0.rmf`
* MOS RMFs:
  `https://xmm-tools.cosmos.esa.int/external/xmm_ccf/ccf/extras/responses/MOS/15eV/m1_e15_im_pall_c.rmf`
  and `.../m2_e15_im_pall_c.rmf`

## SAS caveat

SAS was **not** run.  The PPS spectra are the official SAS pipeline products,
so the reduction is official; the raw-ODF path (`epproc`, `especget`,
`specgroup`, `epatplot`) is documented in
`Tools/xmm_xspec/SAS_RAW_PATH.md` but is outside this test's 16.5 GB SAS image
and ~2.9 GB CCF budget.  The PN RMF is the current CCF v22.0 extras matrix, a
later calibration product than the PPS 2024 reduction.
