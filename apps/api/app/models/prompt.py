from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.types import JSON, Integer, DateTime, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Prompt(Base):
    __tablename__ = "prompts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    goal: Mapped[str] = mapped_column(Text)  # DEFINE 단계 입력 목표
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    versions: Mapped[list["PromptVersion"]] = relationship(back_populates="prompt", cascade="all, delete-orphan")

class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_id: Mapped[int] = mapped_column(ForeignKey("prompts.id"))
    version: Mapped[int] = mapped_column(Integer)  # 1부터 증가
    text: Mapped[str] = mapped_column(Text)        # 전체 프롬프트 텍스트
    diff_note: Mapped[dict | None] = mapped_column(JSON, default=None)  # 라인 변경 메모
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
    prompt: Mapped["Prompt"] = relationship(back_populates="versions")

class Run(Base):
    __tablename__ = "runs"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    prompt_version_id: Mapped[int] = mapped_column(ForeignKey("prompt_versions.id"))
    input_payload: Mapped[dict] = mapped_column(JSON)
    output_text: Mapped[str] = mapped_column(Text)
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"))
    metrics: Mapped[dict] = mapped_column(JSON)  # {"bleu":..., "f1":..., "distinct":...}
    created_at: Mapped["DateTime"] = mapped_column(DateTime(timezone=True), server_default=func.now())
