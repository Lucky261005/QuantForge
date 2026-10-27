from sqlalchemy.orm import Session

from app.models.strategy import Strategy
from app.models.user import User
from app.repositories.strategy import StrategyRepository
from app.schemas.strategy import ParamSpecRead, StrategyCatalogEntry, StrategyCreate, StrategyUpdate
from app.strategies import strategy_registry
from app.utils.exceptions import NotFoundError, PermissionDeniedError, ValidationFailedError


class StrategyService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = StrategyRepository(db)

    @staticmethod
    def catalog() -> list[StrategyCatalogEntry]:
        return [
            StrategyCatalogEntry(
                key=impl.key,
                label=impl.label,
                description=impl.description,
                params=[
                    ParamSpecRead(name=p.name, type=p.type, default=p.default, min=p.min, max=p.max)
                    for p in impl.param_specs
                ],
            )
            for impl in strategy_registry.list_all()
        ]

    def _validate_and_resolve_params(self, strategy_type: str, parameters: dict) -> dict:
        try:
            impl = strategy_registry.get(strategy_type)
        except KeyError as exc:
            raise ValidationFailedError(str(exc)) from exc

        valid_names = {p.name for p in impl.param_specs}
        unknown = set(parameters) - valid_names
        if unknown:
            raise ValidationFailedError(f"Unknown parameter(s) for '{strategy_type}': {sorted(unknown)}")

        resolved = impl.resolve_params(**parameters)
        for spec in impl.param_specs:
            value = resolved[spec.name]
            if spec.min is not None and value < spec.min:
                raise ValidationFailedError(f"Parameter '{spec.name}' must be >= {spec.min}")
            if spec.max is not None and value > spec.max:
                raise ValidationFailedError(f"Parameter '{spec.name}' must be <= {spec.max}")
        return resolved

    def create(self, owner_id: int, payload: StrategyCreate) -> Strategy:
        resolved_params = self._validate_and_resolve_params(payload.strategy_type, payload.parameters)
        strategy = Strategy(
            owner_id=owner_id,
            name=payload.name,
            description=payload.description,
            strategy_type=payload.strategy_type,
            parameters=resolved_params,
            is_public=payload.is_public,
        )
        strategy = self.repo.create(strategy)
        self.repo.commit()
        return strategy

    def get_owned(self, strategy_id: int, user: User) -> Strategy:
        strategy = self.repo.get(strategy_id)
        if not strategy:
            raise NotFoundError("Strategy not found")
        if strategy.owner_id != user.id and not strategy.is_public:
            raise PermissionDeniedError("You do not have access to this strategy")
        return strategy

    def list_for_owner(self, owner_id: int, offset: int, limit: int) -> tuple[list[Strategy], int]:
        return self.repo.list_for_owner(owner_id, offset, limit), self.repo.count_for_owner(owner_id)

    def update(self, strategy_id: int, user: User, payload: StrategyUpdate) -> Strategy:
        strategy = self.get_owned(strategy_id, user)
        if strategy.owner_id != user.id:
            raise PermissionDeniedError("Only the owner can modify this strategy")

        if payload.name is not None:
            strategy.name = payload.name
        if payload.description is not None:
            strategy.description = payload.description
        if payload.is_public is not None:
            strategy.is_public = payload.is_public
        if payload.parameters is not None:
            strategy.parameters = self._validate_and_resolve_params(strategy.strategy_type, payload.parameters)

        self.repo.commit()
        return strategy

    def delete(self, strategy_id: int, user: User) -> None:
        strategy = self.get_owned(strategy_id, user)
        if strategy.owner_id != user.id:
            raise PermissionDeniedError("Only the owner can delete this strategy")
        self.repo.delete(strategy)
        self.repo.commit()
