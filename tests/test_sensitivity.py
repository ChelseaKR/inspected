"""The judgment calls, re-run against their alternatives.

These tests are built on hand-made geography rather than on the shared fixtures, because
the point of each one is a difference between two runs and the difference has to be
arranged deliberately. Nothing here is sampled from the real retrievals.
"""

from __future__ import annotations

from typing import Any

import pytest

from inspected.geometry import BUFFER_ZERO, MAKE_VALID, load_territories
from inspected.placement import Placement, Record, classify, containment_signatures
from inspected.sensitivity import (
    TYPE_VARIANTS,
    _transitions,
    _types_present,
    repair_comparison,
    type_inclusion,
    untouched_outlines,
)


def square(w: float, s: float, e: float, n: float) -> list[list[float]]:
    return [[w, s], [e, s], [e, n], [w, n], [w, s]]


def bowtie(w: float, s: float, e: float, n: float) -> list[list[float]]:
    """Two lobes crossing at the middle. `make_valid` keeps both; `buffer(0)` keeps one."""
    return [[w, s], [e, n], [w, n], [e, s], [w, s]]


def feature(oid: int, name: str, kind: str, ring: list[list[float]]) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": {"OBJECTID": oid, "Utility": name, "Type": kind},
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }


def collection(*features: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {"a": {"type": "FeatureCollection", "features": list(features)}}


def record(oid: int, lon: float, lat: float, incident: str = "SAMPLE") -> Record:
    return Record(
        object_id=oid,
        damage="Destroyed (>50%)",
        incident=incident,
        county="Sample County East",
        year=2025,
        lon=lon,
        lat=lat,
    )


@pytest.fixture
def two_types() -> dict[str, dict[str, Any]]:
    """An investor-owned square and a cooperative square that do not touch."""
    return collection(
        feature(1, "Wires IOU", "IOU", square(-121.0, 38.0, -120.5, 38.5)),
        feature(2, "Rural Co-op", "CO-OP", square(-119.0, 38.0, -118.5, 38.5)),
    )


def test_the_rule_as_built_is_the_first_row_and_is_the_reference(
    two_types: dict[str, dict[str, Any]],
) -> None:
    records = (record(1, -120.75, 38.25),)
    block = type_inclusion(two_types, records, 0)
    first = block["variants"][0]
    assert first["variant"] == "the rule as built"
    assert first["types_read_as_territories"] == ["CO-OP", "IOU", "POU", "Tribal"]
    assert "contested_difference_from_the_rule_as_built" not in first


def test_every_other_variant_carries_a_difference_with_an_interval(
    two_types: dict[str, dict[str, Any]],
) -> None:
    records = (record(1, -120.75, 38.25),)
    block = type_inclusion(two_types, records, 0)
    for row in block["variants"][1:]:
        difference = row["contested_difference_from_the_rule_as_built"]
        assert difference["interval_method"] == "newcombe-score-95"
        assert difference["interval_low"] is not None
        assert difference["interval_high"] is not None


def test_every_variant_measures_the_same_record_set(
    two_types: dict[str, dict[str, Any]],
) -> None:
    records = tuple(record(i, -120.75, 38.25) for i in range(1, 6))
    block = type_inclusion(two_types, records, 0)
    for row in block["variants"]:
        assert sum(row["counts"].values()) == len(records)
        for key in ("placed", "contested", "uncovered"):
            assert row[key]["denominator"] == len(records)


def test_dropping_an_included_type_makes_records_uncovered_rather_than_placed(
    two_types: dict[str, dict[str, Any]],
) -> None:
    """The cost of a narrower rule is a false statement about coverage, not a tidier one."""
    records = (record(1, -120.75, 38.25), record(2, -118.75, 38.25))
    block = type_inclusion(two_types, records, 0)
    rows = {row["variant"]: row for row in block["variants"]}
    assert rows["the rule as built"]["counts"] == {
        "placed_in_exactly_one_territory": 2,
        "contested_between_two_or_more": 0,
        "covered_by_no_published_territory": 0,
        "coordinate_not_usable": 0,
    }
    without = rows["without CO-OP"]["counts"]
    assert without["placed_in_exactly_one_territory"] == 1
    assert without["covered_by_no_published_territory"] == 1


def test_reading_an_overlay_type_as_a_territory_raises_the_contested_share() -> None:
    collections = collection(
        feature(1, "Wires IOU", "IOU", square(-121.0, 38.0, -120.5, 38.5)),
        feature(2, "Choice Energy", "CCA", square(-121.0, 38.0, -120.5, 38.5)),
    )
    records = (record(1, -120.75, 38.25),)
    rows = {
        r["variant"]: r for r in type_inclusion(collections, records, 0)["variants"]
    }
    assert rows["the rule as built"]["contested"]["numerator"] == 0
    assert rows["with CCA read as a territory"]["contested"]["numerator"] == 1


def test_a_type_the_publisher_adds_later_is_reported_rather_than_absorbed() -> None:
    collections = collection(
        feature(1, "Wires IOU", "IOU", square(-121.0, 38.0, -120.5, 38.5)),
        feature(2, "Direct Access Co", "ESP", square(-119.0, 38.0, -118.5, 38.5)),
    )
    block = type_inclusion(collections, (record(1, -120.75, 38.25),), 0)
    assert block["unexpected_published_types"] == ["ESP"]
    assert "ESP" in block["published_types_present_in_this_retrieval"]


def test_the_undocumented_type_field_is_stated_in_the_output() -> None:
    block = type_inclusion(
        collection(feature(1, "Wires IOU", "IOU", square(-121.0, 38.0, -120.5, 38.5))),
        (record(1, -120.75, 38.25),),
        0,
    )
    assert (
        "documents none of its values"
        in (block["the_published_type_field_is_undocumented"])
    )


def test_the_variant_list_covers_both_inclusions_and_both_exclusions() -> None:
    labels = [label for label, _ in TYPE_VARIANTS]
    assert labels[0] == "the rule as built"
    for expected in ("CO-OP", "Tribal", "CCA", "ADMIN"):
        assert any(expected in label for label in labels[1:]), expected


def test_the_two_repairs_are_compared_over_the_whole_record_set() -> None:
    collections = collection(
        feature(1, "Bowtie Utility", "IOU", bowtie(-121.0, 38.0, -120.0, 39.0))
    )
    records = tuple(record(i, -120.9, 38.1 + i * 0.1) for i in range(1, 8))
    chosen, _ = load_territories(collections)
    block = repair_comparison(collections, records, chosen)
    assert block["chosen"] == MAKE_VALID
    assert block["alternative"] == BUFFER_ZERO
    changed = block["records_with_a_different_outcome"]
    assert changed["denominator"] == len(records)
    assert sum(row["records"] for row in block["transitions"]) == changed["numerator"]


def test_a_repair_that_drops_a_lobe_is_counted_as_a_disagreement() -> None:
    """`buffer(0)` keeps one lobe of a bowtie and `make_valid` keeps both."""
    collections = collection(
        feature(1, "Bowtie Utility", "IOU", bowtie(-121.0, 38.0, -120.0, 39.0))
    )
    chosen, _ = load_territories(collections)
    alternative, _ = load_territories(collections, strategy=BUFFER_ZERO)
    grid = tuple(
        record(i, -121.0 + 0.05 * (i % 20), 38.0 + 0.05 * (i // 20))
        for i in range(1, 400)
    )
    left = containment_signatures(grid, chosen)
    right = containment_signatures(grid, alternative)
    assert left != right, "the two repairs must disagree somewhere on a bowtie"
    block = repair_comparison(collections, grid, chosen)
    assert block["records_with_a_different_outcome"]["numerator"] > 0
    assert block["placed_difference"]["state"] == "measured"


def test_two_repairs_that_agree_report_no_disagreement() -> None:
    collections = collection(
        feature(1, "Square Utility", "IOU", square(-121.0, 38.0, -120.0, 39.0))
    )
    records = (record(1, -120.5, 38.5), record(2, -119.0, 38.5))
    chosen, _ = load_territories(collections)
    block = repair_comparison(collections, records, chosen)
    assert block["records_with_a_different_outcome"]["numerator"] == 0
    assert block["transitions"] == []
    assert block["placed_difference"]["difference"] == 0.0


def test_the_disagreement_count_is_a_census_not_a_difference_of_totals() -> None:
    """Two totals can match while the records behind them do not."""
    collections = collection(
        feature(1, "Bowtie Utility", "IOU", bowtie(-121.0, 38.0, -120.0, 39.0))
    )
    chosen, _ = load_territories(collections)
    grid = tuple(
        record(i, -121.0 + 0.05 * (i % 20), 38.0 + 0.05 * (i // 20))
        for i in range(1, 400)
    )
    block = repair_comparison(collections, grid, chosen)
    changed = block["records_with_a_different_outcome"]["numerator"]
    placed_gap = abs(
        block["placed_under_the_chosen_repair"]["numerator"]
        - block["placed_under_the_alternative"]["numerator"]
    )
    assert changed >= placed_gap


def test_a_variant_with_no_usable_geography_still_reports_a_denominator() -> None:
    collections = collection(
        feature(1, "Wires IOU", "IOU", square(-121.0, 38.0, -120.5, 38.5))
    )
    records = (record(1, -100.0, 38.25),)
    block = type_inclusion(collections, records, 0)
    first = block["variants"][0]
    assert first["counts"]["coordinate_not_usable"] == 1
    assert first["contested"]["denominator"] == 1


def test_the_classification_underneath_the_variants_is_the_published_one(
    two_types: dict[str, dict[str, Any]],
) -> None:
    """A variant row must be the same measurement the rest of the project makes."""
    records = (record(1, -120.75, 38.25), record(2, -118.75, 38.25))
    territories, _ = load_territories(two_types)
    direct: Placement = classify(records, territories, 0)
    row = type_inclusion(two_types, records, 0)["variants"][0]
    assert row["counts"]["placed_in_exactly_one_territory"] == direct.placed
    assert row["counts"]["contested_between_two_or_more"] == direct.contested


def test_every_kind_of_transition_is_named() -> None:
    """The classifier is tested directly: it decides what the head to head reports."""
    chosen = (None, (), ("A",), ("A", "B"), ("A", "B"), ("A",))
    alternative = (("A",), ("A",), (), ("A", "C"), ("A",), ("A",))
    moves, changed, same_outcome = _transitions(chosen, alternative)
    assert changed == 5
    assert same_outcome == 1, "contested under both, but with a different pair"
    assert moves == {
        ("coordinate_not_usable", "placed_in_exactly_one_territory"): 1,
        ("covered_by_no_published_territory", "placed_in_exactly_one_territory"): 1,
        ("placed_in_exactly_one_territory", "covered_by_no_published_territory"): 1,
        ("contested_between_two_or_more", "contested_between_two_or_more"): 1,
        ("contested_between_two_or_more", "placed_in_exactly_one_territory"): 1,
    }


def test_the_type_census_reads_past_a_feature_it_cannot_parse() -> None:
    """`load_territories` refuses such a feature outright, and runs first. The census
    is defensive about it anyway, because it is the check that would otherwise silently
    report a shorter list of types than the retrieval holds."""
    collections = collection(
        feature(1, "Wires IOU", "IOU", square(-121.0, 38.0, -120.5, 38.5))
    )
    collections["a"]["features"].extend(
        [{"type": "Feature"}, {"properties": {"Type": "  "}}, {"properties": None}]
    )
    assert _types_present(collections) == ["IOU"]


def test_an_outline_no_record_falls_inside_cannot_move_a_published_figure() -> None:
    """The question a reader asks about one named entity, answered as a count.

    Two squares, one of which no record is anywhere near. Whether that entity belongs in
    a retail service territory set is not decided here and is not decidable from this
    data. What is decidable is whether it could be moving anything, and the whole record
    set is placed again without it to answer that rather than reasoning about it.
    """
    collections = collection(
        feature(1, "Wires IOU", "IOU", square(-121.0, 38.0, -120.5, 38.5)),
        feature(2, "Empty Utility", "POU", square(-119.0, 38.0, -118.5, 38.5)),
    )
    territories, _ = load_territories(collections)
    records = (record(1, -120.75, 38.25), record(2, -120.6, 38.4))
    placement = classify(records, territories, 0)
    block = untouched_outlines(placement, records, territories)

    assert block["outlines_no_record_falls_inside"] == ["Empty Utility"]
    assert block["outlines_no_record_falls_inside_count"] == 1
    assert block["outlines_indexed"] == 2
    assert block["records_inside_at_least_one_of_them"]["numerator"] == 0
    assert block["records_inside_at_least_one_of_them"]["denominator"] == 2
    assert block["records_with_a_different_outcome_without_them"]["numerator"] == 0


def test_an_outline_that_does_hold_records_is_not_reported_as_holding_none() -> None:
    """Guard the guard: the count above must be able to come back empty."""
    collections = collection(
        feature(1, "Wires IOU", "IOU", square(-121.0, 38.0, -120.5, 38.5))
    )
    territories, _ = load_territories(collections)
    records = (record(1, -120.75, 38.25),)
    block = untouched_outlines(classify(records, territories, 0), records, territories)
    assert block["outlines_no_record_falls_inside"] == []
    assert block["records_with_a_different_outcome_without_them"]["numerator"] == 0


def test_removing_every_outline_leaves_every_record_inside_none_of_them() -> None:
    """The degenerate case: an empty index cannot be built, and does not need to be."""
    collections = collection(
        feature(1, "Empty Utility", "POU", square(-119.0, 38.0, -118.5, 38.5))
    )
    territories, _ = load_territories(collections)
    records = (record(1, -120.75, 38.25),)
    block = untouched_outlines(classify(records, territories, 0), records, territories)
    assert block["outlines_no_record_falls_inside"] == ["Empty Utility"]
    assert block["records_inside_at_least_one_of_them"]["numerator"] == 0
    assert block["records_with_a_different_outcome_without_them"]["numerator"] == 0
