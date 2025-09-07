from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_session
from app.models.prompt import PromptVersion, Run
from app.schemas.runs import RunRequest, RunResponse
from app.services.llm import run_llm
from app.services.outputs import save_run_artifact

router = APIRouter(prefix="/runs", tags=["runs"])

@router.post("", response_model=RunResponse)
async def run_prompt(req: RunRequest, session: AsyncSession = Depends(get_session)):
    vq = select(PromptVersion).where(PromptVersion.id == req.prompt_version_id)
    pv = (await session.execute(vq)).scalar_one_or_none()
    if not pv:
        raise HTTPException(404, "Prompt version not found")
    out, latency = run_llm(pv.text, req.input_payload)
    run = Run(prompt_version_id=pv.id, input_payload=req.input_payload, output_text=out, latency_ms=latency)
    session.add(run)
    await session.flush()
    save_run_artifact(run.id, {"prompt": pv.text, "input": req.input_payload, "output": out, "latency_ms": latency})
    await session.commit()
    return RunResponse(run_id=run.id, output_text=out, latency_ms=latency)
