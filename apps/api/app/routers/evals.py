from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_session
from app.models.prompt import Run, Evaluation
from app.schemas.evals import EvalRequest, EvalResponse
from app.services.evals.bleu import bleu
from app.services.evals.f1 import f1_token
from app.services.evals.distinct import distinct_1

router = APIRouter(prefix="/evals", tags=["evals"])

@router.post("/run", response_model=EvalResponse)
async def eval_run(req: EvalRequest, session: AsyncSession = Depends(get_session)):
    rq = select(Run).where(Run.id == req.run_id)
    r = (await session.execute(rq)).scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Run not found")
    metrics = {"distinct1": distinct_1(r.output_text)}
    if req.reference_text:
        try:
            metrics["bleu"] = bleu(r.output_text, req.reference_text)
        except Exception:
            metrics["bleu"] = 0.0
        metrics["f1"] = f1_token(r.output_text, req.reference_text)
    ev = Evaluation(run_id=r.id, metrics=metrics)
    session.add(ev)
    await session.commit()
    return EvalResponse(evaluation_id=ev.id, metrics=metrics)
