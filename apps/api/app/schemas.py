from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime

class PromptCreate(BaseModel):
    name: str = "Untitled"

class PromptOut(BaseModel):
    id: int
    name: str
    text: str | None

class EventCreate(BaseModel):
    kind: Literal["SET_FULL_TEXT", "ROLLBACK"]
    text: Optional[str] = None
    note: Optional[str] = None

class EventOut(BaseModel):
    id: int
    kind: str
    note: Optional[str] = None
    created_at: datetime

class CriterionIn(BaseModel):
    key: str
    desc: str
    type: str = "boolean"
    weight: float = 1.0

class CriterionOut(CriterionIn):
    id: int

class RunCreate(BaseModel):
    prompt_id: int
    model: str = "gpt-5"
    params: dict = {}
    input_text: str

class RunOut(BaseModel):
    id: int
    prompt_id: int
    model: str
    input_text: str
    output_text: str | None
