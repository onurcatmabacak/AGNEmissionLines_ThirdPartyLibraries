.PHONY: help test validate audit catalog plan smoke docker-smoke

help:
	@echo "make test        - pytest"
	@echo "make validate    - schema + SHA-256 output audit"
	@echo "make catalog     - regenerate outputs/output_catalog.json"
	@echo "make plan        - plan 3C 120"
	@echo "make docker-smoke- build/run optical_linefit smoke test"
	@echo "make smoke       - no-Docker planner + repo validation"

test:
	.venv/bin/python -m pytest -q

validate:
	.venv/bin/python pipeline/validate_outputs.py

audit:
	.venv/bin/python pipeline/audit_repo.py

catalog:
	.venv/bin/python pipeline/build_output_manifest.py

plan:
	.venv/bin/python pipeline/plan_analysis.py --source 3C120_z_0.0330 --goal auto

docker-smoke:
	docker build -f Tools/optical_linefit/dockerfile -t optical_linefit .
	rm -rf /tmp/agn-smoke && mkdir -p /tmp/agn-smoke
	docker run --rm -v "$$PWD/inputs/PDS456_z_0.1840/raw":/app/input:ro -v /tmp/agn-smoke:/app/output optical_linefit --fits /app/input/ADP.2023-04-20T08:25:01.842_XSHOOTER_VIS.fits --out /app/output --z 0.184 --name smoke
	test -s /tmp/agn-smoke/optical_lines_summary.json

smoke: audit plan test validate
