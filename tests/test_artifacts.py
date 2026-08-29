"""The publication rules, each exercised against something that should break it.

A gate nobody has watched fail is not a gate. Every rule in :mod:`wildfire_service_territory_overlap.artifacts`
gets an input here that must be refused, as well as one that must pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from wildfire_service_territory_overlap.artifacts import (
    BY_NAME,
    BY_SIZE,
    DECLARED,
    ORDERINGS,
    PublicationRefused,
    _walk,
    assert_aggregate_only,
    assert_differences_carry_intervals,
    assert_no_locating_fields,
    assert_no_ranking,
    assert_rates_are_denominated,
    assert_territories_sorted_by_name,
    check_all,
    generic_path,
    serialise,
    write_json,
)
from wildfire_service_territory_overlap.intervals import Rate


def measured() -> dict[str, Any]:
    return Rate.of("a share", 3, 12).as_dict()


def unmeasured() -> dict[str, Any]:
    return Rate.not_measured("a share", reason="nothing to divide").as_dict()


def test_a_well_formed_rate_passes() -> None:
    assert_rates_are_denominated({"x": measured()})
    assert_rates_are_denominated({"x": unmeasured()})


@pytest.mark.parametrize(
    "dropped",
    ["numerator", "denominator", "interval_low", "interval_high", "interval_method"],
)
def test_a_rate_missing_any_required_field_is_refused(dropped: str) -> None:
    node = measured()
    del node[dropped]
    with pytest.raises(PublicationRefused, match="missing"):
        assert_rates_are_denominated({"x": node})


def test_a_rate_with_a_value_and_no_denominator_is_refused() -> None:
    node = measured()
    node["denominator"] = 0
    with pytest.raises(PublicationRefused, match="not zero percent"):
        assert_rates_are_denominated({"x": node})


def test_a_measured_rate_with_no_interval_is_refused() -> None:
    node = measured()
    node["interval_low"] = None
    with pytest.raises(PublicationRefused, match="missing interval_low"):
        assert_rates_are_denominated({"x": node})


def test_a_measured_rate_with_no_interval_method_is_refused() -> None:
    node = measured()
    node["interval_method"] = "none"
    with pytest.raises(PublicationRefused, match="names no interval method"):
        assert_rates_are_denominated({"x": node})


def test_a_not_measured_rate_carrying_a_zero_is_refused() -> None:
    node = unmeasured()
    node["rate"] = 0.0
    with pytest.raises(PublicationRefused, match="not a zero"):
        assert_rates_are_denominated({"x": node})


def test_a_rate_nested_deep_in_a_list_is_still_checked() -> None:
    node = measured()
    del node["denominator"]
    with pytest.raises(PublicationRefused):
        assert_rates_are_denominated({"a": [{"b": [{"c": node}]}]})


def test_a_difference_without_an_interval_is_refused() -> None:
    with pytest.raises(PublicationRefused, match="missing interval_low"):
        assert_differences_carry_intervals(
            {"d": {"difference": 0.2, "state": "measured"}}
        )


def test_a_measured_difference_with_a_null_interval_is_refused() -> None:
    payload = {
        "difference": 0.2,
        "interval_low": None,
        "interval_high": 0.3,
        "interval_method": "newcombe-score-95",
        "state": "measured",
    }
    with pytest.raises(PublicationRefused, match="no interval"):
        assert_differences_carry_intervals({"d": payload})


def test_a_prose_field_called_difference_is_not_mistaken_for_one() -> None:
    assert_differences_carry_intervals({"d": {"difference": "a sentence about it"}})


@pytest.mark.parametrize(
    "key", ["latitude", "LONGITUDE", "Address", "apn", "siteaddress", "x", "objectid"]
)
def test_anything_that_could_place_a_structure_is_refused(key: str) -> None:
    with pytest.raises(PublicationRefused, match="never a position"):
        assert_no_locating_fields({"rows": [{key: 1}]})


def test_a_key_that_merely_contains_a_forbidden_word_is_allowed() -> None:
    assert_no_locating_fields({"geometry_state": "repaired", "geometry_note": "n"})


def test_a_collection_longer_than_the_ceiling_is_refused() -> None:
    with pytest.raises(PublicationRefused, match="record listing under another name"):
        assert_aggregate_only({"rows": list(range(11))}, max_rows=10)


def test_a_collection_at_the_ceiling_passes() -> None:
    assert_aggregate_only({"rows": list(range(10))}, max_rows=10)


@pytest.mark.parametrize("key", ["rank", "SCORE", "grade", "worst", "rating"])
def test_a_key_that_rates_a_utility_is_refused(key: str) -> None:
    with pytest.raises(PublicationRefused, match="does not rate, rank, or score"):
        assert_no_ranking({"rows": [{key: 1}]})


def test_territory_rows_out_of_name_order_are_refused() -> None:
    with pytest.raises(PublicationRefused, match="not in name order"):
        assert_territories_sorted_by_name(
            [{"territory": "Zulu"}, {"territory": "Alpha"}]
        )


def test_territory_rows_in_name_order_pass() -> None:
    assert_territories_sorted_by_name([{"territory": "Alpha"}, {"territory": "Zulu"}])


def test_check_all_runs_every_rule() -> None:
    tree = {"territories": [{"territory": "Alpha", "share": measured()}]}
    check_all(tree, max_rows=5)


def test_check_all_ignores_a_territories_key_that_is_not_a_list() -> None:
    check_all({"territories": "none indexed"}, max_rows=5)


def test_serialise_is_stable_for_the_same_tree() -> None:
    tree = {"b": 1, "a": {"d": 2, "c": 3}}
    assert serialise(tree) == serialise({"a": {"c": 3, "d": 2}, "b": 1})
    assert serialise(tree).endswith("\n")


def test_a_refused_artifact_is_not_written_at_all(tmp_path: Path) -> None:
    target = tmp_path / "out" / "measurements.json"
    bad = measured()
    del bad["denominator"]
    with pytest.raises(PublicationRefused):
        write_json({"share": bad}, target, max_rows=5)
    assert not target.exists(), "a refused artifact must leave nothing behind"


def test_a_clean_artifact_is_written(tmp_path: Path) -> None:
    target = tmp_path / "out" / "measurements.json"
    written = write_json({"share": measured()}, target, max_rows=5)
    assert written.read_text(encoding="utf-8").startswith("{")


def _coverage_tree(rows: list[dict[str, Any]], total: int) -> dict[str, Any]:
    return {
        "placement_coverage": {"counts": {"contested_between_two_or_more": total}},
        "contested_groups": rows,
    }


def test_a_contested_groups_table_that_accounts_for_every_record_passes() -> None:
    check_all(_coverage_tree([{"records": 30}, {"records": 20}], 50), max_rows=32)


def test_a_truncated_contested_groups_table_is_refused() -> None:
    """The cut issue #22 reports, caught before anything is written.

    `assert_aggregate_only` cannot see this: its ceiling is never below 32 and the cap
    is 25, so the only length rule in the module is numerically incapable of firing on
    this collection.
    """
    with pytest.raises(PublicationRefused, match="15 short"):
        check_all(_coverage_tree([{"records": 30}, {"records": 20}], 65), max_rows=32)


def test_a_contested_groups_table_longer_than_its_total_is_also_refused() -> None:
    """Over as well as under. A double count is a wrong number, not a safe one."""
    with_extra = [{"records": 30}, {"records": 20}, {"records": 5}]
    with pytest.raises(PublicationRefused, match="55 of 50"):
        check_all(_coverage_tree(with_extra, 50), max_rows=32)


def test_the_contested_check_stays_quiet_when_there_is_nothing_to_compare() -> None:
    """A tree without the coverage block is not an artifact this rule can judge."""
    check_all({"contested_groups": [{"records": 3}]}, max_rows=32)
    check_all({"placement_coverage": {"counts": {}}}, max_rows=32)
    check_all({"placement_coverage": "not a block"}, max_rows=32)


def test_a_collection_nobody_declared_an_order_for_is_refused() -> None:
    """Fail closed on arrival. A new collection cannot reach a reader undeclared."""
    with pytest.raises(PublicationRefused, match="nothing has declared"):
        check_all({"newly_added_rows": [{"a": 1}, {"a": 2}]}, max_rows=32)


def test_a_name_ordered_collection_out_of_name_order_is_refused() -> None:
    with pytest.raises(PublicationRefused, match="declared in name order"):
        check_all(
            {"territories": [{"territory": "Zulu"}, {"territory": "Alpha"}]},
            max_rows=32,
        )


def test_contested_groups_out_of_size_order_are_refused() -> None:
    rows = [
        {"records": 10, "territories": ["A", "B"]},
        {"records": 90, "territories": ["C", "D"]},
    ]
    with pytest.raises(PublicationRefused, match="declared in size order"):
        check_all(_coverage_tree(rows, 100), max_rows=32)


def test_contested_groups_in_size_order_pass() -> None:
    rows = [
        {"records": 90, "territories": ["C", "D"]},
        {"records": 10, "territories": ["A", "B"]},
    ]
    check_all(_coverage_tree(rows, 100), max_rows=32)


def test_a_row_missing_the_field_its_order_runs_on_is_refused_not_crashed() -> None:
    """A checker that raises KeyError reads as a bug in the checker, not in the data."""
    with pytest.raises(PublicationRefused, match="does not carry it"):
        check_all(
            {"territories": [{"territory": "Alpha"}, {"name": "Beta"}]}, max_rows=32
        )


def test_a_single_row_collection_has_no_order_to_get_wrong() -> None:
    check_all({"territories": [{"territory": "Alpha"}]}, max_rows=32)


def test_every_declared_exception_to_name_order_says_why() -> None:
    """The half that keeps the ledger from becoming a way to opt out of the rule.

    A collection can be published in an order other than by name, and three are. Each
    has to carry the reason next to the declaration, in words, long enough to argue
    with.
    """
    exceptions = {
        path: reason
        for path, (kind, reason) in ORDERINGS.items()
        if kind in (DECLARED, BY_SIZE)
    }
    assert exceptions, "the ledger records no exception, so this test checks nothing"
    for path, reason in exceptions.items():
        assert len(reason) > 60, f"{path} is excused in one line. Say why."
    by_name = [path for path, (kind, _) in ORDERINGS.items() if kind == BY_NAME]
    assert len(by_name) > len(exceptions), "name order must remain the rule"


def test_the_ordering_ledger_describes_collections_that_are_actually_published(
    published_artifact: dict[str, Any],
) -> None:
    """No entry outlives the collection it describes, and none is missing.

    The same shape as the CodeQL acceptance gate: a ledger that can only grow becomes a
    list of things that used to be true. Every path declared here must appear in the
    published artifact, and every collection in the published artifact must be declared.
    """
    published: set[str] = set()
    for path, node in _walk(published_artifact):
        if isinstance(node, list):
            published.add(generic_path(path))
    assert published, "the published artifact carries no collection at all"
    assert published - set(ORDERINGS) == set(), "an undeclared published collection"
    assert set(ORDERINGS) - published == set(), (
        "ORDERINGS declares an order for a collection the artifact no longer carries"
    )
