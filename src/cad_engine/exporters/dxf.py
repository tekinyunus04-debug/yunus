from __future__ import annotations

from dataclasses import dataclass
import math

from cad_engine.document import Document
from cad_engine.entities import Arc, Circle, Insert, Line, LinearDimension, Polyline, Text
from cad_engine.units import DXF_UNIT_CODES


@dataclass(slots=True)
class DxfExporter:
    version: str = "AC1027"  # AutoCAD 2013+

    def export(self, document: Document) -> str:
        bounds = document.bounds()
        units_code = DXF_UNIT_CODES[document.units]

        parts: list[str] = []
        a = parts.append

        a("0\nSECTION\n2\nHEADER")
        a(f"9\n$ACADVER\n1\n{self.version}")
        a(f"9\n$INSUNITS\n70\n{units_code}")
        a(f"9\n$EXTMIN\n10\n{bounds.min.x}\n20\n{bounds.min.y}\n30\n0.0")
        a(f"9\n$EXTMAX\n10\n{bounds.max.x}\n20\n{bounds.max.y}\n30\n0.0")
        a("0\nENDSEC")

        a("0\nSECTION\n2\nTABLES")
        a(f"0\nTABLE\n2\nLAYER\n70\n{len(document.layers)}")
        for layer in document.layers.values():
            flags = 4 if layer.locked else 0
            if not layer.visible:
                flags |= 1
            a("0\nLAYER")
            a(f"2\n{layer.name}")
            a(f"70\n{flags}")
            a("62\n7")
            a(f"6\n{layer.linetype}")
        a("0\nENDTAB")
        a("0\nENDSEC")

        a("0\nSECTION\n2\nBLOCKS")
        for block in document.blocks.values():
            a("0\nBLOCK")
            a(f"2\n{block.name}\n70\n0\n10\n{block.base_point[0]}\n20\n{block.base_point[1]}\n30\n0.0")
            for entity in block.entities:
                a(self._entity_to_dxf(entity))
            a("0\nENDBLK")
        a("0\nENDSEC")

        a("0\nSECTION\n2\nENTITIES")
        for entity in document.visible_entities():
            a(self._entity_to_dxf(entity))
        a("0\nENDSEC")

        a("0\nEOF")
        return "\n".join(parts) + "\n"

    def export_file(self, document: Document, path: str) -> None:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(self.export(document))

    def _entity_to_dxf(self, entity: Line | Circle | Arc | Polyline | Text | LinearDimension | Insert) -> str:
        if isinstance(entity, Line):
            return (
                "0\nLINE\n"
                f"8\n{entity.layer}\n"
                f"10\n{entity.start.x}\n20\n{entity.start.y}\n30\n0.0\n"
                f"11\n{entity.end.x}\n21\n{entity.end.y}\n31\n0.0"
            )

        if isinstance(entity, Circle):
            return (
                "0\nCIRCLE\n"
                f"8\n{entity.layer}\n"
                f"10\n{entity.center.x}\n20\n{entity.center.y}\n30\n0.0\n"
                f"40\n{entity.radius}"
            )

        if isinstance(entity, Arc):
            start_deg = math.degrees(entity.start_angle) % 360.0
            end_deg = math.degrees(entity.end_angle) % 360.0
            return (
                "0\nARC\n"
                f"8\n{entity.layer}\n"
                f"10\n{entity.center.x}\n20\n{entity.center.y}\n30\n0.0\n"
                f"40\n{entity.radius}\n"
                f"50\n{start_deg}\n51\n{end_deg}"
            )

        if isinstance(entity, Polyline):
            vertices = [f"10\n{v.x}\n20\n{v.y}\n30\n0.0" for v in entity.vertices]
            closed_flag = 1 if entity.closed else 0
            return (
                "0\nLWPOLYLINE\n"
                f"8\n{entity.layer}\n"
                f"90\n{len(entity.vertices)}\n"
                f"70\n{closed_flag}\n"
                + "\n".join(vertices)
            )

        if isinstance(entity, Text):
            return (
                "0\nTEXT\n"
                f"8\n{entity.layer}\n"
                f"10\n{entity.position.x}\n20\n{entity.position.y}\n30\n0.0\n"
                f"40\n{entity.height}\n1\n{entity.value}\n50\n{math.degrees(entity.rotation)}"
            )

        if isinstance(entity, LinearDimension):
            # simplified dimension entity for interoperability: keep def-points + text
            return (
                "0\nDIMENSION\n"
                f"8\n{entity.layer}\n"
                f"10\n{entity.dim_line_point.x}\n20\n{entity.dim_line_point.y}\n30\n0.0\n"
                f"13\n{entity.p1.x}\n23\n{entity.p1.y}\n33\n0.0\n"
                f"14\n{entity.p2.x}\n24\n{entity.p2.y}\n34\n0.0\n"
                f"1\n{entity.display_text()}"
            )

        return (
            "0\nINSERT\n"
            f"8\n{entity.layer}\n"
            f"2\n{entity.block_name}\n"
            f"10\n{entity.insertion_point.x}\n20\n{entity.insertion_point.y}\n30\n0.0\n"
            f"41\n{entity.scale_x}\n42\n{entity.scale_y}\n50\n{math.degrees(entity.rotation)}"
        )
