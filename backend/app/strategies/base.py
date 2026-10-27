"""Strategy ABC — the plugin contract for both built-in and user-authored strategies.

A new strategy is one class: set `key`/`label`/`description`/`param_specs`, implement
`generate_signals`, and decorate with `@register_strategy`. Nothing else needs editing.
"""

from abc import ABC, abstractmethod
from typing import Any, ClassVar

import pandas as pd

from app.core.params import ParamSpec


class Strategy(ABC):
    key: ClassVar[str]
    label: ClassVar[str]
    description: ClassVar[str] = ""
    param_specs: ClassVar[list[ParamSpec]] = []

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame, **params: Any) -> pd.Series:
        """Return a target-position series aligned to `df.index`, valued in
        {-1, 0, 1} (short / flat / long). The backtest engine applies a one-bar
        lag to whatever this returns, so implementations may use data up to and
        including the current bar without introducing lookahead bias."""
        ...

    def resolve_params(self, **overrides: Any) -> dict[str, Any]:
        merged = {p.name: p.default for p in self.param_specs}
        merged.update(overrides)
        return merged

    def compute(self, df: pd.DataFrame, **overrides: Any) -> pd.Series:
        params = self.resolve_params(**overrides)
        return self.generate_signals(df, **params)
