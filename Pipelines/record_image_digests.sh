#!/usr/bin/env bash
# Record local image IDs/digests for provenance.  These are not a substitute
# for publishing images to a registry; they make the tested local build
# auditable.  Run after `bash Pipelines/build_images.sh`.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$ROOT/docs/image_digests.json"
python3 - "$OUT" <<'PY'
import json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
out=Path(sys.argv[1])
tools=[]
for line in Path('Pipelines/build_images.sh').read_text().splitlines():
    if line.startswith('DOCKER_TOOLS=('):
        tools=line.split('(',1)[1].rstrip(')').split()
        break
rows=[]
for tool in tools:
    try:
        fmt='{{.Id}}\t{{.Size}}\t{{json .RepoDigests}}'
        x=subprocess.run(['docker','image','inspect',tool,'--format',fmt],
                         capture_output=True,text=True,check=True).stdout.strip()
        image_id,size,digests=x.split('\t')
        rows.append({'tool':tool,'image':tool,'image_id':image_id,
                     'size_bytes':int(size),'repo_digests':json.loads(digests)})
    except Exception as exc:
        rows.append({'tool':tool,'image':tool,'error':str(exc)})
data={'schema_version':'1.0.0','recorded_utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
      'images':rows}
out.write_text(json.dumps(data,indent=2)+'\n')
print(f'wrote {out} ({len(rows)} images)')
PY
