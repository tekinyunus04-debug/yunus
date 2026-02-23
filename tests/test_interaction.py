from cad_engine.geometry import Vec2
from cad_engine.interaction import MousePanZoomController
from cad_engine.viewport import InfiniteCanvasViewport


def test_mouse_pan_updates_center_with_zoom_scaling():
    vp = InfiniteCanvasViewport(width=1000, height=800, zoom=2.0)
    controller = MousePanZoomController(vp)

    controller.begin_pan(100, 100)
    controller.pan_to(120, 130)

    assert vp.center.x == -10.0
    assert vp.center.y == 15.0


def test_wheel_zoom_keeps_anchor_world_point_stable():
    vp = InfiniteCanvasViewport(width=1000, height=800, zoom=1.0)
    controller = MousePanZoomController(vp)
    anchor_screen = Vec2(700, 500)

    before = vp.screen_to_world(anchor_screen)
    controller.wheel_zoom(anchor_screen.x, anchor_screen.y, direction=1)
    after = vp.screen_to_world(anchor_screen)

    assert round(before.x, 8) == round(after.x, 8)
    assert round(before.y, 8) == round(after.y, 8)
