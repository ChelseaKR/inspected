"""The gate every published number passes through, and the deterministic writer.

Four rules are enforced here rather than reviewed by eye, because a rule that lives in a
style guide gets broken by the next contributor and a rule that raises does not.

``assert_rates_are_denominated``
    Nothing shaped like a rate leaves this project without its numerator, its
    denominator, its interval and the method that produced the interval. A measured rate
    must have a positive denominator and a real interval. A not-measured rate must have
    no value and no interval, so a measurement that could not be made can never be read
    as a zero.

``assert_no_locating_fields``
    No coordinate, address, parcel number, or per-structure identifier appears in a
    published artifact. The source file carries all of them and none is fetched, so this
    is a second lock on a door that is already shut.

``assert_aggregate_only``
    No published collection may be longer than the number of things being reported on.
    A per-structure list cannot appear without tripping it, whatever it is named.

``assert_no_ranking``
    Territories come out sorted by name, and no key in the output orders, scores, or
    grades one against another. This project describes geography; it does not rate
    companies, and the output should not be one edit away from doing so.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

RATE_KEYS: tuple[str, ...] = (
    "numerator",
    "denominator",
    "interval_low",
    "interval_high",
    "interval_method",
    "state",
)

LOCATING_KEYS: frozenset[str] = frozenset(
    {
        "apn",
        "address",
        "coordinates",
        "geometry",
        "lat",
        "latitude",
        "lon",
        "long",
        "longitude",
        "objectid",
        "parcel",
        "siteaddress",
        "streetname",
        "streetnumber",
        "x",
        "y",
        "zipcode",
    }
)

RANKING_KEYS: frozenset[str] = frozenset(
    {"best", "grade", "position", "rank", "ranking", "rating", "score", "worst"}
)


class PublicationRefused(ValueError):
    """An artifact broke one of this project's publication rules and was not written."""


def _walk(node: Any, path: str = "$") -> list[tuple[str, Any]]:
    found = [(path, node)]
    if isinstance(node, dict):
        for key, value in node.items():
            found.extend(_walk(value, f"{path}.{key}"))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_walk(value, f"{path}[{index}]"))
    return found


def _check_measured_rate(path: str, node: dict[str, Any]) -> None:
    if node["denominator"] <= 0:
        raise PublicationRefused(
            f"{path}: a measured rate has a denominator of {node['denominator']}. "
            "Zero out of zero is not zero percent."
        )
    for key in ("rate", "interval_low", "interval_high"):
        if node.get(key) is None:
            raise PublicationRefused(f"{path}: a measured rate is missing {key}")
    if node["interval_method"] in ("", "none"):
        raise PublicationRefused(f"{path}: a measured rate names no interval method")


def _check_not_measured_rate(path: str, node: dict[str, Any]) -> None:
    for key in ("rate", "interval_low", "interval_high"):
        if node.get(key) is not None:
            raise PublicationRefused(
                f"{path}: a not-measured rate carries {key}. A measurement that could "
                "not be made has no value, not a zero."
            )


def assert_rates_are_denominated(tree: Any) -> None:
    """Refuse any rate-shaped object that does not carry its denominator and interval."""
    for path, node in _walk(tree):
        if not isinstance(node, dict) or "rate" not in node:
            continue
        missing = [key for key in RATE_KEYS if key not in node]
        if missing:
            raise PublicationRefused(
                f"{path}: a rate is missing {', '.join(missing)}. A count without a "
                "denominator is not a risk and a rate without an interval is not a "
                "comparison."
            )
        if node["state"] == "measured":
            _check_measured_rate(path, node)
        else:
            _check_not_measured_rate(path, node)


def assert_differences_carry_intervals(tree: Any) -> None:
    """A difference between two proportions needs an interval for the difference itself."""
    for path, node in _walk(tree):
        if not isinstance(node, dict) or "difference" not in node:
            continue
        if not isinstance(node.get("difference"), float | int | type(None)):
            continue
        for key in ("interval_low", "interval_high", "interval_method", "state"):
            if key not in node:
                raise PublicationRefused(f"{path}: a difference is missing {key}")
        if node["state"] == "measured" and node["interval_low"] is None:
            raise PublicationRefused(f"{path}: a measured difference has no interval")


def assert_no_locating_fields(tree: Any) -> None:
    """Refuse an artifact carrying anything that could place a structure or an asset."""
    for path, node in _walk(tree):
        if not isinstance(node, dict):
            continue
        for key in node:
            if key.lower() in LOCATING_KEYS:
                raise PublicationRefused(
                    f"{path}.{key}: published artifacts carry counts about geography, "
                    "never a position. Nothing here locates a structure, a parcel, or "
                    "any piece of anybody's infrastructure."
                )


def assert_aggregate_only(tree: Any, max_rows: int) -> None:
    """Refuse a collection long enough to be a record-level listing."""
    for path, node in _walk(tree):
        if isinstance(node, list) and len(node) > max_rows:
            raise PublicationRefused(
                f"{path}: a published collection holds {len(node)} entries against a "
                f"ceiling of {max_rows}. Published output is aggregate; a list this "
                "long is a record listing under another name."
            )


def assert_no_ranking(tree: Any) -> None:
    """Refuse a key that orders, scores, or grades one territory against another."""
    for path, node in _walk(tree):
        if not isinstance(node, dict):
            continue
        for key in node:
            if key.lower() in RANKING_KEYS:
                raise PublicationRefused(
                    f"{path}.{key}: this project publishes descriptive geography. It "
                    "does not rate, rank, or score any named utility, and an artifact "
                    "key that does is refused."
                )


def assert_territories_sorted_by_name(rows: list[dict[str, Any]]) -> None:
    """Refuse territory rows in any order other than alphabetical."""
    names = [str(row["territory"]) for row in rows]
    if names != sorted(names):
        raise PublicationRefused(
            "territory rows are not in name order. Ordering them by a measured value "
            "is a ranking, whichever direction it runs."
        )


def check_all(tree: dict[str, Any], *, max_rows: int) -> None:
    """Every publication rule, in one call, before anything is written."""
    assert_rates_are_denominated(tree)
    assert_differences_carry_intervals(tree)
    assert_no_locating_fields(tree)
    assert_aggregate_only(tree, max_rows)
    assert_no_ranking(tree)
    rows = tree.get("territories")
    if isinstance(rows, list):
        assert_territories_sorted_by_name(rows)


def serialise(tree: dict[str, Any]) -> str:
    """One representation, so an unchanged measurement is an unchanged file."""
    return json.dumps(tree, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_json(tree: dict[str, Any], path: Path, *, max_rows: int) -> Path:
    """Check, then write. An artifact that fails a rule is not written at all."""
    check_all(tree, max_rows=max_rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(serialise(tree), encoding="utf-8")
    return path
