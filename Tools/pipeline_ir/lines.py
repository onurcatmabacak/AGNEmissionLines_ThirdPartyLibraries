"""IR/NIR/MIR/FIR emission-line registry (vacuum wavelengths in microns).

The registry is deliberately data-only: no fitting logic.  Each line carries the
rest wavelength, family, blend group and the diagnostics it can support, so the
router, fitter and scorer share one source of truth.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Line:
    name: str
    rest_um: float
    family: str          # recombination, forbidden, fine_structure, molecular, pah
    species: str
    blend_group: str | None = None
    diagnostics: tuple[str, ...] = ()
    # broad component allowed / expected in type-1 AGN
    broad: bool = False
    suite: str | None = None   # method-class override (e.g. UV lines)


# Vacuum wavelengths.  Optical values are the usual vacuum values; the small
# air/vacuum split is recorded in the plan (Appendix A) and applied by adapters.
LINES: tuple[Line, ...] = (
    # --- rest-frame UV (observable in optical at z>0.5) ---
    Line("OVI1034", 0.10340, "recombination", "O VI", "OVI", ("AGN", "ionization"), True, "uv"),
    Line("Lyalpha1216", 0.12157, "recombination", "H I", "Lyalpha", ("AGN", "IGM"), True, "uv"),
    Line("NV1240", 0.12400, "recombination", "N V", "NV", ("AGN", "ionization"), True, "uv"),
    Line("SiIV1397", 0.13970, "recombination", "Si IV", "SiIV", ("AGN",), True, "uv"),
    Line("CIV1549", 0.15490, "recombination", "C IV", "CIV", ("AGN", "BHmass"), True, "uv"),
    Line("CIII1908", 0.19080, "forbidden", "C III]", "CIII", ("AGN", "ionization"), True, "uv"),
    Line("MgII2798", 0.27980, "recombination", "Mg II", "MgII", ("AGN", "BHmass"), True, "uv"),
    # --- optical rest-frame (also observable in NIR at z>0.5) ---
    Line("OII3727", 0.37271, "forbidden", "[O II]", "OII", ("SFR", "ionization")),
    Line("OII3729", 0.37299, "forbidden", "[O II]", "OII", ("SFR", "ionization")),
    Line("NeIII3869", 0.38688, "forbidden", "[Ne III]", "NeIII", ("AGN", "ionization")),
    Line("Hbeta4861", 0.48627, "recombination", "H I", "Hbeta", ("BHmass", "extinction"), True),
    Line("OIII4959", 0.49603, "forbidden", "[O III]", "OIII", ("AGN", "density")),
    Line("OIII5007", 0.50082, "forbidden", "[O III]", "OIII", ("AGN", "ionization")),
    Line("NII6548", 0.65498, "forbidden", "[N II]", "Halpha", ("AGN", "BPT")),
    Line("Halpha6563", 0.65646, "recombination", "H I", "Halpha", ("BHmass", "extinction"), True),
    Line("NII6585", 0.65853, "forbidden", "[N II]", "Halpha", ("AGN", "BPT")),
    Line("SII6718", 0.67183, "forbidden", "[S II]", "SII", ("density",)),
    Line("SII6732", 0.67327, "forbidden", "[S II]", "SII", ("density",)),
    Line("SIII9069", 0.90687, "forbidden", "[S III]", "SIII", ("ionization",)),
    Line("SIII9532", 0.95320, "forbidden", "[S III]", "SIII", ("ionization",)),
    # --- NIR ---
    Line("HeI10833", 1.08333, "recombination", "He I", None, ("ionization",)),
    Line("Pagamma10941", 1.09410, "recombination", "H I", "PaGamma", ("BHmass",), True),
    Line("FeII12570", 1.25699, "forbidden", "[Fe II]", "FeII", ("shocks",)),
    Line("Pabeta12822", 1.28216, "recombination", "H I", "Pabeta", ("BHmass", "extinction"), True),
    Line("FeII16440", 1.64394, "forbidden", "[Fe II]", "FeII", ("shocks",)),
    Line("Paalpha18756", 1.87561, "recombination", "H I", "Paalpha", ("BHmass", "extinction"), True),
    Line("SiVI19630", 1.96280, "forbidden", "[Si VI]", "coronal", ("AGN", "coronal")),
    Line("HeI20587", 2.05870, "recombination", "He I", None, ("ionization",)),
    Line("H2_21218", 2.12183, "molecular", "H2", "H2", ("molecular",)),
    Line("Brgamma21661", 2.16612, "recombination", "H I", "Brgamma", ("BHmass", "extinction"), True),
    Line("Brbeta26258", 2.62585, "recombination", "H I", "Brbeta", ("BHmass",), True),
    Line("Bralpha40523", 4.05230, "recombination", "H I", "Bralpha", ("BHmass",), True),
    # --- MIR ---
    Line("ArII6985", 6.98540, "fine_structure", "[Ar II]", None, ("ionization",)),
    Line("ArIII8989", 8.99140, "fine_structure", "[Ar III]", None, ("ionization",)),
    Line("SIV10511", 10.51050, "fine_structure", "[S IV]", None, ("AGN", "ionization")),
    Line("NeII12814", 12.81350, "fine_structure", "[Ne II]", None, ("AGN", "SFR")),
    Line("NeV14322", 14.32200, "fine_structure", "[Ne V]", "NeV", ("AGN", "coronal")),
    Line("NeIII15555", 15.55500, "fine_structure", "[Ne III]", None, ("AGN", "ionization")),
    Line("SIII18713", 18.71300, "fine_structure", "[S III]", "SIII_MIR", ("ionization",)),
    Line("NeV24318", 24.31800, "fine_structure", "[Ne V]", "NeV", ("AGN", "coronal")),
    Line("OIV25890", 25.89000, "fine_structure", "[O IV]", None, ("AGN", "ionization")),
    Line("SIII33480", 33.48000, "fine_structure", "[S III]", "SIII_MIR", ("ionization",)),
    Line("SiII34815", 34.81500, "fine_structure", "[Si II]", None, ("PDR",)),
    # --- FIR ---
    Line("NIII57317", 57.31700, "fine_structure", "[N III]", None, ("PDR", "ionization")),
    Line("OI63184", 63.18400, "fine_structure", "[O I]", "OI", ("PDR",)),
    Line("OIII88356", 88.35600, "fine_structure", "[O III]", None, ("PDR", "ionization")),
    Line("NII121898", 121.89800, "fine_structure", "[N II]", None, ("PDR",)),
    Line("OI145525", 145.52500, "fine_structure", "[O I]", "OI", ("PDR",)),
    Line("CII157741", 157.74100, "fine_structure", "[C II]", None, ("PDR", "SFR")),
)

BY_NAME = {ln.name: ln for ln in LINES}


def band_of(um: float) -> str:
    """Observed-band label used to choose the tool suite."""
    if um < 1.1:          # SDSS/BOSS optical red edge is ~1.04 um
        return "optical"
    if um < 5.0:
        return "nir"
    if um < 30.0:
        return "mir"
    return "fir"


# Doublet / blend ratios used as physical priors (parent -> (child, ratio)).
TIES = {
    "OIII": {"OIII4959": ("OIII5007", 1.0 / 2.98)},
    "OII": {"OII3727": ("OII3729", 1.0 / 1.5)},
    "Halpha": {"NII6548": ("NII6585", 1.0 / 2.94)},
}
