from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func, Float, JSON
from sqlalchemy.orm import relationship
from .db.db import Base

class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, default="Untitled")
    events = relationship("PromptEvent", back_populates="prompt", cascade="all, delete-orphan")

class PromptEvent(Base):
    __tablename__ = "prompt_events"
    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), index=True, nullable=False)
    kind = Column(String(64), nullable=False)  # e.g., SET_FULL_TEXT, ROLLBACK
    text = Column(Text, nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    prompt = relationship("Prompt", back_populates="events")

class Criterion(Base):
    __tablename__ = "criteria"
    id = Column(Integer, primary_key=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), index=True, nullable=False)
    key = Column(String(64), nullable=False)     # "c1" 같은 식별자
    desc = Column(String(512), nullable=False)
    type = Column(String(32), default="boolean") # "boolean" | "score"
    weight = Column(Float, default=1.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Run(Base):
    __tablename__ = "runs"
    id = Column(Integer, primary_key=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), index=True, nullable=False)
    model = Column(String(64), default="gpt-5")
    params = Column(JSON, default={})
    input_text = Column(Text, nullable=False)
    output_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs.id", ondelete="CASCADE"), index=True, nullable=False)
    total = Column(Float, default=0.0)
    details = Column(JSON, default={})   # {"c1": {"pass":true,"score":1,"reason":"..."}, ...}
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
