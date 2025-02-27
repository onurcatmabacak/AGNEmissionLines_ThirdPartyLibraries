# AGNEmissionLines_ThirdPartyLibraries
Confirming that the results from EmissionLineAnalysis repo is true.

https://github.com/remingtonsexton/BADASS3

https://github.com/yukawa1/fantasy/

https://github.com/legolason/PyQSOFit

https://github.com/jtschindler/sculptor

There are 4 different codes to analyze the AGN spectrum of IeRASS J053448.4+212608.

SCULPTOR:

The GUI can be run in a virtual environment in which the necessary python packages can be installed using requirements.txt. The spectrum is sculptor/data_conversion/spectrum.fits

PyQSOFit:

It uses the same virtual environment as SCULPTOR. All the settings are in main.py. You can edit and run main.py for analyzing the spectrum.fits file.

Fantasy AGN:

The analysis code (main.py) is run in a docker container. The container saves all the output of the analysis in output folder. To analyze please run bash run.sh.

BADASS3:

Using the same logic to run Fantasy AGN code, we utilize a docker container that runs main.py and saves the output in output folder. To analyze please run bash run.sh. 