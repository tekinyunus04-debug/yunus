from __future__ import annotations

# AutoCAD $INSUNITS mapping (subset commonly used in engineering workflows)
DXF_UNIT_CODES: dict[str, int] = {
    "unitless": 0,
    "inch": 1,
    "feet": 2,
    "mile": 3,
    "mm": 4,
    "cm": 5,
    "m": 6,
    "km": 7,
    "microinch": 8,
    "mil": 9,
    "yard": 10,
}


def normalize_units(units: str) -> str:
    key = units.strip().lower()
    aliases = {
        "millimeter": "mm",
        "millimeters": "mm",
        "centimeter": "cm",
        "centimeters": "cm",
        "meter": "m",
        "meters": "m",
        "in": "inch",
        "ft": "feet",
    }
    normalized = aliases.get(key, key)
    if normalized not in DXF_UNIT_CODES:
        supported = ", ".join(sorted(DXF_UNIT_CODES))
        raise ValueError(f"Unsupported unit '{units}'. Supported units: {supported}")
    return normalized
