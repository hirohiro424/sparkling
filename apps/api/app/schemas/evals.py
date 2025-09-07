from pydantic import BaseModel
from typing import Optional, Dict

class EvalRequest(BaseModel):
    run_id: int
    reference_text: Optional[str] = None  # 있으면 BLEU/F1, 없으면 distinct만

class EvalResponse(BaseModel):
    evaluation_id: int
    metrics: Dict
