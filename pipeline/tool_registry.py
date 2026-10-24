"""Canonical tool registry: SED fitting is not line fitting.

The registry lets the orchestrator and documentation use one vocabulary.  A
tool's ``kind`` is one of:

``sed``      broad-band SED/torus model (stars + AGN + dust)
``line``     spectral line/continuum decomposition
``host``     stellar-host/AGN continuum decomposition
``ratio``    line-ratio consistency

``uncertainty`` is deliberately descriptive: several tools are least-squares
codes with covariance or Monte Carlo errors, not MCMC samplers.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Tool:
    name: str
    kind: str
    wave: tuple[str, ...]
    uncertainty: str
    mcmc: bool
    config: str
    runner: str
    description: str


TOOLS: tuple[Tool, ...] = (
    Tool("pyqsofit_uv", "line", ("UV", "optical"), "covariance; optional MC/emcee MCMC", True,
         "configs/pyqsofit/uv/config.json", "Pipelines/run_pyqsofit_uv_docker.sh",
         "PyQSOFit UV/optical broad+narrow line decomposition"),
    Tool("qsofitmore_line", "line", ("UV", "optical"), "parametric Monte Carlo (lmfit refit, 200 realizations)", False,
         "configs/qsofitmore_line/default", "Pipelines/run_qsofitmore_line_docker.sh",
         "QSOFITMORE UV/optical AGN continuum + broad/narrow line decomposition"),
    Tool("ir_linefit", "line", ("UV", "optical", "NIR", "MIR", "FIR"), "least-squares covariance", False,
         "configs/ir_linefit/default/config.json", "Pipelines/run_ir.sh",
         "Generic local-Gaussian IR/optical line fitter"),
    Tool("nir_linefit", "line", ("NIR",), "least-squares covariance", False,
         "configs/nir_linefit/default/config.json", "Pipelines/run_nir_linefit_docker.sh",
         "JWST NIRSpec x1d / PSF-extracted line fitter"),
    Tool("pahfit_mir", "line", ("MIR",), "least-squares + MC uncertainty", False,
         "configs/pahfit_mir/default/config.json", "Pipelines/run_pahfit_mir_docker.sh",
         "PAHFIT PAH/dust/gas decomposition"),
    Tool("fir_linefit", "line", ("FIR",), "curve_fit covariance", False,
         "configs/fir_linefit/default/config.json", "Pipelines/run_fir_linefit_docker.sh",
         "PACS/HIFI FIR Gaussian line fitter"),
    Tool("cafe_line", "line", ("NIR", "MIR"), "LMFIT covariance + MC", False,
         "configs/cafe_line/default", "Pipelines/run_cafe_line_docker.sh",
         "CAFE continuum/PAH/line decomposition for JWST NIRSpec/MIRI"),
    Tool("s3fit_line", "line", ("UV", "optical", "NIR"), "mock-spectrum Monte Carlo", False,
         "configs/s3fit_line/default", "Pipelines/run_s3fit_line_docker.sh",
         "S3Fit simultaneous spectrum + photometric-SED/line fit"),
    Tool("gandalf_line", "line", ("optical", "NIR"), "MPFIT covariance/bootstrap", False,
         "configs/gandalf_line/default", "Pipelines/run_gandalf_line_docker.sh",
         "GANDALF/pPXF stellar+gas decomposition"),
    Tool("galspec_line", "line", ("optical", "NIR"), "full-continuum emcee MCMC", True,
         "configs/galspec_line/default", "Pipelines/run_galspec_line_docker.sh",
         "GalSpec full-continuum + Gaussian line decomposition"),
    Tool("pyqsofitspec_line", "line", ("UV", "optical"), "parametric bootstrap", False,
         "configs/pyqsofitspec_line/default", "Pipelines/run_pyqsofitspec_line_docker.sh",
         "PyQSOFitSpec skew-normal lines + bootstrap"),
    Tool("qgfit", "line", ("UV", "optical"), "continuum MCMC + LSQ line errors", True,
         "configs/qgfit/default", "Pipelines/run_qgfit_docker.sh",
         "QGfit AGN/host/Fe II + multi-component lines"),
    Tool("sheap_line", "line", ("UV", "optical"), "JAX optimisation + parametric-bootstrap MC", False,
         "configs/sheap_line/default", "Pipelines/run_sheap_line_docker.sh",
         "SHEAP AGN spectral decomposition / BH mass"),
    Tool("manga_dap", "line", ("optical",), "DAP formal covariance (1/sqrt(IVAR)); no MCMC; official full-method subset", False,
         "configs/manga_dap/default", "Pipelines/run_manga_dap_docker.sh",
         "Official SDSS MaNGA DAP (sdss-mangadap 4.5.0): HYB10 binning, pPXF, SASUKE on 9 central bins; all-spaxel reference is published MAPS"),
    Tool("ppxf_host", "host", ("optical", "NIR"), "pPXF formal errors", False,
         "configs/ppxf_host/default/config.json", "Pipelines/run_ppxf_host_docker.sh",
         "pPXF stellar kinematics and host fraction"),
    Tool("rxte_xspec", "line", ("X-ray",), "XSPEC covariance; Delta chi-square line significance; no MCMC", False,
         "configs/rxte_xspec/default", "Pipelines/run_rxte_xspec_docker.sh",
         "Official RXTE/PCA stdprod spectra (HEASoft/PyXspec): absorbed power law + Fe K-alpha"),
    Tool("sdss_zline", "reference", ("optical",), "official SDSS speclinefit errors", False,
         "ZLINE HDU in inputs/<source>/raw/spec-*.fits", "pipeline/compare_line_tools.py",
         "Official SDSS BOSS narrow-line anchor"),
    Tool("crossband", "ratio", ("NIR", "MIR", "FIR"), "analytic ratio propagation", False,
         "configs/crossband/default/config.json", "Pipelines/run_crossband_docker.sh",
         "Cross-band line-ratio consistency"),
    Tool("cigale_sed", "sed", ("UV", "optical", "NIR", "MIR", "FIR"), "pdf_analysis posterior", False,
         "configs/cigale_sed/skirtor2016/config.json", "Pipelines/run_cigale_sed_docker.sh",
         "CIGALE stellar+dust+AGN torus SED"),
    Tool("agnfitter_sed", "sed", ("UV", "optical", "NIR", "MIR"), "ultranest nested sampling", True,
         "configs/agnfitter_sed/default/config.json", "Pipelines/run_agnfitter_sed_docker.sh",
         "AGNfitter-rx SED/torus posterior"),
)
BY_NAME = {t.name: t for t in TOOLS}


def as_dicts():
    return [asdict(t) for t in TOOLS]


def by_kind(kind: str):
    return [t for t in TOOLS if t.kind == kind]


if __name__ == "__main__":
    import json
    print(json.dumps(as_dicts(), indent=2))
