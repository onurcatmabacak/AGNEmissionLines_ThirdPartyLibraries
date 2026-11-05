# GalSpec long-chain configuration

A 25,000-step configuration intended to move beyond the ~8.2 retained-τ
production chain.  The 25,000-step run itself reached only 17.3 retained τ;
a 70,000-step, 5,000-burn run is the current corrective attempt.  It is not automatically accepted: inspect `tau_max` and
ESS in the output and require retained `n_steps_kept/tau_max >= 50` before calling it
converged.  Run with:

```bash
python pipeline/run_new_tools.py --source 04592649654_z_0.5874 \
  --tools galspec_line --galspec-config configs/galspec_line/long \
  --phased --threads 8
```
