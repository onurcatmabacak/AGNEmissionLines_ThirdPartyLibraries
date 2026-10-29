# QGfit long continuum chain

100 walkers x **10,000 steps** with **1,500 burn-in** (8,500 retained), line
MCMC disabled.  This is the corrective run for the production 100 x 1,000
chain, which reached only N_tau = 8.0 (tau_max 99.5 steps) and had not burned
in: its 200-step burn was only ~2 tau and the trace showed strong drift in
`f_old`, `host_shift`, `sigma` and `m_s`.

Measured result (`outputs/qgfit/04592649654_z_0.5874/long`): tau_max 151.6,
**N_tau = 56.1**, acceptance 0.374, MCMC/LSQ width ratio 0.59 —
`continuum.mcmc.converged = true`.  The 9,000-step attempt reached 48.5 tau and
was one step short of the gate; the host block must stay fixed, because freeing
it puts a tau ~599 ridge back into the chain (that is why 6,500 free-host steps
only reached 38 tau).
