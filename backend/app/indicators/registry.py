"""Decorator-based registry so adding a new indicator means adding one function,
not editing a dispatch table. Strategies use the same pattern (see strategies/registry.py)."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.core.params import ParamSpec

IndicatorFn = Callable[..., pd.DataFrame]


@dataclass(frozen=True)
class IndicatorSpec:
    key: str
    label: str
    output_columns: list[str]
    params: list[ParamSpec]
    fn: IndicatorFn = field(repr=False)

    def compute(self, df: pd.DataFrame, **params: Any) -> pd.DataFrame:
        merged = {p.name: p.default for p in self.params}
        merged.update(params)
        return self.fn(df, **merged)


class IndicatorRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, IndicatorSpec] = {}

    def register(
        self, key: str, label: str, output_columns: list[str], params: list[ParamSpec] | None = None
    ) -> Callable[[IndicatorFn], IndicatorFn]:
        def decorator(fn: IndicatorFn) -> IndicatorFn:
            self._specs[key] = IndicatorSpec(
                key=key, label=label, output_columns=output_columns, params=params or [], fn=fn
            )
            return fn

        return decorator

    def get(self, key: str) -> IndicatorSpec:
        if key not in self._specs:
            raise KeyError(f"Unknown indicator '{key}'. Available: {sorted(self._specs)}")
        return self._specs[key]

    def list_all(self) -> list[IndicatorSpec]:
        return list(self._specs.values())


indicator_registry = IndicatorRegistry()
register_indicator = indicator_registry.register
