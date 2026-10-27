"""Shared parameter-spec primitive: describes one tunable numeric parameter for an
indicator or strategy. Used both to validate incoming values and to let the frontend
render a dynamic parameter form directly from `GET /strategies/catalog`."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParamSpec:
    name: str
    type: str  # "int" | "float"
    default: float
    min: float | None = None
    max: float | None = None
