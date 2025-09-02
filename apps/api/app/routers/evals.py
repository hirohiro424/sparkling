from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db.db import get_session, engine, Base
from ..models import Run, Criterion, Evaluation
from pydantic import BaseModel

router = APIRouter(prefix="/evals", tags=["evals"])

@router.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

class EvalOut(BaseModel):
    id:int; total:float; details:dict

@router.post("/{run_id}", response_model=EvalOut)
async def evaluate(run_id:int, db: AsyncSession = Depends(get_session)):
    r = (await db.execute(select(Run).where(Run.id==run_id))).scalar_one_or_none()
    if not r: raise HTTPException(404, "run not found")
    crits = (await db.execute(select(Criterion).where(Criterion.prompt_id==r.prompt_id))).scalars().all()

    out = r.output_text or ""
    details = {}
    total, weight_sum = 0.0, 0.0
    for c in crits:
        passed = False
        score = 0.0
        # 간단 예: boolean은 키워드/형식 규칙, score는 길이나 비율 등
        txt = out.lower()
        if c.type == "boolean":
            if "bullet" in c.desc.lower():
                passed = ("- " in out) or ("•" in out) or ("1." in out)
            elif "concise" in c.desc.lower():
                passed = (len(out.split()) <= 300)
            else:
                passed = (len(out.strip()) > 0)
            score = 1.0 if passed else 0.0
        else:
            # 점수형: 아주 단순한 길이 기반(예시)
            score = max(0.0, min(1.0, 300/ max(1,len(out.split()))))
            passed = score >= 0.6

        details[c.key] = {"pass": passed, "score": score, "weight": c.weight, "desc": c.desc}
        total += score * c.weight
        weight_sum += c.weight

    final = (total / weight_sum) if weight_sum else 0.0
    e = Evaluation(run_id=run_id, total=final, details=details)
    db.add(e); await db.commit()
    return EvalOut(id=e.id, total=final, details=details)
