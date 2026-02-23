from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from cad_engine.entities import Arc, Circle, Insert, Line, LinearDimension, Polyline, Text
from cad_engine.geometry import BoundingBox, Mat3, Vec2
from cad_engine.units import normalize_units

EntityType = Line | Circle | Arc | Polyline | Text | LinearDimension | Insert


@dataclass(slots=True)
class Layer:
    name: str
    color: str = "#111111"
    visible: bool = True
    locked: bool = False
    linetype: str = "CONTINUOUS"


@dataclass(slots=True)
class BlockDefinition:
    name: str
    base_point: tuple[float, float] = (0.0, 0.0)
    entities: list[EntityType] = field(default_factory=list)


@dataclass(slots=True)
class Layout:
    name: str
    kind: str = "model"  # model or paper
    paper_size_mm: tuple[float, float] = (841.0, 594.0)
    viewport_center: tuple[float, float] = (0.0, 0.0)
    viewport_scale: float = 1.0


@dataclass(slots=True)
class Document:
    units: str = "mm"
    entities: list[EntityType] = field(default_factory=list)
    layers: dict[str, Layer] = field(default_factory=lambda: {"0": Layer(name="0")})
    blocks: dict[str, BlockDefinition] = field(default_factory=dict)
    layouts: dict[str, Layout] = field(
        default_factory=lambda: {
            "Model": Layout(name="Model", kind="model"),
            "Layout1": Layout(name="Layout1", kind="paper"),
        }
    )
    active_layout: str = "Model"

    def __post_init__(self) -> None:
        self.units = normalize_units(self.units)

    def add_layer(self, layer: Layer) -> None:
        if layer.name in self.layers:
            raise ValueError(f"Layer already exists: {layer.name}")
        self.layers[layer.name] = layer

    def add_layout(self, layout: Layout) -> None:
        if layout.name in self.layouts:
            raise ValueError(f"Layout already exists: {layout.name}")
        self.layouts[layout.name] = layout

    def set_active_layout(self, name: str) -> None:
        if name not in self.layouts:
            raise KeyError(f"Layout not found: {name}")
        self.active_layout = name

    def create_block(self, name: str, base_point: tuple[float, float] = (0.0, 0.0)) -> BlockDefinition:
        if name in self.blocks:
            raise ValueError(f"Block already exists: {name}")
        block = BlockDefinition(name=name, base_point=base_point)
        self.blocks[name] = block
        return block

    def add_block_entity(self, block_name: str, entity: EntityType) -> None:
        block = self.blocks.get(block_name)
        if block is None:
            raise KeyError(f"Block not found: {block_name}")
        block.entities.append(entity)

    def add_entity(self, entity: EntityType) -> None:
        layer = self.layers.get(entity.layer)
        if layer is None:
            raise KeyError(f"Layer not found: {entity.layer}")
        if layer.locked:
            raise PermissionError(f"Layer is locked: {entity.layer}")
        self.entities.append(entity)

    def extend(self, entities: Iterable[EntityType]) -> None:
        for entity in entities:
            self.add_entity(entity)

    def visible_entities(self) -> list[EntityType]:
        return [e for e in self.entities if self.layers[e.layer].visible]

    def entity_bounds(self, entity: EntityType) -> BoundingBox:
        if not isinstance(entity, Insert):
            return entity.bounds()

        block = self.blocks.get(entity.block_name)
        if block is None or not block.entities:
            return entity.bounds()

        base = Vec2(*block.base_point)
        transform = (
            Mat3.translation(entity.insertion_point.x, entity.insertion_point.y)
            @ Mat3.rotation(entity.rotation)
            @ Mat3.scale(entity.scale_x, entity.scale_y)
            @ Mat3.translation(-base.x, -base.y)
        )

        b = block.entities[0].transform(transform).bounds()
        for block_entity in block.entities[1:]:
            b = b.union(block_entity.transform(transform).bounds())
        return b

    def bounds(self) -> BoundingBox:
        visible = self.visible_entities()
        if not visible:
            raise ValueError("Document is empty or no visible entities")

        bounds = self.entity_bounds(visible[0])
        for entity in visible[1:]:
            bounds = bounds.union(self.entity_bounds(entity))
        return bounds
