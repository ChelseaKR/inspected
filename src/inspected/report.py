"""The measurements, rendered once, deterministically, as Markdown.

Every number on the page comes from the artifact rather than from a second calculation,
so the document and the JSON cannot disagree. A rate that could not be made prints as
``not measured`` and never as ``0.0%``.
"""

from __future__ import annotations

from typing import Any

NOT_MEASURED = "not measured"


def pct(value: float | None) -> str:
    """One decimal place, except where that would print a real measurement as zero.

    A share of three in a hundred thousand is a measurement. Rendering it as `0.0%`
    alongside an interval of `0.0% to 0.0%` reads as certainty about an absence, which is
    the one thing this project is trying never to say by accident.
    """
    if value is None:
        return NOT_MEASURED
    if value == 0.0:
        return "0.0%"
    # On magnitude, not on sign. Testing `value * 100 < 0.05` sent every negative number
    # down the high-precision branch, so a difference of minus a third of a percentage
    # point printed to four decimals beside a positive one printed to one.
    if abs(value) * 100 < 0.05:
        return f"{value * 100:.4f}%"
    return f"{value * 100:.1f}%"


def count(value: int) -> str:
    """Thousands separated. Six-figure record counts are the point of several tables."""
    return f"{value:,}"


def span(low: float, high: float) -> str:
    """Both ends of an interval, at enough precision to tell them apart.

    :func:`pct` prints one decimal place. Over a six-figure denominator two genuinely
    different bounds round to the same string, and an interval printed as `0.7% to 0.7%`
    reads as certainty, which is the opposite of what an interval is there to say. The
    precision rises until the two ends differ, or until four places has shown that they
    really do not.
    """
    rendered = [
        (f"{low * 100:.{places}f}%", f"{high * 100:.{places}f}%")
        for places in (1, 2, 3, 4)
    ]
    for lower, upper in rendered:
        if lower != upper:
            return f"{lower} to {upper}"
    lower, upper = rendered[0]
    return f"{lower} to {upper}"


def interval(node: dict[str, Any]) -> str:
    if node.get("state") != "measured":
        return NOT_MEASURED
    return span(node["interval_low"], node["interval_high"])


def rate_line(node: dict[str, Any]) -> str:
    if node.get("state") != "measured":
        return f"| {node['label']} | {NOT_MEASURED} | {node['numerator']} | 0 | {NOT_MEASURED} |"
    return (
        f"| {node['label']} | {pct(node['rate'])} | {count(node['numerator'])} | "
        f"{count(node['denominator'])} | {interval(node)} |"
    )


def _header(tree: dict[str, Any]) -> list[str]:
    prov = tree["provenance"]
    return [
        "# Which published electric service territory is a burned structure in?",
        "",
        "Unofficial. Not affiliated with, endorsed by, or approved by CAL FIRE, the",
        "California Energy Commission, or any electric utility. This is descriptive",
        "geography over two public datasets. It is not a risk rating of any company and",
        "it contains no information about the location of anybody's infrastructure.",
        "",
        f"Damage inspections retrieved {prov['dins_retrieved']}. Territory boundaries",
        f"retrieved {prov['territories_retrieved']}, publisher item last modified",
        f"{prov['territories_item_modified']}.",
        "",
        "This document is generated. Every figure below is read from",
        "`measurements.json`, which is produced by the same run.",
        "",
    ]


def _coverage(tree: dict[str, Any]) -> list[str]:
    cov = tree["placement_coverage"]
    lines = [
        "## Can the join be made at all",
        "",
        f"The record set holds {count(cov['fire_records'])} wildfire damage-inspection",
        f"records. {count(cov['excluded_by_hazard_filter'])} records in the published file describe a",
        "hazard other than fire and are excluded here rather than counted as wildfire.",
        "",
        "| Outcome | Share | Records | Of | 95% interval |",
        "|---|---:|---:|---:|---|",
    ]
    lines.extend(rate_line(node) for node in cov["rates"])
    lines.extend(
        [
            "",
            "A record inside two or more published territories is not awarded to either.",
            "The publisher states that the boundaries are approximate and that not all",
            "entities are represented, so public data does not say which entity such a",
            "record belongs to, and this project does not decide on its behalf.",
            "",
        ]
    )
    return lines


def _representativeness(tree: dict[str, Any]) -> list[str]:
    rep = tree["representativeness"]
    diff = rep["difference"]
    verdict = (
        "The interval excludes zero. The records that can be attributed to a single "
        "territory are therefore not a representative slice of the record set, and any "
        "territory-level reading of them carries that difference with it."
        if diff.get("excludes_zero")
        else "The interval includes zero, so this comparison does not establish a "
        "difference between the two populations."
    )
    return [
        "## Do the records that can be attributed look like the ones that cannot",
        "",
        "| Population | Destroyed share | Destroyed | Inspected | 95% interval |",
        "|---|---:|---:|---:|---|",
        rate_line(rep["placed"]),
        rate_line(rep["contested"]),
        rate_line(rep["uncovered"]),
        "",
        f"Difference, placed minus contested: {pct(diff['difference'])} "
        f"({interval(diff)}, Newcombe score).",
        "",
        verdict,
        "",
    ]


def _contested(tree: dict[str, Any]) -> list[str]:
    rows = tree["contested_groups"]
    lines = [
        "## Where the published boundaries overlap",
        "",
        "Counts of records falling inside each combination of published outlines. This",
        "is a description of the boundary layer, not of any utility. The combinations",
        "are listed by size because size is what is being reported.",
        "",
    ]
    lines.extend(
        [
            "The last column is the share of each combination's records sitting",
            "within 250 metres of the nearest edge among the outlines involved. A",
            "contested record stops being contested when any of them ceases to",
            "contain it, so that is the edge an approximation error moves first; a",
            "combination near 100% here is a thin seam between outlines, and one",
            "near 0% is an interior region where two published territories genuinely",
            "cover the same ground.",
            "",
            "| Published outlines a record falls inside | Records | Within 250 m of an edge |",
            "|---|---:|---:|",
        ]
    )
    for row in rows:
        rate_250 = _edge_band_rate(row, 250)
        cell = (
            NOT_MEASURED
            if rate_250["state"] != "measured"
            else f"{pct(rate_250['rate'])} ({interval(rate_250)})"
        )
        lines.append(
            f"| {', '.join(row['territories'])} | {count(row['records'])} | {cell} |"
        )
    lines.append("")
    return lines


def _edge_band_rate(row: dict[str, Any], band_m: int) -> dict[str, Any]:
    """The one band rate a contested-group row carries for a given distance."""
    proximity: dict[str, Any] = row["boundary_proximity"]
    index: int = proximity["bands_m"].index(band_m)
    rate: dict[str, Any] = proximity["rates"][index]
    return rate


def _territories(tree: dict[str, Any]) -> list[str]:
    lines = [
        "## Every published territory, in name order",
        "",
        "Counts, and two within-territory shares. No damage rate is published for a",
        "territory and no territory is ordered against another. The concentration",
        "column is why: where one incident supplies most of a territory's records, a",
        "territory-level damage rate would be a statement about that one fire.",
        "",
        "A territory appears in more than one row of the contested count, because a",
        "record inside three outlines is contested for all three.",
        "",
        "| Territory | Type | Placed | Contested | Incidents | Largest incident share |"
        " Within 250 m of the edge | Geometry |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for row in tree["territories"]:
        share = row["incident_concentration"]["share"]
        bands = row["boundary_proximity"]["rates"]
        near = next((b for b in bands if "250 m" in b["label"]), None)
        lines.append(
            f"| {row['territory']} | {row['published_type']} | "
            f"{count(row['records_placed_here'])} | "
            f"{count(row['records_contested_here'])} | "
            f"{row['distinct_incidents_among_placed']} | "
            f"{pct(share['rate']) if share['state'] == 'measured' else NOT_MEASURED} | "
            f"{pct(near['rate']) if near and near['state'] == 'measured' else NOT_MEASURED} | "
            f"{row['geometry_state']} |"
        )
    lines.append("")
    return lines


def _ledger(tree: dict[str, Any]) -> list[str]:
    ledger = tree["geometry_ledger"]
    lines = [
        "## The published polygons, as they arrived",
        "",
        f"{ledger['territories_indexed']} outlines were read as electric service",
        f"territories. {ledger['territories_repaired']} of them failed an OGC validity",
        "check on retrieval and were repaired before any containment question was asked",
        "of them, because an invalid polygon answers that question undefined rather than",
        "refusing it. The repaired ones are named here and flagged in the table above.",
        "",
    ]
    if ledger["repaired"]:
        lines.extend([f"- {name}" for name in ledger["repaired"]])
        lines.append("")
    repaired_share = ledger["records_placed_via_repaired_geometry"]
    lines.extend(
        [
            f"{count(repaired_share['numerator'])} placed records, "
            f"{pct(repaired_share['rate'])} "
            f"of the placed total ({interval(repaired_share)}), sit inside one of those",
            "repaired polygons. A different repair would place a different set, so that",
            "figure is the size of this project's exposure to the choice.",
            "",
            f"{ledger['unusable_count']} outlines could not be repaired into a testable",
            "shape. Those are removed from the index and are not reported as holding",
            "zero records.",
            "",
            "Two published entity types are not read as service territories:",
            "",
        ]
    )
    lines.extend(
        f"- **{row['published_type']}**: {row['reason']}"
        for row in tree["excluded_types"]
    )
    lines.append("")
    return lines


def _by_fire(tree: dict[str, Any]) -> list[str]:
    block = tree["attributability_by_fire"]
    incidents = block["by_incident"]
    lines = [
        "## Is the unattributable share a property of the data or of the fire",
        "",
        "The headline is one number over the whole record set, which reads as a property",
        "of the two datasets. It is mostly not. The published outlines overlap in",
        "particular places, so whether a record is contested is largely settled by where",
        "its fire burned.",
        "",
        f"Of {count(incidents['distinct_incidents'])} distinct incidents in the record set,",
        f"{pct(incidents['one_way_or_the_other']['rate'])} "
        f"({interval(incidents['one_way_or_the_other'])}) fall entirely on one side: every",
        "classified record contested, or none of them. Those incidents hold",
        f"{pct(incidents['records_in_an_incident_that_falls_entirely_on_one_side']['rate'])}",
        "of the records that carry an incident name.",
        "",
        "| Incidents | Share | Incidents | Of | 95% interval |",
        "|---|---:|---:|---:|---|",
        rate_line(incidents["every_record_contested"]),
        rate_line(incidents["no_record_contested"]),
        rate_line(incidents["split_both_ways"]),
        "",
        "The same thing seen by year. The boundaries are one retrieval and are identical",
        "for every row, so the movement down this column is where each year's fires",
        "burned and not a change in the published boundaries. No trend is published.",
        "",
        "| Incident year | Records | Classified | Contested share | 95% interval |",
        "|---:|---:|---:|---:|---|",
    ]
    for row in block["by_incident_year"]:
        node = row["contested"]
        lines.append(
            f"| {row['year']} | {count(row['records'])} | "
            f"{count(row['records_classified'])} | "
            f"{pct(node['rate']) if node['state'] == 'measured' else NOT_MEASURED} | "
            f"{interval(node)} |"
        )
    lines.append("")
    lines.extend(_by_county(block))
    return lines


def _by_county(block: dict[str, Any]) -> list[str]:
    """The same cut by county, in name order, with the same refusals stated."""
    lines = [
        "The same cut by county, from CAL FIRE's own county field. In name order, never",
        "in size order, and no county is compared against another. This says where in",
        f"California the published outlines overlap: {block['counties_named_in_the_record_set']}",
        "counties are named in the record set, and",
        f"{count(block['records_carrying_no_county_name'])} records carry no county name and are",
        "left out of this cut alone.",
        "",
        block["county_note"],
        "",
        "| County | Records | Classified | Contested share | 95% interval |",
        "|---|---:|---:|---:|---|",
    ]
    for row in block["by_county"]:
        node = row["contested"]
        lines.append(
            f"| {row['county']} | {count(row['records'])} | "
            f"{count(row['records_classified'])} | "
            f"{pct(node['rate']) if node['state'] == 'measured' else NOT_MEASURED} | "
            f"{interval(node)} |"
        )
    lines.append("")
    return lines


def _sensitivity_types(tree: dict[str, Any]) -> list[str]:
    block = tree["sensitivity"]["type_inclusion"]
    lines = [
        "## What the inclusion rule is worth",
        "",
        "Which published outlines count as a service territory is a judgment, and this is",
        "the whole record set placed again under each way that judgment could have gone.",
        "The first row is the rule this project uses. Nothing here chooses between them,",
        "and the difference column is the conservative bound rather than the tight one,",
        "because the same records are being measured twice.",
        "",
        block["the_published_type_field_is_undocumented"],
        "",
        "| Inclusion rule | Outlines | Contested | Contested share | 95% interval |"
        " Difference from the rule as built | Inside no published territory |",
        "|---|---:|---:|---:|---|---|---:|",
    ]
    for row in block["variants"]:
        node = row["contested"]
        difference = row.get("contested_difference_from_the_rule_as_built")
        moved = (
            "reference"
            if difference is None
            else f"{pct(difference['difference'])} ({interval(difference)})"
        )
        lines.append(
            f"| {row['variant']} | {row['territories_indexed']} | "
            f"{count(node['numerator'])} | {pct(node['rate'])} | "
            f"{interval(node)} | {moved} | "
            f"{count(row['counts']['covered_by_no_published_territory'])} |"
        )
    lines.extend(
        [
            "",
            "A rule that drops an included type does not only move records out of the",
            "contested column. It moves them into the last one, where they are published",
            "as inside no published territory, which is a statement about coverage that",
            "the dropped entity's own published polygon contradicts.",
            "",
        ]
    )
    return lines


def _sensitivity_repair(tree: dict[str, Any]) -> list[str]:
    block = tree["sensitivity"]["repair_strategy"]
    changed = block["records_with_a_different_outcome"]
    # Two renderings, chosen by what the artifact carries rather than by a version
    # number. A tree built before the third repair joined carries no census keys, and
    # its committed REPORT.md must keep matching exactly what its own run wrote. The
    # branch goes away at the next deliberate refresh, when every published tree is
    # three-repair; until then both readings are kept honest.
    widened = "strategies_compared" in block
    lines = [
        "## What the repair is worth",
        "",
    ]
    if widened:
        union = block["records_where_any_two_repairs_disagree"]
        strategies = block["strategies_compared"]
        lines.extend(
            [
                f"All {len(strategies)} repairs "
                f"({', '.join(f'`{s}`' for s in strategies)}) run to completion over",
                f"the same records. {count(union['numerator'])} of "
                f"{count(union['denominator'])} records, {pct(union['rate'])}",
                f"({interval(union)}), come out differently under at least one pair of",
                "them. That count is a census of the disagreement and not an estimate",
                "of it, and it bounds how much of the result the choice of repair can",
                "move. The pairwise counts:",
                "",
                "| Between | Records |",
                "|---|---:|",
            ]
        )
        lines.extend(
            f"| `{row['between'][0]}` and `{row['between'][1]}` | {count(row['records'])} |"
            for row in block["pairwise_disagreements"]
        )
        lines.extend(
            [
                "",
                f"The pair ADR 0007 documents in detail: {count(changed['numerator'])}",
                f"of {count(changed['denominator'])} records, {pct(changed['rate'])}",
                f"({interval(changed)}), come out differently under "
                f"`{block['alternative']}` than under `{block['chosen']}`.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Both repairs run to completion over the same records. "
                f"{count(changed['numerator'])}",
                f"of {count(changed['denominator'])} records, {pct(changed['rate'])}",
                f"({interval(changed)}), come out differently under "
                f"`{block['alternative']}` than",
                f"under `{block['chosen']}`. That count is a census of the disagreement "
                "and not an",
                "estimate of it.",
                "",
            ]
        )
    if block["transitions"]:
        lines.extend(
            [
                "| Under the repair used here | Under the alternative | Records |",
                "|---|---|---:|",
            ]
        )
        lines.extend(
            f"| {row['under_the_chosen_repair'].replace('_', ' ')} | "
            f"{row['under_the_alternative'].replace('_', ' ')} | "
            f"{count(row['records'])} |"
            for row in block["transitions"]
        )
    else:
        lines.append(
            "The repairs place every record the same way."
            if widened
            else "The two repairs place every record the same way."
        )
    difference = block["placed_difference"]
    lines.extend(
        [
            "",
            "| Repair | Placed share | Placed | Of | 95% interval |",
            "|---|---:|---:|---:|---|",
            rate_line(block["placed_under_the_chosen_repair"]),
            rate_line(block["placed_under_the_alternative"]),
            "",
            f"Difference in the placed share: {pct(difference['difference'])} "
            f"({interval(difference)}, Newcombe score). The same records are placed twice,",
            "so that interval is the conservative bound.",
            "",
        ]
    )
    if widened:
        lines.extend(
            [
                "No repair is correct. Each is an answer to a question the published",
                "polygon does not answer, and the disagreement between them is the size of",
                "the ambiguity the invalid geometry leaves behind. The default did not",
                "move to gain this measurement; it was already `make_valid` under ADR 0007.",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Neither repair is correct. Both are answers to a question the published",
                "polygon does not answer, and the gap between them is the size of the",
                "ambiguity the invalid geometry leaves behind.",
                "",
            ]
        )
    return lines


def _untouched(tree: dict[str, Any]) -> list[str]:
    block = tree["sensitivity"]["untouched_outlines"]
    inside = block["records_inside_at_least_one_of_them"]
    changed = block["records_with_a_different_outcome_without_them"]
    lines = [
        "## The outlines that hold nothing",
        "",
        "Whether a particular named entity in the published layer operates a retail",
        "distribution system is the publisher's classification to make, and this project",
        "does not make it. The narrower question can be answered with a count: could that",
        "outline be moving a figure here?",
        "",
        f"{block['outlines_no_record_falls_inside_count']} of the"
        f" {block['outlines_indexed']} outlines read as service territories hold no",
        f"record at all. {count(inside['numerator'])} records of"
        f" {count(inside['denominator'])} fall inside one of them",
        f"({interval(inside)}). Placing the whole record set again with all of them",
        f"removed changes the outcome of {count(changed['numerator'])} records",
        f"({interval(changed)}), so no figure in this document depends on any of them.",
        "",
    ]
    if block["outlines_no_record_falls_inside"]:
        lines.extend(f"- {name}" for name in block["outlines_no_record_falls_inside"])
        lines.append("")
    lines.extend([block["note"], ""])
    return lines


def _limits() -> list[str]:
    return [
        "## What this does not measure",
        "",
        "- **Nothing about physical infrastructure.** No pole, conductor, substation, or",
        "  circuit position is read, inferred, approximated, or published, from these",
        "  sources or any other. An analysis that would need one is not built here.",
        "- **No comparison between utilities.** A territory's damage figures are driven",
        "  by which fires burned in it, and the concentration column shows how strongly.",
        "  Nothing here says any utility is more or less exposed than any other.",
        "- **No rate against population, housing, customers, or meters.** The record set",
        "  is defined by fire and by state responsibility area. A denominator drawn from",
        "  a differently defined population would not contain this numerator.",
        "- **Coverage is not exposure.** A territory with few placed records may have",
        "  burned little, may sit mostly outside the state responsibility area, or may",
        "  have most of its records contested. These are different facts and this",
        "  project does not merge them.",
        "",
    ]


def _county_agreement(tree: dict[str, Any]) -> list[str]:
    block = tree["coordinate_county_agreement"]
    compared = block["records_compared"]
    lines = [
        "## Does the coordinate agree with the recorded county",
        "",
        "CAL FIRE records a county name on every row, and this project reports it as",
        "published. This section measures that field against an authoritative county",
        "boundary layer rather than trusting it or correcting it: how often a record's",
        f"coordinate lands outside the county its publisher recorded. {count(compared['numerator'])}",
        f"of {count(compared['denominator'])} records could be compared at all; the rest had no usable",
        "coordinate or a county label the boundary layer does not carry, and they stay",
        "in every other denominator in this project.",
        "",
        "| Outcome | Share | Records | Of | 95% interval |",
        "|---|---:|---:|---:|---|",
        rate_line(block["agreed"]),
        rate_line(block["disagreed"]),
        rate_line(block["matched_no_county"]),
        rate_line(block["unmatchable_label"]),
        "",
        "Counted, never corrected. The boundary layer's publisher warns that its own",
        "boundary errors will exist, so a disagreement is evidence that two published",
        "sources differ and not a verdict on which one is right. No damage rate is",
        "published for a county here either.",
        "",
        "| County | Compared | Agreed | Matched no county | Disagreed share | 95% interval |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in block["by_county"]:
        node = row["disagreed"]
        lines.append(
            f"| {row['county']} | {count(row['resolved'])} | "
            f"{count(row['agreed'])} | {count(row['matched_no_county'])} | "
            f"{pct(node['rate']) if node['state'] == 'measured' else NOT_MEASURED} | "
            f"{interval(node) if node['state'] == 'measured' else NOT_MEASURED} |"
        )
    lines.append("")
    return lines


def _by_structure_class(tree: dict[str, Any]) -> list[str]:
    rows = tree["representativeness_by_category"]
    lines = [
        "## The placed and contested populations, by structure class",
        "",
        "The placed-versus-contested check from above, run again inside each structure",
        "class CAL FIRE publishes. A difference confined to one class would hide inside",
        "the aggregate; a difference spread across every class is sturdier than one",
        "number. Classes in name order; none is compared against another.",
        "",
        "| Structure class | Placed destroyed share | Contested destroyed share | Difference (Newcombe) |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        placed = row["placed"]
        contested = row["contested"]
        if "difference" in row:
            diff = row["difference"]
            cell = (
                f"{pct(diff['difference'])} ({interval(diff)})"
                if diff["state"] == "measured"
                else NOT_MEASURED
            )
        else:
            cell = NOT_MEASURED
        lines.append(
            f"| {row['structure_category']} | "
            f"{pct(placed['rate']) if placed['state'] == 'measured' else NOT_MEASURED} | "
            f"{pct(contested['rate']) if contested['state'] == 'measured' else NOT_MEASURED} | "
            f"{cell} |"
        )
    lines.append("")
    return lines


def render(tree: dict[str, Any]) -> str:
    """The whole document, deterministic for a given artifact."""
    lines: list[str] = []
    for section in (
        _header(tree),
        _coverage(tree),
        _representativeness(tree),
        _by_structure_class(tree),
        _by_fire(tree),
        _county_agreement(tree),
        _territories(tree),
        _contested(tree),
        _ledger(tree),
        _sensitivity_repair(tree),
        _sensitivity_types(tree),
        _untouched(tree),
        _limits(),
    ):
        lines.extend(section)
    return "\n".join(lines).rstrip() + "\n"
