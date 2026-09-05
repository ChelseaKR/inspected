# Expansion roadmap

Drafted 2026-08-22 against `0.1.0` (tagged in `CHANGELOG.md`, not yet cut as a git tag).
This is a plan, not a promise: items land when their gates can hold, and any item here
that turns out to violate a rule in `docs/adr/` gets dropped rather than argued around.

**Status at 2026-08-23**: Phase 0 through Phase 2 are shipped except as noted. Items
0.2, 0.3 and 0.4 shipped in #2; 1.2 in #4; 1.4 in #5; 1.8 in #9; 1.3 in #6; 2.1 in #3;
2.5 in #7 with `docs/adr/0011`; 2.6 in #8; and 1.5, 1.7 and half of 1.6 in #9. With
the owner's approval, 0.1 shipped: signed annotated tag `v0.1.0`, verified against
`.github/allowed_signers`, released through the three-job workflow with wheel, sdist,
SBOM and provenance attestation attached; and 0.5 shipped as a branch ruleset on
`main` that is PR-only behind its six checks. It shipped carrying one bypass actor,
the repository admin role at `bypass_mode: always`, and was recorded here as carrying
none until 2026-08-28, when the ruleset was read back. The item ships as it stands,
with one deliberate bypass actor recorded rather than hidden: a required check the
pushing account can skip is a required check by agreement, and that is the posture,
not an oversight. On 2026-08-23,
1.1 shipped as a registration in the portfolio applicability manifest, superseding
this repository's own scoping table; 2.4 shipped as edge bands on the contested
groups; and the deliberate refresh carried 2.2 (`docs/adr/0013`, the coordinate-county
comparison over the new CDT source) and 2.3 (`STRUCTURECATEGORY`, representativeness by
structure class) into the published figures, diffed leaf by leaf against the pin they
replaced: nothing removed, nothing measured moved.

**Status at 2026-09-04**: the paragraph above stopped at 2026-08-23 and the merges
since went past it. #24 renamed the project (`docs/adr/0014`). #33 repaired four gates that
were numerically incapable of firing and two defects in published output, and filed the
backlog that became issues #16 to #23. #34 held the README's headline figures to the
published artifact.

Three items then moved partway, and each is recorded as partway rather than as done,
with the open half named and filed:

- **1.6** in #40. Six of the accessibility review's structural checks moved from a dated
  reading into rules that run on every build, and #61 made it seven. Still open: the
  assistive-technology pass, issue #49. No screen reader has touched these tables and
  no rule substitutes for one.
- **3.4** in #41. The comparison is decided in `docs/adr/0015` and built against
  hand-written fixtures, before the data exists, in the mould of `docs/adr/0012`. The
  search for a source finished on 2026-09-05 and `docs/adr/0018` records it. Its answer
  is not the one the row used to guess at: a qualifying set does exist, Napa County's own
  ATC damage assessments for 2020, collected by county building inspectors and carrying
  no address, parcel number or assessed value. It is not pinned, because the county names
  its two fires `GLASS COMPLEX 2020` and `NAPA LIGHTNING COMPLEX 2020` where CAL FIRE
  names them `Glass` and `LNU Lightning Cmplx`, so the comparison joins nothing and now
  refuses rather than reporting a naming convention as total disagreement. Still open,
  issue #53: a county set this project can join without deciding that two published names
  are one fire.
- **4.2** in #42. Every string the report prints on its own account lives in a catalog,
  and a second edition is a catalog rather than a second renderer. Still open: a Spanish
  catalog reviewed by somebody who reads Spanish, issue #55, and a decision about the
  row labels that live inside `measurements.json`, issue #56.

#60 then fixed four document defects and widened the document rules from three
documents to all thirty-three, which immediately refused a fourth nobody had read.

Still open: 3.1 and 3.2 wait for a human to send the letter drafts under
`docs/outreach/` (issues #50 and #51); 3.3 waits for a reviewer (issue #52); 4.1 waits
for an archive deposit (issue #54); 4.3 is corrected below rather than waiting; and 4.4
has no acquisition gap to contribute yet (issue #58).

## What constrains every item below

These are settled. No roadmap item may weaken them.

- **Contested ground is reported, never resolved** (ADR 0003). Nothing adds a tie-break,
  a default award, or a "best guess" placement.
- **No damage rate is published for a territory or a county**, ordered or not (ADR 0004,
  and the county note in `measure.py`). New cuts carry the contested share, coverage, and
   concentration evidence, not destroyed-over-inspected per named place or company.
- **No trend is drawn through incident years** while the territory layer is one retrieval
  (ADR 0008).
- **No infrastructure location** is read, inferred, or published. No address, parcel, or
  coordinate is republished (`artifacts.check_all` refuses them).
- **Nothing ranks.** Name order everywhere; `assert_no_ranking` stays load-bearing.
- **A measurement that could not be made is never a zero.**
- **Every new judgment call ships with its sensitivity**, the way the inclusion rule and
  the geometry repair did.

## Phase 0: Ship the release that exists

The pipeline is built, measured, and hardened; the release is not.

| # | Item | Gate it adds |
|---|---|---|
| 0.1 | Cut and push signed annotated tag `v0.1.0`; dispatch the release workflow from `main`; confirm the `allowed_signers` verification gate passes end-to-end | First real exercise of `release.yml`; the accepted CodeQL entries get re-read against the live run |
| 0.2 | SBOM for the release artifact (CycloneDX), attached to the release | Supply-chain: closes the "no SBOM" row |
| 0.3 | `osv-scanner` alongside `pip-audit` in `make audit` and CI | Second vulnerability feed; both must pass |
| 0.4 | OpenSSF Scorecard workflow, results published, regressions triaged like CodeQL findings | Scorecard fails the job or is written down with reasoning, same convention as `.github/codeql-accepted.json` |
| 0.5 | Branch ruleset / protection on `main`: PR-only, required checks = the `make verify` list (owner action, noted as such) | CI/CD standard moves from "not met" to met |

## Phase 1: Close the standards ledger

Each row below retires one "Not met" cell in the README conformance table.

| # | Item | Notes |
|---|---|---|
| 1.1 | Portfolio standards **manifest entry** for this repository, superseding the scoping derived in the README | Unblocks every other row; without it nothing has decided which standards bind |
| 1.2 | **Refresh cadence and staleness SLA.** Define what makes a retrieval stale (calendar age? publisher-side `last modified`? a major fire event?), and state it in the README status line | Data Governance L1; pairs with 2.1 |
| 1.3 | **Performance budget**, recorded and enforced. Full fixture build ~18 s today doing twelve placements; set the budget (e.g. offline `make verify` wall-clock ceiling) and add a slow-marked benchmark test that fails past it | Performance standard |
| 1.4 | **Operations runbook**: what each acquisition guard refusal means, how to run a deliberate refresh, what to do when the schema guard raises, how to rebuild `published/` | Observability Tier C |
| 1.5 | **Ethics / residual-risk artifact**, dated, restating the unofficial framing, the no-infrastructure rule, and what the measurements could be misread as | Responsible-Tech |
| 1.6 | **Accessibility pass on generated output**: read `REPORT.md` tables with a screen reader, write the ACR. Output stays Markdown/JSON, colour-free | Documents what already holds rather than adding UI |
| 1.7 | **Severity convention + secret-leak runbook** appended to `SECURITY.md` | Incident Response |
| 1.8 | **Definition of Done and metrics ledger** for this repo's development stream, including the AI-development baseline/outcome rows | Quality & Metrics |

## Phase 2: Deepen the measurement

Every item lands with its denominator, its interval, and (where it embeds a judgment)
its own sensitivity run.

| # | Item | Why it is in scope | Constraints |
|---|---|---|---|
| 2.1 | Promote the **leaf-by-leaf refresh diff** from a one-off in `PROVENANCE.md` into `tools/diff_artifacts.py`, wired into the refresh procedure | A published number changing quietly is the failure mode; the check exists once and should exist always | Refuses removed keys; emits the comparison artifact the way the 2026-08-17 refresh did |
| 2.2 | **Coordinate-county disagreement count.** Records whose coordinate falls in one county while the publisher's `COUNTY` field names another, counted, never corrected | The README already reports the county as published; counting the disagreement measures CAL FIRE's field without issuing a second opinion about where a structure is | Needs an ADR extending 0009; authoritative county boundaries used only to count; output is counts + interval, counties in name order |
| 2.3 | **Widen the fetched field set** behind the existing schema guard (candidate: structure class), then re-run the placed-vs-contested representativeness check within each class | One dimension (destroyed) shows the contested third is not biased; more dimensions make the claim sturdier or honestly weaker | Fields refused if address-adjacent; no new per-territory rates; sensitivity on any filter introduced |
| 2.4 | **Edge bands for contested groups.** Extend boundary-proximity bands from single territories to the overlap combinations | Quantifies how much of each overlap is thin-edge artefact versus interior overlap | Counts only; combinations stay largest-first (a size, not a ranking) |
| 2.5 | **A third geometry repair**, compared against `make_valid` and `buffer(0)` in the disagreement census | Two repairs bound the ambiguity from two sides; a third tightens or widens the bound | Only if a defensible third strategy exists; `REPAIR_STRATEGIES` gate already forces the comparison before adoption |
| 2.6 | **Design for a second territory-layer retrieval.** When boundaries are next deliberately refreshed, the by-year cut gains a second boundary set for the first time | ADR 0008's "no trend" rule will face a temptation it has not yet met: two retrievals invite a before/after story | Needs an ADR now, before the data exists: comparisons published as paired per-value diffs, never as a fitted direction |

## Phase 3: External grounding

The findings are locatable in the publisher's data; the publishers have not heard them.

| # | Item | Notes |
|---|---|---|
| 3.1 | **Overlap letter to the CEC.** The twelve named combinations are exactly what their metadata invites feedback about. Draft in-repo, send, record the outcome (response, silence, correction) in `PROVENANCE.md` | ADR 0003 calls the overlaps "fixable at the source"; this is the path to finding out |
| 3.2 | **Type-field domain request.** Ask the publisher for the documented meaning of the six `Type` values; the absence of any definition is already measured and stated in the output | Directly narrows the open half of ADR 0006 |
| 3.3 | **Expert review of the inclusion rule**, focused on the 24 indexed outlines that hold records (the other 35 provably move nothing, ADR 0010). Any resulting rule change lands as a new sensitivity row, not an edit | Listed under "What still needs a person"; the reviewer checks the publisher's classification, not this code |
| 3.4 | **Bounded county cross-check**: one county's own inspection records against this project's counts for that county | Tests the pipeline against ground truth outside CAL FIRE's file; scope kept to one county and reported as agreement/disagreement counts |

## Phase 4: Reach

| # | Item | Notes |
|---|---|---|
| 4.1 | **Archive and DOI** (e.g. Zenodo) for tagged releases; `CITATION.cff` already exists and should gain the DOI | Makes the negative result citable |
| 4.2 | **Spanish edition of `REPORT.md`**, generated from `measurements.json` with a reviewed string catalog; figures render identically in both languages | California's other language; requires an ADR amending the English-only declaration in `docs/I18N.md`. Numbers are never re-formatted per locale inside one artifact, and the determinism gate must hold across both editions |
| 4.3 | **PyPI distribution**: this project's own name is clear after the rename to `wildfire-service-territory-overlap`. The dependency's is not. **Corrected 2026-09-04**: the sequence this row used to state, publish `perimeter` first and then drop the URL, cannot be executed. The name `perimeter` on PyPI is held by an unrelated Django package from YunoJuno, checked against the PyPI API on 2026-09-04, so `perimeter` cannot publish under the name this project pins. This is `docs/adr/0014` one level down | The real sequence: `perimeter` picks a distribution name that is free, publishes under it, and then the pin here changes to that name. Two of those three steps are the other repository's call. Until then the direct reference stays, and the `allow-direct-references` comment in `pyproject.toml` keeps its reasoning. Issue #57 |
| 4.4 | **Upstream contributions to `perimeter`** where acquisition gaps surface here | The relationship is already "consume, don't re-implement"; contributing fixes keeps it that way |

## Explicit non-goals

Refused expansions, so nobody has to re-litigate them in an issue:

- Resolving contested records by any rule, including "smallest polygon wins".
- Territory-level or county-level damage rates, in any ordering, including unordered tables side by side.
- Trend lines across incident years within a single boundary retrieval.
- Anything requiring asset locations: circuit proximity, pole density, feeder mapping.
- Republishing addresses, parcels, or coordinates.
- Scores, grades, or league tables of named companies or places.
- Scheduled silent refreshes of the pins. A refresh stays deliberate, hand-run, and diffed (2.1).

## Definition of done for any item above

Tests covering the new behaviour and its refusal paths; a sensitivity run if the item
embeds a judgment; an ADR if it changes one; `CHANGELOG.md` entry; `published/`
regenerated only through the deliberate-refresh procedure; `make verify` green,
determinism gate included; the README conformance table updated to state what became
true, not what is intended.
