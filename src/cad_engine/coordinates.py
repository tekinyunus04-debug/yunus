from __future__ import annotations

from dataclasses import dataclass
import math

from cad_engine.geometry import Mat3, Vec2


@dataclass(frozen=True, slots=True)
class CoordinateSystem:
    origin: Vec2 = Vec2(0.0, 0.0)
    rotation_radians: float = 0.0

    @property
    def ucs_to_wcs(self) -> Mat3:
        return Mat3.translation(self.origin.x, self.origin.y) @ Mat3.rotation(self.rotation_radians)

    @property
    def wcs_to_ucs(self) -> Mat3:
        inv_rotation = Mat3.rotation(-self.rotation_radians)
        inv_translation = Mat3.translation(-self.origin.x, -self.origin.y)
        return inv_rotation @ inv_translation

    def to_wcs(self, point: Vec2) -> Vec2:
        return self.ucs_to_wcs.transform_point(point)

    def to_ucs(self, point: Vec2) -> Vec2:
        return self.wcs_to_ucs.transform_point(point)

    @classmethod
    def from_degrees(cls, origin: Vec2, angle_deg: float) -> "CoordinateSystem":
        return cls(origin=origin, rotation_radians=math.radians(angle_deg))
