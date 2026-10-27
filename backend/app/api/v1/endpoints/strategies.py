from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.schemas.common import Message, Page
from app.schemas.strategy import StrategyCatalogEntry, StrategyCreate, StrategyRead, StrategyUpdate
from app.services.audit_service import AuditService
from app.services.strategy_service import StrategyService

router = APIRouter(prefix="/strategies", tags=["strategies"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/catalog", response_model=list[StrategyCatalogEntry])
def get_catalog() -> list[StrategyCatalogEntry]:
    """Built-in strategy types with their parameter schemas — the contract the
    frontend's Strategy Builder uses to render a dynamic parameter form."""
    return StrategyService.catalog()


@router.post("", response_model=StrategyRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_WRITE)
def create_strategy(request: Request, payload: StrategyCreate, user: CurrentUser, db: DbSession) -> StrategyRead:
    strategy = StrategyService(db).create(user.id, payload)
    AuditService(db).record(
        user_id=user.id,
        action="strategy.create",
        resource_type="strategy",
        resource_id=strategy.id,
        details={"strategy_type": strategy.strategy_type},
        ip_address=request.client.host if request.client else None,
    )
    return StrategyRead.model_validate(strategy)


@router.get("", response_model=Page[StrategyRead])
def list_strategies(user: CurrentUser, db: DbSession, page: int = 1, page_size: int = 20) -> Page[StrategyRead]:
    service = StrategyService(db)
    items, total = service.list_for_owner(user.id, (page - 1) * page_size, page_size)
    return Page.create([StrategyRead.model_validate(s) for s in items], total, page, page_size)


@router.get("/{strategy_id}", response_model=StrategyRead)
def get_strategy(strategy_id: int, user: CurrentUser, db: DbSession) -> StrategyRead:
    strategy = StrategyService(db).get_owned(strategy_id, user)
    return StrategyRead.model_validate(strategy)


@router.put("/{strategy_id}", response_model=StrategyRead)
@limiter.limit(settings.RATE_LIMIT_WRITE)
def update_strategy(
    request: Request, strategy_id: int, payload: StrategyUpdate, user: CurrentUser, db: DbSession
) -> StrategyRead:
    strategy = StrategyService(db).update(strategy_id, user, payload)
    AuditService(db).record(
        user_id=user.id,
        action="strategy.update",
        resource_type="strategy",
        resource_id=strategy.id,
        ip_address=request.client.host if request.client else None,
    )
    return StrategyRead.model_validate(strategy)


@router.delete("/{strategy_id}", response_model=Message)
def delete_strategy(request: Request, strategy_id: int, user: CurrentUser, db: DbSession) -> Message:
    StrategyService(db).delete(strategy_id, user)
    AuditService(db).record(
        user_id=user.id,
        action="strategy.delete",
        resource_type="strategy",
        resource_id=strategy_id,
        ip_address=request.client.host if request.client else None,
    )
    return Message(message="Strategy deleted")
