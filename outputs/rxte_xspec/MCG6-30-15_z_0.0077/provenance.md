# RXTE/PCA provenance

Source: **MCG-6-30-15** (ObsID `20310-01-02-00`, z = 0.007749).

## Official products

The spectra are the HEASARC **stdprod** PCA products, i.e. the official
reduced products of the RXTE Guest Observer Facility.  They were not
produced by `pcabackest` or `saextrct` in this repository.

* base URL: `https://heasarc.gsfc.nasa.gov/FTP/xte/data/archive/AO2/P20310/20310-01-02-00/stdprod/`
* source: `xp20310010200_s2.pha.gz` (4873 bytes, SHA256 `71a81418d6d5bfe505db8f0ed6bc16d129002e02afaa552c99f169f7c8b9d1c5`)
* background model: `xp20310010200_b2.pha.gz` (5232 bytes, SHA256 `73a17e95f1973a8e64bce8b296831c68ceebd842a88cdcee92ba04da48a7c4aa`)
* response: `xp20310010200.rsp.gz` (42483 bytes, SHA256 `f8abbc408ed3d351c96cd3ec35b710cc77470afecc28090de628b1ff5054788e`)

HEASARC does not publish a per-file checksum alongside these stdprod
files.  The SHA256 values above pin the exact bytes downloaded on the
production run and are checked by `download.sh`.

## Response and background

* response: 129 PHA channels, 300 energy bins, 1.50-80.00 keV.
* The RSP HISTORY records `marfrmf 3.2.6`: the five individual PCU
  RMFs were summed and multiplied by the 5-PCU ARF.  No synthetic
  response is used.
* background: `xp20310010200_b2.pha.gz` is the official PCA background
  **model** (`b2`), not a measured background spectrum.  XSPEC
  subtracts it and propagates its `STAT_ERR`.  The background model
  systematics are not included in the statistical errors; this is the
  dominant caveat for PCA line measurements.
* exposure: 5887.99999999909 s; source counts 575925.0; background counts 498100.9209308028; net counts 77824.07906919718.

## Software

* XSPEC: 13.0.0
* HEASoft: `10Aug2026_V6.37`
* PyXspec: `/opt/conda/heasoft/lib/python/xspec/__init__.py`
* Python: 3.12.14

## Raw vs PPS/PPS-equivalent caveat

The `stdprod` products are the official PCA screening/reduction
products.  Re-running `pcabackest`/`saextrct` from the raw PCA event
files would change the good-time intervals, the background model and
the response generation; it would not be the same dataset.  This tool
therefore fits the official products and states that choice explicitly.
It does not claim to reproduce the RXTE PCA reduction chain.
