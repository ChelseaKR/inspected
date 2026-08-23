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
