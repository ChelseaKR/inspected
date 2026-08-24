# Contributing

## The one gate

```
make verify
```

CI runs the same target. The two must stay identical: if you add a check, add it to the
`verify` list, not only to the workflow.

`make verify` runs `uv lock --check`, ruff, `ruff format --check`, `mypy --strict`,
pytest with branch coverage against a 90% floor, `pip-audit`, an offline build over the
fixtures, and the determinism gate.

## Setup

```
uv sync --locked
```

`uv sync --locked`, never `--frozen`. `--frozen` means "do not resolve", not "the lock is
current": against a `pyproject.toml` the lockfile does not satisfy, `--frozen` exits 0 and
installs the stale set.

## What needs care

**`src/wildfire_service_territory_overlap/artifacts.py`.** These are the rules about what this project will say
about a named company. Weakening one is not a refactor. Every rule has a test that feeds
it something it must refuse; keep that pairing.

**`src/wildfire_service_territory_overlap/intervals.py`.** The only route a proportion takes to an artifact. If you
find yourself dividing two integers anywhere else, that is the bug.

**`src/wildfire_service_territory_overlap/sources.py`.** Reviewed endpoints and quoted publisher caveats. A change
here moves published numbers or points the acquisition somewhere new. `PROVENANCE.md`
must be updated in the same change; a test compares them.

**`src/wildfire_service_territory_overlap/acquire.py`.** Run by hand, never in CI. It must never gain a retry under
a different identity, a browser-shaped User-Agent, or a path that writes a partial walk.

## Things this project will not do

- Publish a rate without its denominator and its interval.
- Publish a zero for a measurement that could not be made.
- Publish a damage rate for a named utility, or order territories by any measured value.
- Read, infer, approximate, or publish the location of any physical utility asset, from
  any source.
- Award a contested record to one of the territories contesting it.
- Fetch an address, parcel number or assessed value it does not need.

A change that does any of these will be declined regardless of how well it is written.

## Refreshing the data

```
make acquire        # network, by hand, never in CI
make report         # rebuild published/ from data/raw/
```

Then copy the new feature counts, byte counts and hashes from `data/raw/acquisition.json`
into `src/wildfire_service_territory_overlap/sources.py`, update `PROVENANCE.md` and the figures in `README.md`,
and commit the new `published/` tree. `data/raw/` stays out of git.

## Style

Prose in comments and documentation explains why, not what. No em dashes or en dashes.

## Your first change: a walkthrough

Follow this walkthrough to make and verify your first change using only uv:

1. Setup and offline build:
   Run `uv sync --locked` to install pinned dependencies.
   Run `make report-offline` (or `uv run python -m wildfire_service_territory_overlap.cli --fixture --dins fixtures/dins_sample.json --iou-pou fixtures/else_iou_pou_sample.geojson --other fixtures/else_other_sample.geojson --counties fixtures/county_boundaries_sample.geojson --out build/offline`).
   This builds artifacts into `build/offline/measurements.json` and `build/offline/REPORT.md`.
   Notice `"is_fixture": true` inside `measurements.json`: this flag distinguishes offline fixture runs from live published data.

2. Inspect the generated report:
   Open `build/offline/REPORT.md`. Locate the invented territories documented in `fixtures/README.md` (such as Alpha Electric Company, Beta Municipal Utility, Gamma Rural Cooperative, and Delta Choice Energy).

3. Observe the determinism gate in action:
   Break something tiny on purpose to see how the gates protect determinism. For example, edit `fixtures/else_iou_pou_sample.geojson` and rename a territory inside the fixture. Run `make determinism`.
   Watch the gate refuse: two builds of byte-identical inputs must agree byte for byte, and any deviation or nondeterminism is rejected. Revert your temporary change before continuing.

4. Understanding the verification gates:
   `make verify` runs the following sequential gates. If a gate fails, here is what it means:
   - `lock-check`: `uv lock --check` fails when `pyproject.toml` and `uv.lock` are out of sync.
   - `sync`: `uv sync --locked` fails if dependencies cannot be cleanly installed from the lockfile.
   - `lint`: `ruff check .` fails when code style or static quality rules are violated.
   - `format`: `ruff format --check .` fails if code formatting deviates from ruff formatting rules.
   - `typecheck`: `mypy --strict src` fails when static type annotations are missing or inconsistent.
   - `test`: `pytest` with coverage fails when unit tests fail or branch coverage drops below the 90% floor.
   - `audit`: `pip-audit` fails if any dependency contains known vulnerabilities.
   - `report-offline`: fails if the offline report generation pipeline breaks on committed fixtures.
   - `determinism`: fails if two consecutive builds from the same inputs produce different output bytes.

For in-depth operational guidance and refusal troubleshooting, consult `docs/RUNBOOK.md`.
