"""Auto-enable the MaNGA pPXF shard inside the image.

Python imports ``sitecustomize`` at interpreter start-up, before the DAP CLI
runs, which is the only hook that needs no change to sdss-mangadap itself.
Enabled only when ``MANGADAP_SHARD_WORKERS > 1``.
"""
import os
import sys

if os.environ.get("MANGADAP_SHARD_WORKERS", "0") not in ("", "0", "1"):
    try:
        import shard_ppxf
        shard_ppxf.install()
    except Exception as exc:  # noqa: BLE001 - never break the DAP because of this
        print(f"[mangadap-shard] not installed: {type(exc).__name__}: {exc}",
              file=sys.stderr)
