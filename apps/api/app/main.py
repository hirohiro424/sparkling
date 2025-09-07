# apps/api/app/main.py
from __future__ import annotations
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from difflib import unified_diff

# --- DB (SQLite, SQLAlchemy 2.0 style) ---
from sqlalchemy import create_engine, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session

DATABASE_URL = "sqlite:///./dev.db"
engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

class Base(DeclarativeBase):
    pass

class PromptSession(Base):
    __tablename__ = "prompt_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    goal: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    versions: Mapped[List[PromptVersion]] = relationship("PromptVersion", back_populates="session", cascade="all, delete-orphan")

class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("prompt_sessions.id"))
    version_idx: Mapped[int] = mapped_column(Integer)
    prompt_text: Mapped[str] = mapped_column(Text)
    output_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[PromptSession] = relationship("PromptSession", back_populates="versions")

Base.metadata.create_all(engine)

import os
from openai import OpenAI

# --- FastAPI app ---
# OpenAI client (requires OPENAI_API_KEY)
if not os.getenv("OPENAI_API_KEY"):
    # not raising here so the API still boots for non-run endpoints
    pass
client = OpenAI()

app = FastAPI(title="Sparkling Minimal API", docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- deps ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- util ---
def draft_v1(goal: str) -> str:
    return f"""# ROLE\nYou are an assistant that {goal}.\n\n# INSTRUCTIONS\n- Follow the task precisely.\n- Ask once for missing critical info.\n- Be concise.\n\n# OUTPUT\n- Provide the final answer only.\n\n# SAFETY\n- If uncertain, state assumptions briefly.\n"""

def apply_edits(base: str, conditions: List[str] | None, formatting: List[str] | None, forbidden: List[str] | None, replacements: List[List[int | str]] | None) -> str:
    lines = base.splitlines()
    # replacements: list[[idx, text]]
    if replacements:
        for pair in replacements:
            if isinstance(pair, (list, tuple)) and len(pair) == 2:
                idx, text = int(pair[0]), str(pair[1])
                if 0 <= idx < len(lines):
                    lines[idx] = text
    prompt = "\n".join(lines)

    def append_section(header: str, items: List[str] | None):
        nonlocal prompt
        if not items:
            return
        if f"# {header}" not in prompt:
            prompt += f"\n\n# {header}\n"
        else:
            prompt += "\n"
        prompt += "\n".join(f"- {it}" for it in items)

    append_section("CONDITIONS", conditions)
    append_section("FORMATTING", formatting)
    append_section("FORBIDDEN", [f"Do NOT: {f}" for f in (forbidden or [])])
    return prompt

class EvalResultModel(BaseModel):
    passed: List[str]
    failed: List[str]
    score: float
    notes: List[str]

def simple_eval(prompt: str, checklist: Optional[List[str]]) -> EvalResultModel:
    default_checks = [
        "ROLE 섹션이 존재한다",
        "INSTRUCTIONS 섹션이 존재한다",
        "OUTPUT 섹션이 존재한다",
        "모호한 지시가 구체화되어 있다",
        "금지사항이 명시되어 있다",
        "출력 형식이 명시되어 있다",
    ]
    checks = checklist or default_checks
    p = prompt.lower()
    passed, failed, notes = [], [], []

    def has(word: str) -> bool:
        return word.lower() in p

    if has("# role"): passed.append(checks[0])
    else: failed.append(checks[0]); notes.append("ROLE 섹션 추가 권장")

    if has("# instructions"): passed.append(checks[1])
    else: failed.append(checks[1]); notes.append("INSTRUCTIONS 섹션 필요")

    if has("# output"): passed.append(checks[2])
    else: failed.append(checks[2]); notes.append("OUTPUT 섹션 필요")

    vague_terms = ["be creative", "do your best", "help me"]
    if any(v in p for v in vague_terms):
        failed.append(checks[3]); notes.append("모호 표현을 구체 요구로 바꾸기")
    else:
        passed.append(checks[3])

    if any(k in p for k in ["forbidden", "do not:", "금지"]):
        passed.append(checks[4])
    else:
        failed.append(checks[4]); notes.append("금지사항 섹션/라인 추가")

    if any(m in p for m in ["json", "markdown", "format", "형식", "# formatting"]):
        passed.append(checks[5])
    else:
        failed.append(checks[5]); notes.append("출력 형식 명시")

    total = len(checks)
    score = round(len(passed) / total * 100, 1) if total else 100.0
    return EvalResultModel(passed=passed, failed=failed, score=score, notes=notes)

# --- Schemas ---
class DefineReq(BaseModel):
    goal: str = Field(..., description="프롬프팅 목표 설명")

class DefineResp(BaseModel):
    session_id: int
    version: int
    prompt: str

class EditReq(BaseModel):
    session_id: int
    raw_prompt: Optional[str] = None  # 전체 텍스트로 교체하고 싶으면 사용
    add_conditions: Optional[List[str]] = None
    add_formatting: Optional[List[str]] = None
    add_forbidden: Optional[List[str]] = None
    replace_lines: Optional[List[List[int | str]]] = None  # [[idx, text], ...]

class EditResp(BaseModel):
    session_id: int
    version: int
    prompt: str

class ResultReq(BaseModel):
    session_id: int
    version: Optional[int] = None  # 지정 없으면 최신
    output_text: str

class VersionMeta(BaseModel):
    version: int
    created_at: datetime
    has_output: bool

class SessionResp(BaseModel):
    session_id: int
    goal: str
    created_at: datetime
    versions: List[VersionMeta]

class EvalReq(BaseModel):
    session_id: int
    version: Optional[int] = None  # 기본 최신
    checklist: Optional[List[str]] = None

class RunReq(BaseModel):
    session_id: int
    version: Optional[int] = None  # 지정 없으면 최신 프롬프트 사용
    model: str = "gpt-5"
    temperature: float = 0.7
    max_output_tokens: Optional[int] = None
    user_input: Optional[str] = None  # 선택적으로 유저 메시지 추가
# --- Routes ---
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/define", response_model=DefineResp)
def define(req: DefineReq, db: Session = Depends(get_db)):
    session = PromptSession(goal=req.goal)
    db.add(session)
    db.flush()  # session.id 확보
    v1_text = draft_v1(req.goal)
    v = PromptVersion(session_id=session.id, version_idx=1, prompt_text=v1_text)
    db.add(v)
    db.commit()
    return DefineResp(session_id=session.id, version=1, prompt=v1_text)

@app.post("/edit", response_model=EditResp)
def edit(req: EditReq, db: Session = Depends(get_db)):
    session = db.get(PromptSession, req.session_id)
    if not session:
        raise HTTPException(404, "unknown session_id")
    latest = db.query(PromptVersion).filter_by(session_id=session.id).order_by(PromptVersion.version_idx.desc()).first()
    base = latest.prompt_text if latest else draft_v1(session.goal)

    if req.raw_prompt:
        newp = req.raw_prompt
    else:
        newp = apply_edits(base, req.add_conditions or [], req.add_formatting or [], req.add_forbidden or [], req.replace_lines or [])

    new_version = (latest.version_idx + 1) if latest else 1
    v = PromptVersion(session_id=session.id, version_idx=new_version, prompt_text=newp)
    db.add(v)
    db.commit()
    return EditResp(session_id=session.id, version=new_version, prompt=newp)

@app.post("/result")
def attach_result(req: ResultReq, db: Session = Depends(get_db)):
    q = db.query(PromptVersion).filter_by(session_id=req.session_id)
    if req.version is not None:
        q = q.filter_by(version_idx=req.version)
    v = q.order_by(PromptVersion.version_idx.desc()).first()
    if not v:
        raise HTTPException(404, "version not found")
    v.output_text = req.output_text
    db.commit()
    return {"ok": True, "session_id": req.session_id, "version": v.version_idx}

@app.get("/session/{session_id}", response_model=SessionResp)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = db.get(PromptSession, session_id)
    if not session:
        raise HTTPException(404, "not found")
    versions = db.query(PromptVersion).filter_by(session_id=session.id).order_by(PromptVersion.version_idx).all()
    metas = [VersionMeta(version=v.version_idx, created_at=v.created_at, has_output=bool(v.output_text)) for v in versions]
    return SessionResp(session_id=session.id, goal=session.goal, created_at=session.created_at, versions=metas)

@app.get("/session/{session_id}/version/{version}")
def get_version(session_id: int, version: int, db: Session = Depends(get_db)):
    v = db.query(PromptVersion).filter_by(session_id=session_id, version_idx=version).first()
    if not v:
        raise HTTPException(404, "not found")
    return {"session_id": session_id, "version": version, "prompt": v.prompt_text, "output": v.output_text}

@app.get("/session/{session_id}/diff")
def get_diff(session_id: int, v1: int = Query(...), v2: int = Query(...), db: Session = Depends(get_db)):
    a = db.query(PromptVersion).filter_by(session_id=session_id, version_idx=v1).first()
    b = db.query(PromptVersion).filter_by(session_id=session_id, version_idx=v2).first()
    if not a or not b:
        raise HTTPException(404, "version not found")
    diff = unified_diff(a.prompt_text.splitlines(), b.prompt_text.splitlines(), fromfile=f"v{v1}", tofile=f"v{v2}", lineterm="")
    return {"diff": "\n".join(diff)}

@app.post("/eval", response_model=EvalResultModel)
def evaluate(req: EvalReq, db: Session = Depends(get_db)):
    q = db.query(PromptVersion).filter_by(session_id=req.session_id)
    if req.version is not None:
        q = q.filter_by(version_idx=req.version)
    v = q.order_by(PromptVersion.version_idx.desc()).first()
    if not v:
        raise HTTPException(404, "version not found")
    return simple_eval(v.prompt_text, req.checklist)

@app.post("/run")
def run_model(req: RunReq, db: Session = Depends(get_db)):
    q = db.query(PromptVersion).filter_by(session_id=req.session_id)
    if req.version is not None:
        q = q.filter_by(version_idx=req.version)
    v = q.order_by(PromptVersion.version_idx.desc()).first()
    if not v:
        raise HTTPException(404, "version not found")

    # Build Responses API call using the versioned prompt as system instructions
    messages = [
        {"role": "system", "content": [{"type": "text", "text": v.prompt_text}]}
    ]
    if req.user_input:
        messages.append({"role": "user", "content": [{"type": "text", "text": req.user_input}]})

    try:
        resp = client.responses.create(
            model=req.model,
            input=messages,
            temperature=req.temperature,
            max_output_tokens=req.max_output_tokens,
        )
    except Exception as e:
        raise HTTPException(500, f"OpenAI call failed: {e}")

    # Prefer helper if present; fallback to manual extraction
    output_text = getattr(resp, "output_text", None)
    if not output_text:
        try:
            # consolidated across SDKs: outputs -> content -> text
            parts = []
            for item in getattr(resp, "output", []) or []:
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", None) == "output_text":
                        parts.append(getattr(c, "text", ""))
            output_text = "".join(parts) if parts else str(resp)
        except Exception:
            output_text = str(resp)

    # Save result onto this version
    v.output_text = output_text
    db.commit()

    usage = getattr(resp, "usage", None)
    usage_dict = {
        "input_tokens": getattr(usage, "input_tokens", None) if usage else None,
        "output_tokens": getattr(usage, "output_tokens", None) if usage else None,
        "total_tokens": getattr(usage, "total_tokens", None) if usage else None,
    }

    return {
        "ok": True,
        "session_id": req.session_id,
        "version": v.version_idx,
        "model": req.model,
        "output": output_text,
        "usage": usage_dict,
    }

# Run tip: uvicorn app.main:app --reload --port 8000
