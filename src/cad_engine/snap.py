from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from cad_engine.entities import Arc, Circle, Insert, Line, LinearDimension, Polyline, Text
from cad_engine.geometry import Vec2
from cad_engine.viewport import InfiniteCanvasViewport


@dataclass(frozen=True, slots=True)
class SnapCandidate:
    kind: str
    point: Vec2
    distance: float


class ObjectSnapEngine:
    def __init__(self, pixel_tolerance: float = 12.0) -> None:
        self.pixel_tolerance = pixel_tolerance

    def collect_candidates(
        self,
        entities: Iterable[Line | Circle | Arc | Polyline | Text | LinearDimension | Insert],
    ) -> list[tuple[str, Vec2]]:
        points: list[tuple[str, Vec2]] = []
        for entity in entities:
            if isinstance(entity, Line):
                points.append(("endpoint", entity.start))
                points.append(("endpoint", entity.end))
                points.append(("midpoint", Vec2((entity.start.x + entity.end.x) / 2, (entity.start.y + entity.end.y) / 2)))
            elif isinstance(entity, Circle):
                points.append(("center", entity.center))
            elif isinstance(entity, Arc):
                points.append(("center", entity.center))
                points.append(("endpoint", entity.point_at(entity.start_angle)))
                points.append(("endpoint", entity.point_at(entity.end_angle)))
            elif isinstance(entity, Polyline):
                for v in entity.vertices:
                    points.append(("vertex", v))
            elif isinstance(entity, Text):
                points.append(("text_insert", entity.position))
            elif isinstance(entity, LinearDimension):
                points.append(("dim_point", entity.p1))
                points.append(("dim_point", entity.p2))
            else:
                points.append(("insert", entity.insertion_point))
        return points

    def nearest(
        self,
        entities: Iterable[Line | Circle | Arc | Polyline | Text | LinearDimension | Insert],
        cursor_world: Vec2,
        viewport: InfiniteCanvasViewport,
        include_grid: bool = True,
    ) -> SnapCandidate | None:
        best: SnapCandidate | None = None
        cursor_screen = viewport.world_to_screen(cursor_world)

        for kind, p in self.collect_candidates(entities):
            d = viewport.world_to_screen(p).distance_to(cursor_screen)
            if d <= self.pixel_tolerance and (best is None or d < best.distance):
                best = SnapCandidate(kind=kind, point=p, distance=d)

        if include_grid and viewport.grid_enabled:
            g = viewport.snap_to_grid(cursor_world)
            d = viewport.world_to_screen(g).distance_to(cursor_screen)
            if d <= self.pixel_tolerance and (best is None or d < best.distance):
                best = SnapCandidate(kind="grid", point=g, distance=d)

        return best
