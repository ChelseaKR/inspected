# Accessibility conformance review

Dated 2026-08-22, against the output of version `0.1.0` as rendered from the
2026-08-17 pins. This review is static and structural. It was not performed with a
screen reader or any assistive technology, and it says so rather than implying
otherwise; that pass remains open and is listed under what was not done.

## What this project's accessibility surface is

Two generated artifacts, `published/REPORT.md` and `published/measurements.json`, plus
the repository documents around them. No web UI, no colour, no images, no animation,
no time-dependent content.

## What was checked and holds

| Check | State |
|---|---|
| Every data table has a header row (`| Outcome | Share | ...`) | Holds in all report tables; the renderer emits headers before rows |
| Table cells carry their own context (denominator columns sit beside share columns) | Holds: no rate appears without its denominator column |
| No meaning conveyed by colour anywhere in the output | Holds by construction: the artifacts contain no ANSI codes and no styling |
| No meaning conveyed by shape, size, or position alone | Holds: order is alphabetical or explicitly labelled as a size, and each row is self-describing |
| Not-measured values render as words ("not measured"), never as blank or zero | Holds, enforced by `artifacts.py` at write time |
| Intervals print both ends, widening precision when the ends would round together | Holds: "0.7% to 0.7%" cannot be emitted |
| No em dash or en dash in any document or source file | Holds, enforced by test; screen readers read these inconsistently mid-sentence |
| Headings are hierarchical (`#`, then `##` sections) | Holds in the generated report |
| Links are descriptive phrases, never bare URLs or "here" | Holds in README, PROVENANCE, and the report |
| The JSON artifact is machine-readable for transform into any accessible format | Holds: one stable serialisation, sorted keys |

## What was not done

- **No assistive-technology pass.** Nobody has navigated the generated tables with a
  screen reader. Markdown pipe tables are a known rough edge for some of them; whether
  these tables survive that navigation is untested and this review does not claim it.
- **No reading-order audit beyond heading structure.** Whether a section sequence
  makes sense linearly is a judgment this document defers to an actual pass.
- **No plain-language review** beyond the project's own writing rules.

## Standing rule

The publication rules that already fail closed do most of the accessibility work this
project needs: a rate without its denominator, a not-measured value printed as zero,
or an interval printed as false certainty would all mislead far more than formatting
ever could, and none of them can ship. This review covers the layer above that.
