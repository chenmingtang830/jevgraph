import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/build_visual_report.py"


def _module():
    spec = importlib.util.spec_from_file_location("build_visual_report", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_visual_report_is_self_contained_and_uses_cents_per_100(tmp_path: Path) -> None:
    module = _module()
    output = tmp_path / "index.html"
    module.build(
        evidence_path=ROOT / "docs/evidence/direct-reasoning-none-2026-09-20.json",
        template_path=ROOT / "docs/report/template.html",
        output_path=output,
    )
    rendered = output.read_text(encoding="utf-8")

    assert "__REPORT_DATA__" not in rendered
    assert "0.4100985" in rendered
    assert "1.224625" in rendered
    assert "1.46184575" in rendered
    assert "<link rel=\"stylesheet\"" not in rendered
    assert "<script src=" not in rendered
    assert json.loads(
        (ROOT / "docs/evidence/direct-reasoning-none-2026-09-20.json").read_text(encoding="utf-8")
    )["release"] == "v0.5.1"
