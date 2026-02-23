from __future__ import annotations

from dataclasses import dataclass

from cad_engine.geometry import Vec2
from cad_engine.viewport import InfiniteCanvasViewport


@dataclass(slots=True)
class MousePanZoomController:
    viewport: InfiniteCanvasViewport
    pan_sensitivity: float = 1.0
    zoom_step: float = 1.12

    _last_mouse: Vec2 | None = None

    def begin_pan(self, x: float, y: float) -> None:
        self._last_mouse = Vec2(x, y)

    def pan_to(self, x: float, y: float) -> None:
        if self._last_mouse is None:
            self._last_mouse = Vec2(x, y)
            return

        current = Vec2(x, y)
        dx_px = current.x - self._last_mouse.x
        dy_px = current.y - self._last_mouse.y

        # screen delta -> world delta; drag direction mirrors CAD behavior
        dx_world = -dx_px / self.viewport.zoom * self.pan_sensitivity
        dy_world = dy_px / self.viewport.zoom * self.pan_sensitivity
        self.viewport.pan(dx_world, dy_world)
        self._last_mouse = current

    def end_pan(self) -> None:
        self._last_mouse = None

    def wheel_zoom(self, x: float, y: float, direction: int) -> None:
        factor = self.zoom_step if direction > 0 else 1.0 / self.zoom_step
        self.viewport.zoom_at(factor=factor, anchor_screen=Vec2(x, y))
