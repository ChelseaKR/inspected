"""Build the measurements from files already on disk. No network, ever.

``--fixture`` marks the output as built from the committed sample files rather than from
the real retrievals, so a fixture build can never be mistaken for the published one.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from inspected import artifacts, measure, report, sensitivity
from inspected.geometry import load_territories
from inspected.placement import classify, measure_boundary_distances, read_records
from inspected.sources import DINS, ELSE_IOU_POU, ELSE_OTHER, RETRIEVED

ARTIFACT_NAME = "measurements.json"
REPORT_NAME = "REPORT.md"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build(
    *,
    dins_path: Path,
    iou_pou_path: Path,
    other_path: Path,
    out_dir: Path,
    is_fixture: bool,
) -> tuple[Path, Path]:
    """Measure, check, and write both artifacts. Nothing is written if a check fails."""
    collections = {
        ELSE_IOU_POU.key: _read_json(iou_pou_path),
        ELSE_OTHER.key: _read_json(other_path),
    }
    territories, unusable = load_territories(collections)
    records, excluded = read_records(_read_json(dins_path))
    placement = classify(records, territories, excluded)
    measure_boundary_distances(placement, territories)

    tree: dict[str, Any] = {
        "is_fixture": is_fixture,
        "provenance": {
            "dins_retrieved": DINS.retrieved,
            "dins_landing_page": DINS.landing_page,
            "territories_retrieved": RETRIEVED,
            "territories_item_modified": ELSE_IOU_POU.item_modified,
            "territories_landing_page": ELSE_IOU_POU.landing_page,
            "affiliation": (
                "Unofficial. Not affiliated with, endorsed by, or approved by CAL FIRE, "
                "the California Energy Commission, or any electric utility."
            ),
        },
        "placement_coverage": measure.placement_coverage(placement),
        "representativeness": measure.representativeness(placement),
        "attributability_by_fire": measure.attributability_by_fire(placement),
        "territories": measure.territory_rows(placement, territories),
        "contested_groups": measure.contested_groups(placement),
        "geometry_ledger": measure.geometry_ledger(placement, territories, unusable),
        "sensitivity": {
            "type_inclusion": sensitivity.type_inclusion(
                collections, records, excluded
            ),
            "repair_strategy": sensitivity.repair_comparison(
                collections, records, territories
            ),
        },
        "excluded_types": measure.excluded_type_note(),
    }

    ceiling = max(len(territories) + len(unusable), 32)
    artifact_path = artifacts.write_json(
        tree, out_dir / ARTIFACT_NAME, max_rows=ceiling
    )
    report_path = out_dir / REPORT_NAME
    report_path.write_text(report.render(tree), encoding="utf-8")
    return artifact_path, report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="inspected",
        description="Measure how much of the DINS record set a published electric "
        "service territory boundary can account for. Reads local files only.",
    )
    parser.add_argument("--dins", type=Path, required=True)
    parser.add_argument("--iou-pou", type=Path, required=True)
    parser.add_argument("--other", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="the inputs are the committed samples, not the real retrievals",
    )
    args = parser.parse_args(argv)
    artifact, document = build(
        dins_path=args.dins,
        iou_pou_path=args.iou_pou,
        other_path=args.other,
        out_dir=args.out,
        is_fixture=args.fixture,
    )
    print(f"wrote {artifact}")
    print(f"wrote {document}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
