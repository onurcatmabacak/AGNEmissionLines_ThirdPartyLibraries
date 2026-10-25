# crossmission

Post-processing configuration for `pipeline/compare_xray_optical.py`.
The tool reads the production row from `xmm_xspec/xmm_lines.csv` or
`rxte_xspec/rxte_lines.csv` and the same source's `pyqsofit_uv` line table.
It writes a per-object comparison only; **two objects do not justify a
correlation fit**.  PDS 456 is flagged tentative because its public HST/STIS
spectrum covers C IV but not H-beta/Mg II and the broad C IV S/N is < 3.
