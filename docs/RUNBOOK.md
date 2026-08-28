# Operations runbook

This repository has exactly one operational surface: a by-hand acquisition, a local
pipeline over it, and the gates around both. No hosted service, no telemetry, no SLO
surface. What follows is what to do when each piece refuses, because every refusal in
this project is deliberate and each one means something specific.

Unofficial. Nothing here speaks for CAL FIRE, the California Energy Commission, or any
electric utility.

## The two builds, and which one is which

- `make report` builds `published/` from `data/raw/`, which exists only on a machine
  that has run `make acquire`. This is the real tree.
- `make report-offline` builds into `build/offline/` from the committed fixtures and
  marks its output with `"is_fixture": true`. It runs anywhere, offline, in about a
  second, and it is what CI measures.

A fixture build can never be mistaken for the real one because the flag travels inside
the artifact itself. Never point `--out` at `published/` while passing `--fixture`.

## A deliberate refresh, start to finish

Triggers and cadence live in `PROVENANCE.md`. The procedure:

1. Set the current artifact aside for comparison:
   `cp published/measurements.json "$OLD"` where `$OLD` lives outside the repository.
2. Run `make acquire`. Network, by hand, never from CI. It writes `data/raw/`.
3. Update `src/wildfire_service_territory_overlap/sources.py`: the new retrieval dates, SHA-256 hashes, byte
   counts and feature counts. The tests hold `PROVENANCE.md` and `README.md` to agree
   with that file, so the document cannot be updated without the source record, or the
   other way round.
4. Run `make report`.
5. Compare: `python -m wildfire_service_territory_overlap.artifact_diff "$OLD" published/measurements.json`.
   Changed and added values are expected on a real refresh; removed values stop the
   run unless `--allow-removals` names them deliberate.
6. Read the generated `published/REPORT.md` end to end. The figures are checked by
   machinery; whether they still say something coherent is not.
7. Write a dated section into `PROVENANCE.md` saying what moved, sizes included,
   following the 2026-08-17 pattern. Update the README status line if the headline
   moved. Add a `CHANGELOG.md` entry.
8. Commit `published/` and the source-record edits together. Never commit
   `data/raw/`.

## When acquisition refuses

All of these come from `src/wildfire_service_territory_overlap/acquire.py`, and all of them leave `data/raw/`
without a file you can trust.

**`AcquisitionBlocked`: a 401, 403 or 429, or an access control on the route.**
Stop. Do not retry in a loop and do not route around the control; routing around one
would convert a public-data project into an unauthorized one. Wait, re-read the
publisher's terms and dataset page, and raise it with the publisher if the block looks
like a misconfiguration. A 429 means back off on human timescales.

**`AcquisitionFailed`: an HTTP error status, an error payload, or a refused endpoint.**
Retry once after a few minutes in case it was transient. If it persists, it is the
publisher's service telling you something; treat the day as a bad day for acquiring,
not as a problem to solve with more requests.

**`IncompleteAcquisition`: the layer's own record count disagrees before versus after
the walk, or identifiers came back duplicated or not strictly increasing.** The walk
fetched part of a dataset and cannot prove otherwise, so nothing it produced may be
measured or published. Delete everything under `data/raw/` from that run. Re-run later;
if it fails the same way twice, suspect the pinned `perimeter` walk rather than the
network: check whether the pin still matches upstream, and take the discrepancy to
that repository instead of re-implementing the walk here with the same defect.

**`SchemaError` at build time: the retrieval is missing a column every measurement
reads.** This is an acquisition fault surfacing late, almost always a publisher-side
field rename or removal. Re-acquire. Do not measure what is left, and do not edit
`REQUIRED_COLUMNS` to make the error go away until the change is confirmed on the
publisher's own layer metadata; if a column is gone for good, that is a pipeline
change and it triggers a full refresh with a dated `PROVENANCE.md` entry explaining it.

## When a gate refuses

**`tools/determinism.sh` reports a difference.** Two builds over byte-identical inputs
produced different bytes, which means nondeterminism entered the pipeline: an
unordered iteration, a timestamp, a set leaking into output order. Fix the code. The
gate does not have a tolerance setting because there is no acceptable amount.

**`PublicationRefused` during `make report`.** One of the publication rules caught the
artifact: a rate without its denominator or interval, a not-measured rate carrying a
value, a locating field, a collection long enough to be a record listing, a ranking
key, or territory rows out of name order. The fix is in the measurement that produced
the shape, never in the rule. Loosening a rule to let a number through is the one
failure mode this repository exists to prevent.

**Coverage below 90.** Add tests for whatever landed uncovered. Lowering the floor is
not among the options.

**`uv lock --check` fails.** The lockfile and `pyproject.toml` disagree. Re-lock
deliberately, review the resolution, and commit both together.

## Re-reading the protection on `main`

The conformance table states what the branch ruleset does. Nothing in this repository
can check that from a test: the ruleset lives in repository settings, and the test suite
runs offline against committed files. So it is re-read by hand, and the command is here
rather than in somebody's memory.

```sh
gh api repos/OWNER/REPO/rulesets --jq '.[].id'
gh api repos/OWNER/REPO/rulesets/RULESET_ID \
  --jq '{enforcement, bypass_actors, checks: [.rules[] | select(.type=="required_status_checks") | .parameters.required_status_checks[].context]}'
```

Three things have to agree with the README's CI/CD row: `enforcement` is `active`, the
six contexts are all present, and `bypass_actors` is what the row says it is. On
2026-08-28 the third disagreed. The row had said `with no bypass actors` since it was
written; the ruleset carried `RepositoryRole` 5, repository admin, at `bypass_mode:
always`. The row now says so. A required check that the one account which pushes can
skip is a required check by agreement rather than by configuration, and the difference
only shows up if somebody reads the setting back.

Re-read it on every refresh of the pin, and whenever the conformance table is touched.

## What must never happen

- `data/raw/` is never committed, at any granularity, ever.
- `published/` is never edited by hand. If a figure is wrong, the pipeline is wrong.
- Fixture output never becomes `published/` output.
- The fetched field list never grows without `sources.py`, `PROVENANCE.md`, and the
  schema guard moving together; the provenance test reads all three against each
  other precisely so that collection stays disclosed.
