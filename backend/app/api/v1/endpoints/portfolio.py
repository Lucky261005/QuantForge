from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.schemas.common import Page
from app.schemas.portfolio import PortfolioRead, TransactionCreate, TransactionRead
from app.services.audit_service import AuditService
from app.services.portfolio_service import PortfolioService
from app.utils.exceptions import ValidationFailedError

router = APIRouter(prefix="/portfolio", tags=["portfolio"])
limiter = Limiter(key_func=get_remote_address)


@router.get("", response_model=PortfolioRead)
def get_portfolio(user: CurrentUser, db: DbSession) -> PortfolioRead:
    portfolio = PortfolioService(db).get_or_create(user.id)
    return PortfolioRead.model_validate(portfolio)


@router.post("/transactions", response_model=PortfolioRead, status_code=201)
@limiter.limit(settings.RATE_LIMIT_WRITE)
def create_transaction(request: Request, payload: TransactionCreate, user: CurrentUser, db: DbSession) -> PortfolioRead:
    service = PortfolioService(db)
    match payload.type.value:
        case "deposit":
            portfolio = service.deposit(user.id, payload.amount or 0)
        case "withdraw":
            portfolio = service.withdraw(user.id, payload.amount or 0)
        case "buy":
            if not payload.symbol:
                raise ValidationFailedError("symbol is required for a buy transaction")
            portfolio = service.buy(user.id, payload.symbol.upper(), payload.quantity, payload.price or None)
        case "sell":
            if not payload.symbol:
                raise ValidationFailedError("symbol is required for a sell transaction")
            portfolio = service.sell(user.id, payload.symbol.upper(), payload.quantity, payload.price or None)
        case _:
            raise ValidationFailedError(f"Unknown transaction type '{payload.type}'")
    AuditService(db).record(
        user_id=user.id,
        action=f"portfolio.{payload.type.value}",
        resource_type="portfolio",
        resource_id=portfolio.id,
        details={"symbol": payload.symbol, "quantity": payload.quantity, "amount": payload.amount},
        ip_address=request.client.host if request.client else None,
    )
    return PortfolioRead.model_validate(portfolio)


@router.get("/transactions", response_model=Page[TransactionRead])
def list_transactions(user: CurrentUser, db: DbSession, page: int = 1, page_size: int = 20) -> Page[TransactionRead]:
    service = PortfolioService(db)
    items, total = service.list_transactions(user.id, (page - 1) * page_size, page_size)
    return Page.create([TransactionRead.model_validate(t) for t in items], total, page, page_size)
