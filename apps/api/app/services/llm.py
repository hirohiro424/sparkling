import time
from app.core.config import settings

TEMPLATE = """# Role
You are a helpful assistant.

# Goal
{goal}

# Instructions
- Follow the goal precisely.
- Be concise.
- Provide structured output (headings and lists).
- Cite assumptions if needed.

# Output Format
JSON with fields: "summary", "steps", "notes".
"""

def build_v1_prompt(goal: str) -> str:
    # Anthropic 가이드라인/일반 베스트프랙티스 참고한 '명확/구체/형식/평가' 틀을 최소화 버전으로 반영
    return TEMPLATE.format(goal=goal)

def run_llm(prompt_text: str, inputs: dict) -> tuple[str, int]:
    # MVP: 실제 LLM 호출 없이, prompt_text와 inputs를 합쳐 에코 + 지연 측정
    t0 = time.time()
    output = f"[DUMMY OUTPUT]\\nPrompt:\\n{prompt_text}\\n\\nInputs:\\n{inputs}"
    latency_ms = int((time.time() - t0) * 1000)
    return output, latency_ms
