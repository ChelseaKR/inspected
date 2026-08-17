"""The projection, the validity ledger, and the boundary distances."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from shapely.geometry import LineString, MultiPolygon, Polygon

from inspected.geometry import (
    AS_PUBLISHED,
    REPAIRED,
    Territory,
    TerritoryLoadError,
    boundary_segments,
    distances_to_boundary,
    load_territories,
    project_lonlat,
    territory_index,
)


def feature(
    oid: int, name: str, kind: str, ring: list[list[float]] | None
) -> dict[str, Any]:
    geometry = None if ring is None else {"type": "Polygon", "coordinates": [ring]}
    return {
        "type": "Feature",
        "properties": {"OBJECTID": oid, "Utility": name, "Type": kind},
        "geometry": geometry,
    }


def square(w: float, s: float, e: float, n: float) -> list[list[float]]:
    return [[w, s], [e, s], [e, n], [w, n], [w, s]]


BOWTIE = [
    [-122.5, 40.0],
    [-122.0, 40.5],
    [-122.5, 40.5],
    [-122.0, 40.0],
    [-122.5, 40.0],
]


def collection(*features: dict[str, Any]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": list(features)}


def test_the_pinned_pipeline_agrees_with_the_published_albers_definition() -> None:
    pyproj = pytest.importorskip("pyproj")
    lons = np.array([-121.4934, -118.2437, -124.0, -114.5])
    lats = np.array([38.5767, 34.0522, 41.5, 32.8])
    x, y = project_lonlat(lons, lats)
    reference = pyproj.Transformer.from_crs("EPSG:4269", "EPSG:3310", always_xy=True)
    rx, ry = reference.transform(lons, lats)
    assert np.allclose(x, rx, atol=1e-6)
    assert np.allclose(y, ry, atol=1e-6)


def test_the_projection_is_stable_across_calls() -> None:
    lons, lats = np.array([-121.0]), np.array([38.0])
    first = project_lonlat(lons, lats)
    second = project_lonlat(lons, lats)
    assert first[0][0] == second[0][0]
    assert first[1][0] == second[1][0]


def test_a_valid_polygon_is_recorded_as_published() -> None:
    usable, unusable = load_territories(
        {"a": collection(feature(1, "Valid Co", "IOU", square(-121, 38, -120, 39)))}
    )
    assert unusable == ()
    assert usable[0].geometry_state == AS_PUBLISHED
    assert usable[0].repaired is False
    assert usable[0].geometry_note == ""


def test_an_invalid_polygon_is_repaired_and_named() -> None:
    usable, unusable = load_territories(
        {"a": collection(feature(1, "Bowtie Co", "CO-OP", BOWTIE))}
    )
    assert unusable == ()
    assert usable[0].geometry_state == REPAIRED
    assert usable[0].repaired is True
    assert "validity check" in usable[0].geometry_note
    assert usable[0].geometry.is_valid
    assert isinstance(usable[0].geometry, MultiPolygon)


def test_a_feature_with_no_geometry_is_unusable_not_empty() -> None:
    usable, unusable = load_territories(
        {"a": collection(feature(1, "Ghost Co", "POU", None))}
    )
    assert usable == ()
    assert len(unusable) == 1
    assert "no geometry" in unusable[0].geometry_note


def test_a_polygon_that_cannot_be_repaired_is_removed_from_the_index() -> None:
    # A zero-area ring repairs to a line, which containment cannot be tested against.
    degenerate = [[-121.0, 38.0], [-120.0, 38.0], [-121.0, 38.0]]
    usable, unusable = load_territories(
        {"a": collection(feature(1, "Sliver Co", "POU", degenerate))}
    )
    assert usable == ()
    assert len(unusable) == 1
    assert "no polygonal geometry" in unusable[0].geometry_note


def test_types_outside_the_wires_set_are_skipped() -> None:
    usable, _ = load_territories(
        {
            "a": collection(
                feature(1, "Keep Co", "IOU", square(-121, 38, -120, 39)),
                feature(2, "Drop Co", "CCA", square(-121, 38, -120, 39)),
                feature(3, "Drop Admin", "ADMIN", square(-121, 38, -120, 39)),
            )
        }
    )
    assert [t.name for t in usable] == ["Keep Co"]


def test_territories_come_back_in_name_order() -> None:
    usable, _ = load_territories(
        {
            "a": collection(
                feature(1, "Zulu Co", "IOU", square(-121, 38, -120, 39)),
                feature(2, "Alpha Co", "IOU", square(-119, 38, -118, 39)),
            )
        }
    )
    assert [t.name for t in usable] == ["Alpha Co", "Zulu Co"]


@pytest.mark.parametrize(
    ("props", "message"),
    [
        ({"OBJECTID": 1, "Type": "IOU"}, "no Utility name"),
        ({"OBJECTID": 1, "Utility": "  ", "Type": "IOU"}, "no Utility name"),
        ({"OBJECTID": 1, "Utility": "A Co"}, "no Type"),
        ({"Utility": "A Co", "Type": "IOU"}, "no integer OBJECTID"),
    ],
)
def test_a_feature_missing_a_reviewed_field_is_refused(
    props: dict[str, Any], message: str
) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": props,
                "geometry": {"type": "Polygon", "coordinates": [square(-1, 0, 1, 2)]},
            }
        ],
    }
    with pytest.raises(TerritoryLoadError, match=message):
        load_territories({"a": payload})


def test_a_feature_with_no_properties_is_refused() -> None:
    payload = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
    with pytest.raises(TerritoryLoadError, match="no properties"):
        load_territories({"a": payload})


def test_something_that_is_not_a_feature_collection_is_refused() -> None:
    with pytest.raises(TerritoryLoadError, match="not a FeatureCollection"):
        load_territories({"a": {"type": "Feature"}})


def test_an_empty_index_is_refused_rather_than_answering_every_question_no() -> None:
    with pytest.raises(TerritoryLoadError, match="no usable territory geometry"):
        territory_index(())


def test_boundary_segments_cover_the_holes_as_well_as_the_shell() -> None:
    shell = [(0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0), (0.0, 0.0)]
    hole = [(4.0, 4.0), (6.0, 4.0), (6.0, 6.0), (4.0, 6.0), (4.0, 4.0)]
    segments = boundary_segments(Polygon(shell, [hole]))
    assert len(segments) == 8
    assert all(isinstance(s, LineString) for s in segments)


def test_boundary_segments_handle_a_multipolygon() -> None:
    a = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    b = Polygon([(5, 5), (6, 5), (6, 6), (5, 6)])
    assert len(boundary_segments(MultiPolygon([a, b]))) == 8


def test_boundary_distance_is_measured_in_metres_from_the_nearest_edge() -> None:
    box = Polygon([(0, 0), (1000, 0), (1000, 1000), (0, 1000)])
    xs = np.array([500.0, 10.0, 999.0])
    ys = np.array([500.0, 500.0, 500.0])
    distances = distances_to_boundary(box, xs, ys)
    assert distances[0] == pytest.approx(500.0)
    assert distances[1] == pytest.approx(10.0)
    assert distances[2] == pytest.approx(1.0)


def test_boundary_distance_on_no_points_returns_nothing_rather_than_failing() -> None:
    box = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    assert len(distances_to_boundary(box, np.empty(0), np.empty(0))) == 0


def test_a_territory_dataclass_reports_repair_from_its_state() -> None:
    plain = Territory("A", "IOU", 1, "a", Polygon(), AS_PUBLISHED, "")
    fixed = Territory("B", "IOU", 2, "a", Polygon(), REPAIRED, "note")
    assert not plain.repaired
    assert fixed.repaired
