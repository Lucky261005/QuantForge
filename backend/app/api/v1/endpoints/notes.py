from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession, PageNumber, PageSize
from app.schemas.common import Message, Page
from app.schemas.research_note import ResearchNoteCreate, ResearchNoteRead, ResearchNoteUpdate
from app.services.notes_service import NotesService

router = APIRouter(prefix="/notes", tags=["research-notes"])


@router.post("", response_model=ResearchNoteRead, status_code=201)
def create_note(payload: ResearchNoteCreate, user: CurrentUser, db: DbSession) -> ResearchNoteRead:
    note = NotesService(db).create(user.id, payload)
    return ResearchNoteRead.model_validate(note)


@router.get("", response_model=Page[ResearchNoteRead])
def list_notes(
    user: CurrentUser, db: DbSession, page: PageNumber = 1, page_size: PageSize = 20
) -> Page[ResearchNoteRead]:
    service = NotesService(db)
    items, total = service.list_for_owner(user.id, (page - 1) * page_size, page_size)
    return Page.create([ResearchNoteRead.model_validate(n) for n in items], total, page, page_size)


@router.get("/{note_id}", response_model=ResearchNoteRead)
def get_note(note_id: int, user: CurrentUser, db: DbSession) -> ResearchNoteRead:
    note = NotesService(db).get_owned(note_id, user)
    return ResearchNoteRead.model_validate(note)


@router.put("/{note_id}", response_model=ResearchNoteRead)
def update_note(note_id: int, payload: ResearchNoteUpdate, user: CurrentUser, db: DbSession) -> ResearchNoteRead:
    note = NotesService(db).update(note_id, user, payload)
    return ResearchNoteRead.model_validate(note)


@router.delete("/{note_id}", response_model=Message)
def delete_note(note_id: int, user: CurrentUser, db: DbSession) -> Message:
    NotesService(db).delete(note_id, user)
    return Message(message="Research note deleted")
