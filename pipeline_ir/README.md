# pipeline_ir — IR emission-line slice

This is the **first vertical slice** of `docs/IR_EXTENSION_PLAN.md`: the P0/P1
foundations for NIR/MIR/FIR AGN emission-line analysis.  It is additive; the
existing optical pipeline is untouched.

## What is implemented

| piece | file | status |
|---|---|---|
| line registry (42 optical/NIR/MIR/FIR lines) | `lines.py` | done |
| SDSS DR18 eFEDS/BOSS FITS adapter (ivar, z, z_err, masks) | `spectrum.py` | done |
| coverage/router: `λ_rest=λ_obs/(1+z)`, per-line coverage, observed-band suite selection, refusals | `router.py` | done |
| local continuum + Gaussian line fitter with doublet ratios and tied narrow-line kinematics | `fit.py` | done |
| CLI: route, fit, JSON/CSV + figure per object | `run.py` | done |
| synthetic NIR/MIR/FIR line generator | `synthetic.py` | done |
| self-test (real SDSS DR18 + synthetic IR) | `selftest.py` | done |

## Usage

```bash
# route only
.venv/bin/python -m pipeline_ir.run --fits input/spec-*.fits --out results_ir/demo --dry-run

# route + fit
.venv/bin/python -m pipeline_ir.run --fits input/spec-00000-59345-04492075003.fits \
    --out results_ir/demo

# self-test
.venv/bin/python -m pipeline_ir.selftest
```

Outputs per object: `<stem>.route.json`, `<stem>.measurements.csv`,
`<stem>.fit.pdf/png`.

## Test results (SDSS DR18 eFEDS)

Three real DR18 spectra were routed and fitted.  Example (z=0.2693):

| line | fit flux (1e-17) | SDSS ZLINE area | ratio |
|---|---:|---:|---:|
| Hα (narrow+broad) | 3123 | 3069 | 1.02 |
| Hβ | 627 | 587 | 1.07 |
| [O III] 5007 | 212 | 234 | 0.91 |

Synthetic NIR/MIR/FIR injections are recovered to ~1–5 % in flux and ~1–7 % in
FWHM at S/N≈50, R=2000.

## z > 0.5 SDSS DR18 test

`input_zgt05/` contains five SDSS DR18 eFEDS QSOs downloaded for this test
(z = 0.5874, 0.6506, 0.9901, 1.1289, 1.8297; QSO BROADLINE; median S/N 51–70).
The router correctly moves from optical lines at z≈0.6–1.0 to rest-frame UV
lines at z>1, and correctly refuses Hα for all five (observed Hα > 1.03 µm).

| z | routed suites | main detections | ZLINE comparison |
|---|---|---|---|
| 0.5874 | optical, uv | Mg II, [O II], [Ne III], [O III] | O III 0.75 (diagnostic) |
| 0.6506 | optical, uv | Mg II, Hβ, [O III] | Hβ **1.05**, O III 0.41 (diagnostic) |
| 0.9901 | optical, uv | Mg II, C III], Hβ, [O III] | Hβ **0.90**, O III **0.68** |
| 1.1289 | optical, uv | Mg II, C III] | Mg II 1.43, C III] 1.35 (diagnostic) |
| 1.8297 | uv | C IV, C III], Mg II | C IV **1.28**; Mg II 3.57 (diagnostic) |

Checks marked **bold** are pass gates; the two diagnostics are blend/systematic
limited (Hβ broad wing affecting [O III] at z=0.65; UV Fe II/continuum blending
affecting broad Mg II at z=1.83).  These are exactly the effects the plan's
host/Fe II/UV-continuum work is meant to remove.

Run:

```bash
bash run_ir.sh --input-dir input_zgt05 --out results_ir/zgt05
.venv/bin/python -m pipeline_ir.selftest   # now 60/60 checks
```

## Limitations (deliberate, first slice)

- The **generic `local_gaussian` fitter** is used for every band; the plan's
  tool wrappers (BADASS-NIR, PAHFIT, CAFE, pyspeckit/CLASS/CASA) are not wired
  yet.
- Broad/narrow decomposition is implemented only for Hα/Hβ; NIR/MIR/FIR lines
  are single Gaussians in this slice.
- No telluric/PAH/fringe/background modelling yet; no PAH features; no upper
  limit survival analysis beyond a 3σ integrated-flux limit.
- No SED/torus companion yet (CIGALE/X-CIGALE, AGNfitter-RX, PROSPECTOR-AGN).
- No optical-tool regression in the new path yet; the existing optical
  `run_pipeline.sh` is unchanged.

## Next slices (from the plan)

1. Wire BADASS/PyQSOFit NIR line lists and host decomposition (pPXF/STARLIGHT).
2. Add PAHFIT/CAFE for MIR and pyspeckit/CLASS/CASA for FIR behind the same
   `ToolPlugin` interface.
3. Add the per-object candidate search/scorer and the provenance schema.
4. Add the SED/torus companion and the host/SED comparison.
