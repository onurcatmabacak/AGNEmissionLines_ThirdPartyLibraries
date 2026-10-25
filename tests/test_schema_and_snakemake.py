import json
from pathlib import Path

import jsonschema


def test_catalog_schema_is_json_schema():
    schema = json.loads(Path("schemas/output_catalog.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    cat = json.loads(Path("outputs/output_catalog.json").read_text())
    jsonschema.validate(cat, schema)


def test_snakemake_workflow_declares_dependencies():
    text = Path("workflow/Snakefile").read_text()
    assert "rule all" in text
    assert "rule run_tool" in text
    assert "DEPENDENCIES" in text
    assert "crossmission" in text


def test_caveat_matrix_covers_every_registered_tool():
    import yaml
    from pipeline.tool_registry import TOOLS
    data = yaml.safe_load(Path("configs/caveats.yaml").read_text())
    have = {t["tool"] for t in data["tools"]}
    assert {t.name for t in TOOLS} <= have
    assert Path("docs/CAVEAT_MATRIX.md").is_file()
    assert Path("docs/caveat_matrix.json").is_file()


def test_repository_consistency_audit():
    from pipeline.audit_repo import main as audit
    assert audit() == 0
