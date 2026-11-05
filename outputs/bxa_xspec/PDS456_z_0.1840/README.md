# BXA — PDS 456, XMM-Newton EPIC PPS spectra (real data)

Bayesian evidence comparison on the **real** XMM-Newton PPS spectra that back the
`xmm_xspec` product (PN + MOS1 + MOS2, 2–10 keV, C-stat), with BXA 5.1.1 prior
transforms and UltraNest nested sampling.

| | |
|---|---|
| input | `inputs/PDS456_z_0.1840/xray/xmm_0721010201` (official PPS SRSPEC + responses) |
| band | 2–10 keV — 0.5 keV leaves an unmodelled soft excess that holds χ²/dof at 2.70 |
| sampler | `speed="auto"` (slice sampling), 300 live points, `frac_remain=0.05`, `dlogz=2` |
| images | `Tools/bxa_xspec` (on top of `xmm_xspec`: HEASoft/XSPEC 13 + PyXspec) |

## Results (converged models)

| model | ln Z | Δ ln Z vs pl | χ²/dof | n calls |
|---|---:|---:|---:|---:|
| `pl` — absorbed power law | −342.06 ± 0.27 | — | 1.727 | 13 235 |
| `pl_line_narrow` — + 50 eV Fe Kα | −342.92 ± 0.46 | **−0.86** | 1.665 | 40 005 |

**The 50 eV Fe Kα line is disfavoured in evidence terms even though it improves
the fit by Δχ² = 27.3.** That is the Occam penalty doing its job: the
prior-independent Δχ² is significant, the prior-weighted evidence is not. Both
numbers are quoted above; neither alone is the whole story.

## Not converged (no evidence quoted)

`pl_line_broad`, `pcfabs`, `warmabs` were stopped after the sampler reached
~0.02 % efficiency at 75–95 % of the evidence volume. The C-stat peak is flat
along the line normalisation, so the constrained prior volume collapses to a
thin sheet and the integral does not close in reasonable time. Their σ/covering
hypotheses are recorded as not converged rather than given a number.

## Data check that came before any of this

A 25-start χ² scan (with `fixed` parameters genuinely frozen) fixed the model
suite: `cutoffpl_cabs` is **unidentifiable** here (χ²/dof 2.701 vs 2.696 for a
plain power law, Δχ² = 2.6 for two extra parameters) and was dropped, and the
0.5–10 keV band was replaced by 2–10 keV.

## Files

`bxa_evidence.csv` (assembled from each model's UltraNest `info/results.json`),
`chains/<model>/` (per-model sampler output: `results.json`, `post_summary.csv`,
weighted posterior), `run.json`, `config.effective.json`, `prepared/` (the exact
spectra handed to XSPEC).
