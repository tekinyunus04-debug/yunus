from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
import math

from cad_engine.geometry import BoundingBox, Mat3, Vec2


class Entity(Protocol):
    id: str
    layer: str

    def bounds(self) -> BoundingBox: ...

    def transform(self, matrix: Mat3) -> "Entity": ...


@dataclass(frozen=True, slots=True)
class Line:
    id: str
    start: Vec2
    end: Vec2
    layer: str = "0"
    color: str = "#111111"
    line_weight: float = 0.35

    def bounds(self) -> BoundingBox:
        return BoundingBox.from_points(self.start, self.end)

    def length(self) -> float:
        return self.start.distance_to(self.end)

    def transform(self, matrix: Mat3) -> "Line":
        return Line(
            id=self.id,
            start=matrix.transform_point(self.start),
            end=matrix.transform_point(self.end),
            layer=self.layer,
            color=self.color,
            line_weight=self.line_weight,
        )


@dataclass(frozen=True, slots=True)
class Circle:
    id: str
    center: Vec2
    radius: float
    layer: str = "0"
    color: str = "#111111"
    line_weight: float = 0.35

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError("Circle radius must be positive")

    def bounds(self) -> BoundingBox:
        r = self.radius
        return BoundingBox(
            min=Vec2(self.center.x - r, self.center.y - r),
            max=Vec2(self.center.x + r, self.center.y + r),
        )

    def transform(self, matrix: Mat3) -> "Circle":
        transformed_center = matrix.transform_point(self.center)
        axis_point = matrix.transform_point(self.center + Vec2(self.radius, 0.0))
        transformed_radius = transformed_center.distance_to(axis_point)
        return Circle(
            id=self.id,
            center=transformed_center,
            radius=transformed_radius,
            layer=self.layer,
            color=self.color,
            line_weight=self.line_weight,
        )


@dataclass(frozen=True, slots=True)
class Arc:
    id: str
    center: Vec2
    radius: float
    start_angle: float
    end_angle: float
    layer: str = "0"
    color: str = "#111111"
    line_weight: float = 0.35

    def __post_init__(self) -> None:
        if self.radius <= 0:
            raise ValueError("Arc radius must be positive")

    def bounds(self) -> BoundingBox:
        critical_angles = [
            self.start_angle,
            self.end_angle,
            0.0,
            math.pi / 2,
            math.pi,
            (3 * math.pi) / 2,
        ]
        pts = [self.point_at(a) for a in critical_angles if self.contains_angle(a)]
        return BoundingBox.from_points(*pts)

    def contains_angle(self, angle: float) -> bool:
        start = self.start_angle % (2 * math.pi)
        end = self.end_angle % (2 * math.pi)
        ang = angle % (2 * math.pi)
        if start <= end:
            return start <= ang <= end
        return ang >= start or ang <= end

    def transform(self, matrix: Mat3) -> "Arc":
        transformed_center = matrix.transform_point(self.center)
        transformed_start = matrix.transform_point(self.point_at(self.start_angle))
        transformed_end = matrix.transform_point(self.point_at(self.end_angle))

        new_radius = transformed_center.distance_to(transformed_start)
        start_angle = math.atan2(
            transformed_start.y - transformed_center.y,
            transformed_start.x - transformed_center.x,
        )
        end_angle = math.atan2(
            transformed_end.y - transformed_center.y,
            transformed_end.x - transformed_center.x,
        )
        return Arc(
            id=self.id,
            center=transformed_center,
            radius=new_radius,
            start_angle=start_angle,
            end_angle=end_angle,
            layer=self.layer,
            color=self.color,
            line_weight=self.line_weight,
        )

    def point_at(self, angle: float) -> Vec2:
        return Vec2(
            self.center.x + self.radius * math.cos(angle),
            self.center.y + self.radius * math.sin(angle),
        )


@dataclass(slots=True)
class Polyline:
    id: str
    vertices: list[Vec2]
    closed: bool = False
    layer: str = "0"
    color: str = "#111111"
    line_weight: float = 0.35
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.vertices) < 2:
            raise ValueError("Polyline requires at least 2 vertices")

    def bounds(self) -> BoundingBox:
        return BoundingBox.from_points(*self.vertices)

    def transform(self, matrix: Mat3) -> "Polyline":
        return Polyline(
            id=self.id,
            vertices=[matrix.transform_point(v) for v in self.vertices],
            closed=self.closed,
            layer=self.layer,
            color=self.color,
            line_weight=self.line_weight,
            metadata=dict(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class Text:
    id: str
    position: Vec2
    value: str
    height: float = 2.5
    rotation: float = 0.0
    layer: str = "0"
    color: str = "#111111"

    def __post_init__(self) -> None:
        if self.height <= 0:
            raise ValueError("Text height must be positive")

    def bounds(self) -> BoundingBox:
        width = max(len(self.value), 1) * self.height * 0.6
        return BoundingBox(
            min=self.position,
            max=Vec2(self.position.x + width, self.position.y + self.height),
        )

    def transform(self, matrix: Mat3) -> "Text":
        return Text(
            id=self.id,
            position=matrix.transform_point(self.position),
            value=self.value,
            height=self.height,
            rotation=self.rotation,
            layer=self.layer,
            color=self.color,
        )


@dataclass(frozen=True, slots=True)
class LinearDimension:
    id: str
    p1: Vec2
    p2: Vec2
    dim_line_point: Vec2
    text: str | None = None
    layer: str = "0"
    color: str = "#111111"

    def measured_value(self) -> float:
        return self.p1.distance_to(self.p2)

    def display_text(self, precision: int = 2) -> str:
        if self.text:
            return self.text
        return f"{self.measured_value():.{precision}f}"

    def bounds(self) -> BoundingBox:
        return BoundingBox.from_points(self.p1, self.p2, self.dim_line_point)

    def transform(self, matrix: Mat3) -> "LinearDimension":
        return LinearDimension(
            id=self.id,
            p1=matrix.transform_point(self.p1),
            p2=matrix.transform_point(self.p2),
            dim_line_point=matrix.transform_point(self.dim_line_point),
            text=self.text,
            layer=self.layer,
            color=self.color,
        )


@dataclass(frozen=True, slots=True)
class Insert:
    id: str
    block_name: str
    insertion_point: Vec2
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation: float = 0.0
    layer: str = "0"

    def bounds(self) -> BoundingBox:
        # exact bounds require block lookup; insertion point is safe fallback bound anchor.
        return BoundingBox.from_points(self.insertion_point)

    def transform(self, matrix: Mat3) -> "Insert":
        return Insert(
            id=self.id,
            block_name=self.block_name,
            insertion_point=matrix.transform_point(self.insertion_point),
            scale_x=self.scale_x,
            scale_y=self.scale_y,
            rotation=self.rotation,
            layer=self.layer,
        )
