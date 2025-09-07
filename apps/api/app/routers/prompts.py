from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_session
from app.models.prompt import Prompt, PromptVersion
from app.schemas.prompts import DefineRequest, DefineResponse, EditRequest, EditResponse, PromptVersionOut
from app.services.llm import build_v1_prompt

router = APIRouter(prefix="/prompts", tags=["prompts"])

@router.post("/define", response_model=DefineResponse)
async def define(req: DefineRequest, session: AsyncSession = Depends(get_session)):
    prompt = Prompt(title=req.title, goal=req.goal)
    session.add(prompt)
    await session.flush()
    v1_text = build_v1_prompt(req.goal)
    v1 = PromptVersion(prompt_id=prompt.id, version=1, text=v1_text, diff_note=None)
    session.add(v1)
    await session.commit()
    return DefineResponse(prompt_id=prompt.id, version=PromptVersionOut(id=v1.id, version=1, text=v1.text))

@router.post("/{prompt_id}/edit", response_model=EditResponse)
async def edit(prompt_id: int, req: EditRequest, session: AsyncSession = Depends(get_session)):
    # 간단화: changes 배열을 합쳐 전체 텍스트로 덮어쓰기(라인 편집은 차후 확장)
    new_text = "\n".join(req.changes)
    # 최신 버전 번호 조회
    q = select(func.max(PromptVersion.version)).where(PromptVersion.prompt_id == prompt_id)
    max_ver = (await session.execute(q)).scalar() or 0
    new_ver = PromptVersion(prompt_id=prompt_id, version=max_ver + 1, text=new_text, diff_note=req.note)
    session.add(new_ver)
    await session.commit()
    return EditResponse(prompt_id=prompt_id, version=PromptVersionOut(id=new_ver.id, version=new_ver.version, text=new_ver.text))
