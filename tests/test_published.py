"""The committed artifacts, checked as published.

`published/` is built by hand from retrievals that are not in git, so CI cannot rebuild
it. What CI can do is read what was committed and hold it to every rule the writer holds
a fresh build to. If a number in `published/measurements.json` were edited by hand, or a
rate lost its denominator, or a coordinate appeared, these tests fail.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from wildfire_service_territory_overlap.artifacts import check_all
from wildfire_service_territory_overlap.report import render

PUBLISHED = Path(__file__).resolve().parents[1] / "published"


def test_the_published_artifact_passes_every_publication_rule(
    published_artifact: dict[str, Any],
) -> None:
    ceiling = max(
        len(published_artifact["territories"]),
        len(published_artifact["attributability_by_fire"]["by_county"]),
        32,
    )
    check_all(published_artifact, max_rows=ceiling)


def test_the_published_artifact_is_the_real_retrieval_not_a_fixture(
    published_artifact: dict[str, Any],
) -> None:
    assert published_artifact["is_fixture"] is False


def test_the_four_outcomes_account_for_every_fire_record(
    published_artifact: dict[str, Any],
) -> None:
    coverage = published_artifact["placement_coverage"]
    assert sum(coverage["counts"].values()) == coverage["fire_records"]
    assert coverage["counts_sum_to_fire_records"] is True


def test_the_coverage_shares_sum_to_one(published_artifact: dict[str, Any]) -> None:
    total = sum(
        rate["rate"] for rate in published_artifact["placement_coverage"]["rates"]
    )
    assert abs(total - 1.0) < 1e-9


def test_placed_and_contested_together_are_every_record_with_a_territory(
    published_artifact: dict[str, Any],
) -> None:
    counts = published_artifact["placement_coverage"]["counts"]
    rep = published_artifact["representativeness"]
    assert rep["placed"]["denominator"] == counts["placed_in_exactly_one_territory"]
    assert rep["contested"]["denominator"] == counts["contested_between_two_or_more"]


def test_every_territory_row_names_a_published_entity_type(
    published_artifact: dict[str, Any],
) -> None:
    allowed = {"IOU", "POU", "CO-OP", "Tribal"}
    for row in published_artifact["territories"]:
        assert row["published_type"] in allowed


def test_no_community_choice_aggregator_became_a_territory(
    published_artifact: dict[str, Any],
) -> None:
    names = " ".join(row["territory"] for row in published_artifact["territories"])
    assert "Clean Power Alliance" not in names
    assert "CleanPowerSF" not in names
    assert {row["published_type"] for row in published_artifact["excluded_types"]} == {
        "CCA",
        "ADMIN",
    }


def test_per_territory_placed_counts_sum_to_the_placed_total(
    published_artifact: dict[str, Any],
) -> None:
    placed = sum(
        row["records_placed_here"] for row in published_artifact["territories"]
    )
    counts = published_artifact["placement_coverage"]["counts"]
    assert placed == counts["placed_in_exactly_one_territory"]


def test_contested_counts_exceed_the_contested_total_because_they_double_count(
    published_artifact: dict[str, Any],
) -> None:
    contested = sum(
        row["records_contested_here"] for row in published_artifact["territories"]
    )
    total = published_artifact["placement_coverage"]["counts"][
        "contested_between_two_or_more"
    ]
    assert contested >= total, (
        "a record inside three outlines is contested for all three, so the per-territory "
        "counts must not be read as a partition"
    )


def test_a_territory_reporting_a_contest_names_who_it_is_with(
    published_artifact: dict[str, Any],
) -> None:
    for row in published_artifact["territories"]:
        if row["records_contested_here"] > 0:
            assert row["contested_with"], row["territory"]
            assert row["contested_with"] == sorted(row["contested_with"])


def test_boundary_bands_are_nested_within_each_territory(
    published_artifact: dict[str, Any],
) -> None:
    for row in published_artifact["territories"]:
        rates = row["boundary_proximity"]["rates"]
        if any(r["state"] != "measured" for r in rates):
            continue
        numerators = [r["numerator"] for r in rates]
        assert numerators == sorted(numerators)


def test_the_published_sensitivity_re_places_the_whole_record_set(
    published_artifact: dict[str, Any],
) -> None:
    total = published_artifact["placement_coverage"]["fire_records"]
    for row in published_artifact["sensitivity"]["type_inclusion"]["variants"]:
        assert sum(row["counts"].values()) == total
        assert row["contested"]["denominator"] == total


def test_the_rule_as_built_variant_reproduces_the_headline(
    published_artifact: dict[str, Any],
) -> None:
    """The sensitivity run and the main pipeline must not have drifted apart."""
    variants = published_artifact["sensitivity"]["type_inclusion"]["variants"]
    reference = variants[0]
    assert reference["variant"] == "the rule as built"
    assert reference["counts"] == published_artifact["placement_coverage"]["counts"]
    assert "contested_difference_from_the_rule_as_built" not in reference
    for row in variants[1:]:
        assert "contested_difference_from_the_rule_as_built" in row


def test_the_published_inclusion_rule_is_the_one_the_variants_measure(
    published_artifact: dict[str, Any],
) -> None:
    block = published_artifact["sensitivity"]["type_inclusion"]
    assert block["rule_as_built"] == ["CO-OP", "IOU", "POU", "Tribal"]
    assert block["unexpected_published_types"] == [], (
        "the publisher shipped a Type this project has never reviewed"
    )
    assert set(block["published_types_present_in_this_retrieval"]) >= {
        "CCA",
        "CO-OP",
        "IOU",
        "POU",
        "Tribal",
    }


def test_the_repair_comparison_is_a_census_over_the_record_set(
    published_artifact: dict[str, Any],
) -> None:
    block = published_artifact["sensitivity"]["repair_strategy"]
    total = published_artifact["placement_coverage"]["fire_records"]
    changed = block["records_with_a_different_outcome"]
    assert changed["denominator"] == total
    assert sum(row["records"] for row in block["transitions"]) == changed["numerator"]
    assert (
        block["placed_under_the_chosen_repair"]["numerator"]
        == (
            published_artifact["placement_coverage"]["counts"][
                "placed_in_exactly_one_territory"
            ]
        )
    )


def test_the_published_repair_delta_is_measured_rather_than_estimated(
    published_artifact: dict[str, Any],
) -> None:
    difference = published_artifact["sensitivity"]["repair_strategy"][
        "placed_difference"
    ]
    assert difference["state"] == "measured"
    assert difference["interval_method"] == "newcombe-score-95"
    assert difference["interval_low"] <= difference["difference"]
    assert difference["difference"] <= difference["interval_high"]


def test_the_incident_and_year_cuts_stay_inside_the_record_set(
    published_artifact: dict[str, Any],
) -> None:
    block = published_artifact["attributability_by_fire"]
    counts = published_artifact["placement_coverage"]["counts"]
    classified = (
        counts["placed_in_exactly_one_territory"]
        + counts["contested_between_two_or_more"]
        + counts["covered_by_no_published_territory"]
    )
    assert sum(r["records_classified"] for r in block["by_incident_year"]) <= classified
    assert block["by_incident"]["records_carrying_an_incident_name"] <= classified
    years = [row["year"] for row in block["by_incident_year"]]
    assert years == sorted(years)


def test_no_year_row_is_compared_against_another_year(
    published_artifact: dict[str, Any],
) -> None:
    """Each year carries its own interval and no difference between years is published."""
    for row in published_artifact["attributability_by_fire"]["by_incident_year"]:
        assert "difference" not in row
        assert row["contested"]["interval_method"] in ("wilson-score-95", "none")


def test_the_county_cut_accounts_for_every_record_in_the_set(
    published_artifact: dict[str, Any],
) -> None:
    block = published_artifact["attributability_by_fire"]
    rows = block["by_county"]
    total = published_artifact["placement_coverage"]["fire_records"]
    assert len(rows) == block["counties_named_in_the_record_set"]
    assert (
        sum(row["records"] for row in rows) + block["records_carrying_no_county_name"]
        == total
    )


def test_counties_are_in_name_order_and_none_is_compared_against_another(
    published_artifact: dict[str, Any],
) -> None:
    rows = published_artifact["attributability_by_fire"]["by_county"]
    names = [row["county"] for row in rows]
    assert names == sorted(names)
    for row in rows:
        assert "difference" not in row
        assert row["contested"]["interval_method"] in ("wilson-score-95", "none")


def test_no_county_row_carries_a_damage_rate(
    published_artifact: dict[str, Any],
) -> None:
    """ADR 0004's refusal holds for a place name as well as for a company name."""
    banned = ("destroyed", "damage", "loss")
    for row in published_artifact["attributability_by_fire"]["by_county"]:
        for key in _every_key(row):
            assert not any(word in key.lower() for word in banned), row["county"]


def _every_key(node: Any) -> list[str]:
    keys: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            keys.append(key)
            keys.extend(_every_key(value))
    elif isinstance(node, list):
        for value in node:
            keys.extend(_every_key(value))
    return keys


def test_an_outline_holding_no_record_is_shown_to_move_nothing(
    published_artifact: dict[str, Any],
) -> None:
    """The count that stands in for an entity-level judgment this project will not make."""
    block = published_artifact["sensitivity"]["untouched_outlines"]
    rows = {row["territory"]: row for row in published_artifact["territories"]}
    named = block["outlines_no_record_falls_inside"]
    assert named == sorted(named)
    assert len(named) == block["outlines_no_record_falls_inside_count"]
    assert block["outlines_indexed"] == len(rows)
    for name in named:
        assert rows[name]["records_placed_here"] == 0
        assert rows[name]["records_contested_here"] == 0
    inside = block["records_inside_at_least_one_of_them"]
    changed = block["records_with_a_different_outcome_without_them"]
    total = published_artifact["placement_coverage"]["fire_records"]
    assert inside["denominator"] == total
    assert changed["denominator"] == total
    assert inside["numerator"] == 0, (
        "an outline reported as holding no record must hold no record"
    )
    assert changed["numerator"] == 0


def test_the_untouched_outline_count_names_no_judgment(
    published_artifact: dict[str, Any],
) -> None:
    """A number, not a classification. The wording is the point of the measurement."""
    note = published_artifact["sensitivity"]["untouched_outlines"]["note"].lower()
    assert "does not establish" in note
    for phrase in ("not a real utility", "should be excluded", "is not a territory"):
        assert phrase not in note


def test_every_measured_rate_has_a_denominator_that_contains_it(
    published_artifact: dict[str, Any],
) -> None:
    for node in _rate_nodes(published_artifact):
        if node["state"] != "measured":
            continue
        assert 0 <= node["numerator"] <= node["denominator"]
        assert node["interval_low"] <= node["rate"] <= node["interval_high"]


def _rate_nodes(node: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(node, dict):
        if "rate" in node and "denominator" in node:
            found.append(node)
        for value in node.values():
            found.extend(_rate_nodes(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(_rate_nodes(value))
    return found


def test_the_published_artifact_actually_contains_rates(
    published_artifact: dict[str, Any],
) -> None:
    """Guard the guard: the rule tests above pass trivially over an artifact with none."""
    assert len(_rate_nodes(published_artifact)) > 50


def test_the_report_matches_the_artifact_it_was_rendered_from(
    published_artifact: dict[str, Any], published_report: str
) -> None:
    assert render(published_artifact) == published_report


# A California coordinate, in both halves. The longitude pattern is the one this check
# has always carried. The latitude pattern is new: the check was named for coordinates
# and could only ever match a longitude, so a latitude reaching a published file was
# invisible to the one test that exists to see it.
CALIFORNIA_LONGITUDE = re.compile(r"-1[12][0-9]\.[0-9]{3,}")
CALIFORNIA_LATITUDE = re.compile(r"\b(?:3[2-9]|4[0-2])\.[0-9]{3,}")


def test_no_coordinate_appears_anywhere_in_the_published_files(
    published_report: str,
) -> None:
    raw = (PUBLISHED / "measurements.json").read_text(encoding="utf-8")
    for where, text in (("measurements.json", raw), ("REPORT.md", published_report)):
        assert not CALIFORNIA_LONGITUDE.search(text), f"a longitude reached {where}"
        assert not CALIFORNIA_LATITUDE.search(text), f"a latitude reached {where}"


def test_the_coordinate_patterns_match_a_coordinate() -> None:
    """Guard the guard.

    A pattern that matches nothing passes this file forever and reports nothing. Both
    halves are run against coordinates of the shape DINS publishes, and against the
    numbers that legitimately appear in these artifacts, so the check is known to be
    able to fire and known not to fire on a rate or a count.
    """
    for longitude in ("-122.6789", "-118.24368", "-124.4096"):
        assert CALIFORNIA_LONGITUDE.search(longitude), longitude
    for latitude in ("38.4567", "34.05223", "41.9981"):
        assert CALIFORNIA_LATITUDE.search(latitude), latitude

    # The numbers these artifacts do carry, none of which is a position.
    for innocent in ("0.6214", "132520", "37.9%", "1000", "-0.0043", "2025"):
        assert not CALIFORNIA_LONGITUDE.search(innocent), innocent
        assert not CALIFORNIA_LATITUDE.search(innocent), innocent

    # A latitude embedded in a longitude must not be read as a latitude.
    assert not CALIFORNIA_LATITUDE.search("-132.4567")


def test_the_published_report_never_ranks_a_utility(published_report: str) -> None:
    """Scanned over the findings, not over the section that states the refusals.

    "What this does not measure" says in plain words that nothing here claims any utility
    is more or less exposed than any other. That sentence has to contain the phrasing it
    disclaims, so the scan stops before it.
    """
    findings, _, refusals = published_report.partition("## What this does not measure")
    assert "more or less exposed than any other" in refusals, (
        "the refusal this scan excludes must actually be stated somewhere"
    )
    lowered = findings.lower()
    for phrase in (
        "most at risk",
        "least at risk",
        "riskiest",
        "safest",
        "worst performing",
        "best performing",
        "highest risk",
        "lowest risk",
        "more exposed than",
        "less exposed than",
    ):
        assert phrase not in lowered, f"the report says {phrase!r}"


def test_the_published_report_disclaims_affiliation(published_report: str) -> None:
    assert "Not affiliated with, endorsed by, or approved by" in published_report


def test_the_published_report_says_what_it_does_not_measure(
    published_report: str,
) -> None:
    assert "Nothing about physical infrastructure" in published_report
    assert "No comparison between utilities" in published_report


def test_no_dash_character_appears_in_the_published_documents(
    published_report: str,
) -> None:
    for dash in ("\u2014", "\u2013"):
        assert dash not in published_report
