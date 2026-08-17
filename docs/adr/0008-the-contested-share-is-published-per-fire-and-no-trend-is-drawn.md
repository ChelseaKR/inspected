# 8. The contested share is published per fire, and no trend is drawn through it

Date: 2026-08-17

## Status

Accepted.

## Context

The headline is one number over one record set, and a single number reads as a property
of the two datasets: as though 37.9% of any California damage inspection is
unattributable. Three cuts of the same data were tested to see whether that reading
holds.

**By incident.** It does not hold, and it is not close. Of the 405 incidents in the file,
353 have no contested record at all and 29 have nothing but contested records. 382 of 405,
94.3% with an interval of 91.6% to 96.2%, fall entirely on one side. Those incidents hold
62.4% of the records that carry an incident name. Whether a record is contested is
mostly decided before the join runs, by where its fire burned relative to the places the
published outlines overlap.

**By incident year.** The same thing, at a coarser grain: the contested share by year
runs from 0.0% in 2013 to 92.5% in 2025, with every year carrying its own denominator and
interval. This is a restatement of the incident result rather than a second finding,
because a year is mostly a handful of large fires.

**By county.** Not tested. CAL FIRE publishes a county field and this project does not
fetch it. Fetching it means a new acquisition and a new pin, which moves every figure in
the repository, so it is named as an open item rather than half-built.

The dangerous reading of the year table is a trend. It is not available here and it will
not be available from this data: the territory layer is one retrieval, so every row in
the table is measured against identical boundaries. A rise across years describes where
that year's fires burned. Printed as a line it would read as the published data getting
better or worse, which is a claim about a publisher that the measurement cannot support.

A leave-one-out cut was also considered and dropped: for each published outline, how many
contested records would resolve to exactly one if that outline alone were removed. It
computes cleanly and it is the most actionable thing here for the publisher. It also
attaches a large number to a named entity as the cause of the ambiguity, readers rank
such tables whatever the sort order, and the pairwise combinations already published in
`contested_groups` carry most of the same information without naming a culprit. Not
built.

## Decision

Publish the incident split as counts and rates over the incident set, and the contested
share per incident year as rates over that year's classified records. Publish the
statement that no trend is drawn and why, in the artifact and in the generated report.

No slope, no direction, no year-over-year difference, and no comparison between two years
is published. Each year carries a Wilson interval and a reader may compare two rows; the
project does not do it for them, because doing it would mean asserting that the
comparison means something.

## Consequences

The headline gains its most important qualifier: it is an average over a record set whose
composition is fires, and a different set of fires would produce a different number. That
makes the figure less quotable and more true.

`by_incident_year` carries the year, the fire records, the classified records and the
share. Two denominators rather than one, because a year whose records could not be placed
has a share that is not measured rather than a share of zero.

The incident split names no incident. It is a count of incidents in each bucket, not a
list of which fires are contested, because that list would be a list of which fires
burned in whose overlap and it would read as the league table ADR 0004 refuses by another
route. A territory row still names its own largest incident, which is a within-territory
count and is what makes the case against a per-territory damage rate.
