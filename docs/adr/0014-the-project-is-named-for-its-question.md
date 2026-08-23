# 14. The project is named for its question: wildfire-service-territory-overlap

Date: 2026-08-23

## Status

Accepted. Renames the distribution, the package, and the repository in one motion.

## Context

The project was named `inspected`, a nod to the D of CAL FIRE's Damage INSpection data.
Two problems surfaced. First, the name says how an input file is called and nothing
about what this project measures: whether a burned structure can be attributed to one
published electric service territory, and how much of the record set lands instead in
contested ground where two or more published outlines overlap. Second, and more
concretely, `inspected` on PyPI belongs to an unrelated code-description tool, which
blocked the roadmap's distribution item regardless of what happens with the `perimeter`
pin.

The rename was required to carry the question itself. Every word of
`wildfire-service-territory-overlap` is load-bearing: wildfire (the hazard filter that
defines the record set), service territory (the CEC layers this project measures
against), overlap (the mechanism by which a record becomes contested). California sits
in the description rather than the name; CAL FIRE and CEC anchor it already.

## Decision

One identity everywhere, accepted at full length:

- repository: `ChelseaKR/wildfire-service-territory-overlap`;
- distribution and import name: `wildfire-service-territory-overlap` /
  `wildfire_service_territory_overlap`;
- console script and module entry points renamed to match;
- the User-Agent names the new project and repository.

A shorter split identity (descriptive distribution, short import) was considered and
rejected: two names for one thing is exactly the confusion class the `perimeter`
Dependabot collision documents. This pipeline is imported rarely by third parties, so
import length costs little.

## Consequences

No measurement changes. The published pair is untouched by a rename, because no input,
field, rule, or formula moved; the determinism gate holds as before. The v0.1.0 tag and
GitHub release keep their original names and artifacts under GitHub's redirect, and the
old repository URL redirects indefinitely. The next release ships on PyPI under the new
distribution name, which is available there today. Historical records keep their old
wording on purpose: ADR 0001's title uses "inspected" as an ordinary English word about
inspected structures, and the 0.1.0 CHANGELOG section describes the release as it
shipped.
