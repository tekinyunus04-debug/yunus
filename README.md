# yunus CAD Engine

Uygulamana gömülebilecek, mimar/mühendis odaklı 2D CAD çekirdeği (AutoCAD-benzeri temel platform).

## Eklenen kapsam (hepsi)
- Geometri: `Line`, `Circle`, `Arc`, `Polyline`, `Text`, `LinearDimension`, `Insert`
- DXF/SVG export
- Sonsuz tuval/ekran: pan, zoom, world↔screen
- Grid + adaptive step + grid snap
- UCS/WCS koordinat sistemi
- Object Snap: endpoint, midpoint, center, vertex, text insert, dim points, grid
- Spatial hash ile hızlı window selection
- Block tanımı ve INSERT yerleştirme (block geometrisine göre doğru sınır/bounds hesabı)
- Layout yönetimi (Model/Paper)
- Undo/Redo geçmiş yönetimi (katman, blok, layout ve entity durumunu geri alır)
- Katman/linetype/lock/visibility
- **Türkçe masaüstü arayüz** (`TurkishCadUI`) ve pürüzsüz mouse pan/zoom denetleyicisi (`MousePanZoomController`)

## Kurulum
```bash
pip install -e .
```

## Hızlı kullanım
```python
from cad_engine import CadEngine, DrawingSession, DxfExporter

engine = CadEngine.create(units="mm")
engine.add_layer("walls", linetype="CONTINUOUS")

# UCS
engine.set_ucs((1000, 500), angle_deg=30)
draw = DrawingSession(engine, use_ucs=True)

draw.line((0, 0), (5000, 0), layer="walls")
draw.text((100, 120), "A-101", layer="walls")
draw.linear_dimension((0, 0), (5000, 0), (2500, 200), layer="walls")

# Block
engine.create_block("door")
engine.add_block_entity("door", draw.line((0, 0), (900, 0), layer="walls"))
draw.insert_block("door", (1200, 0), layer="walls")

# Snap + seçim
snap = engine.snap((1200, 10), include_grid=True)
selected = engine.query_window((0, -100), (6000, 1000))

# Layout + undo/redo
engine.add_layout("A1", kind="paper")
engine.activate_layout("A1")
engine.undo()
engine.redo()

# DXF
DxfExporter().export_file(engine.document, "plan.dxf")
```

## Türkçe arayüz (mouse hareketleri)
```python
from cad_engine import CadEngine, DrawingSession, TurkishCadUI

engine = CadEngine.create()
draw = DrawingSession(engine)
draw.line((0, 0), (100, 0))
draw.circle((50, 30), 20)

ui = TurkishCadUI(engine)
ui.run()
```

Mouse kontrolleri:
- Sol tuş sürükle: pan
- Tekerlek: imleç odaklı zoom (Windows/Mac)
- Linux: `Button-4 / Button-5` zoom

## Test
```bash
pytest
```
