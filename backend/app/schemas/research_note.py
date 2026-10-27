from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResearchNoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    tags: list[str] = Field(default_factory=list)
    related_strategy_id: int | None = None
    related_backtest_id: int | None = None


class ResearchNoteUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None


class ResearchNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    tags: list[str]
    related_strategy_id: int | None
    related_backtest_id: int | None
    created_at: datetime
    updated_at: datetime
