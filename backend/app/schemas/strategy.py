from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ParamSpecRead(BaseModel):
    name: str
    type: str
    default: float
    min: float | None
    max: float | None


class StrategyCatalogEntry(BaseModel):
    key: str
    label: str
    description: str
    params: list[ParamSpecRead]


class StrategyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    strategy_type: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    is_public: bool = False


class StrategyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parameters: dict[str, Any] | None = None
    is_public: bool | None = None


class StrategyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    name: str
    description: str | None
    strategy_type: str
    parameters: dict[str, Any]
    is_public: bool
    created_at: datetime
    updated_at: datetime
