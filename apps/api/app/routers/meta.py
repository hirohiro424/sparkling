from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.db import get_session
from ..models import Run, Evaluation
from ..services.llm import call_llm

router = APIRouter(prefix="/meta", tags=["meta"])

@router.post("/review/{run_id}")
async def meta_review(run_id:int, db:AsyncSession=Depends(get_session)):
    r = (await db.execute(select(Run).where(Run.id==run_id))).scalar_one_or_none()
    e = (await db.execute(select(Evaluation).where(Evaluation.run_id==run_id))).scalar_one_or_none()
    if not r or not e: raise HTTPException(404, "run/eval not found")
    sys = "You produce meta-prompts that improve an existing prompt without overfitting."
    user = f"""Output:\n{r.output_text}\n\nFailures:\n{e.details}\n\nReturn improved guidance as bullet points."""
    text = await call_llm(sys, user, model="gpt-5")
    return {"meta": text}
