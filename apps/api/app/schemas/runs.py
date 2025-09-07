from pydantic import BaseModel
from typing import Dict

class RunRequest(BaseModel):
    prompt_version_id: int
    input_payload: Dict

class RunResponse(BaseModel):
    run_id: int
    output_text: str
    latency_ms: int
