# Upstream gaps in `perimeter`

Roadmap item 4.4 says this project contributes fixes to
[`perimeter`](https://github.com/ChelseaKR/perimeter) where acquisition gaps surface
here, so the relationship stays "consume, do not re-implement" rather than drifting into
a local fork. This file is where a gap is named once it has been found: what it is, the
code here that compensates for it, and the change that would let the compensation go.

The failure mode being guarded against is a local workaround that quietly becomes
permanent. Writing one down is not the same as fixing it, and this file does not claim
any of these has been sent upstream. The pin is a commit rather than a branch, so an
upstream fix reaches this project only when the pin moves, deliberately.

## Audit of 2026-09-05

Against `perimeter` at commit `dac60195c50786f33f69a8fab70b6230894ed374`, which is what
`pyproject.toml` pins and what `uv.lock` installs. Read at that commit, not on `main`.

Read in full on this side: `src/wildfire_service_territory_overlap/acquire.py`,
`tests/test_acquire.py`, `src/wildfire_service_territory_overlap/sources.py`, the schema
guard and `REQUIRED_COLUMNS` in `src/wildfire_service_territory_overlap/placement.py`,
and the two mypy overrides in `pyproject.toml`. Read at the pinned commit upstream:
`perimeter/acquire.py`, `perimeter/sources.py`, the required-column lists in
`perimeter/schema.py`, `perimeter/dins.py`, and upstream's own `pyproject.toml`,
`Makefile` and `tests/test_acquire.py`.

Four gaps, all in the acquisition. Each row below is expanded underneath.

| Gap | What compensates for it here | The upstream change |
|---|---|---|
| The walk sends `perimeter`'s User-Agent and takes no other | A second copy of the fetch path, so three of the four layers can name this project | A `user_agent` argument, defaulting to today's constant |
| The walk cannot return geometry | `fetch_feature_pages`, a second paged walk holding a second copy of the offset rule | Geometry, format and spatial reference as arguments, or the offset loop exposed |
| Completeness is one count, read once, before the walk | A second count read after the walk, plus uniqueness and ordering checks on the identifiers | Read the count again after the walk, and check the identifiers |
| The package is checked with `mypy --strict` and ships no `py.typed` | Two mypy overrides, one narrowed to a single rule in a single module | One empty file at `src/perimeter/py.typed` |

### Gap 1: the walk sends its own name and takes no other

`perimeter.acquire` reads `USER_AGENT` from a module constant inside its private `_get`,
and neither `layer_record_count` nor `fetch_layer` accepts a User-Agent. A consuming
project has no way to say who is actually calling.

Measured here on 2026-09-05 with the socket substituted: every request the DINS
acquisition makes, the two count queries and each page of the walk, goes out as
`perimeter-coverage/0.1 (+https://github.com/ChelseaKR/perimeter)`. That is the largest
of the four layers at 132,522 records. The other three carry this project's own
User-Agent, because `acquire.py` holds its own `USER_AGENT`, its own `_get` and its own
`layer_record_count`, the last two near-copies of upstream's.

Two costs, not one. An operator at CAL FIRE reading their logs sees a project name that
does not lead back to the caller, which is what an honest User-Agent is for. And the
refusals inside the copied `_get`, HTTPS only, stop on a 401, 403 or 429, refuse a
non-JSON challenge page, refuse an error payload, now exist twice, so a fix to
upstream's copy does not reach this project even when the pin moves.

The upstream change: a `user_agent` argument on `layer_record_count` and `fetch_layer`,
defaulting to the constant they use today and passed through to `_get`. Upstream already
holds a test that its request names the project rather than imitating a browser. This
asks only that the project it names can be the caller.

### Gap 2: the paged walk cannot return geometry

`fetch_layer` pins `returnGeometry=false` and `f=json`. That is the right default for
`perimeter`, which measures how complete the fields of a file are and needs no polygons
to do it, and upstream tests the field lists to keep geometry out of them.

The consequence here is that the two territory layers and the county layer, which are
polygons, cannot be read through it. `fetch_feature_pages` in `acquire.py` is a second
paged walk carrying a second copy of the one rule the pin exists to avoid duplicating:
step the offset by the rows received, never by the page size asked for. That rule was
wrong once, upstream, and there are now two implementations of it in this project's
dependency graph. The local `_write` similarly duplicates upstream's public `write_rows`
because that writer takes attribute rows and cannot write a GeoJSON feature collection.

The upstream change: geometry, output format and output spatial reference as arguments
to `fetch_layer`, or the offset loop factored out so a caller that needs geometry reuses
the stepping rule instead of rewriting it. Either one, not both.

### Gap 3: completeness is one count, read once, before the walk

`perimeter.acquire.acquire` reads the layer's own record count before the walk and
compares it with the number of rows collected. It reads it once, and it compares only
the total.

Reading it once leaves an ambiguity upstream's own refusal message concedes: "If the
layer was republished mid-walk, re-run the acquisition; if it was not, the walk is
dropping records" hands the operator a guess. Comparing only the total is blind to a
different failure: a page served twice while another is stepped over produces exactly
the right count and the wrong rows.

What compensates here: `acquire_dins` reads the count before and after the walk and
raises `IncompleteAcquisition` naming a republication when the two disagree, so the
operator is told which of the two happened. `assert_walk_is_whole` then refuses
identifiers that repeat, and identifiers that do not come back strictly increasing.
`tests/test_acquire.py` exercises all three refusals against walks that should fail
them.

The upstream change: read the count again after the walk and split the one refusal into
two, and check the identifiers for uniqueness and strict increase. The walk already asks
for `orderByFields=OBJECTID ASC`, and `OBJECTID` is the first entry of both
`FRAP_REQUIRED_COLUMNS` and `DINS_REQUIRED_COLUMNS`, so both checks are available
without asking the service for anything it is not already sending.

### Gap 4: the package is typed and does not say so

Upstream sets `strict = true` under `[tool.mypy]` and its `verify` target runs
`mypy --strict src`. The wheel built from the pinned commit carries no `py.typed`
marker, so every consumer sees an untyped package.

What that costs here is both mypy overrides in `pyproject.toml`, measured on 2026-09-05:

- dropping `perimeter.*` from `ignore_missing_imports` produces
  `Skipping analyzing "perimeter.acquire": module is installed, but missing library
  stubs or py.typed marker`;
- dropping `disallow_subclassing_any = false` produces
  `Class cannot subclass "AcquisitionFailed" (has type "Any")`, because the base class
  resolves to `Any` for the same reason;
- adding an empty `py.typed` to the installed package and dropping both overrides leaves
  `mypy --strict src` green, so the marker is the whole of the fix as far as this
  project is concerned.

The upstream change: one empty file at `src/perimeter/py.typed`. Hatchling includes it in
the wheel under the existing `packages` setting. It is a claim about the whole package
rather than about `acquire` alone, which is why it belongs behind upstream's own strict
run and is not asserted from here.

## Checked and found not to be a gap

Recorded so the next audit does not re-open them.

- **`fetch_layer` ends the walk on a short page when the service sets no
  `exceededTransferLimit`.** This looked like trust in a flag the service need not send.
  It is deliberate and tested upstream, in `test_a_short_page_ends_the_walk_even_without_the_transfer_flag`
  and `test_a_full_page_without_the_transfer_flag_is_still_followed`, and a walk cut
  short that way is refused by the count check rather than written. The walk here is
  more conservative, ending only on an empty page, which costs one extra request per
  layer and is a difference in taste, not a defect to report.
- **The fetched field list.** `fetch_layer` already takes its fields as an argument, so
  this project passes its own nine and never downloads the address and parcel columns
  upstream fetches for its own purposes. Nothing here works around the upstream list.
- **`sources.py` and the schema guard.** `REQUIRED_COLUMNS` in `placement.py` is the
  nine columns this project measures, a deliberate subset chosen by the refusal to
  download addresses, not a copy of `DINS_REQUIRED_COLUMNS` kept in sync by hand.
  Nothing in either file exists because upstream fails to surface something.
- **The exception types.** `AcquisitionBlocked` and `AcquisitionFailed` are public
  upstream and are what this module raises. `IncompleteAcquisition` is a local subclass
  because upstream has no name for a walk that finished without evidence, which is a
  consequence of Gap 3 rather than a separate one.
