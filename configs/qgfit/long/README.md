# QGfit long continuum chain

100 walkers x **6,500 steps** with **1,500 burn-in** (5,000 retained), line
MCMC disabled.  This is the corrective run for the production 100 x 1,000
chain, which reached only N_tau = 8.0 (tau_max 99.5 steps) and had not burned
in: its 200-step burn was only ~2 tau and the trace showed strong drift in
`f_old`, `host_shift`, `sigma` and `m_s`.

At the old tau the retained chain is 50.2 tau.  This is still a check, not a
guarantee: tau can grow.  The 5,500-step variant was superseded because its
200-step burn inherited the same transient.
