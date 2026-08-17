"""Shared fixture geography, loaded once per session from the committed sample files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from inspected.geometry import Territory, load_territories
from inspected.placement import (
    Placement,
    Record,
    classify,
    measure_boundary_distances,
    read_records,
)
from inspected.sources import ELSE_IOU_POU, ELSE_OTHER

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
PUBLISHED = Path(__file__).resolve().parents[1] / "published"


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def sample_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = read(FIXTURES / "dins_sample.json")
    return rows


@pytest.fixture(scope="session")
def territories() -> tuple[Territory, ...]:
    usable, _ = load_territories(
        {
            ELSE_IOU_POU.key: read(FIXTURES / "else_iou_pou_sample.geojson"),
            ELSE_OTHER.key: read(FIXTURES / "else_other_sample.geojson"),
        }
    )
    return usable


@pytest.fixture(scope="session")
def unusable() -> tuple[Territory, ...]:
    _, bad = load_territories(
        {
            ELSE_IOU_POU.key: read(FIXTURES / "else_iou_pou_sample.geojson"),
            ELSE_OTHER.key: read(FIXTURES / "else_other_sample.geojson"),
        }
    )
    return bad


@pytest.fixture(scope="session")
def records(sample_rows: list[dict[str, Any]]) -> tuple[tuple[Record, ...], int]:
    return read_records(sample_rows)


@pytest.fixture(scope="session")
def placement(
    records: tuple[tuple[Record, ...], int], territories: tuple[Territory, ...]
) -> Placement:
    kept, excluded = records
    result = classify(kept, territories, excluded)
    measure_boundary_distances(result, territories)
    return result


@pytest.fixture(scope="session")
def published_artifact() -> dict[str, Any]:
    payload: dict[str, Any] = read(PUBLISHED / "measurements.json")
    return payload


@pytest.fixture(scope="session")
def published_report() -> str:
    return (PUBLISHED / "REPORT.md").read_text(encoding="utf-8")
