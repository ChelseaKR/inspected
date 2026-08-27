## What this changes

<!-- One paragraph: what moved and why. Link the issue it closes. -->

Closes #

## Does this change published figures?

Required. Tick exactly one. Published figures are anything under `published/`.

- [ ] No. Nothing under `published/` moves, and the offline fixture build is the only
      build this change ran.
- [ ] Yes. Something under `published/` moves, so this change went through the
      deliberate-refresh procedure in `docs/RUNBOOK.md`, including the artifact diff
      against the pin it replaces, and `PROVENANCE.md` gained the dated section.

## Definition of done

Copied from `docs/DEFINITION_OF_DONE.md`, item for item.
`tests/test_provenance_and_standards.py` holds the two together: a box that exists there
and not here fails the build, so this list cannot quietly fall behind the rules it
states. Tick the sections your change is in.

### Any change

- [ ] `make verify` passes locally, end to end: lockfile drift, lint, format, mypy
      `--strict`, tests with the branch-coverage floor, pip-audit, the offline report,
      and the determinism gate.
- [ ] No new dependency without a reason written next to its pin.
- [ ] `CHANGELOG.md` carries an entry under `[Unreleased]`.
- [ ] The README conformance table still states what is true, not what is intended; if
      this change moved a row, the row moved with it.

### A change to measurement code

Everything above, plus:

- [ ] New behaviour has tests, including at least one refusal path: what the code does
      when it declines to measure is part of the behaviour.
- [ ] Every rate the change produces carries numerator, denominator and interval, and
      passes `artifacts.check_all`; if it cannot be measured, it is not-measured shaped,
      never zero.
- [ ] Collections stay aggregate-only and name-ordered; no key ranks or scores.
- [ ] The determinism gate still holds over byte-identical inputs.
- [ ] If the change embeds a judgment call, a sensitivity variant measuring what the
      judgment is worth ships in the same change (the standard set by ADR 0006).
- [ ] If the change touches what is fetched from publishers: `sources.py`,
      `PROVENANCE.md`, and the schema guard move together, or the change does not ship.

### A change to published figures

Everything above, plus:

- [ ] It went through the deliberate-refresh procedure in `docs/RUNBOOK.md`, including
      the artifact diff against the pin it replaces.
- [ ] `PROVENANCE.md` gained a dated section saying what moved, sizes included.
- [ ] The committed `published/REPORT.md` renders from the committed
      `published/measurements.json`, which the report-matches-artifact test holds.

### A change to docs only

- [ ] No em dash or en dash anywhere (a test holds this, but do not make the test do
      your proofreading).
- [ ] Claims about the repository are checkable by a reader with the repository.

## Anything a reviewer should argue with

<!-- A judgment call, a number that moved, a rule you think is wrong. This section is
     not optional politeness: a decision nobody was told about is a decision nobody
     reviewed. -->
