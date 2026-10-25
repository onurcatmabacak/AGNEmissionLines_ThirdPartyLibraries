# QGfit long continuum chain

100 walkers x 5,500 steps (200 burn-in), line MCMC disabled.  This is the
corrective run for the production 100 x 1,000 chain, which reached only
N_tau = 8.0 (tau_max 99.5 steps).  The 5,500-step budget gives 5,300 retained
steps, or 53.3 tau at the old estimate.  It must still be checked after the
run; tau can grow.  Line MCMC is not enabled: the 50 x 300 pilot was unstable.
