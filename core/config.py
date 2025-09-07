# core/config.py (추가/보완)
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parents[1]

# .env 로딩을 이미 하고 있다면 그대로 유지
env_file = BASE_DIR / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

JSONL_PATH = DATA_DIR / "prompts.jsonl"

# ▼ 로그 폴더/파일
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LLM_LOG_PATH = LOG_DIR / "llm.jsonl"
