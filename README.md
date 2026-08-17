# inspected

**Can a California wildfire damage inspection be attributed to a published electric
service territory? For 37.9% of the record set, using public data alone, no.**

**Unofficial. Not affiliated with, endorsed by, or approved by CAL FIRE, the California
Energy Commission, SMUD, or any electric utility.** This is descriptive geography over
two public datasets. It is not a risk rating of any company, it ranks nobody, and it
contains no information about the location of anybody's infrastructure.

**Status:** Beta, version `0.1.0`, no tag cut. Measured against pinned retrievals of
CAL FIRE DINS and the CEC Electric Load Serving Entities layers, all three retrieved
2026-08-17. The figures move only when those retrievals are deliberately refreshed.

## Quick start

```bash
uv sync --locked
make verify                # lint, types, tests, coverage floor, determinism
```

Then read [`published/REPORT.md`](published/REPORT.md), which is generated, and
[`published/measurements.json`](published/measurements.json), which it is generated from.
`make report-offline` rebuilds the whole pipeline over committed fixtures, offline, in
about a second.

## The question, and why it is worth asking

The useful wildfire analysis for an electric utility joins fire outcomes to network
assets. Asset locations are not public and should not be. So the question that can be
asked from public data is the one below it: **given a structure that burned, which
published service territory boundary is it inside?**

That sounds like a solved problem. Both inputs are public: CAL FIRE publishes 132,522
damage-inspection records with coordinates, and the California Energy Commission
publishes service territory outlines for investor-owned utilities, publicly owned
utilities, cooperatives and tribal utilities. The join is a point-in-polygon.

It does not come out clean, and how it fails is the finding.

## What was measured

Over the 132,520 records the published file marks as wildfire, out of 132,522 total:

| Outcome | Records | Share | 95% interval |
|---|---:|---:|---|
| Inside exactly one published territory | 82,353 | 62.1% | 61.9% to 62.4% |
| Inside two or more published territories | 50,167 | 37.9% | 37.6% to 38.1% |
| Inside no published territory | 0 | 0.0000% | 0.0000% to 0.0029% |
| Coordinate not usable | 0 | 0.0000% | 0.0000% to 0.0029% |

Wilson score intervals. The denominator is the wildfire record set, stated on every row.

**More than a third of the record set is inside more than one published outline.** The
CEC's own metadata says why: *"Boundaries are approximate, for absolute territory
information, contact the appropriate load serving entity."* The published polygons do not
tile the state, they overlap, and the overlaps are not small. A water wholesaler's
published area covers much of southern California and contests records with six other
entities. A pooling authority for agricultural water districts overlays part of the
Central Valley and contests 12,241 records with one investor-owned utility. For a
record inside two outlines, public data does not say which entity serves it, and this
project does not decide on its behalf: it is counted as contested and it is never awarded
to the larger polygon, the smaller one, or the one listed first.

**The records that cannot be attributed look like the ones that can.** Destroyed share
among placed records: 52.95% of 82,353. Among contested records: 53.38% of 50,167.
Difference of minus 0.43 percentage points, Newcombe interval minus 0.98 to plus 0.13.
The interval includes zero, so this comparison does not establish that the attributable
subset is unrepresentative on damage outcome. That is the useful half of a bad result: a
third of the data cannot be attributed, but on this dimension it does not appear to be a
biased third.

**A territory-level damage rate would describe one fire, not a territory.** Which is why
no such rate is published here in any form. The evidence is published instead, as the
share of each territory's placed records contributed by its single largest incident: two
territories are at 100%, a third at 99.7%, a fourth at 82.9%. Dividing destroyed by inspected
inside those boundaries and printing the answers next to each other would produce a
league table of which fires happened where, labelled with company names.

**91.7% of the placed records depend on a geometry repair.** Eight published polygons
fail an OGC validity check on retrieval, and two of the eight are the largest territories
in the state. An invalid polygon answers a containment question undefined rather than
refusing it, so each is repaired before use, named in the report, and flagged on its row.
A different repair places a different set of records. That figure is the size of the
exposure, published rather than left implicit.

## The rules this project is built on

**Every published rate carries its denominator and its interval.** Not by convention:
`Rate` cannot be constructed without a denominator, and `artifacts.check_all` refuses to
write an artifact containing a rate-shaped object missing either. A rate with a zero
denominator is not zero percent, it is not measured, and the writer refuses a
not-measured rate that carries a value.

**A measurement that could not be made is never a zero.** A coordinate outside California
is reported as not measured, not as uncovered. A territory with no placed records has no
boundary-proximity bands, not a row of zeros.

**Nothing here touches infrastructure.** No pole, conductor, substation, or circuit
position is read, inferred, approximated, or published, from these sources or any other.
The CEC layers are administrative outlines. An analysis that would need an asset location
is not built here.

**No utility is compared to another.** Every collection in the output is sorted by name,
`assert_no_ranking` refuses an artifact key that scores or grades, and
`tests/test_published.py` reads the generated report for comparative phrasing.

**An acquisition that fetched part of a dataset must not report as complete.** Each layer
is asked for its own record count before and after the walk, identifiers must come back
strictly increasing and unique, and a walk that fails any of those writes nothing. The
DINS walk is [`perimeter`](https://github.com/ChelseaKR/perimeter)'s, pinned to a commit;
these checks are applied to its output rather than assumed of it.

## Relationship to `perimeter`

[`perimeter`](https://github.com/ChelseaKR/perimeter) measures the completeness of the
DINS file itself: how many cells in each field hold a value, how many hold a code meaning
unknown, how many hold nothing. This project takes the file as given and asks a different
question, about geography rather than about fields, and consumes `perimeter` as a
dependency rather than re-implementing its acquisition. Nothing here repeats a
measurement published there.

## Layout

```
src/inspected/
  sources.py     provenance and the publishers' own caveats, quoted
  acquire.py     the only module that opens a socket; run by hand, never in CI
  geometry.py    the pinned projection, the validity ledger, boundary distances
  placement.py   the four outcomes, and the schema guard on the retrieval
  intervals.py   Wilson and Newcombe; the only route a proportion takes to an artifact
  measure.py     the measurements, and a written record of the ones not built
  artifacts.py   the publication rules, enforced before anything is written
  report.py      the generated document
published/       measurements.json and REPORT.md, from the real retrievals
fixtures/        hand-written, never sampled from the real file
docs/adr/        the decisions, with their reasoning
```

## What still needs a person

- Nobody with California utility service territory expertise has reviewed the decision to
  read CEC's `CO-OP` and `Tribal` types as service territories and to exclude `CCA` and
  `ADMIN`. The reasoning is in `docs/adr/0002`.
- The overlap finding has not been raised with the publisher. CEC's metadata invites
  reports of missing territories at the address in its own text; whether the overlaps are
  intended is not established here.
- The 91.7% repair exposure is measured but its sensitivity is not: the alternative repair
  strategies have not been run against each other.

## Standards conformance

Held to the portfolio's shared engineering standards, pinned in `.standards-version` to
`v2.0.0`. Every row states what is true on 2026-08-17, not what is intended.

The applicability manifest has no entry for this repository, so nothing has decided which
standards bind it. The scoping below was derived here and a manifest entry supersedes it.

| Standard | State |
|---|---|
| Code Quality | Applies: uv, ruff, mypy `--strict`, pytest with branch coverage against a 90% floor, complexity capped at 10, `uv lock --check` as the drift gate and `uv sync --locked` as the install |
| Security & Supply-Chain | Applies: semgrep, gitleaks, pip-audit, CodeQL over actions and python, zizmor over the workflows, every action SHA-pinned, `permissions: contents: read` at the top of every workflow, `persist-credentials: false` on every checkout. Not met: no SBOM, no OpenSSF Scorecard workflow, no osv-scanner alongside pip-audit |
| CI/CD | Applies (not met): `main` carries no ruleset and no branch protection, so the gates report and block nothing. Applying a protection profile is a live repository setting and the owner's call |
| Observability | Applies (Tier C): A library and a CLI writing to stdout. No hosted service, no telemetry, no SLO surface. Not met: no operations runbook |
| Accessibility | Applies (not met): Output is Markdown and JSON, with no rendered UI and no colour encoding, so WCAG has little surface here. Not met: no ACR, and the generated tables have not been read with a screen reader |
| Internationalization | Applies (not met): `docs/I18N.md` records the declaration. English only, no catalog |
| AI Evaluation | N/A: No model, no LLM, no generated text anywhere in the pipeline or the output |
| Quality & Metrics | Applies: Fail-closed gates throughout: the retrieval schema guard, the acquisition completeness checks, the publication rules, the coverage floor, and a determinism gate whose own failure modes are tested. Not met: no Definition of Done, no metrics ledger |
| Documentation | Applies: README, `PROVENANCE.md`, `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `CITATION.cff`, a `docs/adr/` log, this table, and a `.standards-version` pin a test reads |
| Release & Versioning | Applies (not met): Version `0.1.0` in `pyproject.toml` and `CITATION.cff`, no tag cut, no signed tag, no published artifact. A hardened three-job release workflow is committed, its allowed-signers list names no principal, and it has never run |
| Responsible-Tech Framework | Applies: Unofficial framing on the README and on the generated report, no claim about any utility's posture, no address, parcel number, assessed value or coordinate republished, no ranking of any named company, and an acquisition that stops rather than routing around an access control. Not met: no dated ethics or residual-risk artifacts |
| Performance | Applies (not met): A CLI over local files. The full build runs in about 50 seconds, dominated by boundary distances; no budget is recorded |
| Incident Response | Applies: `SECURITY.md` routes reports to GitHub private vulnerability reporting with a 72-hour acknowledgment target. Not met: no severity convention, no secret-leak runbook |
| Data Governance | Applies (L1, handled above the tier): Openly licensed public civic data, republished only as counts. `data/raw/` is gitignored, the address and parcel columns are never fetched, fixtures are hand-written rather than sampled, and a test refuses a published artifact carrying a coordinate. Not met: no refresh cadence or staleness SLA |
| AI Development Measurement | Applies (not met): No baseline and no outcome metrics recorded for this repository's development stream |

## Licence

Apache-2.0. Source data is published by CAL FIRE under a Creative Commons Attribution
licence and by the California Energy Commission under its own conditions of use, and is
reproduced here only as counts.
