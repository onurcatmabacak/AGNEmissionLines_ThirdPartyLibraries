# AGNEmissionLines_ThirdPartyLibraries
Confirming that the results from EmissionLineAnalysis repo is true.

https://github.com/remingtonsexton/BADASS3

https://github.com/yukawa1/fantasy/

https://github.com/legolason/PyQSOFit

https://github.com/jtschindler/sculptor

https://github.com/TheSkyentist/GELATO

https://github.com/multiwavelength/gleam

There are 6 different codes to analyze the AGN spectrum of IeRASS J053448.4+212608.

SCULPTOR:

The GUI can be run in a virtual environment in which the necessary python packages can be installed using requirements.txt. The spectrum is sculptor/data_conversion/spectrum.fits

PyQSOFit:

It uses the same virtual environment as SCULPTOR. All the settings are in main.py. You can edit and run main.py for analyzing the spectrum.fits file.

Fantasy AGN:

The analysis code (main.py) is run in a docker container. The container saves all the output of the analysis in output folder. To analyze please run bash run.sh.

BADASS3:

Using the same logic to run Fantasy AGN code, we utilize a docker container that runs main.py and saves the output in output folder. To analyze please run bash run.sh. 

GELATO

Same logic, just run "bash run.sh"

GLEAM

Same logic, just run "bash run.sh"
---

## Unified pipeline

A single pipeline now drives all six tools over many spectra:

```bash
cp ~/agn_data/efeds/*.fits input/   # or: bash run_pipeline.sh --fetch 10
bash run_pipeline.sh                # adapts, runs everything, collects results
```

It adapts each raw FITS to every tool's native layout (`pipeline/prepare_inputs.py`),
runs the tools in parallel (Docker + local), and collects comparable outputs.
Tidy layout: `input/` (raw) → `runs/<object>/{inputs,outputs}/<tool>` →
`results/<tool>/<object>/` with `results/index.csv`.  See **`pipeline/README.md`**
for the dataset, input-format matrix, Docker notes and configuration.  The test
dataset lives in the global folder `~/agn_data/` (SDSS DR18 eFEDS).

One-time setup: install Docker, add yourself to the `docker` group, and build the
images (`bash pipeline/build_images.sh`); `run_pipeline.sh` handles the rest.
