# `ppxf_host` — host–AGN decomposition with pPXF (Docker)

pPXF fit to the rest-frame optical part of the QSO spectrum, with eMILES
stellar templates, an additive Legendre AGN continuum and emission-line masks.

## Build / run

```bash
bash Pipelines/build_images.sh ppxf_host
.venv/bin/python pipeline/run_new_tools.py --only 04592649654_z_0.5874 --tools ppxf_host --force
```

Input is generated at `work/prepared/<source_key>/pyqsofit/spectrum.fits`;
output is `outputs/<source_key>/ppxf_host/`.

## Reliability contract

`ppxf_summary.json` now contains:

* `host_fraction`, `host_fraction_err`, `host_fraction_upper_limit`;
* `host_fraction_reliable` and `reliability_reasons`;
* `sigma_kms`, `sigma_err_kms`, χ²_red, rest window and mask width.

A host fraction is **not** reported as a measurement when it sits on the
0.02 floor, when σ is at its starting value, or when the fit window lacks the
4000 Å break.  Those cases are upper limits and are flagged.

The empty-template failure at z≈1.1 was fixed by interpolating each template
onto the spectrum's log grid rather than dropping templates whose rest
coverage was shorter than the spectrum.

## Results

At z=0.587 the host fraction is 0.109±0.02 and reliable (σ=689±45 km/s).
At z=0.651 the host is 0.127 but σ hits the 1000 km/s upper bound, so the
host/sigma solution is flagged (`sigma_at_upper`).  At z≳0.99 the optical
spectrum lacks the 4000 Å break; host and σ are upper limits and are flagged,
not reported as detections.  The high χ²_red is dominated by AGN Fe II/Balmer
continuum and broad-line wings.

## Remaining limitations

* Host and AGN are degenerate with a low-order polynomial; no torus or
  simultaneous line fit.
* No MCMC; σ errors come from the pPXF covariance.
* A full spectral fitting model with Fe II templates is the next refinement.
