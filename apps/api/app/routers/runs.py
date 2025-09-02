from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.db import get_session, engine, Base
from ..models import Prompt, PromptEvent, Run
from ..schemas import RunCreate, RunOut
from ..services.llm import call_llm

router = APIRouter(prefix="/runs", tags=["runs"])

@router.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@router.post("", response_model=RunOut)
async def create_run(body: RunCreate, db: AsyncSession = Depends(get_session)):
    # 최신 프롬프트 텍스트
    p = (await db.execute(select(Prompt).where(Prompt.id==body.prompt_id))).scalar_one_or_none()
    if not p: raise HTTPException(404, "prompt not found")
    ev = (await db.execute(
        select(PromptEvent).where(PromptEvent.prompt_id==body.prompt_id).order_by(PromptEvent.created_at.desc(), PromptEvent.id.desc())
    )).scalars().first()
    text = ev.text if ev else ""

    # 시스템 메타(간단)
    system = "You are a careful assistant. Follow the given prompt exactly."
    user = f"[PROMPT]\n{text}\n\n[INPUT]\n{body.input_text}"

    out = await call_llm(system, user, model=body.model)
    r = Run(prompt_id=body.prompt_id, model=body.model, params=body.params, input_text=body.input_text, output_text=out)
    db.add(r); await db.commit()
    return RunOut(id=r.id, prompt_id=r.prompt_id, model=r.model, input_text=r.input_text, output_text=r.output_text)

@router.get("/{run_id}", response_model=RunOut)
async def get_run(run_id:int, db: AsyncSession = Depends(get_session)):
    r = (await db.execute(select(Run).where(Run.id==run_id))).scalar_one_or_none()
    if not r: raise HTTPException(404, "run not found")
    return RunOut(id=r.id, prompt_id=r.prompt_id, model=r.model, input_text=r.input_text, output_text=r.output_text)
