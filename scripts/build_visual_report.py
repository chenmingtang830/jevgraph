"""Build the offline three-page project report from committed aggregate evidence.

The resulting ``docs/report/index.html`` has no network dependency.  It intentionally embeds only
sanitized aggregate measurements; raw FewRel sentences, prompts, credentials, and HTTP headers do
not enter this report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE = ROOT / "docs/evidence/direct-reasoning-none-2026-09-20.json"
DEFAULT_PROJECT_EVIDENCE = ROOT / "docs/evidence/project-report-2026-09-20.json"
DEFAULT_TEMPLATE = ROOT / "docs/report/template.html"
DEFAULT_OUTPUT = ROOT / "docs/report/index.html"
MARKER = "__REPORT_DATA__"


def _cost_per_100_cents(cost_usd: float, planned_cases: int) -> float:
    """Convert total USD to cents per 100 planned decisions."""
    return cost_usd * 10_000 / planned_cases


def report_data(
    evidence: dict[str, object], project_evidence: dict[str, object]
) -> dict[str, object]:
    fewrel = evidence["fewrel"]
    models = evidence["models"]
    assert isinstance(fewrel, dict)
    assert isinstance(models, dict)
    planned_cases = fewrel["planned_cases"]
    assert planned_cases == 160

    model_specs = (
        ("typesafe-ai/jev", "Jev", "illustrative"),
        ("openai/gpt-5.6-luna", "GPT-5.6 Luna", "receipt"),
        ("deepseek/deepseek-v4.1-flash", "DeepSeek V4.1 Flash", "receipt"),
    )
    report_models: list[dict[str, object]] = []
    for key, name, cost_basis in model_specs:
        item = models[key]
        assert isinstance(item, dict)
        if cost_basis == "illustrative":
            total_cost = item["illustrative_input_list_price_equivalent_usd"]
            cost_per_100 = item[
                "illustrative_input_list_price_equivalent_per_100_planned_cases_cents"
            ]
        else:
            total_cost = item["provider_reported_cost_usd"]
            cost_per_100 = item["provider_reported_cost_per_100_planned_cases_cents"]
        assert isinstance(total_cost, (float, int))
        assert isinstance(cost_per_100, (float, int))
        computed_cost_per_100 = _cost_per_100_cents(float(total_cost), int(planned_cases))
        assert abs(computed_cost_per_100 - float(cost_per_100)) < 1e-9
        report_models.append(
            {
                "key": key,
                "name": name,
                "costBasis": cost_basis,
                "accuracy": item["planned_case_accuracy"],
                "coverage": item["coverage"],
                "successful": item["successful_requests"],
                "attempted": item["attempted_requests"],
                "p50": item["request_latency_p50_ms"],
                "p95": item["request_latency_p95_ms"],
                "runtime": item["sequential_request_time_ms"],
                "inputTokens": item["input_tokens"],
                "outputTokens": item["output_tokens"],
                "totalCostUsd": total_cost,
                "costPer100Cents": cost_per_100,
                "unknownCostRequests": item["unknown_cost_requests"],
                "failureModes": item.get("failure_modes", []),
            }
        )

    return {
        "release": evidence["release"],
        "date": evidence["date"],
        "taskMode": evidence["task_mode"],
        "fewrel": fewrel,
        "request": evidence["shared_request_configuration"],
        "models": report_models,
        "costAudit": evidence["cost_audit"],
        "limitations": evidence["limitations"],
        "e2eSmoke": project_evidence["e2e_smoke"],
        "docjev": project_evidence["docjev"],
        "releaseUrl": "https://github.com/chenmingtang830/jevgraph/releases/tag/v0.5.1",
        "evidenceUrl": "../evidence/direct-reasoning-none-2026-09-20.json",
        "projectEvidenceUrl": "../evidence/project-report-2026-09-20.json",
    }


def build(
    *,
    evidence_path: Path,
    project_evidence_path: Path = DEFAULT_PROJECT_EVIDENCE,
    template_path: Path,
    output_path: Path,
) -> None:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    project_evidence = json.loads(project_evidence_path.read_text(encoding="utf-8"))
    payload = json.dumps(
        report_data(evidence, project_evidence), ensure_ascii=False, separators=(",", ":")
    )
    template = template_path.read_text(encoding="utf-8")
    if template.count(MARKER) != 1:
        raise ValueError(f"Expected exactly one {MARKER} marker in {template_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(template.replace(MARKER, payload), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--project-evidence", type=Path, default=DEFAULT_PROJECT_EVIDENCE)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build(
        evidence_path=args.evidence,
        project_evidence_path=args.project_evidence,
        template_path=args.template,
        output_path=args.out,
    )


if __name__ == "__main__":
    main()
