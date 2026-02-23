from __future__ import annotations

from xml.sax.saxutils import escape
import math

from cad_engine.document import Document
from cad_engine.entities import Arc, Circle, Insert, Line, LinearDimension, Polyline, Text


class SvgExporter:
    def __init__(self, stroke_scale: float = 1.0) -> None:
        self.stroke_scale = stroke_scale

    def export(self, document: Document) -> str:
        bounds = document.bounds().expand(10)
        width = bounds.max.x - bounds.min.x
        height = bounds.max.y - bounds.min.y

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{bounds.min.x} '
                f'{-bounds.max.y} {width} {height}" width="{width}" height="{height}">'
            ),
            '<g fill="none" stroke-linecap="round" stroke-linejoin="round">',
        ]

        for entity in document.visible_entities():
            lines.append(self._entity_to_svg(entity))

        lines.append("</g>")
        lines.append("</svg>")
        return "\n".join(lines)

    def _entity_to_svg(self, entity: Line | Circle | Arc | Polyline | Text | LinearDimension | Insert) -> str:
        if isinstance(entity, Line):
            return (
                f'<line x1="{entity.start.x}" y1="{-entity.start.y}" '
                f'x2="{entity.end.x}" y2="{-entity.end.y}" '
                f'stroke="{escape(entity.color)}" stroke-width="{entity.line_weight * self.stroke_scale}" />'
            )

        if isinstance(entity, Circle):
            return (
                f'<circle cx="{entity.center.x}" cy="{-entity.center.y}" r="{entity.radius}" '
                f'stroke="{escape(entity.color)}" stroke-width="{entity.line_weight * self.stroke_scale}" />'
            )

        if isinstance(entity, Arc):
            start = entity.point_at(entity.start_angle)
            end = entity.point_at(entity.end_angle)
            delta = (entity.end_angle - entity.start_angle) % (2 * math.pi)
            large_arc = int(delta > math.pi)
            path = f'M {start.x} {-start.y} A {entity.radius} {entity.radius} 0 {large_arc} 1 {end.x} {-end.y}'
            return f'<path d="{path}" stroke="{escape(entity.color)}" stroke-width="{entity.line_weight * self.stroke_scale}" />'

        if isinstance(entity, Polyline):
            pts = " ".join(f"{v.x},{-v.y}" for v in entity.vertices)
            tag = "polygon" if entity.closed else "polyline"
            return f'<{tag} points="{pts}" stroke="{escape(entity.color)}" stroke-width="{entity.line_weight * self.stroke_scale}" />'

        if isinstance(entity, Text):
            rotation = -math.degrees(entity.rotation)
            return (
                f'<text x="{entity.position.x}" y="{-entity.position.y}" '
                f'font-size="{entity.height}" fill="{escape(entity.color)}" '
                f'transform="rotate({rotation} {entity.position.x} {-entity.position.y})">{escape(entity.value)}</text>'
            )

        if isinstance(entity, LinearDimension):
            txt = entity.display_text()
            return (
                f'<g stroke="{escape(entity.color)}" stroke-width="0.2">'
                f'<line x1="{entity.p1.x}" y1="{-entity.p1.y}" x2="{entity.p2.x}" y2="{-entity.p2.y}" />'
                f'<text x="{entity.dim_line_point.x}" y="{-entity.dim_line_point.y}" fill="{escape(entity.color)}">{escape(txt)}</text>'
                "</g>"
            )

        p = entity.insertion_point
        return (
            f'<g stroke="#666" stroke-dasharray="2,2">'
            f'<circle cx="{p.x}" cy="{-p.y}" r="2" />'
            f'<text x="{p.x + 2}" y="{-p.y - 2}" fill="#666">{escape(entity.block_name)}</text>'
            "</g>"
        )
