"""The publication rules, each exercised against something that should break it.

A gate nobody has watched fail is not a gate. Every rule in :mod:`inspected.artifacts`
gets an input here that must be refused, as well as one that must pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from inspected.artifacts import (
    PublicationRefused,
    assert_aggregate_only,
    assert_differences_carry_intervals,
    assert_no_locating_fields,
    assert_no_ranking,
    assert_rates_are_denominated,
    assert_territories_sorted_by_name,
    check_all,
    serialise,
    write_json,
)
from inspected.intervals import Rate


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
