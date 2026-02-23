from __future__ import annotations

from dataclasses import dataclass
import math


EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x - other.x, self.y - other.y)

    def scale(self, factor: float) -> "Vec2":
        return Vec2(self.x * factor, self.y * factor)

    def dot(self, other: "Vec2") -> float:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vec2") -> float:
        return self.x * other.y - self.y * other.x

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vec2":
        length = self.length()
        if length <= EPSILON:
            raise ValueError("Cannot normalize zero-length vector")
        return self.scale(1.0 / length)

    def distance_to(self, other: "Vec2") -> float:
        return (self - other).length()


@dataclass(frozen=True, slots=True)
class BoundingBox:
    min: Vec2
    max: Vec2

    @classmethod
    def from_points(cls, *pts: Vec2) -> "BoundingBox":
        if not pts:
            raise ValueError("BoundingBox requires at least one point")
        return cls(
            min=Vec2(min(p.x for p in pts), min(p.y for p in pts)),
            max=Vec2(max(p.x for p in pts), max(p.y for p in pts)),
        )

    def union(self, other: "BoundingBox") -> "BoundingBox":
        return BoundingBox(
            min=Vec2(min(self.min.x, other.min.x), min(self.min.y, other.min.y)),
            max=Vec2(max(self.max.x, other.max.x), max(self.max.y, other.max.y)),
        )

    def expand(self, margin: float) -> "BoundingBox":
        return BoundingBox(
            min=Vec2(self.min.x - margin, self.min.y - margin),
            max=Vec2(self.max.x + margin, self.max.y + margin),
        )


@dataclass(frozen=True, slots=True)
class Mat3:
    m11: float = 1.0
    m12: float = 0.0
    m13: float = 0.0
    m21: float = 0.0
    m22: float = 1.0
    m23: float = 0.0
    m31: float = 0.0
    m32: float = 0.0
    m33: float = 1.0

    @staticmethod
    def translation(tx: float, ty: float) -> "Mat3":
        return Mat3(m13=tx, m23=ty)

    @staticmethod
    def rotation(radians: float) -> "Mat3":
        c = math.cos(radians)
        s = math.sin(radians)
        return Mat3(m11=c, m12=-s, m21=s, m22=c)

    @staticmethod
    def scale(sx: float, sy: float) -> "Mat3":
        return Mat3(m11=sx, m22=sy)

    def transform_point(self, pt: Vec2) -> Vec2:
        return Vec2(
            x=self.m11 * pt.x + self.m12 * pt.y + self.m13,
            y=self.m21 * pt.x + self.m22 * pt.y + self.m23,
        )

    def __matmul__(self, other: "Mat3") -> "Mat3":
        a = self
        b = other
        return Mat3(
            m11=a.m11 * b.m11 + a.m12 * b.m21 + a.m13 * b.m31,
            m12=a.m11 * b.m12 + a.m12 * b.m22 + a.m13 * b.m32,
            m13=a.m11 * b.m13 + a.m12 * b.m23 + a.m13 * b.m33,
            m21=a.m21 * b.m11 + a.m22 * b.m21 + a.m23 * b.m31,
            m22=a.m21 * b.m12 + a.m22 * b.m22 + a.m23 * b.m32,
            m23=a.m21 * b.m13 + a.m22 * b.m23 + a.m23 * b.m33,
            m31=a.m31 * b.m11 + a.m32 * b.m21 + a.m33 * b.m31,
            m32=a.m31 * b.m12 + a.m32 * b.m22 + a.m33 * b.m32,
            m33=a.m31 * b.m13 + a.m32 * b.m23 + a.m33 * b.m33,
        )
