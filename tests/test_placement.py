"""Every branch of the classification, over geography designed to reach all of them."""

from __future__ import annotations

from typing import Any

import pytest

from inspected.geometry import Territory
from inspected.placement import (
    BOUNDARY_BANDS_M,
    Placement,
    Record,
    SchemaError,
    assert_columns,
    classify,
    measure_boundary_distances,
    read_records,
)

ALPHA = "Alpha Electric Company"
BETA = "Beta Municipal Utility"
GAMMA = "Gamma Rural Cooperative"


def test_the_hazard_filter_keeps_fire_and_counts_what_it_dropped(
    records: tuple[tuple[Record, ...], int],
) -> None:
    kept, excluded = records
    assert excluded == 1, "the fixture holds one flood record"
    assert len(kept) == 12
    assert all(r.damage is not None for r in kept)


def test_every_fire_record_lands_in_exactly_one_of_the_four_outcomes(
    placement: Placement,
) -> None:
    assert placement.classified == placement.fire_records
    assert placement.placed == 6
    assert placement.contested == 3
    assert placement.uncovered == 1
    assert placement.not_measured == 2


def test_a_contested_record_is_not_awarded_to_either_territory(
    placement: Placement,
) -> None:
    assert placement.tallies[ALPHA].contested == 3
    assert placement.tallies[BETA].contested == 3
    assert placement.tallies[ALPHA].placed + placement.tallies[BETA].placed == 5
    assert placement.contested_groups[(ALPHA, BETA)] == 3


def test_contested_partners_are_recorded_both_ways(placement: Placement) -> None:
    assert placement.tallies[ALPHA].contested_with[BETA] == 3
    assert placement.tallies[BETA].contested_with[ALPHA] == 3


def test_a_missing_coordinate_is_not_measured_rather_than_uncovered() -> None:
    record = Record(1, "Destroyed (>50%)", "X", 2020, None, None)
    assert not record.has_usable_coordinate


@pytest.mark.parametrize(
    ("lon", "lat"),
    [(-100.0, 40.0), (-120.0, 10.0), (-180.0, 38.0), (-120.0, 60.0)],
)
def test_a_coordinate_outside_california_is_refused_not_corrected(
    lon: float, lat: float
) -> None:
    assert not Record(1, "No Damage", "X", 2020, lon, lat).has_usable_coordinate


def test_an_in_state_coordinate_is_usable() -> None:
    assert Record(1, "No Damage", "X", 2020, -121.0, 38.5).has_usable_coordinate


def test_a_record_inside_no_published_outline_is_uncovered(
    placement: Placement,
) -> None:
    assert placement.uncovered == 1
    assert placement.destroyed_uncovered == 1


def test_a_repaired_bowtie_still_holds_its_record(placement: Placement) -> None:
    assert placement.tallies[GAMMA].placed == 1


def test_an_excluded_entity_type_never_becomes_a_territory(
    territories: tuple[Territory, ...],
) -> None:
    names = {t.name for t in territories}
    assert "Delta Choice Energy" not in names, (
        "a CCA overlays a territory, it is not one"
    )
    assert names == {ALPHA, BETA, GAMMA}


def test_boundary_bands_measure_distance_from_the_published_edge(
    placement: Placement,
) -> None:
    alpha = placement.tallies[ALPHA]
    assert alpha.distance_state == "measured"
    # One fixture record sits about 87 m inside Alpha's western edge.
    assert alpha.within_band[100] == 1
    assert alpha.within_band[1000] == 1
    assert set(alpha.within_band) == set(BOUNDARY_BANDS_M)


def test_bands_are_nested_so_a_wider_band_never_holds_fewer(
    placement: Placement,
) -> None:
    for tally in placement.tallies.values():
        if tally.distance_state != "measured":
            continue
        counts = [tally.within_band[band] for band in sorted(BOUNDARY_BANDS_M)]
        assert counts == sorted(counts)


def test_a_territory_with_no_placements_has_no_bands_rather_than_zeroes(
    territories: tuple[Territory, ...],
) -> None:
    empty = classify((), territories, 0)
    measure_boundary_distances(empty, territories)
    for tally in empty.tallies.values():
        assert tally.distance_state == "not_measured"
        assert tally.within_band == {}


def test_classify_with_no_usable_coordinates_still_returns_a_result(
    territories: tuple[Territory, ...],
) -> None:
    result = classify((Record(1, "No Damage", "X", 2020, None, None),), territories, 0)
    assert result.not_measured == 1
    assert result.placed == 0
    assert result.classified == 1


def test_largest_incident_breaks_ties_on_the_name_not_on_dict_order(
    placement: Placement,
) -> None:
    alpha = placement.tallies[ALPHA]
    largest = alpha.largest_incident
    assert largest is not None
    assert largest == ("SAMPLE ONE", 3)


def test_a_territory_with_no_incidents_reports_none(
    territories: tuple[Territory, ...],
) -> None:
    empty = classify((), territories, 0)
    assert empty.tallies[ALPHA].largest_incident is None


def test_years_are_counted_from_the_published_start_date(placement: Placement) -> None:
    assert placement.years[2020] == 3
    assert sum(placement.years.values()) == placement.fire_records


def test_a_row_missing_a_column_is_refused_not_read_as_a_value() -> None:
    rows: list[dict[str, Any]] = [{"OBJECTID": 1, "DAMAGE": "No Damage"}]
    with pytest.raises(SchemaError, match="HAZARDTYPE"):
        assert_columns(rows)


def test_an_empty_retrieval_is_refused() -> None:
    with pytest.raises(SchemaError, match="no rows"):
        assert_columns([])


def test_read_records_refuses_a_file_without_the_hazard_column() -> None:
    rows = [
        {
            "OBJECTID": 1,
            "DAMAGE": "No Damage",
            "INCIDENTNAME": "X",
            "INCIDENTSTARTDATE": 0,
            "LATITUDE": 38.0,
            "LONGITUDE": -121.0,
        }
    ]
    with pytest.raises(SchemaError):
        read_records(rows)


def test_a_non_numeric_coordinate_is_refused_rather_than_coerced() -> None:
    rows = [
        {
            "OBJECTID": 1,
            "DAMAGE": "No Damage",
            "HAZARDTYPE": "Fire",
            "INCIDENTNAME": "X",
            "INCIDENTSTARTDATE": 1_600_000_000_000,
            "LATITUDE": "38.0",
            "LONGITUDE": True,
        }
    ]
    kept, _ = read_records(rows)
    assert kept[0].lat is None and kept[0].lon is None
    assert not kept[0].has_usable_coordinate


def test_a_missing_start_date_leaves_the_year_unknown_rather_than_guessed() -> None:
    rows = [
        {
            "OBJECTID": 1,
            "DAMAGE": "No Damage",
            "HAZARDTYPE": "Fire",
            "INCIDENTNAME": "X",
            "INCIDENTSTARTDATE": None,
            "LATITUDE": 38.0,
            "LONGITUDE": -121.0,
        }
    ]
    kept, _ = read_records(rows)
    assert kept[0].year is None
