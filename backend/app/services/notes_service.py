from sqlalchemy.orm import Session

from app.models.research_note import ResearchNote
from app.models.user import User
from app.repositories.research_note import ResearchNoteRepository
from app.schemas.research_note import ResearchNoteCreate, ResearchNoteUpdate
from app.utils.exceptions import NotFoundError, PermissionDeniedError


class NotesService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ResearchNoteRepository(db)

    def create(self, owner_id: int, payload: ResearchNoteCreate) -> ResearchNote:
        note = self.repo.create(
            ResearchNote(
                owner_id=owner_id,
                title=payload.title,
                content=payload.content,
                tags=payload.tags,
                related_strategy_id=payload.related_strategy_id,
                related_backtest_id=payload.related_backtest_id,
            )
        )
        self.repo.commit()
        return note

    def list_for_owner(self, owner_id: int, offset: int, limit: int) -> tuple[list[ResearchNote], int]:
        return self.repo.list_for_owner(owner_id, offset, limit), self.repo.count_for_owner(owner_id)

    def get_owned(self, note_id: int, user: User) -> ResearchNote:
        note = self.repo.get(note_id)
        if not note:
            raise NotFoundError("Research note not found")
        if note.owner_id != user.id:
            raise PermissionDeniedError("You do not have access to this note")
        return note

    def update(self, note_id: int, user: User, payload: ResearchNoteUpdate) -> ResearchNote:
        note = self.get_owned(note_id, user)
        if payload.title is not None:
            note.title = payload.title
        if payload.content is not None:
            note.content = payload.content
        if payload.tags is not None:
            note.tags = payload.tags
        self.repo.commit()
        return note

    def delete(self, note_id: int, user: User) -> None:
        note = self.get_owned(note_id, user)
        self.repo.delete(note)
        self.repo.commit()
