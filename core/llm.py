import os, json
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from openai import OpenAI
from core.config import LLM_LOG_PATH

class LLMError(Exception):
    pass

_client = None
def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL") 
        if not api_key:
            raise LLMError("환경변수 OPENAI_API_KEY가 없습니다.")
        _client = OpenAI(api_key=api_key, base_url=base_url)
    return _client

def _now():
    return datetime.now(timezone.utc).isoformat()

def _append_jsonl(obj: Dict[str, Any]):
    try:
        with LLM_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _console(*args):
    if os.getenv("LLM_LOG_CONSOLE", "1") == "1":  # 기본 on
        print(*args)

def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: Optional[float] = None,   # reasoning 모델이면 None 유지
    max_tokens: int = 800,
    reasoning_effort: Optional[str] = None,  # "low"|"medium"|"high" 또는 None
    text_verbosity: Optional[str] = None,    # "low"|"medium"|"high" (선택)
) -> str:
    """
    Responses API 호출 + 콘솔/파일 로깅.
    반환값은 최종 텍스트. (자세한 메타는 data/logs/llm.jsonl에 JSONL로 저장)
    """
    client = _get_client()
    model = model or os.getenv("OPENAI_MODEL", "gpt-5")

    # 요청 kwargs 구성
    kwargs: Dict[str, Any] = {
        "model": model,
        "input": messages,                 
        "max_output_tokens": max_tokens,
    }
    no_temp_models = ("gpt-5", "o1", "o3")
    if (temperature is not None) and (not any(model.startswith(m) for m in no_temp_models)):
        kwargs["temperature"] = float(temperature)
    if reasoning_effort:
        if reasoning_effort not in {"low", "medium", "high"}:
            raise LLMError(f"지원되지 않는 reasoning_effort: {reasoning_effort}")
        kwargs["reasoning"] = {"effort": reasoning_effort}
    if text_verbosity:
        kwargs["text"] = {"verbosity": text_verbosity}

    # 요청 로그
    req_log = {
        "ts": _now(),
        "event": "llm_request",
        "backend": "openai.responses",
        "kwargs": {k: v for k, v in kwargs.items()},  # API 키/헤더 없음
    }
    _append_jsonl(req_log)
    _console(">>> [LLM req] model:", model,
             "| temp:", temperature,
             "| reason:", reasoning_effort,
             "| max_out:", max_tokens,
             "| text.verbosity:", text_verbosity)

    try:
        resp = client.responses.create(**kwargs)

        usage = getattr(resp, "usage", None)
        truncated = getattr(resp, "truncated", None)

        finish_reason = None
        items = list(getattr(resp, "output", []) or [])
        for item in reversed(items):
            if hasattr(item, "finish_reason"):
                finish_reason = item.finish_reason
                break

        # 응답 로그
        try:
            resp_json = resp.model_dump()  # pydantic → dict
        except Exception:
            resp_json = {"_note": "model_dump failed"}

        res_log = {
            "ts": _now(),
            "event": "llm_response",
            "usage": getattr(usage, "model_dump", lambda: usage)() if usage else None,
            "truncated": truncated,
            "finish_reason": finish_reason,
            "text_len": len(resp.output_text or ""),
            "raw": resp_json,  # ⚠️파일 커질 수 있음.
        }
        _append_jsonl(res_log)

        # 콘솔 요약
        _console(">>> [LLM res] usage:", usage)
        _console(">>> [LLM res] truncated:", truncated, "| finish_reason:", finish_reason)
        _console(">>> [LLM res] text_len:", len(resp.output_text or ""))

        return (resp.output_text or "").strip()

    except Exception as e:
        # 에러도 로그에 남김
        _append_jsonl({
            "ts": _now(),
            "event": "llm_error",
            "error": str(e),
        })
        raise LLMError(f"LLM 호출 실패: {e}")
