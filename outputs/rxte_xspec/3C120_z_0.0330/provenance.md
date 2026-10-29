# RXTE/PCA provenance

Source: **3C 120** (ObsID `10339-02-01-01`, z = 0.033).

## Official products

The spectra are the HEASARC **stdprod** PCA products, i.e. the official
reduced products of the RXTE Guest Observer Facility.  They were not
produced by `pcabackest` or `saextrct` in this repository.

* base URL: `https://heasarc.gsfc.nasa.gov/FTP/xte/data/archive/AO1/P10339/10339-02-01-01/stdprod/`
* source: `xp10339020101_s2.pha.gz` (5013 bytes, SHA256 `508067d831048ba4892e85588d0e779b293b1bacdca81d9075baaaa4860db639`)
* background model: `xp10339020101_b2.pha.gz` (5405 bytes, SHA256 `30808e49e79d0060a85fb2e67422aa101c07c310a1deb9a188bbc8cd8bfc11cf`)
* response: `xp10339020101.rsp.gz` (52624 bytes, SHA256 `a790413ffc0c4d29beb9cdbb1a88a0da69951fb8d31654b8bba21ca21332d5ac`)

HEASARC does not publish a per-file checksum alongside these stdprod
files.  The SHA256 values above pin the exact bytes downloaded on the
production run and are checked by `download.sh`.

## Response and background

* response: 129 PHA channels, 300 energy bins, 1.50-80.00 keV.
* The RSP HISTORY records `marfrmf 3.2.6`: the five individual PCU
  RMFs were summed and multiplied by the 5-PCU ARF.  No synthetic
  response is used.
* background: `xp10339020101_b2.pha.gz` is the official PCA background
  **model** (`b2`), not a measured background spectrum.  XSPEC
  subtracts it and propagates its `STAT_ERR`.  The background model
  systematics are not included in the statistical errors; this is the
  dominant caveat for PCA line measurements.
* exposure: 9807.99999999801 s; source counts 1703352.0; background counts 1408935.4673508722; net counts 294416.53264912777.

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
