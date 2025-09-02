from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from ..db.db import get_session, engine, Base
from ..models import Criterion            # ORM 모델
from ..schemas import CriterionIn, CriterionOut

router = APIRouter(prefix="/criteria", tags=["criteria"])

@router.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@router.get("/{prompt_id}", response_model=list[CriterionOut])
async def list_criteria(prompt_id: int, db: AsyncSession = Depends(get_session)):
    rows = (await db.execute(select(Criterion).where(Criterion.prompt_id==prompt_id))).scalars().all()
    return [CriterionOut(id=r.id, key=r.key, desc=r.desc, type=r.type, weight=r.weight) for r in rows]

@router.post("/{prompt_id}", response_model=list[CriterionOut])
async def replace_criteria(prompt_id: int, items: list[CriterionIn], db: AsyncSession = Depends(get_session)):
    await db.execute(delete(Criterion).where(Criterion.prompt_id==prompt_id))
    for i, it in enumerate(items, start=1):
        db.add(Criterion(prompt_id=prompt_id, key=it.key or f"c{i}", desc=it.desc, type=it.type, weight=it.weight))
    await db.commit()
    rows = (await db.execute(select(Criterion).where(Criterion.prompt_id==prompt_id))).scalars().all()
    return [CriterionOut(id=r.id, key=r.key, desc=r.desc, type=r.type, weight=r.weight) for r in rows]
