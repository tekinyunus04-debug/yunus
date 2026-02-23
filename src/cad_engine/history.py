from __future__ import annotations

from dataclasses import dataclass, field
import copy

from cad_engine.document import BlockDefinition, Document, EntityType, Layer, Layout


@dataclass(frozen=True, slots=True)
class DocumentState:
    units: str
    entities: list[EntityType]
    layers: dict[str, Layer]
    blocks: dict[str, BlockDefinition]
    layouts: dict[str, Layout]
    active_layout: str


@dataclass(slots=True)
class HistoryManager:
    undo_stack: list[DocumentState] = field(default_factory=list)
    redo_stack: list[DocumentState] = field(default_factory=list)

    def _snapshot(self, document: Document) -> DocumentState:
        return DocumentState(
            units=document.units,
            entities=copy.deepcopy(document.entities),
            layers=copy.deepcopy(document.layers),
            blocks=copy.deepcopy(document.blocks),
            layouts=copy.deepcopy(document.layouts),
            active_layout=document.active_layout,
        )

    def _restore(self, document: Document, state: DocumentState) -> None:
        document.units = state.units
        document.entities = copy.deepcopy(state.entities)
        document.layers = copy.deepcopy(state.layers)
        document.blocks = copy.deepcopy(state.blocks)
        document.layouts = copy.deepcopy(state.layouts)
        document.active_layout = state.active_layout

    def checkpoint(self, document: Document) -> None:
        self.undo_stack.append(self._snapshot(document))
        self.redo_stack.clear()

    def undo(self, document: Document) -> bool:
        if not self.undo_stack:
            return False
        self.redo_stack.append(self._snapshot(document))
        self._restore(document, self.undo_stack.pop())
        return True

    def redo(self, document: Document) -> bool:
        if not self.redo_stack:
            return False
        self.undo_stack.append(self._snapshot(document))
        self._restore(document, self.redo_stack.pop())
        return True
