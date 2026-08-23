# Responsible tech: ethics statement and residual risk

Dated 2026-08-22. Written against version `0.1.0` and the 2026-08-17 pins. This
document states what this project will not do, who could be harmed by it being misread,
and what risks remain after the mitigations. It is reviewed whenever a measurement is
added; the date above moves when it is.

Unofficial. Not affiliated with, endorsed by, or approved by CAL FIRE, the California
Energy Commission, or any electric utility.

## What this project is for

It measures how much of California's published wildfire damage-inspection record set
can be attributed to a published electric service territory using public data alone,
and publishes what cannot be attributed along with what can. The finding is a property
of two public datasets. It is descriptive geography.

## What it refuses to do, and why that is ethical content and not style

- **No tie-breaking of contested records.** Awarding a burned structure to a named
  company on the strength of a rule of thumb would be publishing a guess about
  somebody's service obligation as if it were data.
- **No damage rate per territory or per county.** Where one fire supplies most of an
  area's records, that arithmetic describes the fire, not the territory. Publishing it
  next to another area's number invites a comparison the data cannot support.
- **No ranking, scoring or grading** of any named company or place.
- **Nothing about infrastructure.** No pole, conductor, substation or circuit position
  is read or inferred from any source. Asset locations are not public, should not be,
  and nothing here approximates them.
- **No collection beyond the published fields needed.** Addresses, parcels and
  assessed values are never requested; coordinates are requested only to answer which
  polygon a point is in and are never republished.
- **No routing around access controls.** A blocked request stops the acquisition.
- **No silent refreshes.** The figures move when a person deliberately re-measures and
  writes down what moved.

## Residual risk: how this could be misread anyway

| Risk | Who it lands on | What limits it | What does not limit it |
|---|---|---|---|
| The headline is read as a utility safety rating | Any named utility, especially ones with high contested shares through no act of their own | The report says on every page that it ranks nobody; contested share measures boundary overlap, not performance | A reader who sees only a table row with a company name on it |
| The repair sensitivity is read as doubt about specific companies | Utilities whose polygons arrive invalid | Both repairs are named, both are run, and the disagreement size is published rather than hidden | The fact that two of the repaired polygons are the largest territories in the state |
| The county cut is read as a statement about who serves a county | Residents and county governments | The section says it locates overlaps, not service | The words "county" and "territory" sitting near each other |
| Figures are quoted years later without their retrieval date | Whoever acts on the quote | Every page carries its retrieval date; staleness triggers are defined | Screenshots, which carry none of it |
| The inclusion rule misclassifies an entity type | Entities misread into or out of the index | The rule's cost is measured; outlines holding no record provably move nothing | The 24 indexed outlines that do hold records, whose classification remains unreviewed by anybody with sector expertise |

## What we ask of anyone citing this work

Quote the denominator with the figure. Name the retrieval date. Do not turn a contested
share into a claim about a company. That is the whole list.
