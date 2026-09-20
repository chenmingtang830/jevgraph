import json

import pytest

from jevgraph.providers import gateway
from jevgraph.providers.gateway import BudgetExceeded, GatewayJevClient, ProviderFailure


class FakeResponse:
    def __init__(self, data: dict, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code
        self.content = json.dumps(data).encode()

    def json(self) -> dict:
        return self._data


class FakeClient:
    response: FakeResponse
    last_url: str | None = None
    last_headers: dict | None = None

    def __init__(self, **_: object) -> None:
        pass

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def post(self, url: str, *, headers: dict, content: bytes) -> FakeResponse:
        self.__class__.last_url = url
        self.__class__.last_headers = headers
        assert b"secret-key-value" not in content
        return self.__class__.response


def test_gateway_parses_typed_choice_and_provider_cost(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeClient.response = FakeResponse(
        {
            "model": "jev-1.13.0",
            "answers": {
                "edge_1": {
                    "type": "choice",
                    "choice": "founded",
                    "probabilities": {"founded": 0.91, "none": 0.09},
                    "confidence": 0.82,
                }
            },
            "usage": {"input_tokens": 210, "output_tokens": 12},
            "providerMetadata": {"gateway": {"cost": "0.00000882"}},
        }
    )
    monkeypatch.setattr(gateway.httpx, "Client", FakeClient)
    client = GatewayJevClient(
        api_key="secret-key-value",
        approved_budget_usd=0.05,
        call_ceiling=1,
    )
    answers, receipt = client.evaluate(
        state={"evidence": "Mira founded Northstar."},
        questions={
            "edge_1": {
                "type": "choice",
                "instructions": "Choose a relation.",
                "criteria": {"founded": "Founded", "none": "No relation"},
            }
        },
    )

    assert answers["edge_1"].selected == "founded"
    assert answers["edge_1"].confidence == 0.82
    assert receipt.cost_usd == pytest.approx(0.00000882)
    assert receipt.resolved_model == "jev-1.13.0"
    assert FakeClient.last_url == gateway.GATEWAY_URL
    assert FakeClient.last_headers is not None
    assert FakeClient.last_headers["ai-model-id"] == "typesafe-ai/jev"
    assert "secret-key-value" not in json.dumps(receipt.__dict__)


def test_gateway_enforces_call_ceiling_before_second_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeClient.response = FakeResponse(
        {
            "answers": {
                "q": {
                    "choice": "yes",
                    "probabilities": {"yes": 1.0},
                    "confidence": 1.0,
                }
            },
            "usage": {"input_tokens": 10, "output_tokens": 1},
            "providerMetadata": {"gateway": {"cost": 0.0}},
        }
    )
    monkeypatch.setattr(gateway.httpx, "Client", FakeClient)
    client = GatewayJevClient(
        api_key="secret-key-value",
        approved_budget_usd=0.05,
        call_ceiling=1,
    )
    kwargs = {
        "state": "state",
        "questions": {"q": {"type": "choice", "instructions": "?", "criteria": {"yes": "Yes"}}},
    }
    client.evaluate(**kwargs)
    with pytest.raises(BudgetExceeded):
        client.evaluate(**kwargs)


def test_gateway_reserves_one_cent_per_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gateway.httpx, "Client", FakeClient)
    client = GatewayJevClient(
        api_key="secret-key-value",
        approved_budget_usd=0.005,
        call_ceiling=1,
    )
    with pytest.raises(BudgetExceeded):
        client.evaluate(
            state="state",
            questions={"q": {"type": "choice", "instructions": "?", "criteria": {"yes": "Yes"}}},
        )


def test_gateway_reports_sanitized_validation_code(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeClient.response = FakeResponse(
        {
            "answers": {
                "q": {
                    "choice": "yes",
                    "probabilities": {"yes": 0.9},
                    "confidence": 0.8,
                }
            },
            "usage": {"input_tokens": 10, "output_tokens": 1},
        }
    )
    monkeypatch.setattr(gateway.httpx, "Client", FakeClient)
    client = GatewayJevClient(
        api_key="secret-key-value",
        approved_budget_usd=0.05,
        call_ceiling=1,
    )
    with pytest.raises(ProviderFailure) as caught:
        client.evaluate(
            state="private source text",
            questions={
                "q": {
                    "type": "choice",
                    "instructions": "private instruction",
                    "criteria": {"yes": "Yes", "no": "No"},
                }
            },
        )

    assert "probability_keys_mismatch" in caught.value.receipt.error
    assert "private" not in caught.value.receipt.error


def test_gateway_renormalizes_small_rounding_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeClient.response = FakeResponse(
        {
            "answers": {
                "q": {
                    "choice": "yes",
                    "probabilities": {"yes": 0.73, "no": 0.25},
                    "confidence": 0.5,
                }
            },
            "usage": {"input_tokens": 10, "output_tokens": 1},
            "providerMetadata": {"gateway": {"cost": 0.0}},
        }
    )
    monkeypatch.setattr(gateway.httpx, "Client", FakeClient)
    client = GatewayJevClient(
        api_key="secret-key-value",
        approved_budget_usd=0.05,
        call_ceiling=1,
    )
    answers, receipt = client.evaluate(
        state="state",
        questions={
            "q": {
                "type": "choice",
                "instructions": "?",
                "criteria": {"yes": "Yes", "no": "No"},
            }
        },
    )

    assert sum(answers["q"].probabilities.values()) == pytest.approx(1.0)
    assert answers["q"].probabilities["yes"] == pytest.approx(0.73 / 0.98)
    assert receipt.warnings == ("probabilities_renormalized:1",)
