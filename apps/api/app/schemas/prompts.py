from pydantic import BaseModel
from typing import Optional, List, Dict

class DefineRequest(BaseModel):
    title: str
    goal: str

class PromptVersionOut(BaseModel):
    id: int
    version: int
    text: str

class DefineResponse(BaseModel):
    prompt_id: int
    version: PromptVersionOut

class EditRequest(BaseModel):
    changes: List[str]  # 라인 단위 추가/수정(간단: 전체 텍스트로 대체해도 OK)
    note: Optional[Dict] = None

class EditResponse(DefineResponse):
    pass
