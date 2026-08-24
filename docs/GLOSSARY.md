# Glossary

Terms used across the wildfire service territory overlap analysis, defined in the
context of this repository with references to authoritative sources.

### ADMIN
A federal power marketing administration outline published by the California Energy
Commission, specifically the Western Area Power Administration (WAPA). Classified as a
marketing and wholesale transmission footprint rather than a retail electric service
territory, and excluded per [ADR 0002](adr/0002-which-published-outlines-are-service-territories.md).

### Boundary band
A buffer distance (such as 100 meters, 500 meters, or 1 kilometer) measured from a
contested polygon border inward to test whether an overlapping damage record lies close to
the boundary line. Defined in [ADR 0012](adr/0012-two-boundary-retrievals-are-compared-paired-never-modelled.md)
and computed in `src/wildfire_service_territory_overlap/placement.py`.

### CCA
A Community Choice Aggregator established under California Public Utilities Code Section 331.1.
CCAs procure power supply for customers within an incumbent distribution utility's area,
making their boundaries an administrative overlay rather than a distinct physical wires
territory; excluded per [ADR 0002](adr/0002-which-published-outlines-are-service-territories.md).

### CO-OP
An electric cooperative utility owned and operated by the customers it serves. Read as a
valid electric service territory in this analysis per
[ADR 0002](adr/0002-which-published-outlines-are-service-territories.md).

### Contested record
A damage inspection record whose geographic coordinates fall inside two or more distinct
published electric service territory polygons. Reported as an unresolvable overlap in
public data without arbitrary tie-breaking per
[ADR 0003](adr/0003-contested-ground-is-reported-never-resolved.md).

### DINS
The CAL FIRE Damage Inspection database, which records post-fire field inspections of
damaged or destroyed structures with geographic coordinates and damage classifications.
Documented in [PROVENANCE.md](../PROVENANCE.md) and fetched from the CAL FIRE open data portal.

### IOU
An Investor-Owned Utility, a private commercial electric utility regulated by the
California Public Utilities Commission (CPUC). Read as a valid electric service territory
per [ADR 0002](adr/0002-which-published-outlines-are-service-territories.md).

### LSE (Load Serving Entity)
An electric utility, cooperative, or other entity responsible for providing electric
service to retail customers within a designated territory. Sourced from the California
Energy Commission (CEC) electric load serving entity boundary layers described in
[PROVENANCE.md](../PROVENANCE.md).

### Newcombe score interval
A confidence interval method for calculating the difference between two independent
proportions without relying on normal approximation assumptions. Implemented in
`src/wildfire_service_territory_overlap/intervals.py` and used to compare sensitivity
variations against baselines.

### OGC validity check and geometry repair
The process of validating polygon boundaries against Open Geospatial Consortium (OGC)
simple feature standards and applying deterministic topological repairs to invalid geometries.
Evaluated across three distinct repair strategies in
[ADR 0005](adr/0005-an-invalid-published-polygon-is-repaired-and-the-repair-is-measured.md),
[ADR 0007](adr/0007-the-two-repairs-are-run-against-each-other.md), and
[ADR 0011](adr/0011-a-third-repair-joins-the-comparison-and-the-default-does-not-move.md).

### POU
A Publicly Owned Utility, such as a municipal utility district, irrigation district, or
city department providing retail electric distribution. Read as a valid electric service
territory per [ADR 0002](adr/0002-which-published-outlines-are-service-territories.md).

### SRA (State Responsibility Area)
Land where the State of California (CAL FIRE) has financial and operational responsibility
for wildfire prevention and suppression. Defined under California Public Resources Code
Section 4102 and referenced in CAL FIRE inspection metadata.

### Tribal utility
An electric utility owned or operated by a federally recognized Native American tribe
serving tribal lands. Read as a valid electric service territory per
[ADR 0002](adr/0002-which-published-outlines-are-service-territories.md).

### Wilson score interval
An asymmetric confidence interval method for binomial proportions that maintains accurate
coverage even near 0% and 100% or with sparse subsets. Implemented in
`src/wildfire_service_territory_overlap/intervals.py` and used for all published rate intervals
per [ADR 0001](adr/0001-the-denominator-is-the-inspected-record-set.md).
