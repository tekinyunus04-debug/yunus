from __future__ import annotations

from dataclasses import dataclass
import math

from cad_engine.geometry import Vec2


@dataclass(slots=True)
class InfiniteCanvasViewport:
    width: int = 1920
    height: int = 1080
    zoom: float = 1.0
    center: Vec2 = Vec2(0.0, 0.0)
    grid_enabled: bool = True
    grid_base_step: float = 1.0

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Viewport width/height must be positive")
        if self.zoom <= 0:
            raise ValueError("Viewport zoom must be positive")

    def world_to_screen(self, point: Vec2) -> Vec2:
        x = (point.x - self.center.x) * self.zoom + self.width / 2
        y = self.height / 2 - (point.y - self.center.y) * self.zoom
        return Vec2(x, y)

    def screen_to_world(self, point: Vec2) -> Vec2:
        x = (point.x - self.width / 2) / self.zoom + self.center.x
        y = (self.height / 2 - point.y) / self.zoom + self.center.y
        return Vec2(x, y)

    def pan(self, dx_world: float, dy_world: float) -> None:
        self.center = Vec2(self.center.x + dx_world, self.center.y + dy_world)

    def zoom_at(self, factor: float, anchor_screen: Vec2 | None = None) -> None:
        if factor <= 0:
            raise ValueError("Zoom factor must be positive")

        if anchor_screen is None:
            self.zoom *= factor
            return

        anchor_before = self.screen_to_world(anchor_screen)
        self.zoom *= factor
        anchor_after = self.screen_to_world(anchor_screen)
        self.center = Vec2(
            self.center.x + (anchor_before.x - anchor_after.x),
            self.center.y + (anchor_before.y - anchor_after.y),
        )

    def adaptive_grid_step(self, target_pixels: float = 80.0) -> float:
        if target_pixels <= 0:
            raise ValueError("target_pixels must be positive")
        world_step = target_pixels / self.zoom
        power = 10 ** math.floor(math.log10(world_step)) if world_step > 0 else 1
        normalized = world_step / power

        if normalized <= 1:
            nice = 1
        elif normalized <= 2:
            nice = 2
        elif normalized <= 5:
            nice = 5
        else:
            nice = 10

        return nice * power * self.grid_base_step

    def snap_to_grid(self, point: Vec2) -> Vec2:
        step = self.adaptive_grid_step()
        return Vec2(round(point.x / step) * step, round(point.y / step) * step)
