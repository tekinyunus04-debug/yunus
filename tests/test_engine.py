from cad_engine import CadEngine, DrawingSession, DxfExporter, Line, Mat3, SvgExporter, Vec2


def test_session_adds_entities_and_bounds():
    engine = CadEngine.create()
    engine.add_layer("construction", linetype="DASHED")
    draw = DrawingSession(engine)

    draw.line((0, 0), (100, 0))
    draw.circle((50, 50), 10, layer="construction")
    draw.polyline([(0, 0), (0, 10), (10, 10)], closed=False)

    bounds = engine.document.bounds()
    assert bounds.min.x == 0
    assert bounds.min.y == 0
    assert bounds.max.x == 100
    assert bounds.max.y == 60


def test_transform_and_export_svg():
    engine = CadEngine.create()
    draw = DrawingSession(engine)
    draw.arc((0, 0), 5, 0, 90)

    engine.transform_all(Mat3.translation(10, 0))
    svg = SvgExporter().export(engine.document)

    assert "<svg" in svg
    assert "<path" in svg
    assert "M 15.0" in svg


def test_export_dxf_contains_units_layers_and_entities(tmp_path):
    engine = CadEngine.create(units="millimeters")
    engine.add_layer("walls", linetype="CONTINUOUS")
    draw = DrawingSession(engine)
    draw.line((0, 0), (100, 0), layer="walls")
    draw.circle((10, 20), 5, layer="walls")
    draw.text((5, 5), "A-01", layer="walls")

    path = tmp_path / "plan.dxf"
    engine.save_dxf(str(path))
    text = path.read_text(encoding="utf-8")

    assert "$INSUNITS" in text
    assert "70\n4" in text
    assert "LAYER" in text
    assert "2\nwalls" in text
    assert "LINE" in text
    assert "CIRCLE" in text
    assert "TEXT" in text


def test_arc_bounds_are_tight_for_quadrant_arc():
    engine = CadEngine.create()
    draw = DrawingSession(engine)
    draw.arc((0, 0), 10, 0, 90)

    bounds = engine.document.bounds()
    assert round(bounds.min.x, 6) == 0
    assert round(bounds.min.y, 6) == 0
    assert round(bounds.max.x, 6) == 10
    assert round(bounds.max.y, 6) == 10


def test_invalid_units_raise_error():
    try:
        CadEngine.create(units="parsec")
    except ValueError as exc:
        assert "Unsupported unit" in str(exc)
    else:
        raise AssertionError("Expected invalid unit to raise ValueError")


def test_layer_lock_is_enforced():
    engine = CadEngine.create()
    engine.add_layer("locked_layer", locked=True)
    draw = DrawingSession(engine)

    try:
        draw.line((0, 0), (1, 1), layer="locked_layer")
    except PermissionError:
        pass
    else:
        raise AssertionError("Expected PermissionError for locked layer")


def test_dxf_exporter_direct_string_output():
    engine = CadEngine.create()
    draw = DrawingSession(engine)
    draw.polyline([(0, 0), (1, 0), (1, 1)], closed=True)

    dxf = DxfExporter().export(engine.document)
    assert "LWPOLYLINE" in dxf
    assert "70\n1" in dxf
    assert dxf.strip().endswith("EOF")


def test_infinite_canvas_viewport_roundtrip_and_pan_zoom():
    engine = CadEngine.create()
    world = Vec2(2500.0, -500.0)
    screen = engine.viewport.world_to_screen(world)
    back = engine.viewport.screen_to_world(screen)
    assert round(back.x, 6) == world.x
    assert round(back.y, 6) == world.y

    old_center = engine.viewport.center
    engine.viewport.pan(100, 200)
    assert engine.viewport.center.x == old_center.x + 100
    assert engine.viewport.center.y == old_center.y + 200

    engine.viewport.zoom_at(2.0)
    assert engine.viewport.zoom == 2.0


def test_ucs_drawing_and_conversion():
    engine = CadEngine.create()
    engine.set_ucs((100, 100), angle_deg=90)
    draw = DrawingSession(engine, use_ucs=True)
    line = draw.line((10, 0), (10, 10))

    assert round(line.start.x, 6) == 100
    assert round(line.start.y, 6) == 110
    assert round(line.end.x, 6) == 90
    assert round(line.end.y, 6) == 110


def test_spatial_window_query_returns_local_entities():
    engine = CadEngine.create()
    draw = DrawingSession(engine)
    inside = draw.line((10, 10), (20, 20))
    draw.line((500, 500), (600, 600))

    found = engine.query_window((0, 0), (100, 100))
    assert inside in found
    assert len(found) == 1


def test_object_snap_endpoint_and_grid():
    engine = CadEngine.create()
    draw = DrawingSession(engine)
    draw.line((0, 0), (100, 0))

    snap = engine.snap((1.0, 0.0), include_grid=False)
    assert snap is not None
    assert snap.kind in {"endpoint", "midpoint"}

    engine.viewport.zoom = 100
    snap_grid = engine.snap((10.05, 9.95), include_grid=True)
    assert snap_grid is not None


def test_block_insert_layout_and_undo_redo(tmp_path):
    engine = CadEngine.create()
    engine.document.create_block("door")
    draw = DrawingSession(engine)
    engine.document.add_block_entity("door", draw.line((0, 0), (900, 0)))

    ins = draw.insert_block("door", (2000, 1500))
    assert ins.block_name == "door"

    engine.add_layout("A1", kind="paper")
    engine.activate_layout("A1")
    assert engine.document.active_layout == "A1"

    assert engine.undo() is True
    assert engine.document.active_layout == "Model"
    assert engine.redo() is True

    dxf_path = tmp_path / "with_blocks.dxf"
    engine.save_dxf(str(dxf_path))
    txt = dxf_path.read_text(encoding="utf-8")
    assert "BLOCKS" in txt
    assert "INSERT" in txt


def test_dimension_and_text_in_svg_and_dxf(tmp_path):
    engine = CadEngine.create()
    draw = DrawingSession(engine)
    draw.linear_dimension((0, 0), (100, 0), (50, 15))
    draw.text((10, 5), "NOTE")

    svg = SvgExporter().export(engine.document)
    assert "<text" in svg

    path = tmp_path / "dim.dxf"
    engine.save_dxf(str(path))
    content = path.read_text(encoding="utf-8")
    assert "DIMENSION" in content
    assert "TEXT" in content


def test_history_restores_layers_and_blocks_on_undo_redo():
    engine = CadEngine.create()
    engine.add_layer("mechanical")
    engine.create_block("bolt")

    assert "mechanical" in engine.document.layers
    assert "bolt" in engine.document.blocks

    assert engine.undo() is True
    assert "bolt" not in engine.document.blocks
    assert engine.undo() is True
    assert "mechanical" not in engine.document.layers

    assert engine.redo() is True
    assert "mechanical" in engine.document.layers
    assert engine.redo() is True
    assert "bolt" in engine.document.blocks


def test_insert_bounds_uses_block_geometry_for_index_and_document_bounds():
    engine = CadEngine.create()
    engine.create_block("window", base_point=(0, 0))
    engine.add_block_entity("window", Line(id="b1", start=Vec2(0, 0), end=Vec2(2, 0)))
    engine.add_block_entity("window", Line(id="b2", start=Vec2(2, 0), end=Vec2(2, 1)))

    draw = DrawingSession(engine)
    draw.insert_block("window", (10, 10), scale_x=2, scale_y=2)

    b = engine.document.bounds()
    assert round(b.min.x, 6) == 10
    assert round(b.min.y, 6) == 10
    assert round(b.max.x, 6) == 14
    assert round(b.max.y, 6) == 12

    found = engine.query_window((13.5, 11.5), (14.1, 12.1))
    assert len(found) == 1
