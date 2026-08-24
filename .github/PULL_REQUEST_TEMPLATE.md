## Summary

<!-- Briefly describe the purpose of this change and link the issue it resolves. -->
Fixes #

## Definition of Done checklist

- [ ] `make verify` passes locally end to end (lock-check, sync, lint, format, typecheck, test, audit, report-offline, determinism)
- [ ] No new dependency without a reason written next to its pin
- [ ] `CHANGELOG.md` carries an entry under `[Unreleased]`
- [ ] The README conformance table still states what is true, not what is intended; if this change moved a row, the row moved with it

### Measurement code changes (if applicable)

- [ ] New behaviour has tests, including at least one refusal path
- [ ] Every rate produced carries numerator, denominator and interval, and passes `artifacts.check_all`
- [ ] Collections stay aggregate-only and name-ordered; no key ranks, scores, or grades
- [ ] The determinism gate still holds over byte-identical inputs
- [ ] If embedding a judgment call, a sensitivity variant ships in the same change (ADR 0006 standard)
- [ ] If touching publisher data: `sources.py`, `PROVENANCE.md`, and schema guard move together

### Published figures disclosure (required)

Does this change alter published figures in `published/`?

- [ ] **No**: this change does not modify published measurements or reports.
- [ ] **Yes**: this change modifies published figures. (If yes, follow the deliberate refresh procedure in `docs/RUNBOOK.md`, add a dated entry in `PROVENANCE.md`, and verify `published/REPORT.md` matches `published/measurements.json`.)
