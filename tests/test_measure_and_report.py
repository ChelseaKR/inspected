"""The measurements over the fixture geography, and the document rendered from them."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from wildfire_service_territory_overlap import measure, report
from wildfire_service_territory_overlap.artifacts import PublicationRefused, check_all
from wildfire_service_territory_overlap.cli import build
from wildfire_service_territory_overlap.geometry import Territory
from wildfire_service_territory_overlap.placement import Placement, Record, classify
from wildfire_service_territory_overlap.report import NOT_MEASURED, pct

ROOT = Path(__file__).resolve().parents[1]

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


def test_contested_groups_are_counts(placement: Placement) -> None:
    """The fixture geography holds exactly one overlapping combination.

    This test used to be called "and are capped" and passed `limit=1`, which over one
    combination is a slice that removes nothing. It exercised no cap. The cap is
    exercised below, against a placement built for it, because the fixtures cannot
    produce a second combination and a test cannot check what its data cannot express.
    """
    groups = measure.contested_groups(placement, limit=1)
    assert len(placement.contested_groups) == 1, (
        "the fixtures produce one combination, so limit=1 here cuts nothing"
    )
    assert len(groups) == 1
    assert groups[0]["records"] == 3
    assert set(groups[0]["territories"]) == {ALPHA, "Beta Municipal Utility"}


def _placement_with_many_combinations(count: int) -> Placement:
    """A placement carrying `count` overlapping combinations, largest first.

    Combination i holds `count - i` records, so the total is the triangular number and
    any cap below `count` drops a known number of records.
    """
    groups: Counter[tuple[str, ...]] = Counter(
        {
            (f"Territory {i:03d}", f"Territory {i:03d} West"): count - i
            for i in range(count)
        }
    )
    return Placement(
        fire_records=sum(groups.values()),
        excluded_by_hazard=0,
        contested=sum(groups.values()),
        contested_groups=groups,
    )


def test_the_cap_cuts_records_out_of_the_table_when_it_bites() -> None:
    """The reproduction from issue #22, run against the shipped function.

    Thirty combinations against a cap of 25: twenty five rows come back, they account
    for 450 of 465 contested records, and fifteen records are in no row.
    """
    placement = _placement_with_many_combinations(30)
    rows = measure.contested_groups(placement)
    assert len(placement.contested_groups) == 30
    assert len(rows) == 25
    assert sum(row["records"] for row in rows) == 450
    assert placement.contested == 465


def test_a_capped_contested_table_is_refused_before_it_can_be_published() -> None:
    """The cut above, taken to the writer, which is where it has to stop.

    Nothing in the rendering says how many combinations were dropped or how many records
    went with them, so the artifact must not be written at all.
    """
    placement = _placement_with_many_combinations(30)
    tree = {
        "placement_coverage": {
            "counts": {"contested_between_two_or_more": placement.contested}
        },
        "contested_groups": measure.contested_groups(placement),
    }
    with pytest.raises(PublicationRefused, match="450 of 465 contested records"):
        check_all(tree, max_rows=64)


def test_an_uncapped_contested_table_over_the_same_placement_passes() -> None:
    """The same data, nothing dropped, publishes. The rule is about the cut, not the size."""
    placement = _placement_with_many_combinations(30)
    tree = {
        "placement_coverage": {
            "counts": {"contested_between_two_or_more": placement.contested}
        },
        "contested_groups": measure.contested_groups(placement, limit=30),
    }
    check_all(tree, max_rows=64)


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


def test_the_incident_split_accounts_for_every_incident(placement: Placement) -> None:
    block = measure.attributability_by_fire(placement)["by_incident"]
    distinct = block["distinct_incidents"]
    counted = (
        block["every_record_contested"]["numerator"]
        + block["no_record_contested"]["numerator"]
        + block["split_both_ways"]["numerator"]
    )
    assert counted == distinct
    assert block["one_way_or_the_other"]["numerator"] == (
        block["every_record_contested"]["numerator"]
        + block["no_record_contested"]["numerator"]
    )
    for key in ("every_record_contested", "no_record_contested", "split_both_ways"):
        assert block[key]["denominator"] == distinct


def test_a_year_whose_records_could_not_be_placed_is_not_measured(
    placement: Placement,
) -> None:
    """The fixture holds a year of records with unusable coordinates."""
    rows = measure.attributability_by_fire(placement)["by_incident_year"]
    unplaceable = [r for r in rows if r["records_classified"] == 0]
    assert unplaceable, "the fixture must carry a year with nothing classified"
    for row in unplaceable:
        assert row["contested"]["state"] == "not_measured"
        assert row["contested"]["rate"] is None
        assert row["records"] > 0


def test_the_year_rows_carry_both_denominators(placement: Placement) -> None:
    for row in measure.attributability_by_fire(placement)["by_incident_year"]:
        assert row["records_classified"] <= row["records"]
        if row["contested"]["state"] == "measured":
            assert row["contested"]["denominator"] == row["records_classified"]


def test_no_trend_is_drawn_through_the_years(placement: Placement) -> None:
    """A direction over time would be a claim the single boundary snapshot cannot make."""
    block = measure.attributability_by_fire(placement)
    assert "one retrieval" in block["no_trend_is_published"]
    banned = {"trend", "slope", "direction", "improving", "worsening"}
    for row in block["by_incident_year"]:
        for key in _all_keys(row):
            assert not any(word in key.lower() for word in banned), key


def test_an_interval_never_prints_its_two_ends_as_the_same_number() -> None:
    """`0.7% to 0.7%` reads as certainty. The precision rises until the ends differ."""
    assert report.span(0.006555, 0.007464) == "0.66% to 0.75%"
    assert report.span(0.619, 0.624) == "61.9% to 62.4%"
    assert report.span(0.0, 0.000029) == "0.000% to 0.003%"
    assert report.span(0.0, 0.0000041) == "0.0000% to 0.0004%"


def test_two_ends_that_really_are_the_same_still_print() -> None:
    assert report.span(1.0, 1.0) == "100.0% to 100.0%"


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
        "Is the unattributable share a property of the data or of the fire",
        "Every published territory, in name order",
        "Where the published boundaries overlap",
        "The published polygons, as they arrived",
        "What the repair is worth",
        "What the inclusion rule is worth",
        "The outlines that hold nothing",
        "What this does not measure",
    ],
)
def test_the_report_carries_every_section(published_report: str, heading: str) -> None:
    assert heading in published_report


def test_the_report_opens_with_the_unaffiliated_line(published_report: str) -> None:
    head = published_report.split("## ")[0]
    assert "Not affiliated with, endorsed by, or approved by CAL FIRE" in head
    assert "any electric utility" in head


def test_county_rows_are_in_name_order_and_carry_both_denominators(
    placement: Placement,
) -> None:
    block = measure.attributability_by_fire(placement)
    rows = block["by_county"]
    names = [row["county"] for row in rows]
    assert names == sorted(names), (
        "ordering counties by their contested share would be a league table of places"
    )
    assert len(rows) == block["counties_named_in_the_record_set"]
    for row in rows:
        assert row["records_classified"] <= row["records"]
        if row["contested"]["state"] == "measured":
            assert row["contested"]["denominator"] == row["records_classified"]


def test_the_county_cut_accounts_for_every_record_or_says_it_cannot(
    placement: Placement,
) -> None:
    block = measure.attributability_by_fire(placement)
    counted = sum(row["records"] for row in block["by_county"])
    assert counted + block["records_carrying_no_county_name"] == placement.fire_records


def test_no_county_row_carries_a_damage_rate(placement: Placement) -> None:
    """ADR 0004's refusal, restated for a place name instead of a company name."""
    banned = {"destroyed", "damage", "loss", "damaged"}
    for row in measure.attributability_by_fire(placement)["by_county"]:
        for key in _all_keys(row):
            assert not any(word in key.lower() for word in banned), (
                f"{row['county']} carries a key named {key}"
            )


def test_a_county_whose_records_could_not_be_placed_is_not_measured(
    territories: tuple[Territory, ...],
) -> None:
    unplaceable = (Record(1, "No Damage", "X", "Sample County East", 2020, None, None),)
    block = measure.attributability_by_fire(classify(unplaceable, territories, 0))
    row = block["by_county"][0]
    assert row["records"] == 1
    assert row["records_classified"] == 0
    assert row["contested"]["state"] == "not_measured"
    assert row["contested"]["rate"] is None


def _fixture_tree(tmp_path: Path) -> dict[str, Any]:
    artifact_path, _ = build(
        dins_path=ROOT / "fixtures" / "dins_sample.json",
        iou_pou_path=ROOT / "fixtures" / "else_iou_pou_sample.geojson",
        other_path=ROOT / "fixtures" / "else_other_sample.geojson",
        counties_path=ROOT / "fixtures" / "county_boundaries_sample.geojson",
        out_dir=tmp_path / "out",
        is_fixture=True,
    )
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def test_contested_group_rows_carry_edge_bands_passing_the_publication_rules(
    tmp_path: Path,
) -> None:
    tree = _fixture_tree(tmp_path)
    rows = tree["contested_groups"]
    assert rows, "the fixture must produce at least one overlapping combination"
    ceiling = max(len(tree["territories"]), 32)
    check_all(tree, max_rows=ceiling)
    for row in rows:
        proximity = row["boundary_proximity"]
        for rate in proximity["rates"]:
            assert rate["denominator"] == row["records"]


def test_the_report_renders_the_widened_overlap_table_when_bands_exist(
    tmp_path: Path,
) -> None:
    text = report.render(_fixture_tree(tmp_path))
    section = text.split("## Where the published boundaries overlap")[1]
    assert "Within 250 m of an edge" in section
    assert "thin seam" in section


def test_the_artifact_carries_both_new_measurement_blocks(tmp_path: Path) -> None:
    tree = _fixture_tree(tmp_path)
    agreement = tree["coordinate_county_agreement"]
    assert "question" in agreement
    for key in (
        "records_compared",
        "agreed",
        "disagreed",
        "matched_no_county",
        "unmatchable_label",
    ):
        node = agreement[key]
        assert {"numerator", "denominator", "state"} <= set(node), key
    categories = tree["representativeness_by_category"]
    assert categories, "the fixture carries STRUCTURECATEGORY values"
    names = [row["structure_category"] for row in categories]
    assert names == sorted(names)


def test_the_report_renders_the_new_sections(tmp_path: Path) -> None:
    text = report.render(_fixture_tree(tmp_path))
    assert "## Does the coordinate agree with the recorded county" in text
    assert "Counted, never corrected." in text
    assert "## The placed and contested populations, by structure class" in text


def test_a_county_disagreement_is_measured_not_corrected(tmp_path: Path) -> None:
    """The fixture holds a record whose label says West and whose coordinate is East."""
    tree = _fixture_tree(tmp_path)
    block = tree["coordinate_county_agreement"]
    by_county = {row["county"]: row for row in block["by_county"]}
    west = by_county["Sample County West"]
    east = by_county["Sample County East"]
    assert east["disagreed"]["state"] == "measured"
    assert west["disagreed"]["state"] == "measured"
    assert block["unmatchable_label"]["numerator"] == 0


def test_contested_groups_come_out_in_size_order_and_not_in_name_order() -> None:
    """Data built so the two orders disagree, because otherwise this proves nothing.

    The earlier cap tests happen to number their combinations so that name order and
    size order coincide, which means changing the sort key in `contested_groups` passes
    them both. Here the names ascend while the counts descend, so a name sort and a size
    sort produce opposite tables and only one of them is the declared order.
    """
    groups: Counter[tuple[str, ...]] = Counter(
        {("Shared Outline", f"Territory {i:03d}"): i + 1 for i in range(5)}
    )
    total = sum(groups.values())
    placement = Placement(
        fire_records=total,
        excluded_by_hazard=0,
        contested=total,
        contested_groups=groups,
    )
    rows = measure.contested_groups(placement)

    assert [row["records"] for row in rows] == [5, 4, 3, 2, 1]
    assert rows[0]["territories"] == ["Shared Outline", "Territory 004"]
    names = [row["territories"] for row in rows]
    assert names != sorted(names), "the fixture no longer distinguishes the two orders"

    # And the publication rule agrees that this is the order it declares.
    check_all(
        {
            "placement_coverage": {"counts": {"contested_between_two_or_more": total}},
            "contested_groups": rows,
        },
        max_rows=32,
    )


def test_a_size_tie_is_broken_on_the_names_so_the_order_is_total() -> None:
    """Two combinations of equal size must not depend on dict insertion order."""
    groups: Counter[tuple[str, ...]] = Counter(
        {("A", "Z"): 7, ("A", "B"): 7, ("A", "M"): 7}
    )
    placement = Placement(
        fire_records=21, excluded_by_hazard=0, contested=21, contested_groups=groups
    )
    rows = measure.contested_groups(placement)
    assert [row["territories"] for row in rows] == [["A", "B"], ["A", "M"], ["A", "Z"]]
