from pathlib import Path
import json, time

RUN_DIR = Path("data/runs")
RUN_DIR.mkdir(parents=True, exist_ok=True)

def save_run_artifact(run_id: int, data: dict) -> str:
    path = RUN_DIR / f"run_{run_id}_{int(time.time())}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return str(path)
