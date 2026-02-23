from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass

from cad_engine.engine import CadEngine
from cad_engine.entities import Arc, Circle, Insert, Line, LinearDimension, Polyline, Text
from cad_engine.geometry import Vec2
from cad_engine.interaction import MousePanZoomController


@dataclass(slots=True)
class TurkishCadUI:
    engine: CadEngine

    def run(self) -> None:
        root = tk.Tk()
        root.title("CAD Motoru - Türkçe Arayüz")

        info_var = tk.StringVar(value="Hazır")
        toolbar = tk.Frame(root)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        tk.Label(toolbar, text="Durum:").pack(side=tk.LEFT, padx=4)
        tk.Label(toolbar, textvariable=info_var).pack(side=tk.LEFT, padx=4)

        canvas = tk.Canvas(root, bg="#16181d", width=self.engine.viewport.width, height=self.engine.viewport.height)
        canvas.pack(fill=tk.BOTH, expand=True)

        controller = MousePanZoomController(self.engine.viewport)

        def redraw() -> None:
            canvas.delete("all")
            self._draw_grid(canvas)
            for e in self.engine.document.visible_entities():
                self._draw_entity(canvas, e)
            info_var.set(
                f"Merkez: ({self.engine.viewport.center.x:.2f}, {self.engine.viewport.center.y:.2f}) | "
                f"Yakınlaştırma: {self.engine.viewport.zoom:.2f}x"
            )

        def on_pan_start(event: tk.Event) -> None:  # type: ignore[type-arg]
            controller.begin_pan(event.x, event.y)

        def on_pan_move(event: tk.Event) -> None:  # type: ignore[type-arg]
            controller.pan_to(event.x, event.y)
            redraw()

        def on_pan_end(_: tk.Event) -> None:  # type: ignore[type-arg]
            controller.end_pan()

        def on_mousewheel(event: tk.Event) -> None:  # type: ignore[type-arg]
            # Windows/Mac delta handling
            direction = 1 if getattr(event, "delta", 0) > 0 else -1
            controller.wheel_zoom(event.x, event.y, direction)
            redraw()

        def on_linux_wheel_up(event: tk.Event) -> None:  # type: ignore[type-arg]
            controller.wheel_zoom(event.x, event.y, 1)
            redraw()

        def on_linux_wheel_down(event: tk.Event) -> None:  # type: ignore[type-arg]
            controller.wheel_zoom(event.x, event.y, -1)
            redraw()

        canvas.bind("<ButtonPress-1>", on_pan_start)
        canvas.bind("<B1-Motion>", on_pan_move)
        canvas.bind("<ButtonRelease-1>", on_pan_end)
        canvas.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_linux_wheel_up)
        canvas.bind("<Button-5>", on_linux_wheel_down)

        redraw()
        root.mainloop()

    def _screen(self, p: Vec2) -> tuple[float, float]:
        s = self.engine.viewport.world_to_screen(p)
        return s.x, s.y

    def _draw_grid(self, canvas: tk.Canvas) -> None:
        step = self.engine.viewport.adaptive_grid_step()
        center = self.engine.viewport.center
        width, height = self.engine.viewport.width, self.engine.viewport.height

        min_world = self.engine.viewport.screen_to_world(Vec2(0, height))
        max_world = self.engine.viewport.screen_to_world(Vec2(width, 0))

        x = (int(min_world.x // step) - 1) * step
        while x <= max_world.x + step:
            x1, y1 = self._screen(Vec2(x, min_world.y))
            x2, y2 = self._screen(Vec2(x, max_world.y))
            color = "#2e3540" if abs(x) > 1e-9 else "#606e82"
            canvas.create_line(x1, y1, x2, y2, fill=color)
            x += step

        y = (int(min_world.y // step) - 1) * step
        while y <= max_world.y + step:
            x1, y1 = self._screen(Vec2(min_world.x, y))
            x2, y2 = self._screen(Vec2(max_world.x, y))
            color = "#2e3540" if abs(y) > 1e-9 else "#606e82"
            canvas.create_line(x1, y1, x2, y2, fill=color)
            y += step

        cx, cy = self._screen(center)
        canvas.create_oval(cx - 2, cy - 2, cx + 2, cy + 2, outline="#8fb3ff")

    def _draw_entity(self, canvas: tk.Canvas, e: Line | Circle | Arc | Polyline | Text | LinearDimension | Insert) -> None:
        if isinstance(e, Line):
            x1, y1 = self._screen(e.start)
            x2, y2 = self._screen(e.end)
            canvas.create_line(x1, y1, x2, y2, fill=e.color)
            return

        if isinstance(e, Circle):
            cx, cy = self._screen(e.center)
            r = e.radius * self.engine.viewport.zoom
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=e.color)
            return

        if isinstance(e, Arc):
            c = e.center
            r = e.radius
            p1 = self._screen(Vec2(c.x - r, c.y - r))
            p2 = self._screen(Vec2(c.x + r, c.y + r))
            start = -e.start_angle * 180 / 3.141592653589793
            extent = -(e.end_angle - e.start_angle) * 180 / 3.141592653589793
            canvas.create_arc(p1[0], p1[1], p2[0], p2[1], start=start, extent=extent, style=tk.ARC, outline=e.color)
            return

        if isinstance(e, Polyline):
            pts: list[float] = []
            for v in e.vertices:
                sx, sy = self._screen(v)
                pts.extend([sx, sy])
            if e.closed and len(pts) >= 4:
                pts.extend(pts[:2])
            canvas.create_line(*pts, fill=e.color)
            return

        if isinstance(e, Text):
            sx, sy = self._screen(e.position)
            canvas.create_text(sx, sy, text=e.value, fill=e.color, anchor=tk.SW)
            return

        if isinstance(e, LinearDimension):
            x1, y1 = self._screen(e.p1)
            x2, y2 = self._screen(e.p2)
            tx, ty = self._screen(e.dim_line_point)
            canvas.create_line(x1, y1, x2, y2, fill=e.color)
            canvas.create_text(tx, ty, text=e.display_text(), fill=e.color)
            return

        sx, sy = self._screen(e.insertion_point)
        canvas.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, outline="#9a9a9a")
        canvas.create_text(sx + 5, sy - 5, text=e.block_name, fill="#9a9a9a", anchor=tk.SW)
