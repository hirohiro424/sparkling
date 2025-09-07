import re
from core.llm import chat

SYSTEM_ROLE = (
    "Developer: You are a world-class prompt engineer. Your objective is to create execution-ready prompts that reliably guide another AI model. The prompts should be concrete, minimal, and actionable."
)

USER_TEMPLATE = """# Role and Objective
Act as a world-class Prompt Architect. Your task is to produce ONE execution-ready prompt that enables another AI (the "Executor") to accomplish the specified goal with high reliability.

# Specified Goal
{goal}

Begin with a concise checklist (3–7 bullets) of the critical sub-tasks you will follow; keep items conceptual, not implementation-level.

# Guidelines
1. Success Criteria
   - Ensure your prompt has clear, specific, and measurable success criteria.
   - Define what you want to achieve precisely (e.g., "accurate sentiment classification" instead of "good performance").
   - Use quantitative metrics or consistently applied qualitative scales.
   - Targets should be achievable based on relevant benchmarks, experiments, or expert input.

2. Role Crafting
   - Define a role for the prompt that best accomplishes the goal.

3. Prompt Quality Rubric (Internal Only)
   - Privately construct a 5–7 category rubric covering dimensions like Clarity & Specificity, Context & Constraints, Safety & Ethics, Output Structure & Testability, Reasoning & Verification, Style & Audience Fit, and Tooling & Reproducibility.
   - Do not output, mention, or reference this rubric.
   - Thoroughly evaluate your prompt draft against this rubric, iterating and revising (up to 3 silent passes) until it achieves top marks in every category, all without sharing your internal process or rubric.

After producing your prompt, validate in 1–2 lines that it directly addresses the provided goal and fully meets the listed success criteria. If not, perform a silent revision.

# Output Format
- Output a single fenced code block using markdown (```).
- Inside this code block, provide the final, execution-ready prompt as it should be presented to another model.
- Do not include explanations, comments, or additional formatting—only the prompt text within the code block.
"""

_CODEBLOCK_RE = re.compile(r"```(?:[^\n]*)\n(.*?)```", re.S)

def _extract_codeblock(text: str) -> str:
    m = _CODEBLOCK_RE.search(text)
    return m.group(1).strip() if m else text.strip()

def make_draft(goal: str, *, model=None, temperature=None, reasoning_effort="low") -> str:
    messages = [
        {"role": "system", "content": SYSTEM_ROLE},
        {"role": "user", "content": USER_TEMPLATE.format(goal=goal.strip())},
    ]
    raw = chat(
        messages=messages,
        model=model or "gpt-5",
        temperature=temperature,  
        max_tokens=2000,
        reasoning_effort="low",
    )
    return _extract_codeblock(raw)