import json
import time
import uuid
from typing import Dict, List, Optional, Any, Iterable
from .config import JSONL_PATH

def _read_lines() -> List[Dict[str, Any]]:
    if not JSONL_PATH.exists():
        return []
    with JSONL_PATH.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def _write_lines(rows: Iterable[Dict[str, Any]]) -> None:
    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def append_record(record: Dict[str, Any]) -> None:
    record["created_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with JSONL_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def list_prompts() -> List[Dict[str, Any]]:
    return _read_lines()

def latest_by_id(prompt_id: str) -> Optional[Dict[str, Any]]:
    rows = [r for r in _read_lines() if r.get("prompt_id") == prompt_id]
    if not rows:
        return None
    return max(rows, key=lambda r: r.get("version", 0))

def all_versions(prompt_id: str) -> List[Dict[str, Any]]:
    rows = [r for r in _read_lines() if r.get("prompt_id") == prompt_id]
    return sorted(rows, key=lambda r: r.get("version", 0))

def find_ids_by_title(title: str) -> List[str]:
    rows = _read_lines()
    ids = {r["prompt_id"] for r in rows if r.get("title") == title}
    return sorted(ids)

def new_prompt_id() -> str:
    return str(uuid.uuid4())

def save_new_version(prompt_id: str, title: str, content: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    rows = [r for r in _read_lines() if r.get("prompt_id") == prompt_id]
    version = (max([r.get("version", 0) for r in rows]) + 1) if rows else 1
    rec = {
        "prompt_id": prompt_id,
        "version": version,
        "title": title,
        "content": content,
        "meta": meta or {},
    }
    append_record(rec)
    return rec
