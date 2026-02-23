from __future__ import annotations

from dataclasses import dataclass, field
import math
from itertools import count

from cad_engine.coordinates import CoordinateSystem
from cad_engine.document import Document, EntityType, Layer, Layout
from cad_engine.entities import Arc, Circle, Insert, Line, LinearDimension, Polyline, Text
from cad_engine.exporters.dxf import DxfExporter
from cad_engine.geometry import BoundingBox, Mat3, Vec2
from cad_engine.history import HistoryManager
from cad_engine.snap import ObjectSnapEngine, SnapCandidate
from cad_engine.spatial_index import SpatialHashIndex
from cad_engine.viewport import InfiniteCanvasViewport


@dataclass(slots=True)
class CadEngine:
    document: Document
    viewport: InfiniteCanvasViewport = field(default_factory=InfiniteCanvasViewport)
    ucs: CoordinateSystem = field(default_factory=CoordinateSystem)
    osnap: ObjectSnapEngine = field(default_factory=ObjectSnapEngine)
    spatial_index: SpatialHashIndex = field(default_factory=SpatialHashIndex)
    history: HistoryManager = field(default_factory=HistoryManager)

    @classmethod
    def create(cls, units: str = "mm") -> "CadEngine":
        engine = cls(document=Document(units=units))
        engine.rebuild_index()
        return engine

    def add_layer(
        self,
        name: str,
        color: str = "#111111",
        visible: bool = True,
        locked: bool = False,
        linetype: str = "CONTINUOUS",
    ) -> None:
        self.history.checkpoint(self.document)
        self.document.add_layer(Layer(name=name, color=color, visible=visible, locked=locked, linetype=linetype))

    def add_layout(self, name: str, kind: str = "paper", paper_size_mm: tuple[float, float] = (841.0, 594.0)) -> None:
        self.history.checkpoint(self.document)
        self.document.add_layout(Layout(name=name, kind=kind, paper_size_mm=paper_size_mm))

    def activate_layout(self, name: str) -> None:
        self.history.checkpoint(self.document)
        self.document.set_active_layout(name)

    def create_block(self, name: str, base_point: tuple[float, float] = (0.0, 0.0)) -> None:
        self.history.checkpoint(self.document)
        self.document.create_block(name, base_point=base_point)

    def add_block_entity(self, block_name: str, entity: EntityType) -> None:
        self.history.checkpoint(self.document)
        self.document.add_block_entity(block_name, entity)

    def transform_all(self, matrix: Mat3) -> None:
        self.history.checkpoint(self.document)
        self.document.entities = [entity.transform(matrix) for entity in self.document.entities]
        self.rebuild_index()

    def save_dxf(self, path: str) -> None:
        DxfExporter().export_file(self.document, path)

    def set_ucs(self, origin: tuple[float, float], angle_deg: float = 0.0) -> None:
        self.ucs = CoordinateSystem.from_degrees(origin=Vec2(*origin), angle_deg=angle_deg)

    def ucs_to_wcs(self, point: tuple[float, float]) -> Vec2:
        return self.ucs.to_wcs(Vec2(*point))

    def wcs_to_ucs(self, point: tuple[float, float]) -> Vec2:
        return self.ucs.to_ucs(Vec2(*point))

    def rebuild_index(self) -> None:
        self.spatial_index.build([(entity, self.document.entity_bounds(entity)) for entity in self.document.entities])

    def query_window(self, min_point: tuple[float, float], max_point: tuple[float, float]) -> list[EntityType]:
        bounds = BoundingBox(min=Vec2(*min_point), max=Vec2(*max_point))
        return self.spatial_index.query(bounds)

    def snap(self, cursor_world: tuple[float, float], include_grid: bool = True) -> SnapCandidate | None:
        return self.osnap.nearest(self.document.visible_entities(), Vec2(*cursor_world), self.viewport, include_grid)

    def undo(self) -> bool:
        ok = self.history.undo(self.document)
        if ok:
            self.rebuild_index()
        return ok

    def redo(self) -> bool:
        ok = self.history.redo(self.document)
        if ok:
            self.rebuild_index()
        return ok


class DrawingSession:
    def __init__(self, engine: CadEngine, default_layer: str = "0", use_ucs: bool = False) -> None:
        self.engine = engine
        self.default_layer = default_layer
        self.use_ucs = use_ucs
        self._counter = count(1)

    def _next_id(self, prefix: str) -> str:
        return f"{prefix}_{next(self._counter):06d}"

    def _to_wcs(self, point: tuple[float, float]) -> Vec2:
        return self.engine.ucs_to_wcs(point) if self.use_ucs else Vec2(*point)

    def _add(self, entity: EntityType) -> EntityType:
        self.engine.history.checkpoint(self.engine.document)
        self.engine.document.add_entity(entity)
        self.engine.spatial_index.insert(entity, self.engine.document.entity_bounds(entity))
        return entity

    def line(self, start: tuple[float, float], end: tuple[float, float], *, layer: str | None = None) -> Line:
        return self._add(
            Line(id=self._next_id("line"), start=self._to_wcs(start), end=self._to_wcs(end), layer=layer or self.default_layer)
        )

    def circle(self, center: tuple[float, float], radius: float, *, layer: str | None = None) -> Circle:
        if radius <= 0:
            raise ValueError("Circle radius must be positive")
        return self._add(
            Circle(id=self._next_id("circle"), center=self._to_wcs(center), radius=radius, layer=layer or self.default_layer)
        )

    def arc(
        self,
        center: tuple[float, float],
        radius: float,
        start_angle_deg: float,
        end_angle_deg: float,
        *,
        layer: str | None = None,
    ) -> Arc:
        if radius <= 0:
            raise ValueError("Arc radius must be positive")
        return self._add(
            Arc(
                id=self._next_id("arc"),
                center=self._to_wcs(center),
                radius=radius,
                start_angle=math.radians(start_angle_deg),
                end_angle=math.radians(end_angle_deg),
                layer=layer or self.default_layer,
            )
        )

    def polyline(
        self,
        vertices: list[tuple[float, float]],
        *,
        closed: bool = False,
        layer: str | None = None,
    ) -> Polyline:
        return self._add(
            Polyline(
                id=self._next_id("polyline"),
                vertices=[self._to_wcs(v) for v in vertices],
                closed=closed,
                layer=layer or self.default_layer,
            )
        )

    def text(
        self,
        position: tuple[float, float],
        value: str,
        *,
        height: float = 2.5,
        rotation_deg: float = 0.0,
        layer: str | None = None,
    ) -> Text:
        return self._add(
            Text(
                id=self._next_id("text"),
                position=self._to_wcs(position),
                value=value,
                height=height,
                rotation=math.radians(rotation_deg),
                layer=layer or self.default_layer,
            )
        )

    def linear_dimension(
        self,
        p1: tuple[float, float],
        p2: tuple[float, float],
        dim_line_point: tuple[float, float],
        *,
        text: str | None = None,
        layer: str | None = None,
    ) -> LinearDimension:
        return self._add(
            LinearDimension(
                id=self._next_id("dim"),
                p1=self._to_wcs(p1),
                p2=self._to_wcs(p2),
                dim_line_point=self._to_wcs(dim_line_point),
                text=text,
                layer=layer or self.default_layer,
            )
        )

    def insert_block(
        self,
        block_name: str,
        insertion_point: tuple[float, float],
        *,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        rotation_deg: float = 0.0,
        layer: str | None = None,
    ) -> Insert:
        if block_name not in self.engine.document.blocks:
            raise KeyError(f"Block not found: {block_name}")
        return self._add(
            Insert(
                id=self._next_id("insert"),
                block_name=block_name,
                insertion_point=self._to_wcs(insertion_point),
                scale_x=scale_x,
                scale_y=scale_y,
                rotation=math.radians(rotation_deg),
                layer=layer or self.default_layer,
            )
        )
