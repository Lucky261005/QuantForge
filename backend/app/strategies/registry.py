from app.strategies.base import Strategy


class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, type[Strategy]] = {}

    def register(self, strategy_cls: type[Strategy]) -> type[Strategy]:
        self._strategies[strategy_cls.key] = strategy_cls
        return strategy_cls

    def get(self, key: str) -> Strategy:
        if key not in self._strategies:
            raise KeyError(f"Unknown strategy '{key}'. Available: {sorted(self._strategies)}")
        return self._strategies[key]()

    def list_all(self) -> list[Strategy]:
        return [cls() for cls in self._strategies.values()]


strategy_registry = StrategyRegistry()
register_strategy = strategy_registry.register
