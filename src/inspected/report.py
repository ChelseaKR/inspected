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


def interval(node: dict[str, Any]) -> str:
    if node.get("state") != "measured":
        return NOT_MEASURED
    return f"{pct(node['interval_low'])} to {pct(node['interval_high'])}"


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
    lines = [
        "## Where the published boundaries overlap",
        "",
        "Counts of records falling inside each combination of published outlines. This",
        "is a description of the boundary layer, not of any utility. The combinations",
        "are listed by size because size is what is being reported.",
        "",
        "| Published outlines a record falls inside | Records |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {', '.join(row['territories'])} | {count(row['records'])} |"
        for row in tree["contested_groups"]
    )
    lines.append("")
    return lines


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


def _years(tree: dict[str, Any]) -> list[str]:
    lines = [
        "## The span of the record set",
        "",
        "| Incident year | Records |",
        "|---:|---:|",
    ]
    lines.extend(
        f"| {row['year']} | {count(row['records'])} |" for row in tree["years"]
    )
    lines.append("")
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


def render(tree: dict[str, Any]) -> str:
    """The whole document, deterministic for a given artifact."""
    lines: list[str] = []
    for section in (
        _header(tree),
        _coverage(tree),
        _representativeness(tree),
        _territories(tree),
        _contested(tree),
        _ledger(tree),
        _years(tree),
        _limits(),
    ):
        lines.extend(section)
    return "\n".join(lines).rstrip() + "\n"
