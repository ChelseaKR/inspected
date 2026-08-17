# Which published electric service territory is a burned structure in?

Unofficial. Not affiliated with, endorsed by, or approved by CAL FIRE, the
California Energy Commission, or any electric utility. This is descriptive
geography over two public datasets. It is not a risk rating of any company and
it contains no information about the location of anybody's infrastructure.

Damage inspections retrieved 2026-08-17. Territory boundaries
retrieved 2026-08-17, publisher item last modified
2026-08-12.

This document is generated. Every figure below is read from
`measurements.json`, which is produced by the same run.

## Can the join be made at all

The record set holds 132,520 wildfire damage-inspection
records. 2 records in the published file describe a
hazard other than fire and are excluded here rather than counted as wildfire.

| Outcome | Share | Records | Of | 95% interval |
|---|---:|---:|---:|---|
| placed in exactly one published territory | 62.1% | 82,353 | 132,520 | 61.9% to 62.4% |
| inside two or more published territories | 37.9% | 50,167 | 132,520 | 37.6% to 38.1% |
| inside no published territory | 0.0% | 0 | 132,520 | 0.0% to 0.0029% |
| coordinate not usable | 0.0% | 0 | 132,520 | 0.0% to 0.0029% |

A record inside two or more published territories is not awarded to either.
The publisher states that the boundaries are approximate and that not all
entities are represented, so public data does not say which entity such a
record belongs to, and this project does not decide on its behalf.

## Do the records that can be attributed look like the ones that cannot

| Population | Destroyed share | Destroyed | Inspected | 95% interval |
|---|---:|---:|---:|---|
| destroyed share among placed records | 53.0% | 43,609 | 82,353 | 52.6% to 53.3% |
| destroyed share among contested records | 53.4% | 26,780 | 50,167 | 52.9% to 53.8% |
| destroyed share among records in no published territory | not measured | 0 | 0 | not measured |

Difference, placed minus contested: -0.4% (-1.0% to 0.1%, Newcombe score).

The interval includes zero, so this comparison does not establish a difference between the two populations.

## Every published territory, in name order

Counts, and two within-territory shares. No damage rate is published for a
territory and no territory is ordered against another. The concentration
column is why: where one incident supplies most of a territory's records, a
territory-level damage rate would be a statement about that one fire.

A territory appears in more than one row of the contested count, because a
record inside three outlines is contested for all three.

| Territory | Type | Placed | Contested | Incidents | Largest incident share | Within 250 m of the edge | Geometry |
|---|---|---:|---:|---:|---|---|---|
| Aha Macav Power Service | Tribal | 0 | 0 | 0 | not measured | not measured | as_published |
| Alameda Power & Telecom | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Anza Electric Cooperative, Inc. | CO-OP | 305 | 0 | 11 | 39.0% | 5.2% | as_published |
| Azusa Light & Power | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Bear Valley Electric Service | IOU | 0 | 0 | 0 | not measured | not measured | as_published |
| Biggs Municipal Utilities | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Burbank Water & Power | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| City and County of San Francisco - Hetch Hetchy Water and Power | POU | 0 | 4 | 0 | not measured | not measured | repaired |
| City of Anaheim Public Utilities Department | POU | 0 | 46 | 0 | not measured | not measured | as_published |
| City of Banning Electric Department | POU | 23 | 0 | 2 | 69.6% | 95.7% | as_published |
| City of Cerritos | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| City of Corona Department of Water & Power | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| City of Healdsburg Electric Department | POU | 0 | 69 | 0 | not measured | not measured | repaired |
| City of Industry | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| City of Lompoc Electric Division | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| City of Needles | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| City of Palo Alto | POU | 0 | 0 | 0 | not measured | not measured | repaired |
| City of Pittsburg | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| City of Riverside | POU | 0 | 42 | 0 | not measured | not measured | as_published |
| City of Shasta Lake | POU | 25 | 0 | 1 | 100.0% | 0.0% | as_published |
| City of Ukiah Electric Utilities Division | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| City of Vernon Municipal Light Department | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Colton Electric Utility Department | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Eastside Power Authority | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Glendale Water & Power | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Gridley Electric Utility | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Imperial Irrigation District | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Kirkwood Meadows Public Utility District | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Lassen Municipal Utility District | POU | 203 | 85 | 10 | 47.3% | 20.7% | as_published |
| Lathrop Irrigation District | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Liberty Utilities | IOU | 1,512 | 0 | 2 | 73.8% | 5.0% | as_published |
| Lodi Electric Utility | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Los Angeles Department of Water & Power | POU | 18 | 9,794 | 2 | 77.8% | 0.0% | repaired |
| Merced Irrigation District | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Metropolitan Water District of So. Cal | POU | 0 | 37,727 | 0 | not measured | not measured | repaired |
| Modesto Irrigation District | POU | 0 | 40 | 0 | not measured | not measured | as_published |
| Moreno Valley Utility | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Morongo Band of Mission Indians | Tribal | 0 | 0 | 0 | not measured | not measured | as_published |
| PacifiCorp | IOU | 1,957 | 1 | 32 | 22.9% | 0.9% | as_published |
| Pacific Gas & Electric Company | IOU | 65,865 | 12,285 | 271 | 35.9% | 0.4% | repaired |
| Pasadena Water & Power | POU | 0 | 1,880 | 0 | not measured | not measured | as_published |
| Plumas-Sierra Rural Electric Cooperative | CO-OP | 1,060 | 85 | 5 | 48.5% | 4.4% | as_published |
| Port of Oakland | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Port of Stockton | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Power and Water Resource Pooling Authority | POU | 0 | 12,310 | 0 | not measured | not measured | repaired |
| Rancho Cucamonga Municipal Utility | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Redding Electric Utility | POU | 399 | 0 | 2 | 99.7% | 21.6% | as_published |
| Roseville Electric | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Sacramento Municipal Utility District | POU | 10 | 0 | 2 | 60.0% | 0.0% | as_published |
| San Diego Gas & Electric | IOU | 608 | 620 | 8 | 73.4% | 0.0% | as_published |
| Shelter Cove Resort Improvement District | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Silicon Valley Power | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Southern California Edison | IOU | 9,638 | 25,345 | 46 | 16.2% | 1.6% | repaired |
| Surprise Valley Electrification Corporation | CO-OP | 41 | 1 | 5 | 82.9% | 0.0% | as_published |
| Trinity Public Utilities District | POU | 574 | 0 | 5 | 50.5% | 0.0% | as_published |
| Truckee Donner Public Utilities District | POU | 0 | 0 | 0 | not measured | not measured | as_published |
| Turlock Irrigation District | POU | 115 | 0 | 1 | 100.0% | 19.1% | as_published |
| Valley Electrical Association | CO-OP | 0 | 0 | 0 | not measured | not measured | as_published |
| Victorville Municipal Utilities Services | POU | 0 | 0 | 0 | not measured | not measured | as_published |

## Where the published boundaries overlap

Counts of records falling inside each combination of published outlines. This
is a description of the boundary layer, not of any utility. The combinations
are listed by size because size is what is being reported.

| Published outlines a record falls inside | Records |
|---|---:|
| Metropolitan Water District of So. Cal, Southern California Edison | 25,345 |
| Pacific Gas & Electric Company, Power and Water Resource Pooling Authority | 12,241 |
| Los Angeles Department of Water & Power, Metropolitan Water District of So. Cal | 9,794 |
| Metropolitan Water District of So. Cal, Pasadena Water & Power | 1,880 |
| Metropolitan Water District of So. Cal, San Diego Gas & Electric | 620 |
| Lassen Municipal Utility District, Plumas-Sierra Rural Electric Cooperative | 85 |
| City of Healdsburg Electric Department, Power and Water Resource Pooling Authority | 69 |
| City of Anaheim Public Utilities Department, Metropolitan Water District of So. Cal | 46 |
| City of Riverside, Metropolitan Water District of So. Cal | 42 |
| Modesto Irrigation District, Pacific Gas & Electric Company | 40 |
| City and County of San Francisco - Hetch Hetchy Water and Power, Pacific Gas & Electric Company | 4 |
| PacifiCorp, Surprise Valley Electrification Corporation | 1 |

## The published polygons, as they arrived

59 outlines were read as electric service
territories. 8 of them failed an OGC validity
check on retrieval and were repaired before any containment question was asked
of them, because an invalid polygon answers that question undefined rather than
refusing it. The repaired ones are named here and flagged in the table above.

- City and County of San Francisco - Hetch Hetchy Water and Power
- City of Healdsburg Electric Department
- City of Palo Alto
- Los Angeles Department of Water & Power
- Metropolitan Water District of So. Cal
- Pacific Gas & Electric Company
- Power and Water Resource Pooling Authority
- Southern California Edison

75,521 placed records, 91.7% of the placed total (91.5% to 91.9%), sit inside one of those
repaired polygons. A different repair would place a different set, so that
figure is the size of this project's exposure to the choice.

0 outlines could not be repaired into a testable
shape. Those are removed from the index and are not reported as holding
zero records.

Two published entity types are not read as service territories:

- **ADMIN**: A federal power marketing administration. The polygon is a marketing and transmission administration area, not a retail service territory.
- **CCA**: A community choice aggregator procures energy for customers inside another entity's distribution footprint. Its polygon overlays a territory rather than being one, so counting a record into both would count it twice.

## The span of the record set

| Incident year | Records |
|---:|---:|
| 2013 | 279 |
| 2014 | 310 |
| 2015 | 3,192 |
| 2016 | 944 |
| 2017 | 12,757 |
| 2018 | 28,403 |
| 2019 | 2,108 |
| 2020 | 28,626 |
| 2021 | 12,253 |
| 2022 | 3,009 |
| 2023 | 229 |
| 2024 | 8,117 |
| 2025 | 32,293 |

## What this does not measure

- **Nothing about physical infrastructure.** No pole, conductor, substation, or
  circuit position is read, inferred, approximated, or published, from these
  sources or any other. An analysis that would need one is not built here.
- **No comparison between utilities.** A territory's damage figures are driven
  by which fires burned in it, and the concentration column shows how strongly.
  Nothing here says any utility is more or less exposed than any other.
- **No rate against population, housing, customers, or meters.** The record set
  is defined by fire and by state responsibility area. A denominator drawn from
  a differently defined population would not contain this numerator.
- **Coverage is not exposure.** A territory with few placed records may have
  burned little, may sit mostly outside the state responsibility area, or may
  have most of its records contested. These are different facts and this
  project does not merge them.
