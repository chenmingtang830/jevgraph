import json

import pytest

from jevgraph.providers import chat
from jevgraph.providers.chat import GatewayChatClient
from jevgraph.providers.gateway import ProviderFailure


class FakeResponse:
    def __init__(self, data: dict, status_code: int = 200) -> None:
        self._data = data
        self.status_code = status_code
        self.content = json.dumps(data).encode()

    def json(self) -> dict:
        return self._data


class FakeClient:
    response: FakeResponse
    last_content: bytes | None = None

    def __init__(self, **_: object) -> None:
        pass

    def __enter__(self) -> "FakeClient":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def post(self, _: str, *, headers: dict, content: bytes) -> FakeResponse:
        assert headers["Authorization"] == "Bearer secret-key-value"
        self.__class__.last_content = content
        return self.__class__.response


def test_chat_gateway_parses_batched_predictions(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeClient.response = FakeResponse(
        {
            "model": "gpt-5.6-luna-2026-09-01",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": '```json\n{"predictions":{"a":"P1","b":"none"}}\n```'
                    },
                }
            ],
            "usage": {"prompt_tokens": 100, "completion_tokens": 12},
            "providerMetadata": {"gateway": {"cost": "0.0000344"}},
        }
    )
    monkeypatch.setattr(chat.httpx, "Client", FakeClient)
    client = GatewayChatClient(
        api_key="secret-key-value",
        model="gpt-5.6-luna",
        approved_budget_usd=0.05,
        call_ceiling=1,
    )
    predictions, receipt = client.classify(
        criteria={"P1": "creator", "none": "no relation"},
        cases={
            "a": {"sentence": "A made B", "source_entity": "A", "target_entity": "B"},
            "b": {"sentence": "C met D", "source_entity": "C", "target_entity": "D"},
        },
    )

    assert predictions == {"a": "P1", "b": "none"}
    assert receipt.cost_usd == pytest.approx(0.0000344)
    assert receipt.resolved_model == "gpt-5.6-luna-2026-09-01"
    assert FakeClient.last_content is not None
    assert b"secret-key-value" not in FakeClient.last_content
    sent = json.loads(FakeClient.last_content)
    assert sent["temperature"] == 0
    assert sent["max_tokens"] == 16_384


def test_chat_gateway_rejects_missing_case_without_leaking_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeClient.response = FakeResponse(
        {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": '{"predictions":{}}'},
                }
            ],
            "usage": {"prompt_tokens": 20, "completion_tokens": 4},
        }
    )
    monkeypatch.setattr(chat.httpx, "Client", FakeClient)
    client = GatewayChatClient(
        api_key="secret-key-value",
        model="deepseek-v4.1-flash",
        approved_budget_usd=0.05,
        call_ceiling=1,
    )
    with pytest.raises(ProviderFailure) as caught:
        client.classify(
            criteria={"P1": "creator", "none": "no relation"},
            cases={
                "a": {
                    "sentence": "private source sentence",
                    "source_entity": "A",
                    "target_entity": "B",
                }
            },
        )

    assert "prediction_keys_mismatch" in caught.value.receipt.error
    assert "private" not in caught.value.receipt.error
