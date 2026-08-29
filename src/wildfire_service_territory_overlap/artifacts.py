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

``assert_contested_groups_are_whole``
    The overlap table is capped at the largest combinations. The rows must still sum to
    the published contested total, so a combination cut for sitting past the cap cannot
    take its records out of the artifact without the build stopping.

``assert_collections_are_ordered_as_declared``
    Every published collection appears in ``ORDERINGS`` with the order it comes out in,
    and a collection missing from that ledger refuses the artifact. Name order is the
    rule; the three collections that are not in name order carry the reason next to the
    declaration rather than only in the sort key that produces them.
"""

from __future__ import annotations

import json
import re
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


CONTESTED_TOTAL_KEY = "contested_between_two_or_more"


def assert_contested_groups_are_whole(tree: Any) -> None:
    """Refuse a contested-groups table that leaves contested records out of itself.

    ``measure.contested_groups`` keeps the largest ``limit`` combinations and drops the
    rest. Today's retrieval produces twelve against a cap of 25, so nothing is dropped,
    but that is a fact about this retrieval rather than about the code. The published
    territory layer is not static, and a refresh that pushed the count past the cap
    would shorten this table with no line anywhere saying so.

    ``assert_aggregate_only`` cannot catch it. Its ceiling is the number of published
    outlines and never below 32, the cap is 25, so the only length rule in this module
    is numerically incapable of firing on this collection.

    Every contested record falls under exactly one combination of outlines, so the rows
    must sum to the published contested total. Where they do not, the difference is the
    number of records that would have gone missing from the table, and the artifact is
    refused rather than published short.
    """
    if not isinstance(tree, dict):
        return
    rows = tree.get("contested_groups")
    coverage = tree.get("placement_coverage")
    if not isinstance(rows, list) or not isinstance(coverage, dict):
        return
    counts = coverage.get("counts")
    if not isinstance(counts, dict) or CONTESTED_TOTAL_KEY not in counts:
        return
    total = counts[CONTESTED_TOTAL_KEY]
    shown = sum(
        row["records"]
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("records"), int)
    )
    if shown != total:
        raise PublicationRefused(
            f"$.contested_groups: the table accounts for {shown} of {total} contested "
            f"records, {abs(total - shown)} short. A combination dropped for sitting "
            "past the cap takes its records with it and the reader is told neither. "
            "Raise the cap, or publish what was cut with its own denominator, but do "
            "not publish this table short."
        )


BY_NAME = "name"
BY_SIZE = "size"
DECLARED = "declared"

ORDERINGS: dict[str, tuple[str, str]] = {
    # Every published collection, and the order it comes out in. A collection with no
    # entry here is refused, so a new one cannot reach a reader without somebody saying
    # what its order means. The second element is the field a name order runs on, an
    # empty string when the elements are scalars, and the reason when the order is
    # neither by name nor by size.
    "$.attributability_by_fire.by_county": (BY_NAME, "county"),
    "$.attributability_by_fire.by_incident_year": (BY_NAME, "year"),
    "$.contested_groups": (
        BY_SIZE,
        "the row is a combination of outlines rather than an entity, and the largest "
        "combinations are the ones the cap keeps, which a name order cannot select",
    ),
    "$.contested_groups[].boundary_proximity.bands_m": (BY_NAME, ""),
    "$.contested_groups[].boundary_proximity.rates": (
        DECLARED,
        "one rate per band, in the band order printed directly above it",
    ),
    "$.contested_groups[].territories": (BY_NAME, ""),
    "$.coordinate_county_agreement.by_county": (BY_NAME, "county"),
    "$.excluded_types": (BY_NAME, "published_type"),
    "$.geometry_ledger.repaired": (BY_NAME, ""),
    "$.geometry_ledger.unusable": (BY_NAME, ""),
    "$.placement_coverage.rates": (
        DECLARED,
        "the four outcomes in the order the report reads them, placed then contested "
        "then uncovered then not measured, which is a sequence and not a score",
    ),
    "$.representativeness_by_category": (BY_NAME, "structure_category"),
    "$.sensitivity.repair_strategy.pairwise_disagreements": (BY_NAME, "between"),
    "$.sensitivity.repair_strategy.pairwise_disagreements[].between": (
        DECLARED,
        "the two repairs named in the order REPAIR_STRATEGIES declares them, so the "
        "pair reads the same way everywhere it appears",
    ),
    "$.sensitivity.repair_strategy.strategies_compared": (
        DECLARED,
        "REPAIR_STRATEGIES order, which puts the repair that produces the published "
        "figures first and the candidates it was compared against after it",
    ),
    "$.sensitivity.repair_strategy.transitions": (BY_NAME, "under_the_chosen_repair"),
    "$.sensitivity.type_inclusion.published_types_present_in_this_retrieval": (
        BY_NAME,
        "",
    ),
    "$.sensitivity.type_inclusion.rule_as_built": (BY_NAME, ""),
    "$.sensitivity.type_inclusion.unexpected_published_types": (BY_NAME, ""),
    "$.sensitivity.type_inclusion.variants": (
        DECLARED,
        "the rule as built first, because every other row is published as a difference "
        "from it, then the variants in the order ADR 0006 argues them",
    ),
    "$.sensitivity.type_inclusion.variants[].types_read_as_territories": (BY_NAME, ""),
    "$.sensitivity.untouched_outlines.outlines_no_record_falls_inside": (BY_NAME, ""),
    "$.territories": (BY_NAME, "territory"),
    "$.territories[].boundary_proximity.bands_m": (BY_NAME, ""),
    "$.territories[].boundary_proximity.rates": (
        DECLARED,
        "one rate per band, in the band order the row publishes beside it",
    ),
    "$.territories[].contested_with": (BY_NAME, ""),
}

_INDEX = re.compile(r"\[\d+\]")


def generic_path(path: str) -> str:
    """The path with list indices flattened, so one entry covers every row."""
    return _INDEX.sub("[]", path)


def _field_values(rows: list[Any], field_name: str, where: str) -> list[Any]:
    """The values a declared order runs on, refusing a row that does not carry one.

    A missing field is a refusal rather than a traceback: this module is the last thing
    between a measurement and a reader, and it has to say what is wrong with the
    artifact rather than fail in a way that reads as a bug in the checker.
    """
    if not field_name:
        return list(rows)
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or field_name not in row:
            raise PublicationRefused(
                f"{where}: its declared order runs on {field_name!r}, and row {index} "
                "does not carry it. Declare the order this collection is actually in."
            )
    return [row[field_name] for row in rows]


def _name_ordered(rows: list[Any], field_name: str, where: str) -> bool:
    values = _field_values(rows, field_name, where)
    return values == sorted(values)


def _size_ordered(rows: list[Any], where: str) -> bool:
    counts = _field_values(rows, "records", where)
    names = [row.get("territories", []) for row in rows]
    keys = list(zip([-count for count in counts], names, strict=True))
    return keys == sorted(keys)


def assert_collections_are_ordered_as_declared(tree: Any) -> None:
    """Refuse a published collection out of its declared order, or with none declared.

    The README used to claim, without qualification, that every collection in the
    output is sorted by name. That was false in three places, and nothing read it, so
    it stayed false: `contested_groups` is in size order, `type_inclusion.variants`
    puts the rule as built first, and `repair_strategy.strategies_compared` follows
    REPAIR_STRATEGIES. A prose invariant nothing enforces is a claim, not a rule.

    So the claim is a ledger now. Every collection names its order and the reason when
    that order is neither by name nor by size, an undeclared collection refuses the
    artifact rather than publishing in whatever order it happened to come out in, and
    the exceptions are visible in one place instead of being discoverable only by
    reading the sort key.
    """
    for path, node in _walk(tree):
        if not isinstance(node, list):
            continue
        where = generic_path(path)
        declared = ORDERINGS.get(where)
        if declared is None:
            raise PublicationRefused(
                f"{where}: a published collection whose order nothing has declared. "
                "Add it to ORDERINGS with the order it comes out in, and with the "
                "reason when that order is neither by name nor by size. An order "
                "nobody stated is an order nobody checked."
            )
        kind, field_name = declared
        if len(node) < 2:
            continue
        if kind == BY_NAME and not _name_ordered(node, field_name, where):
            raise PublicationRefused(
                f"{where}: declared in name order and is not in it. Ordering a "
                "collection of named entities by a measured value is a ranking, "
                "whichever direction it runs."
            )
        if kind == BY_SIZE and not _size_ordered(node, where):
            raise PublicationRefused(
                f"{where}: declared in size order, largest first with the names "
                "breaking ties, and is not in it."
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
    assert_contested_groups_are_whole(tree)
    assert_collections_are_ordered_as_declared(tree)
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
