from sqlalchemy import select

from app.models.research_note import ResearchNote
from app.repositories.base import BaseRepository


class ResearchNoteRepository(BaseRepository[ResearchNote]):
    model = ResearchNote

    def list_for_owner(self, owner_id: int, offset: int = 0, limit: int = 20) -> list[ResearchNote]:
        stmt = (
            select(ResearchNote)
            .where(ResearchNote.owner_id == owner_id)
            .order_by(ResearchNote.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def count_for_owner(self, owner_id: int) -> int:
        return self.count(owner_id=owner_id)
