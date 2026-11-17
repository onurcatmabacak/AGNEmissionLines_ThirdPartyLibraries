# Results

Every number below was produced from real observations by the tool named in
the second column, and was committed with its own `run.json`, artefacts and
caveat.  **The data and the output trees are no longer shipped** - cloning the
repository used to mean downloading several gigabytes of third-party
observations - so this table is the durable record.  `docs/CAVEAT_MATRIX.md`
states what each tool may and may not claim.

> **Historical record (2026-11-17):** the shipped tree no longer contains any
> `outputs/**/run.json`, so `pipeline/build_results_summary.py` cannot
> regenerate this table.  It records the pre-data-removal products; the two
> MaNGA rows were corrected by hand from their committed product READMEs; the
> NuSTAR row was added by hand on 2026-11-17 from its product README.

| source | tool | product | key numbers |
|---|---|---|---|
| `04592649654_z_0.5874` | `galspec_line` | `-` | ok; snr=45.1, velocity_kms=2.425, fwhm_kms=1622, acceptance_fraction=0.2666 |
| `04592649654_z_0.5874` | `galspec_line_long` | `-` | ok; snr=42.94, velocity_kms=2.715, fwhm_kms=1621, acceptance_fraction=0.1682 |
| `04592649654_z_0.5874` | `gandalf_line` | `-` | ok; snr=132, velocity_kms=-70.92, amplitude=55.97 |
| `04592649654_z_0.5874` | `pyqsofit` | `mcmc` | success; redshift=0.5874 |
| `04592649654_z_0.5874` | `pyqsofit` | `mcmc_converged` | success; redshift=0.5874 |
| `04592649654_z_0.5874` | `pyqsofit` | `mcmc_long` | success; redshift=0.5874 |
| `04592649654_z_0.5874` | `pyqsofit` | `mcmc_long_65k` | success; redshift=0.5874 |
| `04592649654_z_0.5874` | `pyqsofitspec_line` | `-` | snr=48.2034, fwhm_kms=988.4, redshift=0.5874 |
| `04592649654_z_0.5874` | `qgfit` | `expanded_template` | snr=75.26, velocity_kms=-65.45, fwhm_kms=1329, steps=300 |
| `04592649654_z_0.5874` | `qgfit` | `long` | snr=75.26, velocity_kms=-65.45, fwhm_kms=1131, steps=10000 |
| `04592649654_z_0.5874` | `qgfit` | `-` | snr=75.26, velocity_kms=-65.45, fwhm_kms=1131, steps=1000 |
| `04592649654_z_0.5874` | `qsofitmore_line` | `-` | ok;  |
| `04592649654_z_0.5874` | `s3fit_line` | `-` | ok; snr=24.13 |
| `04592649654_z_0.5874` | `sheap_line` | `-` | pass; snr=0.05305, velocity_kms=38.14, fwhm_kms=3685 |
| `3C120_z_0.0330` | `crossmission` | `-` | ok; redshift=0.033 |
| `3C120_z_0.0330` | `qsofitmore_line` | `-` | ok;  |
| `3C120_z_0.0330` | `rxte_hexte` | `-` | ok; cstat_dof=1.138, E_cut_keV=43.02, phoindex=0.9595, delta_cstat_cutoff=0.379 |
| `3C120_z_0.0330` | `rxte_xspec` | `-` | redshift=0.033 |
| `MCG6-30-15_z_0.0077` | `rxte_xspec` | `-` | redshift=0.007749 |
| `NGC1194_z_0.0136` | `manga_dap` | `full` | ok; dap_status_code=0, runtime_s=48731, line_measurements=93102, bpt_agreement=0.9885 |
| `NGC1194_z_0.0136` | `manga_dap` | `full_shard4` | ok; stage=ppxf, shard_workers=4, wall_s=47412, equivalence=bit-exact |
| `NGC1194_z_0.0136` | `manga_dap` | `-` | ok_subset;  |
| `NGC1275_z_0.0176` | `casa_specfit` | `-` | ok; n_components=1, redshift=0.01756 |
| `NGC1275_z_0.0176` | `cube_lines` | `-` | ok; redshift=0.01756 |
| `NGC1275_z_0.0176` | `radio_line` | `-` | ok; chi2nu=0.6324, snr=3.943, snr_integrated=5.083, snr_rms=1.628, velocity_kms=194, fwhm_kms=331.1, amplitude=0.0007715, n_components=1, rms=0.0004739, redshift=0.01756 |
| `NGC1275_z_0.0176` | `submm_line` | `-` | ok; chi2nu=1.402, snr=nan, snr_integrated=5.157, snr_rms=1.566, velocity_kms=172.6, fwhm_kms=262.8, tau=10, tex_K=9.052, n_components=1, rms=0.0004656, redshift=0.01756 |
| `NGC1365_z_0.0035` | `nustar_xspec` | `-` | partial; C-stat/dof FPMA 1.024, FPMB 1.038 (background-subtracted, vign/aperture/detabs ARFs); joint free-cross-cal c=1.07, 1.004 |
| `NGC4051_z_0.0013` | `xmm_rgs` | `-` | ok;  |
| `PDS456_z_0.1840` | `bxa_xspec` | `-` | partial; chi2nu=1.727; BIC prefers pcfabs (dBIC -145.6) over the narrow line (-15.4) |
| `PDS456_z_0.1840` | `cafe_line` | `-` | ok;  |
| `PDS456_z_0.1840` | `crossmission` | `-` | ok; redshift=0.184 |
| `PDS456_z_0.1840` | `ml_joint` | `-` | ok; alpha_ox=-1.37, uv_slope_alpha=1.41, residuals 15% (unit bug fixed) |
| `PDS456_z_0.1840` | `optical_linefit` | `-` | ok;  |
| `PDS456_z_0.1840` | `xmm_sas_raw` | `-` | ok;  |
| `PDS456_z_0.1840` | `xmm_xspec` | `-` | redshift=0.184 |
| `PMNJ0029-7228_z_0.0000` | `radio_line` | `-` | ok; chi2nu=0.5176, snr=5.716, snr_integrated=11.67, snr_rms=5.268, velocity_kms=123.1, fwhm_kms=4.565, amplitude=0.1996, n_components=1, rms=0.03788, redshift=0 |
| `REGION5_HCN_z_0.0000` | `casa_specfit` | `-` | ok; n_components=1, redshift=0 |
| `REGION5_HCN_z_0.0000` | `radio_line` | `-` | ok; chi2nu=0.6658, snr=17.6, snr_integrated=13, snr_rms=2.99, velocity_kms=8.254, fwhm_kms=8, amplitude=0.3535, n_components=1, rms=0.1182, redshift=0 |
| `REGION5_HCN_z_0.0000` | `submm_line` | `-` | ok; chi2nu=1.299, snr=nan, snr_integrated=13.61, snr_rms=2.879, velocity_kms=11.83, fwhm_kms=9.335, tau=0.001, tex_K=9.838, n_components=1, rms=0.1183, redshift=0 |
| `VV114_z_0.0200` | `cafe_line` | `-` | ok;  |
| `spSpec-51908-0277-120_z_0.0859` | `gandalf_line` | `-` | ok; snr=55.12, velocity_kms=68.28, amplitude=55.06 |
| `J012418-711202_z_0.0000` | `radio_line` | `-` | ok; velocity_kms=168.9, fwhm_kms=1.01 (unresolved), amplitude=1.447, snr_integrated=7.0, detected |

| `Mrk509_z_0.0344` | `pyqsofit_uv` | `-` | ok; Lya_na area 3.88e4 (S/N 6.6), Lya_br 3.96e5 (2.0), CIV_br 4.73e5 (1.0) |


_Generated by `pipeline/build_results_summary.py` from 40 archived products; the hand-added NuSTAR row makes 41._
