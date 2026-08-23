# Metrics ledger

One row per development stream, with the baseline and the outcome stated where they
were measured, and "not measured" where they were not. A ledger that only records
flattering streams is a press release; the honest gaps stay visible here on purpose.

| Stream | Window | Baseline | Outcome | Notes |
|---|---|---|---|---|
| Initial build through v0.1.0 | before 2026-08-18 to 2026-08-18 | not instrumented at the time | shipped: one measurement suite over pinned retrievals; 262 tests passing; coverage floor 90 held; `make verify` green | The stream predates this ledger, so its baseline is recorded as absent rather than reconstructed |
| Expansion roadmap execution | 2026-08-22 | 262 tests, 11 source files, 3 workflows, 10 ADRs, no refresh diff tooling, no cadence SLA, no perf budget, two-repair sensitivity | same day: 288 tests (+26), 2 new modules (`artifact_diff`, perf budget gate), 3 new workflows (osv, scorecard, SBOM step), 12 ADRs, supply-chain rows closed in the conformance table, cadence + staleness SLA defined, runbook, DoD, this ledger | AI-assisted session under human review; every change passed the full `make verify` gate list before merge |
| Deliberate refresh 2026-08-23 | 2026-08-23 | pin of 2026-08-17: 5,054 leaves, three sources, two-repair sensitivity, no county-agreement measurement, eight fetched DINS fields | same day: 6,582 leaves compared, 1,528 added, none removed, none of the measured figures changed; four sources; three-repair census (union stays 927); coordinate-county agreement measured over 132,490 records (31 disagree); ninth fetched field | Trigger 3 fired: the pipeline changed shape. Executed per `docs/RUNBOOK.md` |
| Next deliberate refresh | superseded by the row above The refresh procedure in `docs/RUNBOOK.md` is the metric: artifact diff against the replaced pin, dated PROVENANCE entry |

## Engineering health, measured rather than felt

| Metric | State on 2026-08-22 |
|---|---|
| Test count | 288 |
| Branch coverage floor | 90%, enforced |
| Type checking | mypy strict, clean |
| Lint/format | ruff, clean, complexity cap 10 |
| Offline fixture build wall clock | about 1 second locally; budget ceiling 30 seconds, enforced by test |
| Full real build wall clock | about 18 seconds as of the 2026-08-17 pin, twelve placements per build |
| Published values in the current pin | 5,120 leaves in `published/measurements.json`, comparable by `wildfire_service_territory_overlap.artifact_diff` |
| Accepted CodeQL findings with written reasoning | 2, both on the release build, both re-checked when the release runs |

The leaf count above is what a refresh will be diffed against. It is recorded here so
the size of "nothing changed" is known before somebody needs to claim it.
