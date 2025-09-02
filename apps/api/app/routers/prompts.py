from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..db.db import get_session, engine, Base
from ..models import Prompt, PromptEvent
from ..schemas import PromptCreate, PromptOut, EventCreate, EventOut

router = APIRouter(prefix="/prompts", tags=["prompts"])

@router.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@router.post("", response_model=PromptOut)
async def create_prompt(body: PromptCreate, db: AsyncSession = Depends(get_session)):
    p = Prompt(name=body.name)
    db.add(p)
    await db.flush()  # id 생성
    # 빈 본문 스냅샷 1개 생성
    e = PromptEvent(prompt_id=p.id, kind="SET_FULL_TEXT", text="", note="init")
    db.add(e)
    await db.commit()
    return PromptOut(id=p.id, name=p.name, text="")

@router.get("/{prompt_id}", response_model=PromptOut)
async def get_prompt(prompt_id: int, db: AsyncSession = Depends(get_session)):
    q = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    p = q.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "prompt not found")

    # 최신 이벤트의 텍스트를 현재 상태로 간주
    q2 = await db.execute(
        select(PromptEvent).where(PromptEvent.prompt_id == prompt_id).order_by(PromptEvent.created_at.desc(), PromptEvent.id.desc())
    )
    latest = q2.scalars().first()
    text = latest.text if latest else ""
    return PromptOut(id=p.id, name=p.name, text=text)

@router.get("/{prompt_id}/events", response_model=List[EventOut])
async def list_events(prompt_id: int, db: AsyncSession = Depends(get_session)):
    q = await db.execute(
        select(PromptEvent).where(PromptEvent.prompt_id == prompt_id).order_by(PromptEvent.created_at.asc(), PromptEvent.id.asc())
    )
    rows = q.scalars().all()
    return [EventOut(id=r.id, kind=r.kind, note=r.note, created_at=r.created_at) for r in rows]

@router.post("/{prompt_id}/events")
async def add_event(prompt_id: int, body: EventCreate, db: AsyncSession = Depends(get_session)):
    q = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
    p = q.scalar_one_or_none()
    if not p:
        raise HTTPException(404, "prompt not found")

    e = PromptEvent(prompt_id=prompt_id, kind=body.kind, text=body.text, note=body.note)
    db.add(e)
    await db.commit()
    return {"ok": True, "event_id": e.id}

@router.post("/{prompt_id}/rollback")
async def rollback(prompt_id: int, target_event_id: int, db: AsyncSession = Depends(get_session)):
    # 대상 이벤트의 텍스트를 복제하여 최신 스냅샷으로 추가
    q = await db.execute(select(PromptEvent).where(PromptEvent.id == target_event_id, PromptEvent.prompt_id == prompt_id))
    target = q.scalar_one_or_none()
    if not target:
        raise HTTPException(404, "event not found")
    e = PromptEvent(prompt_id=prompt_id, kind="ROLLBACK", text=target.text, note=f"rollback to {target_event_id}")
    db.add(e)
    await db.commit()
    return {"ok": True}
