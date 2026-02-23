from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict

from cad_engine.document import EntityType
from cad_engine.geometry import BoundingBox


@dataclass(slots=True)
class SpatialHashIndex:
    cell_size: float = 100.0
    _cells: dict[tuple[int, int], list[EntityType]] = field(default_factory=lambda: defaultdict(list))

    def _cell_range(self, bounds: BoundingBox) -> tuple[range, range]:
        min_x = int(bounds.min.x // self.cell_size)
        max_x = int(bounds.max.x // self.cell_size)
        min_y = int(bounds.min.y // self.cell_size)
        max_y = int(bounds.max.y // self.cell_size)
        return range(min_x, max_x + 1), range(min_y, max_y + 1)

    def insert(self, entity: EntityType, bounds: BoundingBox | None = None) -> None:
        b = bounds or entity.bounds()
        rx, ry = self._cell_range(b)
        for x in rx:
            for y in ry:
                self._cells[(x, y)].append(entity)

    def build(self, entries: list[tuple[EntityType, BoundingBox]] | list[EntityType]) -> None:
        self._cells.clear()
        for entry in entries:
            if isinstance(entry, tuple):
                entity, bounds = entry
                self.insert(entity, bounds)
            else:
                self.insert(entry)

    def query(self, bounds: BoundingBox) -> list[EntityType]:
        rx, ry = self._cell_range(bounds)
        found: list[EntityType] = []
        seen: set[int] = set()
        for x in rx:
            for y in ry:
                for entity in self._cells.get((x, y), []):
                    key = id(entity)
                    if key not in seen:
                        seen.add(key)
                        found.append(entity)
        return found
