# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Draft letters to the CEC under `docs/outreach/`: one reporting the twelve measured
  boundary overlaps the publisher's own metadata invites feedback on, and one
  requesting written definitions for the six `Type` values that nothing published by
  the party using them defines. Both are marked draft and unsent; sending dates and
  outcomes belong in `PROVENANCE.md`.
- Edge bands for contested groups. Each overlapping combination now carries how
  much of it sits within 100, 250, 500 and 1000 metres of the nearest edge among the
  outlines involved, with its own denominator and Wilson interval: a contested record
  stops being contested when any outline in its combination ceases to contain it, so
  that nearest edge is what an approximation error moves first. A combination near
  100% at 250 metres is a thin seam between outlines; one near 0% is interior ground
  two published territories genuinely cover together. The report's overlap table gains
  the 250 metre column and still renders artifacts from before it existed unchanged.
- `main` is protected by a branch ruleset: force push and deletion refused, every
  change arriving as a merged pull request, the six PR-facing checks required green,
  no bypass actors. The ci.yml header paragraph that recorded the gates as reporting
  without blocking is rewritten to match.

### Changed

Nothing else yet under Unreleased.

## [0.1.0] - 2026-08-18

First release. One entry, because no earlier tag exists: the first measurement and the
work recorded against it before any tag was cut all ship together. Amended 2026-08-22,
before the tag was cut, to fold in the roadmap execution that shipped the same day.

### Added on 2026-08-22, folded in before the tag was cut

- The governance documents from Phase 1 of the roadmap:
  `docs/RESPONSIBLE-TECH.md` (dated ethics statement and residual-risk table),
  `docs/DEFINITION_OF_DONE.md` (done by kind of change),
  `docs/METRICS_LEDGER.md` (baseline and outcome per development stream, gaps
  recorded as unmeasured rather than reconstructed), and `docs/ACR.md` (a static
  accessibility conformance review of the generated output that says plainly it was
  not performed with assistive technology). `SECURITY.md` gains severity levels fitted
  to what a defect could publish or sign, plus the secret-leak procedure.
- ADR 0012, written before the data exists: when the second territory-layer
  retrieval lands, comparisons against the first are paired per-value diffs and
  per-record transition counts, never a modelled direction. Each snapshot keeps its
  own denominator, nothing is differenced into a single headline, and any figure
  spanning both retrievals dates its rows. The by-year cut keeps ADR 0008's no-trend
  rule unchanged within each snapshot.
- A third geometry repair in the sensitivity run. GEOS' structure-preserving
  `make_valid` joins `make_valid` and `buffer(0)` in `REPAIR_STRATEGIES`, the whole
  record set is placed under each, and the comparison publishes a pairwise
  disagreement count for every pair plus a union count bounding how much of the result
  the choice of repair can move. The default does not move; see `docs/adr/0011`. The
  committed `published/` tree still describes the two-repair run against the
  2026-08-17 pin and keeps rendering exactly as written; the three-repair census
  reaches it at the next deliberate refresh.
- A performance budget with a gate on it. `tests/test_performance_budget.py` runs
  the offline fixture build against a recorded 30 second ceiling, generous by design:
  wall clock does not compare across machines, so the budget catches order-of-magnitude
  regressions over byte-identical inputs rather than load noise.
- An operations runbook, `docs/RUNBOOK.md`: the refresh procedure start to finish,
  what each acquisition refusal (`AcquisitionBlocked`, `AcquisitionFailed`,
  `IncompleteAcquisition`) means and what to do, what each build-time gate failure
  means, and the things that must never happen.
- A refresh cadence and a staleness SLA, replacing the recorded absence of both.
  A pin is refreshed at least every twelve months and on three triggers: age of the
  retrieval against continuous fire seasons, a publisher-side last-modified date later
  than the pin on either territory layer, and any change to this pipeline itself,
  which cannot reach an old pin because `data/raw/` is never committed. Every refresh
  stays hand-run, is compared against the artifact it replaces with
  `python -m inspected.artifact_diff` before anything is committed, and writes what
  moved into `PROVENANCE.md`.
- `inspected.artifact_diff`: the leaf-by-leaf refresh comparison from
  `PROVENANCE.md`, promoted from a hand-run exercise into a command.
  `python -m inspected.artifact_diff OLD NEW` reports every added, changed and removed
  value at its path in both trees, pairs list rows by their identifying field where one
  exists so a reordered collection stays silent and a changed row stays attached to its
  name, and refuses to exit zero when published values disappear unless
  `--allow-removals` names the removal deliberate.
- An osv-scanner job in CI, reading the same `uv.lock` that `uv sync --locked`
  installs from, against the OSV database: a second vulnerability feed beside
  pip-audit, failing closed on any reported advisory.
- An OpenSSF Scorecard workflow, publishing results and uploading the SARIF to code
  scanning on a weekly schedule.
- A reproducible CycloneDX SBOM in the release build, generated over the locked build
  environment after `make verify`, attached to the release next to the wheels and
  covered by the provenance attestation.

### Added

- Placement coverage over CAL FIRE DINS against the California Energy Commission's
  published electric service territory outlines: how much of the wildfire record set
  falls inside exactly one territory, inside more than one, inside none, or carries a
  coordinate that cannot be used. Every share carries its denominator and a Wilson
  interval.
- A representativeness check between the placed and contested populations, with a
  Newcombe interval on the difference, so a reader can see whether the third of the
  record set that cannot be attributed resembles the two thirds that can.
- Per-territory counts in name order, with the share of each territory's placed records
  contributed by its single largest incident. No damage rate is published for any
  territory and no territory is ordered against another.
- Boundary-proximity bands at 100, 250, 500 and 1000 metres, operationalizing the
  publisher's statement that the boundaries are approximate.
- A geometry ledger naming the eight published polygons that arrive failing an OGC
  validity check, and measuring what share of the placed total depends on the repair.
- `artifacts.check_all`: publication rules enforced before anything is written. A rate
  without a denominator or an interval, a not-measured rate carrying a zero, a coordinate
  or parcel field, a collection long enough to be a record listing, a key that ranks or
  scores, or territory rows out of name order each refuse the write.
- Acquisition guards on top of the walk consumed from `perimeter`: the layer's own record
  count read before and after, identifiers required to be strictly increasing and unique,
  and nothing written when any of those fails.
- A schema guard on the retrieval, so a file fetched without `HAZARDTYPE` raises instead
  of filtering to zero fire records and producing an honest, empty, misleading report.
- **The county cut, and the pin refresh it needed.** `COUNTY` is the eighth field the
  acquisition requests, and the contested share is published per county with its own two
  denominators and a Wilson interval, in name order. 52 counties are named in the record
  set, 30 records carry no county name, and in 36 of the 52 counties the contested share
  is zero rather than merely low. No damage rate is published for a county, for the same
  reason none is published for a territory. See `docs/adr/0009`.
- **What the refresh moved: nothing.** The artifact built after the re-acquisition was
  compared against the one built before it at every published value. 4,370 values, none
  removed, none changed. The re-acquired DINS file is byte-for-byte the previously pinned
  file once the new column is removed, and both territory layers returned the hashes
  already recorded. `PROVENANCE.md` states this rather than leaving a reader to assume it.
- **What an outline that holds no record is worth.** 35 of the 59 indexed outlines hold
  no record; 0 of 132,520 records fall inside any of them; removing all 35 and placing
  the whole record set again changes the outcome of 0 records. This is a count, not a
  classification: it does not say whether any named entity belongs in the set, it says
  that for 35 of the 59 the answer cannot move a figure published here. See
  `docs/adr/0010`.
- `inspected.sensitivity`: the two judgment calls in this project, re-run over the whole
  record set and published with their denominators and intervals rather than argued for.
  - **The inclusion rule.** Seven readings of the publisher's `Type` field, each one the
    entire record set placed again. Reading `CO-OP` and `Tribal` as service territories,
    the unreviewed half of the rule, is worth 0.065 percentage points on the headline;
    dropping `Tribal` changes nothing at all; dropping `CO-OP` would publish 1,406
    records as inside no published territory. Reading `CCA` as a territory would take the
    contested share to 56.3% and `ADMIN` to 74.4%. The rule is unchanged. See
    `docs/adr/0006`.
  - **The geometry repair.** `make_valid` and `buffer(0)` both run to completion. 927
    records, 0.70% of the record set with an interval of 0.66% to 0.75%, come out
    differently; 770 move from placed to contested and 157 are contested under both but
    between a different pair of outlines. An earlier draft's note that the two disagreed
    on "roughly 770 placements" was a recollection and it missed those 157. See
    `docs/adr/0007`.
- Whether being unattributable is a property of the data or of the fire. 94.3% of the
  405 incidents in the record set fall entirely on one side of the contested line, with
  the contested share by incident year running from 0.0% to 92.5%. No trend is drawn
  through the years and the artifact says why: the territory layer is a single retrieval,
  so every year is measured against identical boundaries. See `docs/adr/0008`.
- That CEC documents none of the six `Type` values is stated in the output and in
  `PROVENANCE.md`, checked against the layer metadata, the FGDC record and the item
  resources on the retrieval date.

### Changed

- Containment narrows by bounding box and then tests against a prepared geometry, rather
  than calling `STRtree.query(predicate="intersects")`, which does not use a prepared
  geometry and re-walks every ring on every test. The full build runs in about 18 seconds
  doing twelve placements of the record set where it took about 50 doing one. A test
  holds the two forms to identical answers, and every published figure is unchanged.
- The Dependabot uv updater failed on every run and therefore checked nothing. The cause
  is a name collision rather than a broken pin: `perimeter` here is a direct git
  reference, and the name on PyPI belongs to an unrelated Django package. It is ignored
  in `.github/dependabot.yml` with that written out, because publishing under this name
  is not available and dropping the URL would resolve somebody else's package.
- The release build writes no Actions cache. `setup-uv` enables one by default on a
  hosted runner, which made the release job a cache write in the `main` scope readable by
  every other workflow, for no reuse a once-per-release build can collect. It does not
  clear `actions/cache-poisoning/poisonable-step`, which the first attempt assumed it
  would: running the workflow moved the alert to `make verify` instead. The query is
  about executing code from an untrusted checkout rather than about writing a cache, so
  every release workflow that builds the commit it releases carries it.
- The CodeQL gate now fails on any finding that is not written down in
  `.github/codeql-accepted.json`, and equally on an entry there whose finding has gone
  away. Two entries today, both on the release build and both reducing to the same fact:
  the job runs a commit that `authorize` has already proved is a signed annotated tag on
  main, which is a runtime check the queries cannot see.
- An interval whose two ends round to the same string is now printed at more decimal
  places until they differ. `0.7% to 0.7%` reads as certainty.
- The repair strategy and the set of included types are parameters on
  `geometry.load_territories`. `geometry.repair` refuses a strategy that is not in
  `REPAIR_STRATEGIES`, so a new repair cannot be used before it has been compared against
  the one in force.
- The per-year record counts moved from a standalone `years` block into the new
  measurement, where each year carries both its record count and the classified count
  that is the denominator of its share.

### Notes

- `perimeter` is consumed as a pinned git dependency rather than vendored. Its paged walk
  is the one this project uses for the damage inspections, and re-implementing it would
  mean re-implementing a defect that has already been found and fixed once.
- `data/raw/` is not in git and never will be.
