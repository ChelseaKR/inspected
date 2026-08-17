"""Re-running the two choices that could have gone another way, and publishing the gap.

Two decisions in this project are judgment calls made from the publisher's own fields.
Both were documented and neither was measured, which meant a reader had to take the
reasoning on trust and the author had to take the size of the exposure on trust too.

``type_inclusion``
    ADR 0002 reads ``IOU``, ``POU``, ``CO-OP`` and ``Tribal`` as service territories and
    excludes ``CCA`` and ``ADMIN``. This runs the entire placement under that rule and
    under six alternatives, and reports what each one does to the headline figure. It
    does not choose between them. The point is that a reader can see which parts of the
    rule the result is sensitive to and which parts make no difference at all.

``repair_comparison``
    ADR 0005 repairs an invalid published polygon with ``make_valid``. An earlier draft
    used ``buffer(0)``, and the note that survived said the two disagreed on "roughly
    770 placements", which is a recollection rather than a measurement. This runs both
    to completion over the same records, counts the records whose outcome changes, and
    names the direction of the change.

``untouched_outlines``
    ADR 0002 declines to decide whether any named entity in the layer operates a
    distribution system, and ADR 0006 measures what the type rule costs without
    reaching that question either. What neither answers is the one a reader arrives
    with about a specific outline: would dropping this one change anything? For an
    outline no record falls inside, that is answerable without deciding what the
    entity is. This counts those outlines, counts the records they touch, and re-places
    the whole record set without them to show that the counts hold.

None of the three decides anything. All produce numbers with denominators and intervals,
in the same shapes the rest of the output uses, so the publication rules in
:mod:`inspected.artifacts` apply to them unchanged.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from inspected.geometry import (
    BUFFER_ZERO,
    MAKE_VALID,
    Territory,
    load_territories,
)
from inspected.intervals import Difference, Rate
from inspected.placement import Placement, Record, classify, containment_signatures
from inspected.sources import (
    PUBLISHED_TYPES,
    TYPE_FIELD_IS_UNDOCUMENTED,
    WIRES_TYPES,
)

TYPE_VARIANTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("the rule as built", WIRES_TYPES),
    ("without CO-OP", ("IOU", "POU", "Tribal")),
    ("without Tribal", ("CO-OP", "IOU", "POU")),
    ("without CO-OP or Tribal", ("IOU", "POU")),
    ("with CCA read as a territory", ("CCA", "CO-OP", "IOU", "POU", "Tribal")),
    ("with ADMIN read as a territory", ("ADMIN", "CO-OP", "IOU", "POU", "Tribal")),
    ("every published type read as a territory", PUBLISHED_TYPES),
)
"""The rule, the two inclusions it could drop, and the two exclusions it could take back."""

CONTESTED_LABEL = "inside two or more published territories"


def _outcome_counts(placement: Placement) -> dict[str, int]:
    return {
        "placed_in_exactly_one_territory": placement.placed,
        "contested_between_two_or_more": placement.contested,
        "covered_by_no_published_territory": placement.uncovered,
        "coordinate_not_usable": placement.not_measured,
    }


def _variant_row(
    label: str,
    kinds: tuple[str, ...],
    placement: Placement,
    indexed: int,
    baseline: Rate | None,
) -> dict[str, Any]:
    total = placement.fire_records
    contested = Rate.of(CONTESTED_LABEL, placement.contested, total)
    row: dict[str, Any] = {
        "variant": label,
        "types_read_as_territories": list(kinds),
        "territories_indexed": indexed,
        "counts": _outcome_counts(placement),
        "contested": contested.as_dict(),
        "placed": Rate.of(
            "placed in exactly one published territory", placement.placed, total
        ).as_dict(),
        "uncovered": Rate.of(
            "inside no published territory", placement.uncovered, total
        ).as_dict(),
    }
    if baseline is not None:
        row["contested_difference_from_the_rule_as_built"] = Difference.between(
            "this variant minus the rule as built, contested share",
            contested,
            baseline,
            note=(
                "The same records measured twice against two different sets of "
                "outlines. The two proportions are positively correlated rather than "
                "independent, so a method built for two independent samples gives a "
                "wider interval here than a paired method would. It is published as "
                "the conservative bound. The exact figures are the two contested "
                "counts, which are a census and not an estimate."
            ),
        ).as_dict()
    return row


def _types_present(collections: dict[str, dict[str, Any]]) -> list[str]:
    """Every ``Type`` value in the retrieval, read before any rule filters one out.

    Taken from the features rather than from the loaded territories, because the loader
    has already dropped everything outside the inclusion rule by the time it returns.
    Reading it from there would leave the unexpected-type check unable to ever fire,
    which is a gate that reports rather than a gate that works.
    """
    kinds: set[str] = set()
    for collection in collections.values():
        for feature in collection.get("features", []):
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                continue
            kind = properties.get("Type")
            if isinstance(kind, str) and kind.strip():
                kinds.add(kind.strip())
    return sorted(kinds)


def type_inclusion(
    collections: dict[str, dict[str, Any]],
    records: tuple[Record, ...],
    excluded_by_hazard: int,
) -> dict[str, Any]:
    """Re-place every record under each inclusion rule, and report what moves.

    The layers are read once, with every published type kept, and each variant is a
    filter over that one read. Reading them per variant would project the same polygons
    seven times for the same answer.
    """
    every, _ = load_territories(collections, keep_types=PUBLISHED_TYPES)
    seen = _types_present(collections)
    baseline: Rate | None = None
    rows: list[dict[str, Any]] = []
    for label, kinds in TYPE_VARIANTS:
        subset = tuple(t for t in every if t.kind in kinds)
        placement = classify(records, subset, excluded_by_hazard)
        rows.append(_variant_row(label, kinds, placement, len(subset), baseline))
        if baseline is None:
            baseline = Rate.of(CONTESTED_LABEL, placement.contested, len(records))
    return {
        "question": (
            "How much of the headline figure rests on reading CO-OP and Tribal as "
            "service territories, and on not reading CCA and ADMIN as territories?"
        ),
        "rule_as_built": list(WIRES_TYPES),
        "published_types_present_in_this_retrieval": seen,
        "unexpected_published_types": sorted(set(seen) - set(PUBLISHED_TYPES)),
        "the_published_type_field_is_undocumented": TYPE_FIELD_IS_UNDOCUMENTED,
        "variants": rows,
        "note": (
            "No rule is chosen here and none is changed. Each row is the whole record "
            "set re-placed against a different set of published outlines, so a reader "
            "can see which parts of the inclusion rule the result depends on. A variant "
            "that raises the uncovered count is reporting that records the dropped "
            "entities do sit over would be published as inside no territory, which is a "
            "statement about coverage that the dropped entity's own polygon contradicts."
        ),
    }


def _signature_outcome(signature: tuple[str, ...] | None) -> str:
    if signature is None:
        return "coordinate_not_usable"
    if not signature:
        return "covered_by_no_published_territory"
    if len(signature) == 1:
        return "placed_in_exactly_one_territory"
    return "contested_between_two_or_more"


def _transitions(
    chosen: tuple[tuple[str, ...] | None, ...],
    alternative: tuple[tuple[str, ...] | None, ...],
) -> tuple[Counter[tuple[str, str]], int, int]:
    """Count the records whose signature differs, by the transition they make."""
    moves: Counter[tuple[str, str]] = Counter()
    changed = 0
    same_outcome_other_outline = 0
    for left, right in zip(chosen, alternative, strict=True):
        if left == right:
            continue
        changed += 1
        pair = (_signature_outcome(left), _signature_outcome(right))
        moves[pair] += 1
        if pair[0] == pair[1]:
            same_outcome_other_outline += 1
    return moves, changed, same_outcome_other_outline


def _placed_count(signatures: tuple[tuple[str, ...] | None, ...]) -> int:
    return sum(1 for s in signatures if s is not None and len(s) == 1)


def repair_comparison(
    collections: dict[str, dict[str, Any]],
    records: tuple[Record, ...],
    chosen: tuple[Territory, ...],
) -> dict[str, Any]:
    """Place every record twice, once under each repair, and count the disagreement."""
    alternative_territories, alternative_unusable = load_territories(
        collections, strategy=BUFFER_ZERO
    )
    chosen_signatures = containment_signatures(records, chosen)
    alternative_signatures = containment_signatures(records, alternative_territories)
    moves, changed, same_outcome = _transitions(
        chosen_signatures, alternative_signatures
    )
    total = len(records)
    chosen_placed = Rate.of(
        f"placed in exactly one published territory, under {MAKE_VALID}",
        _placed_count(chosen_signatures),
        total,
    )
    alternative_placed = Rate.of(
        f"placed in exactly one published territory, under {BUFFER_ZERO}",
        _placed_count(alternative_signatures),
        total,
    )
    return {
        "question": (
            "How much of the result depends on which repair is applied to the polygons "
            "the publisher ships invalid?"
        ),
        "chosen": MAKE_VALID,
        "alternative": BUFFER_ZERO,
        "territories_indexed": {
            MAKE_VALID: len(chosen),
            BUFFER_ZERO: len(alternative_territories),
        },
        "territories_unusable_under_the_alternative": len(alternative_unusable),
        "records_with_a_different_outcome": Rate.of(
            "records the two repairs disagree about",
            changed,
            total,
            note=(
                "Counted per record, not inferred from two totals. A record counts here "
                "if the set of outlines it falls inside is not the same under both "
                "repairs, including when both repairs agree on the kind of outcome."
            ),
        ).as_dict(),
        "records_with_the_same_outcome_but_different_outlines": same_outcome,
        "transitions": [
            {"under_the_chosen_repair": a, "under_the_alternative": b, "records": n}
            for (a, b), n in sorted(moves.items())
        ],
        "placed_under_the_chosen_repair": chosen_placed.as_dict(),
        "placed_under_the_alternative": alternative_placed.as_dict(),
        "placed_difference": Difference.between(
            f"{MAKE_VALID} minus {BUFFER_ZERO}, placed share",
            chosen_placed,
            alternative_placed,
            note=(
                "The same records placed twice, so the two proportions are not "
                "independent and this Newcombe interval is the conservative bound "
                "rather than the tight one. The exact figure is the disagreement count "
                "above, which needs no interval because it is a census of the "
                "difference and not an estimate of it."
            ),
        ).as_dict(),
        "note": (
            "Neither repair is correct. Both are answers to a question the published "
            "polygon does not answer, and the difference between them is the size of "
            "the ambiguity the publisher's invalid geometry leaves behind."
        ),
    }


def untouched_outlines(
    placement: Placement,
    records: tuple[Record, ...],
    chosen: tuple[Territory, ...],
) -> dict[str, Any]:
    """Which published outlines hold no record, and what dropping them would change.

    A reader can reasonably doubt whether a particular outline in this layer belongs in
    a retail service territory set at all. This project does not answer that, because
    answering it means classifying a named organisation from outside the publisher's own
    field, which ADR 0002 refuses. It can answer the narrower question the doubt is
    usually a proxy for: could that outline be moving a published figure?

    For an outline no record falls inside, the answer is no, and it is arithmetic rather
    than judgment. Removing an outline can only change the signature of a record that
    was inside it, so a record inside none of the removed outlines keeps the outcome it
    had. That is asserted here by re-placing the whole record set against the reduced
    index and counting the records whose signature moves, which is a census and not an
    argument.
    """
    untouched = tuple(
        t
        for t in chosen
        if placement.tallies[t.name].placed == 0
        and placement.tallies[t.name].contested == 0
    )
    reduced = tuple(t for t in chosen if t not in untouched)
    names = frozenset(t.name for t in untouched)
    before = containment_signatures(records, chosen)
    # An empty index is not something a spatial tree can be built over, and it is not
    # something this comparison needs one for: with every outline removed, every record
    # with a coordinate is inside none of them, which is what the second branch writes.
    after = (
        containment_signatures(records, reduced)
        if reduced
        else tuple(None if s is None else () for s in before)
    )
    _, changed, _ = _transitions(before, after)
    touching = sum(1 for s in before if s is not None and not names.isdisjoint(s))
    total = len(records)
    return {
        "question": (
            "Is a published outline that a reader might question capable of moving a "
            "published figure at all?"
        ),
        "outlines_no_record_falls_inside": sorted(t.name for t in untouched),
        "outlines_no_record_falls_inside_count": len(untouched),
        "outlines_indexed": len(chosen),
        "records_inside_at_least_one_of_them": Rate.of(
            "records falling inside an outline that holds no record",
            touching,
            total,
            note=(
                "Zero by construction when it is zero: an outline holds no record "
                "exactly when no record falls inside it. It is counted from the "
                "signatures rather than asserted, so the two cannot drift apart."
            ),
        ).as_dict(),
        "records_with_a_different_outcome_without_them": Rate.of(
            "records whose outcome changes when all of them are removed",
            changed,
            total,
            note=(
                "The whole record set placed again against the reduced index. Every "
                "published figure in this repository is a function of these signatures, "
                "so a zero here is the statement that no published figure moves."
            ),
        ).as_dict(),
        "note": (
            "This is a count, not a classification. It does not establish that any of "
            "the outlines named here is or is not a retail service territory, and this "
            "project does not decide that; see ADR 0002 and ADR 0010. What it "
            "establishes is that the question cannot change a figure published here, "
            "because the outlines it would be asked about hold nothing."
        ),
    }
