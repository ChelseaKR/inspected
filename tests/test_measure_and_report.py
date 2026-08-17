"""The measurements over the fixture geography, and the document rendered from them."""

from __future__ import annotations

from typing import Any

import pytest

from inspected import measure, report
from inspected.geometry import Territory
from inspected.placement import Placement, classify
from inspected.report import NOT_MEASURED, pct

ALPHA = "Alpha Electric Company"


def test_coverage_counts_add_up_to_the_record_set(placement: Placement) -> None:
    coverage = measure.placement_coverage(placement)
    counts = coverage["counts"]
    assert sum(counts.values()) == coverage["fire_records"]
    assert coverage["counts_sum_to_fire_records"] is True


def test_every_coverage_rate_is_taken_over_the_whole_record_set(
    placement: Placement,
) -> None:
    coverage = measure.placement_coverage(placement)
    for rate in coverage["rates"]:
        assert rate["denominator"] == coverage["fire_records"]


def test_the_hazard_filter_is_reported_rather_than_hidden(placement: Placement) -> None:
    assert measure.placement_coverage(placement)["excluded_by_hazard_filter"] == 1


def test_representativeness_compares_populations_not_utilities(
    placement: Placement,
) -> None:
    rep = measure.representativeness(placement)
    assert rep["placed"]["denominator"] == placement.placed
    assert rep["contested"]["denominator"] == placement.contested
    assert rep["difference"]["interval_method"] in ("newcombe-score-95", "none")
    assert rep["difference"]["left"]["label"].endswith("among placed records")
    assert rep["difference"]["right"]["label"].endswith("among contested records")


def test_an_empty_uncovered_population_is_not_measured_rather_than_zero(
    territories: tuple[Territory, ...],
) -> None:
    empty = classify((), territories, 0)
    rep = measure.representativeness(empty)
    assert rep["uncovered"]["state"] == "not_measured"
    assert rep["uncovered"]["rate"] is None


def test_territory_rows_are_alphabetical_and_one_per_territory(
    placement: Placement, territories: tuple[Territory, ...]
) -> None:
    rows = measure.territory_rows(placement, territories)
    names = [r["territory"] for r in rows]
    assert names == sorted(names)
    assert len(rows) == len(territories)


def test_no_territory_row_carries_a_damage_rate(
    placement: Placement, territories: tuple[Territory, ...]
) -> None:
    """The rule this project is built around, asserted against the output."""
    banned = {"destroyed", "damage", "loss", "damaged"}
    for row in measure.territory_rows(placement, territories):
        for key in _all_keys(row):
            assert not any(word in key.lower() for word in banned), (
                f"{row['territory']} carries a key named {key}. A damage rate for a "
                "territory is a statement about a utility that the data cannot support."
            )


def _all_keys(node: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            keys.append(key)
            keys.extend(_all_keys(value))
    elif isinstance(node, list):
        for value in node:
            keys.extend(_all_keys(value))
    return keys


def test_incident_concentration_is_a_within_territory_share(
    placement: Placement, territories: tuple[Territory, ...]
) -> None:
    rows = {r["territory"]: r for r in measure.territory_rows(placement, territories)}
    alpha = rows[ALPHA]["incident_concentration"]
    assert alpha["largest_incident"] == "SAMPLE ONE"
    assert alpha["share"]["denominator"] == placement.tallies[ALPHA].placed
    assert alpha["share"]["numerator"] == 3


def test_a_territory_with_nothing_placed_reports_not_measured(
    territories: tuple[Territory, ...],
) -> None:
    empty = classify((), territories, 0)
    rows = measure.territory_rows(empty, territories)
    for row in rows:
        assert row["incident_concentration"]["largest_incident"] is None
        assert row["incident_concentration"]["share"]["state"] == "not_measured"
        for band in row["boundary_proximity"]["rates"]:
            assert band["state"] == "not_measured"


def test_contested_groups_are_counts_and_are_capped(placement: Placement) -> None:
    groups = measure.contested_groups(placement, limit=1)
    assert len(groups) == 1
    assert groups[0]["records"] == 3
    assert set(groups[0]["territories"]) == {ALPHA, "Beta Municipal Utility"}


def test_the_geometry_ledger_sizes_the_repair_rather_than_only_naming_it(
    placement: Placement,
    territories: tuple[Territory, ...],
    unusable: tuple[Territory, ...],
) -> None:
    ledger = measure.geometry_ledger(placement, territories, unusable)
    assert ledger["territories_repaired"] == 1
    assert ledger["repaired"] == ["Gamma Rural Cooperative"]
    share = ledger["records_placed_via_repaired_geometry"]
    assert share["numerator"] == 1
    assert share["denominator"] == placement.placed


def test_excluded_types_explain_themselves() -> None:
    rows = measure.excluded_type_note()
    assert {r["published_type"] for r in rows} == {"CCA", "ADMIN"}
    assert all(len(r["reason"]) > 40 for r in rows)


def test_years_are_ordered_and_complete(placement: Placement) -> None:
    rows = measure.years(placement)
    assert [r["year"] for r in rows] == sorted(r["year"] for r in rows)
    assert sum(r["records"] for r in rows) == placement.fire_records


def test_a_measurement_that_could_not_be_made_never_prints_as_a_percentage() -> None:
    assert pct(None) == NOT_MEASURED


def test_a_tiny_but_real_share_does_not_print_as_flat_zero() -> None:
    assert pct(0.0) == "0.0%"
    assert pct(0.0000029) != "0.0%"
    assert pct(0.5) == "50.0%"


def test_a_not_measured_rate_renders_as_words_in_a_table_row() -> None:
    node = {"label": "x", "state": "not_measured", "numerator": 0}
    assert NOT_MEASURED in report.rate_line(node)


@pytest.mark.parametrize(
    "heading",
    [
        "Can the join be made at all",
        "Do the records that can be attributed look like the ones that cannot",
        "Every published territory, in name order",
        "Where the published boundaries overlap",
        "The published polygons, as they arrived",
        "What this does not measure",
    ],
)
def test_the_report_carries_every_section(published_report: str, heading: str) -> None:
    assert heading in published_report


def test_the_report_opens_with_the_unaffiliated_line(published_report: str) -> None:
    head = published_report.split("## ")[0]
    assert "Not affiliated with, endorsed by, or approved by CAL FIRE" in head
    assert "any electric utility" in head
