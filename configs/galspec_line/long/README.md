# GalSpec long-chain configuration

A 20,000-step emcee configuration intended to move beyond the ~11.7 τ
production chain.  It is not automatically accepted: inspect `tau_max` and
ESS in the output and require `nsteps/tau_max >= 50` before calling it
converged.  Run with:

```bash
python pipeline/run_new_tools.py --source 04592649654_z_0.5874 \
  --tools galspec_line --galspec-config configs/galspec_line/long \
  --phased --threads 8
```
