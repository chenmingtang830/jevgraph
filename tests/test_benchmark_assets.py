from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"


def _svg(name: str) -> tuple[ElementTree.Element, str]:
    path = ASSETS / name
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    return ElementTree.fromstring(text), text


def test_benchmark_charts_are_accessible_social_images() -> None:
    for name in (
        "benchmark-latency.svg",
        "benchmark-cost.svg",
        "benchmark-accuracy.svg",
    ):
        root, text = _svg(name)
        assert root.attrib["width"] == "1200"
        assert root.attrib["height"] == "630"
        assert root.attrib["role"] == "img"
        assert "aria-labelledby" in root.attrib
        assert "<title" in text
        assert "<desc" in text


def test_benchmark_charts_pin_exact_values_and_zero_axes() -> None:
    _, latency = _svg("benchmark-latency.svg")
    assert all(value in latency for value in ("431 ms", "1,699 ms", "1,242 ms"))
    assert '>0</text>' in latency

    _, cost = _svg("benchmark-cost.svg")
    assert all(value in cost for value in ("0.410¢", "1.225¢", "1.462¢"))
    assert "ILLUSTRATIVE" in cost
    assert cost.count("RECEIPT") == 2
    assert '>0</text>' in cost

    _, accuracy = _svg("benchmark-accuracy.svg")
    assert all(value in accuracy for value in ("87.500%", "89.375%", "93.125%"))
    assert '>0%</text>' in accuracy
