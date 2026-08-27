"""Build the measurements from files already on disk. No network, ever.

``--fixture`` marks the output as built from the committed sample files rather than from
the real retrievals, so a fixture build can never be mistaken for the published one.

``--version`` answers from the installed distribution metadata, which the build backend
copies out of ``pyproject.toml``, so the version has one home and no way to drift from
it. It answers or it says it could not; it never guesses.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from importlib import metadata
from pathlib import Path
from typing import Any

from wildfire_service_territory_overlap import artifacts, measure, report, sensitivity
from wildfire_service_territory_overlap.geometry import load_counties, load_territories
from wildfire_service_territory_overlap.placement import (
    classify,
    classify_county_agreement,
    measure_boundary_distances,
    measure_contested_group_distances,
    read_records,
)
from wildfire_service_territory_overlap.sources import (
    DINS,
    ELSE_IOU_POU,
    ELSE_OTHER,
    RETRIEVED,
)

ARTIFACT_NAME = "measurements.json"
REPORT_NAME = "REPORT.md"

# The name of the distribution whose metadata carries the version. Not a second copy of
# the version: `pyproject.toml` holds the only one, the build backend copies it into the
# installed metadata, and this reads it back from there. A test holds this string against
# `project.name` so the lookup cannot go looking for a distribution nobody builds.
DISTRIBUTION = "wildfire-service-territory-overlap"


class _VersionAction(argparse.Action):
    """`--version`, resolved when the flag is used rather than when it is declared.

    `argparse`'s own version action takes a finished string at parser construction time.
    Reading installed metadata into that string runs the lookup on every invocation,
    including the ones that never ask for a version, so a checkout with no installed
    distribution metadata loses the whole command rather than one flag. The lookup
    therefore happens here, inside the flag.

    A version that cannot be read is not reported as a version. There is no fallback
    guess: the answer is the statement that nothing was installed to answer from, on
    stderr, with a nonzero exit, in the same shape this project reports every other
    measurement it could not make.
    """

    def __init__(
        self,
        option_strings: Sequence[str],
        dest: str = argparse.SUPPRESS,
        default: str = argparse.SUPPRESS,
        help: str = "print the installed version and exit",
    ) -> None:
        super().__init__(
            option_strings=list(option_strings),
            dest=dest,
            default=default,
            nargs=0,
            help=help,
        )

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ) -> None:
        try:
            version = metadata.version(DISTRIBUTION)
        except metadata.PackageNotFoundError:
            print(
                f"{parser.prog}: version not measured. Nothing installed under "
                f"{DISTRIBUTION} carries distribution metadata to read it from. "
                "Install the project, with `uv sync --locked`, and ask again.",
                file=sys.stderr,
            )
            raise SystemExit(1) from None
        print(f"{parser.prog} {version}")
        raise SystemExit(0)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build(
    *,
    dins_path: Path,
    iou_pou_path: Path,
    other_path: Path,
    counties_path: Path,
    out_dir: Path,
    is_fixture: bool,
) -> tuple[Path, Path]:
    """Measure, check, and write both artifacts. Nothing is written if a check fails."""
    collections = {
        ELSE_IOU_POU.key: _read_json(iou_pou_path),
        ELSE_OTHER.key: _read_json(other_path),
    }
    territories, unusable = load_territories(collections)
    counties = load_counties(_read_json(counties_path))
    records, excluded = read_records(_read_json(dins_path))
    placement = classify(records, territories, excluded)
    measure_boundary_distances(placement, territories)
    measure_contested_group_distances(placement, territories)
    agreement = classify_county_agreement(records, counties)

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
        "representativeness_by_category": measure.representativeness_by_category(
            placement
        ),
        "coordinate_county_agreement": measure.coordinate_county_agreement(
            agreement, len(records)
        ),
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
            "untouched_outlines": sensitivity.untouched_outlines(
                placement, records, territories
            ),
        },
        "excluded_types": measure.excluded_type_note(),
    }

    # The aggregate ceiling is the largest number of things any one collection here
    # reports on: one row per published outline, or one row per county named in the
    # record set. A list longer than that is a record listing under another name.
    ceiling = max(len(territories) + len(unusable), len(placement.counties), 32)
    artifact_path = artifacts.write_json(
        tree, out_dir / ARTIFACT_NAME, max_rows=ceiling
    )
    report_path = out_dir / REPORT_NAME
    report_path.write_text(report.render(tree), encoding="utf-8")
    return artifact_path, report_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wildfire-service-territory-overlap",
        description="Measure how much of the DINS record set a published electric "
        "service territory boundary can account for. Reads local files only.",
    )
    parser.add_argument("--version", action=_VersionAction)
    parser.add_argument("--dins", type=Path, required=True)
    parser.add_argument("--iou-pou", type=Path, required=True)
    parser.add_argument("--other", type=Path, required=True)
    parser.add_argument("--counties", type=Path, required=True)
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
        counties_path=args.counties,
        out_dir=args.out,
        is_fixture=args.fixture,
    )
    print(f"wrote {artifact}")
    print(f"wrote {document}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
