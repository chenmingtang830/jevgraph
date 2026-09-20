from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_publication_metadata_and_assets_stay_in_sync() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    citation = yaml.safe_load((ROOT / "CITATION.cff").read_text(encoding="utf-8"))
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    acknowledgements = (ROOT / "ACKNOWLEDGEMENTS.md").read_text(encoding="utf-8")
    release_workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")

    assert f'version = "{citation["version"]}"' in pyproject
    assert "docs/assets/jevgraph-overview.svg" in readme
    assert (ROOT / "docs/assets/jevgraph-overview.svg").is_file()
    assert (ROOT / "docs/assets/social/jevgraph-x-launch.svg").is_file()
    assert (ROOT / "docs/assets/social/jevgraph-x-launch.png").is_file()
    assert "LlamaIndex" in acknowledgements
    assert "https://github.com/jerryjliu/docjev" in acknowledgements
    assert "sha256sum dist/*" in release_workflow
    assert "actions/attest-build-provenance@v2" in release_workflow
    assert "Verify tag matches package version" in release_workflow
    assert 'tags:\n      - "v*"' in release_workflow
