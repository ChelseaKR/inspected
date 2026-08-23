"""The performance budget, held where a regression fails a gate rather than a feeling.

The budget is deliberately generous. Wall clock does not compare across machines, and
a tight ceiling on a shared runner fails on load rather than on regressions, which is
how budgets get deleted. What this gate catches is an order-of-magnitude regression
over byte-identical inputs: the containment query was once worth a factor of three on
its own, and that kind of change trips this long before anybody notices otherwise.

The determinism gate guarantees the inputs stay identical between runs, so any change
this test sees is a change in the code.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from inspected.cli import build

ROOT = Path(__file__).resolve().parents[1]

# Recorded here and stated in the README's Performance row. Roughly thirty times the
# measured fixture build, which is headroom for a loaded runner, not permission to be
# slow: anything inside this ceiling but far above one second still shows up in review.
BUDGET_SECONDS = 30.0


@pytest.mark.slow
def test_the_offline_build_holds_its_budget(tmp_path: Path) -> None:
    start = time.monotonic()
    build(
        dins_path=ROOT / "fixtures" / "dins_sample.json",
        iou_pou_path=ROOT / "fixtures" / "else_iou_pou_sample.geojson",
        other_path=ROOT / "fixtures" / "else_other_sample.geojson",
        out_dir=tmp_path / "budget-run",
        is_fixture=True,
    )
    elapsed = time.monotonic() - start
    assert elapsed < BUDGET_SECONDS, (
        f"the offline fixture build took {elapsed:.1f}s against a budget of "
        f"{BUDGET_SECONDS:.0f}s. Either something in the pipeline got dramatically "
        "slower over identical inputs, or the budget no longer describes reality; "
        "decide which before touching this test."
    )
