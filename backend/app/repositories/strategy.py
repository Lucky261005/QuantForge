from sqlalchemy import select

from app.models.strategy import Strategy
from app.repositories.base import BaseRepository


class StrategyRepository(BaseRepository[Strategy]):
    model = Strategy

    def list_for_owner(self, owner_id: int, offset: int = 0, limit: int = 20) -> list[Strategy]:
        stmt = (
            select(Strategy)
            .where(Strategy.owner_id == owner_id)
            .order_by(Strategy.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_for_owner(self, owner_id: int) -> int:
        return self.count(owner_id=owner_id)
