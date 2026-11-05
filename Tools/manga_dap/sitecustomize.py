"""Auto-enable the MaNGA pPXF shard inside the image.

Python imports ``sitecustomize`` at interpreter start-up, before the DAP CLI
runs, which is the only hook that needs no change to sdss-mangadap itself.
Enabled only when ``MANGADAP_SHARD_WORKERS > 1``.
"""
import os
import sys

if os.environ.get("MANGADAP_SHARD_WORKERS", "0") not in ("", "0", "1"):
    # Only stages that have passed the full-data validation are enabled by
    # default.  pPXF is validated (worst relative line-flux difference 0.00e+00
    # against the serial product); EMOM and SASUKE are implemented and
    # unit-tested but break the real pipeline silently, so they must be opted
    # into explicitly with e.g. MANGADAP_SHARD_STAGES=ppxf,emom.
    stages = os.environ.get("MANGADAP_SHARD_STAGES", "ppxf")
    stages = {s.strip().lower() for s in stages.split(",") if s.strip()}
    try:
        if "ppxf" in stages:
            import shard_ppxf
            shard_ppxf.install()
        if "emom" in stages:
            import shard_emom
            shard_emom.install()
        if "sasuke" in stages:
            import shard_sasuke
            shard_sasuke.install()
    except Exception as exc:  # noqa: BLE001 - never break the DAP because of this
        print(f"[mangadap-shard] not installed: {type(exc).__name__}: {exc}",
              file=sys.stderr)
