"""The measurements, and the two the data does not support.

What is published
-----------------
1. **Placement coverage.** Of every wildfire damage-inspection record, the share that
   falls inside exactly one published service territory, the share that falls inside
   more than one, the share that falls inside none, and the share whose coordinate could
   not be used. Denominator: the fire record set.
2. **Whether the placeable records look like the unplaceable ones.** The destroyed share
   among placed records against the destroyed share among contested records, each with
   its own denominator and interval, and the difference with a Newcombe interval. If the
   two populations differ, then any territory-level reading of the placed subset is
   drawn from a subset that is not representative, and the size of that problem is
   published rather than left for the reader to worry about.
3. **Per territory, counts.** Placed, contested, which territories the contest is with,
   how many distinct incidents, and the share of the territory's placed records
   contributed by its single largest incident. Alphabetical.
4. **Per territory, how much of it sits near a published edge.** The publisher says the
   boundaries are approximate. This says how much would move if they are off by 100,
   250, 500 or 1000 metres.

What is not published, and why
------------------------------
**No damage rate is published for a territory.** It would be arithmetic that looks like
a statement about a utility and is not one. Measurement 3 is the evidence: in several
territories a single incident contributes most of the placed records, so a
territory-level destroyed share would be a statement about one fire that happened to
burn there. Publishing that number next to another utility's number would invite a
comparison that the data cannot support, and this project does not publish it in any
form, ordered or unordered.

**No territory is ranked, scored, or ordered by any measured value.** Every collection
in the output is sorted by name.

**No rate is published against a denominator drawn from outside this record set.** Not
housing units, not customers, not meters, not parcels. The numerator here is a
population defined by where fires burned and which land is in the state responsibility
area, and dividing it by a population defined some other way produces a number whose
denominator does not contain its numerator.
"""

from __future__ import annotations

from typing import Any

from inspected.geometry import Territory
from inspected.intervals import Difference, Rate
from inspected.placement import BOUNDARY_BANDS_M, Placement
from inspected.sources import EXCLUDED_TYPES


def placement_coverage(placement: Placement) -> dict[str, Any]:
    """How much of the record set can be attributed at all."""
    total = placement.fire_records
    return {
        "fire_records": total,
        "excluded_by_hazard_filter": placement.excluded_by_hazard,
        "counts": {
            "placed_in_exactly_one_territory": placement.placed,
            "contested_between_two_or_more": placement.contested,
            "covered_by_no_published_territory": placement.uncovered,
            "coordinate_not_usable": placement.not_measured,
        },
        "counts_sum_to_fire_records": placement.classified == total,
        "rates": [
            Rate.of(
                "placed in exactly one published territory", placement.placed, total
            ).as_dict(),
            Rate.of(
                "inside two or more published territories", placement.contested, total
            ).as_dict(),
            Rate.of(
                "inside no published territory", placement.uncovered, total
            ).as_dict(),
            Rate.of("coordinate not usable", placement.not_measured, total).as_dict(),
        ],
    }


def representativeness(placement: Placement) -> dict[str, Any]:
    """Do the records that can be attributed resemble the records that cannot."""
    placed = Rate.of(
        "destroyed share among placed records",
        placement.destroyed_placed,
        placement.placed,
    )
    contested = Rate.of(
        "destroyed share among contested records",
        placement.destroyed_contested,
        placement.contested,
    )
    uncovered = Rate.of(
        "destroyed share among records in no published territory",
        placement.destroyed_uncovered,
        placement.uncovered,
    )
    difference = Difference.between(
        "placed minus contested, destroyed share",
        placed,
        contested,
        note=(
            "A difference whose interval excludes zero means the records that can be "
            "attributed to one territory are not a representative sample of the record "
            "set, and a territory-level reading of them inherits that."
        ),
    )
    return {
        "placed": placed.as_dict(),
        "contested": contested.as_dict(),
        "uncovered": uncovered.as_dict(),
        "difference": difference.as_dict(),
    }


def _band_rates(tally: Any) -> list[dict[str, Any]]:
    if tally.distance_state != "measured":
        return [
            Rate.not_measured(
                f"within {band} m of the published edge",
                reason="no records are placed in this territory, so no distance exists",
            ).as_dict()
            for band in BOUNDARY_BANDS_M
        ]
    return [
        Rate.of(
            f"within {band} m of the published edge",
            tally.within_band[band],
            tally.placed,
            note=(
                "The publisher states the boundaries are approximate. This is how much "
                "of the territory's placed total sits close enough to the edge to be "
                "affected if the approximation is off by this much."
            ),
        ).as_dict()
        for band in BOUNDARY_BANDS_M
    ]


def _concentration(tally: Any) -> dict[str, Any]:
    largest = tally.largest_incident
    if largest is None or tally.placed == 0:
        return {
            "largest_incident": None,
            "share": Rate.not_measured(
                "share of placed records from the largest single incident",
                reason="no records are placed in this territory",
            ).as_dict(),
        }
    name, count = largest
    return {
        "largest_incident": name,
        "share": Rate.of(
            "share of placed records from the largest single incident",
            count,
            tally.placed,
            note=(
                "Where this is high, a territory-level damage rate would describe one "
                "fire rather than a territory. That is why no such rate is published."
            ),
        ).as_dict(),
    }


def territory_rows(
    placement: Placement, territories: tuple[Territory, ...]
) -> list[dict[str, Any]]:
    """One row per published territory, alphabetical, counts and within-row rates only."""
    rows: list[dict[str, Any]] = []
    for territory in territories:
        tally = placement.tallies[territory.name]
        rows.append(
            {
                "territory": territory.name,
                "published_type": territory.kind,
                "source_layer": territory.source_key,
                "geometry_state": territory.geometry_state,
                "geometry_note": territory.geometry_note,
                "records_placed_here": tally.placed,
                "records_contested_here": tally.contested,
                "contested_with": sorted(tally.contested_with),
                "distinct_incidents_among_placed": len(tally.incidents),
                "incident_concentration": _concentration(tally),
                "boundary_proximity": {
                    "state": tally.distance_state,
                    "bands_m": list(BOUNDARY_BANDS_M),
                    "rates": _band_rates(tally),
                },
            }
        )
    return sorted(rows, key=lambda row: str(row["territory"]))


def contested_groups(placement: Placement, limit: int = 25) -> list[dict[str, Any]]:
    """The overlapping combinations, as counts. Largest first is a size, not a ranking."""
    items = sorted(placement.contested_groups.items(), key=lambda kv: (-kv[1], kv[0]))[
        :limit
    ]
    return [{"territories": list(names), "records": count} for names, count in items]


def geometry_ledger(
    placement: Placement,
    territories: tuple[Territory, ...],
    unusable: tuple[Territory, ...],
) -> dict[str, Any]:
    """Which published polygons arrived invalid, and how much rests on the repair.

    Naming the repaired polygons is not enough on its own. The repair is a modelling
    decision, a different repair puts a different set of records inside a different set
    of outlines, and a reader deciding how much to trust the result needs the size of
    the exposure rather than the fact of it.
    """
    from_repaired = sum(
        placement.tallies[t.name].placed for t in territories if t.repaired
    )
    return {
        "territories_indexed": len(territories),
        "territories_repaired": sum(1 for t in territories if t.repaired),
        "repaired": sorted(t.name for t in territories if t.repaired),
        "records_placed_via_repaired_geometry": Rate.of(
            "placed records that sit inside a polygon this project repaired",
            from_repaired,
            placement.placed,
            note=(
                "A repair is a choice. This is how much of the placed total depends on "
                "it, so a reader can weigh the result rather than take it whole."
            ),
        ).as_dict(),
        "unusable": [
            {"territory": t.name, "reason": t.geometry_note}
            for t in sorted(unusable, key=lambda t: t.name)
        ],
        "unusable_count": len(unusable),
        "note": (
            "A polygon that fails an OGC validity check gives undefined answers to a "
            "containment question, so it is repaired before use and named here. A "
            "polygon that cannot be repaired into a testable shape is removed from the "
            "index and is not reported as holding zero records."
        ),
    }


def excluded_type_note() -> list[dict[str, str]]:
    """The published entity types this project does not read as a service territory."""
    return [
        {"published_type": kind, "reason": reason}
        for kind, reason in sorted(EXCLUDED_TYPES.items())
    ]


def years(placement: Placement) -> list[dict[str, int]]:
    """Fire records per incident year, so the span of the record set is visible."""
    return [
        {"year": year, "records": count}
        for year, count in sorted(placement.years.items())
    ]
