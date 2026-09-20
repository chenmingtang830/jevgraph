from __future__ import annotations

import hashlib
import json
import random
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ontology import Ontology

FEWREL_REVISION = "278a2315d2138810a379cd8d5718914dc56e2582"
FEWREL_BASE = f"https://raw.githubusercontent.com/thunlp/FewRel/{FEWREL_REVISION}"
FEWREL_FILES = {
    "train_wiki.json": (
        f"{FEWREL_BASE}/data/train_wiki.json",
        "8e9e58a05d559be773cbe18a8d4a16ba17e6d397663f9f05a056f894a94b92c1",
    ),
    "pid2name.json": (
        f"{FEWREL_BASE}/data/pid2name.json",
        "eeedd25512a8e4c2bc06b78009836d27de81807bcba6ed929debd5cd713c07ea",
    ),
    "val_wiki.json": (
        f"{FEWREL_BASE}/data/val_wiki.json",
        "76bb44c2485b6faed358a3ce040eadafcc8a8835245cd7e6afc1bef672d4a0bf",
    ),
}


@dataclass(frozen=True)
class FewRelCase:
    id: str
    text: str
    source: str
    target: str
    gold_relation: str
    source_token_positions: tuple[int, ...] = ()
    target_token_positions: tuple[int, ...] = ()


@dataclass(frozen=True)
class FewRelSample:
    cases: tuple[FewRelCase, ...]
    ontology: Ontology
    relation_ids: tuple[str, ...]
    seed: int
    source_revision: str = FEWREL_REVISION


@dataclass(frozen=True)
class FewRelEpisode:
    id: str
    relation_ids: tuple[str, ...]
    support: tuple[FewRelCase, ...]
    queries: tuple[FewRelCase, ...]


@dataclass(frozen=True)
class FewRelEpisodeSample:
    episodes: tuple[FewRelEpisode, ...]
    ways: int
    shots: int
    queries_per_relation: int
    seed: int
    split: str = "val_wiki"
    source_revision: str = FEWREL_REVISION


def fetch_fewrel(target_dir: str | Path) -> list[Path]:
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for filename, (url, expected_sha256) in FEWREL_FILES.items():
        path = target / filename
        if not path.exists() or _sha256(path) != expected_sha256:
            request = urllib.request.Request(url, headers={"User-Agent": "jevgraph/0.1"})
            with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
                payload = response.read(20_000_000)
            if len(payload) >= 20_000_000:
                raise ValueError(f"{filename} exceeded the download size limit.")
            if hashlib.sha256(payload).hexdigest() != expected_sha256:
                raise ValueError(f"{filename} failed its pinned SHA-256 check.")
            path.write_bytes(payload)
        paths.append(path)
    citation = target / "SOURCE.md"
    citation.write_text(
        "# FewRel source\n\n"
        f"Revision: `{FEWREL_REVISION}`\n\n"
        "Source: https://github.com/thunlp/FewRel\n\n"
        "FewRel code and repository license: MIT. The examples are derived from Wikipedia and "
        "Wikidata; preserve upstream attribution and terms. Cite Han et al., EMNLP 2018.\n",
        encoding="utf-8",
    )
    return paths


def sample_fewrel(
    data_dir: str | Path,
    *,
    relation_count: int,
    examples_per_relation: int,
    seed: int,
) -> FewRelSample:
    if relation_count < 2 or relation_count > 64:
        raise ValueError("relation_count must be between 2 and 64.")
    if examples_per_relation < 1 or examples_per_relation > 100:
        raise ValueError("examples_per_relation must be between 1 and 100.")
    root = Path(data_dir)
    data = json.loads((root / "train_wiki.json").read_text(encoding="utf-8"))
    names = json.loads((root / "pid2name.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(names, dict):
        raise ValueError("FewRel files have an unexpected shape.")
    rng = random.Random(seed)
    available = sorted(relation_id for relation_id in data if relation_id in names)
    relation_ids = tuple(sorted(rng.sample(available, relation_count)))
    descriptions = {
        relation_id: _relation_description(names[relation_id]) for relation_id in relation_ids
    }
    ontology = Ontology.from_relations("fewrel-1.0-closed-set", descriptions)
    cases: list[FewRelCase] = []
    for relation_id in relation_ids:
        instances = data[relation_id]
        if not isinstance(instances, list) or len(instances) < examples_per_relation:
            raise ValueError(f"FewRel relation {relation_id} lacks enough examples.")
        indexes = sorted(rng.sample(range(len(instances)), examples_per_relation))
        for index in indexes:
            value = instances[index]
            if not isinstance(value, dict):
                raise ValueError("FewRel instance has an unexpected shape.")
            tokens = value.get("tokens")
            head = value.get("h")
            tail = value.get("t")
            if (
                not isinstance(tokens, list)
                or any(not isinstance(token, str) for token in tokens)
                or not isinstance(head, list)
                or not isinstance(tail, list)
                or not head
                or not tail
            ):
                raise ValueError("FewRel instance fields were invalid.")
            case_id = f"{relation_id}:{index}"
            cases.append(
                FewRelCase(
                    id=case_id,
                    text=_join_tokens(tokens),
                    source=str(head[0]),
                    target=str(tail[0]),
                    gold_relation=relation_id,
                    source_token_positions=_entity_positions(head),
                    target_token_positions=_entity_positions(tail),
                )
            )
    rng.shuffle(cases)
    return FewRelSample(tuple(cases), ontology, relation_ids, seed)


def sample_fewrel_episodes(
    data_dir: str | Path,
    *,
    ways: int,
    shots: int,
    queries_per_relation: int,
    episode_count: int,
    seed: int,
    split: str = "val_wiki",
) -> FewRelEpisodeSample:
    """Create deterministic N-way K-shot episodes following the FewRel task shape."""
    if split != "val_wiki":
        raise ValueError("Only the public FewRel 1.0 val_wiki split is supported.")
    if ways not in {5, 10}:
        raise ValueError("ways must be 5 or 10 for the official-compatible track.")
    if shots not in {1, 5}:
        raise ValueError("shots must be 1 or 5 for the official-compatible track.")
    if queries_per_relation < 1 or queries_per_relation > 5:
        raise ValueError("queries_per_relation must be between 1 and 5.")
    if episode_count < 1 or episode_count > 10_000:
        raise ValueError("episode_count must be between 1 and 10,000.")

    path = Path(data_dir) / f"{split}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or len(data) < ways:
        raise ValueError("FewRel validation data has an unexpected shape.")
    available = sorted(data)
    rng = random.Random(seed)
    episodes: list[FewRelEpisode] = []
    for episode_index in range(episode_count):
        relation_ids = tuple(rng.sample(available, ways))
        support: list[FewRelCase] = []
        queries: list[FewRelCase] = []
        for relation_id in relation_ids:
            instances = data.get(relation_id)
            required = shots + queries_per_relation
            if not isinstance(instances, list) or len(instances) < required:
                raise ValueError(f"FewRel relation {relation_id} lacks enough examples.")
            indexes = rng.sample(range(len(instances)), required)
            for position, instance_index in enumerate(indexes):
                case = _case(
                    relation_id,
                    instance_index,
                    instances[instance_index],
                    prefix=f"episode-{episode_index:05d}",
                )
                if position < shots:
                    support.append(case)
                else:
                    queries.append(case)
        rng.shuffle(support)
        rng.shuffle(queries)
        grouped_query_order = tuple(
            relation_id
            for relation_id in relation_ids
            for _ in range(queries_per_relation)
        )
        if tuple(item.gold_relation for item in queries) == grouped_query_order:
            queries = [*queries[1:], queries[0]]
        episodes.append(
            FewRelEpisode(
                id=f"episode-{episode_index:05d}",
                relation_ids=relation_ids,
                support=tuple(support),
                queries=tuple(queries),
            )
        )
    return FewRelEpisodeSample(
        episodes=tuple(episodes),
        ways=ways,
        shots=shots,
        queries_per_relation=queries_per_relation,
        seed=seed,
        split=split,
    )


def _case(relation_id: str, index: int, value: Any, *, prefix: str) -> FewRelCase:
    if not isinstance(value, dict):
        raise ValueError("FewRel instance has an unexpected shape.")
    tokens = value.get("tokens")
    head = value.get("h")
    tail = value.get("t")
    if (
        not isinstance(tokens, list)
        or any(not isinstance(token, str) for token in tokens)
        or not isinstance(head, list)
        or not isinstance(tail, list)
        or not head
        or not tail
    ):
        raise ValueError("FewRel instance fields were invalid.")
    return FewRelCase(
        id=f"{prefix}:{relation_id}:{index}",
        text=_join_tokens(tokens),
        source=str(head[0]),
        target=str(tail[0]),
        gold_relation=relation_id,
        source_token_positions=_entity_positions(head),
        target_token_positions=_entity_positions(tail),
    )


def _entity_positions(entity: list[Any]) -> tuple[int, ...]:
    if len(entity) < 3 or not isinstance(entity[2], list) or not entity[2]:
        return ()
    first_mention = entity[2][0]
    if not isinstance(first_mention, list) or any(
        not isinstance(position, int) or position < 0 for position in first_mention
    ):
        return ()
    return tuple(first_mention)


def _join_tokens(tokens: list[str]) -> str:
    text = " ".join(tokens)
    for punctuation in [".", ",", ";", ":", "?", "!", ")", "]", "}"]:
        text = text.replace(" " + punctuation, punctuation)
    for punctuation in ["(", "[", "{"]:
        text = text.replace(punctuation + " ", punctuation)
    return text


def _relation_description(value: Any) -> str:
    if isinstance(value, list) and len(value) >= 2:
        return f"{value[0]} — {value[1]}"
    if isinstance(value, list) and value:
        return str(value[0])
    return str(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
