"""Projection, the published polygons, and the ledger of the ones that arrive broken.

Two decisions in this module carry the whole spatial result, so both are written down
here rather than left implicit in a library call.

**The projection is pinned as a pipeline, not resolved from a CRS pair.** Asking pyproj
to go from EPSG:4326 to EPSG:3310 lets it choose a datum transformation, and which one
it chooses depends on which PROJ grid files happen to be installed on the machine. That
is a reproducibility hole in a project whose output is supposed to be byte-identical
between runs. :data:`ALBERS_PIPELINE` is a bare projection with no datum step, so it
computes the same numbers on every machine with no grids present at all. The cost is
that a WGS84 coordinate is treated as though it were on GRS80, which in California is a
shift of roughly one to two metres. Every distance this project publishes is a band at
100 metres or wider, and PROVENANCE.md records the trade.

**A polygon the publisher ships invalid is repaired, and the repair is published.**
Eight of the territory polygons fail an OGC validity check on retrieval, with ring
self-intersections and nested shells. Shapely will happily answer a containment question
about an invalid polygon and the answer is undefined. So each one is passed through
``make_valid`` and recorded in a ledger, and every territory in the published output
carries whether its geometry was repaired. A reader who wants to discount the repaired
ones can see which they are. A repair that does not produce a polygonal result at all
removes the territory from the index and is reported as unusable, because a territory
this project cannot test containment against is not a territory it can report zero for.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

import numpy as np
import shapely
from pyproj import Transformer
from shapely.geometry import LineString, MultiPolygon, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree
from shapely.validation import make_valid

from inspected.sources import WIRES_TYPES

ALBERS_PIPELINE: Final[str] = (
    "+proj=pipeline "
    "+step +proj=unitconvert +xy_in=deg +xy_out=rad "
    "+step +proj=aea +lat_0=0 +lon_0=-120 +lat_1=34 +lat_2=40.5 "
    "+x_0=0 +y_0=-4000000 +ellps=GRS80"
)
"""California Albers, as a bare projection. Metres. No datum step, so no grid files."""

REPAIRED: Final[str] = "repaired"
AS_PUBLISHED: Final[str] = "as_published"
UNUSABLE: Final[str] = "unusable"


class TerritoryLoadError(ValueError):
    """The territory layer is not shaped the way this project reads it."""


def transformer() -> Transformer:
    """The one projection used everywhere. Constructed per call; pyproj caches PROJ."""
    return Transformer.from_pipeline(ALBERS_PIPELINE)


def project_lonlat(lon: np.ndarray, lat: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Longitude and latitude in degrees to Albers metres."""
    x, y = transformer().transform(lon, lat)
    return np.asarray(x, dtype="float64"), np.asarray(y, dtype="float64")


def _project_geometry(geom: BaseGeometry) -> BaseGeometry:
    tr = transformer()

    def _apply(coords: np.ndarray) -> np.ndarray:
        x, y = tr.transform(coords[:, 0], coords[:, 1])
        return np.column_stack([x, y])

    projected: BaseGeometry = shapely.transform(geom, _apply)
    return projected


def _polygonal(geom: BaseGeometry) -> BaseGeometry | None:
    """The polygonal part of a geometry, or None when there is not one."""
    if isinstance(geom, Polygon | MultiPolygon):
        return geom if not geom.is_empty else None
    parts = [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]
    if not parts:
        return None
    return MultiPolygon(parts) if len(parts) > 1 else parts[0]


@dataclass(frozen=True)
class Territory:
    """One published service territory outline, projected and validity-checked."""

    name: str
    kind: str
    object_id: int
    source_key: str
    geometry: BaseGeometry
    geometry_state: str
    geometry_note: str

    @property
    def repaired(self) -> bool:
        return self.geometry_state == REPAIRED


def _feature_fields(feature: dict[str, Any]) -> tuple[str, str, int]:
    props = feature.get("properties")
    if not isinstance(props, dict):
        raise TerritoryLoadError("a feature carries no properties object")
    name = props.get("Utility")
    kind = props.get("Type")
    oid = props.get("OBJECTID")
    if not isinstance(name, str) or not name.strip():
        raise TerritoryLoadError(f"a feature carries no Utility name: {props!r}")
    if not isinstance(kind, str) or not kind.strip():
        raise TerritoryLoadError(f"{name} carries no Type")
    if not isinstance(oid, int):
        raise TerritoryLoadError(f"{name} carries no integer OBJECTID")
    return name.strip(), kind.strip(), oid


def load_territories(
    collections: dict[str, dict[str, Any]],
    *,
    keep_types: tuple[str, ...] = WIRES_TYPES,
) -> tuple[tuple[Territory, ...], tuple[Territory, ...]]:
    """Read the published layers into projected territories.

    ``collections`` maps a source key to a GeoJSON FeatureCollection. Returns the
    usable territories and, separately, the ones whose geometry could not be repaired
    into anything containment can be tested against.

    Territories come back sorted by name. Nothing downstream sorts by a measured value,
    and this is where that starts.
    """
    usable: list[Territory] = []
    unusable: list[Territory] = []
    for source_key in sorted(collections):
        collection = collections[source_key]
        features = collection.get("features")
        if not isinstance(features, list):
            raise TerritoryLoadError(f"{source_key} is not a FeatureCollection")
        for feature in features:
            name, kind, oid = _feature_fields(feature)
            if kind not in keep_types:
                continue
            raw = feature.get("geometry")
            if raw is None:
                unusable.append(
                    Territory(
                        name,
                        kind,
                        oid,
                        source_key,
                        Polygon(),
                        UNUSABLE,
                        "the published feature carries no geometry",
                    )
                )
                continue
            geom = _project_geometry(shapely.geometry.shape(raw))
            state, note = AS_PUBLISHED, ""
            if not geom.is_valid:
                repaired = _polygonal(make_valid(geom))
                if repaired is None:
                    unusable.append(
                        Territory(
                            name,
                            kind,
                            oid,
                            source_key,
                            Polygon(),
                            UNUSABLE,
                            "repair produced no polygonal geometry to test against",
                        )
                    )
                    continue
                geom, state = repaired, REPAIRED
                note = (
                    "published geometry failed an OGC validity check and was repaired"
                )
            usable.append(Territory(name, kind, oid, source_key, geom, state, note))
    usable.sort(key=lambda t: (t.name, t.object_id))
    unusable.sort(key=lambda t: (t.name, t.object_id))
    return tuple(usable), tuple(unusable)


def territory_index(territories: tuple[Territory, ...]) -> STRtree:
    """A spatial index over the territory outlines, in the order given."""
    if not territories:
        raise TerritoryLoadError("no usable territory geometry to index")
    return STRtree([t.geometry for t in territories])


def boundary_segments(geom: BaseGeometry) -> list[LineString]:
    """Every edge of a polygon's rings, as individual two-point lines.

    Distance from a point to a whole outline is linear in the number of vertices, and
    the largest territory here carries over a hundred thousand of them. Indexing the
    edges turns tens of billions of comparisons into a tree lookup. The geometry is not
    altered: these are the same edges the polygon already has.
    """
    polys: list[Polygon]
    if isinstance(geom, Polygon):
        polys = [geom]
    elif isinstance(geom, MultiPolygon):
        polys = list(geom.geoms)
    else:  # pragma: no cover - load_territories only ever produces polygonal geometry
        raise TerritoryLoadError(f"cannot take a boundary from {geom.geom_type}")
    segments: list[LineString] = []
    for poly in polys:
        for ring in (poly.exterior, *poly.interiors):
            coords = list(ring.coords)
            segments.extend(
                LineString([coords[i], coords[i + 1]]) for i in range(len(coords) - 1)
            )
    if not segments:
        raise TerritoryLoadError("a territory outline has no edges")
    return segments


def distances_to_boundary(
    geom: BaseGeometry, xs: np.ndarray, ys: np.ndarray
) -> np.ndarray:
    """Metres from each point to the nearest edge of ``geom``."""
    if len(xs) == 0:
        return np.empty(0, dtype="float64")
    segments = boundary_segments(geom)
    tree = STRtree(segments)
    points = shapely.points(xs, ys)
    nearest = tree.nearest(points)
    return np.asarray(
        shapely.distance(points, np.asarray(segments, dtype=object)[nearest]),
        dtype="float64",
    )
