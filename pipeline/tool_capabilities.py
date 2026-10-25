"""Thread/long-run capabilities for every registered tool.

The values are *declared capabilities*, not promises: an upstream code may
ignore the environment variables.  The scheduler uses them to decide which
jobs run serially with a full thread budget and which can run concurrently.
"""
from __future__ import annotations

THREADS = {
    # Heavy optical/IFU/SED workflows with a real multi-thread path or a
    # vectorised BLAS path.
    "s3fit_line": 8, "galspec_line": 8, "qgfit": 8, "pahfit_mir": 8,
    "cafe_line": 8, "manga_dap": 8, "manga_dap_full": 8, "agnfitter_sed": 8,
    "ppxf_host": 4, "gandalf_line": 4, "optical_linefit": 4,
    "ir_linefit": 4, "sheap_line": 4,
    # Mostly single-core upstream codes; env vars are still set so BLAS/NumPy
    # can use them where available.
    "pyqsofit_uv": 1, "qsofitmore_line": 1, "pyqsofitspec_line": 1,
    "xmm_xspec": 1, "rxte_xspec": 1, "crossmission": 1, "crossband": 1,
    "fir_linefit": 1, "nir_linefit": 1, "cigale_sed": 1, "sdss_zline": 0,
}
LONG = {
    "s3fit_line", "galspec_line", "qgfit", "cafe_line",
    "agnfitter_sed", "manga_dap_full",
}
FULL_CAPABILITY = {
    "s3fit_line": "spec+sed, 10 mocks, --threads",
    "galspec_line": "full-continuum emcee; long chain via --galspec-mcmc-steps",
    "pyqsofit_uv": "full UV/optical model; long MCMC via environment",
    "optical_linefit": "joint local H-beta/[O III] fit",
    "qsofitmore_line": "V09 Fe II + Balmer + 200-draw MC",
    "gandalf_line": "native GDL + pPXF full model",
    "qgfit": "continuum MCMC; line MCMC remains a documented caveat",
    "sheap_line": "SPAF/JAX model; validated window is restricted",
    "manga_dap_full": "official all-spaxel S/N=10 DAP (long)",
    "pyqsofitspec_line": "skew-normal line model + parametric bootstrap",
    "pahfit_mir": "full PAH/dust/gas model; systematics flags remain",
    "cafe_line": "continuum/PAH/line model; production subset documented",
    "ir_linefit": "local Gaussian line fit",
    "nir_linefit": "NIR x1d/PSF line fit",
    "fir_linefit": "FIR Gaussian line fit",
    "ppxf_host": "pPXF stellar host/kinematics",
    "xmm_xspec": "official PPS + XSPEC Fe K-alpha fit",
    "rxte_xspec": "official stdprod + XSPEC Fe K-alpha fit",
    "crossmission": "two-object X-ray/optical case study; no correlation",
    "crossband": "analytic cross-band ratio consistency",
    "cigale_sed": "broad-band SED/torus model",
    "agnfitter_sed": "SED/torus nested posterior",
    "sdss_zline": "official SDSS reference product; not a rerun",
    "manga_dap": "official 9-bin subset; all-spaxel reference is published MAPS",
}
DEPENDENT_TOOLS = {"crossmission", "crossband"}


def threads_for(tool: str) -> int:
    return int(THREADS.get(tool, 1))


def is_threaded(tool: str) -> bool:
    return threads_for(tool) > 1


def is_long(tool: str) -> bool:
    return tool in LONG
