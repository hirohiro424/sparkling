# prompts/eval.py
import re
from typing import Optional, Dict, Any
from core.llm import chat

META_TEMPLATE = """When asked to optimize prompts, give answers from your own perspective - explain what specific phrases could be added to, or deleted from, this prompt to more consistently elicit the desired behavior or prevent the undesired behavior.

Here's a prompt:
[PROMPT]

The desired behavior from this prompt is for the agent to [{DESIRED}], but instead it [{UNDESIRED}]. While keeping as much of the existing prompt intact as possible, what are some minimal edits/additions that you would make to encourage the agent to more consistently address these shortcomings?
"""

def extract_goal_from_content(content: str) -> Optional[str]:
    # "# 목표" 섹션 ~ 다음 헤더 전까지를 긁어온다.
    m = re.search(r"#\s*목표\s*\n(.*?)(?=\n#\s|\Z)", content, flags=re.S)
    return m.group(1).strip() if m else None

def build_meta_prompt(prompt_text: str, desired: str, undesired: str) -> str:
    return (
        META_TEMPLATE
        .replace("PROMPT", prompt_text.strip())
        .replace("{DESIRED}", desired.strip())
        .replace("{UNDESIRED}", undesired.strip())
    )

def run_llm_eval(
    prompt_text: str,
    desired: Optional[str],
    undesired: str,
    *,
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 800,
) -> Dict[str, Any]:
    d = (desired or "").strip()
    if not d:
        # 본문에서 목표 자동 추출(없으면 LLM이 추론하도록 힌트)
        d = extract_goal_from_content(prompt_text) or "the intended goal stated in the '# 목표' section (not found; infer best you can)"
    meta_prompt = build_meta_prompt(prompt_text, d, undesired)

    system = {"role": "system", "content": "You are an expert prompt engineer. Be concrete, minimal, and actionable."}
    user = {"role": "user", "content": meta_prompt}
    output = chat([system, user], model=model, temperature=temperature, max_tokens=max_tokens)

    return {
        "meta_prompt": meta_prompt,
        "llm_output": output,
        "desired_used": d,
    }
