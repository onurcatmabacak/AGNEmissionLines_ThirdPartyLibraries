# QGfit long continuum chain

100 walkers x **10,000 steps** with **1,500 burn-in** (8,500 retained), line
MCMC disabled.  This is the corrective run for the production 100 x 1,000
chain, which reached only N_tau = 8.0 (tau_max 99.5 steps) and had not burned
in: its 200-step burn was only ~2 tau and the trace showed strong drift in
`f_old`, `host_shift`, `sigma` and `m_s`.

The 9,000-step run measured tau=154.7 and reached 48.5 tau; 8,500 retained gives 55 tau at that estimate.  This is still a check, not a
guarantee: tau can grow.  The 5,500-step variant was superseded because its
200-step burn inherited the same transient.
