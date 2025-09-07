from typing import List, Dict, Any

"""
라인 기반 수정 규칙
- {"op":"set", "line":3, "text":"새 문장"}        : 3번 라인을 이 텍스트로 교체
- {"op":"insert", "line":4, "text":"추가 문장"}   : 4번 라인 '앞'에 삽입
- {"op":"delete", "line":7}                       : 7번 라인 삭제
라인 번호는 1부터 시작.
"""

def apply_edits(content: str, edits: List[Dict[str, Any]]) -> str:
    lines = content.splitlines()
    # 라인번호가 큰 것부터 처리
    def sort_key(e): 
        return -(e.get("line", 1))
    for e in sorted(edits, key=sort_key):
        op = e.get("op")
        idx = e.get("line", 1) - 1
        if not (0 <= idx <= len(lines)):
            continue
        if op == "set":
            if 0 <= idx < len(lines):
                lines[idx] = e.get("text", "")
        elif op == "insert":
            lines.insert(idx, e.get("text", ""))
        elif op == "delete":
            if 0 <= idx < len(lines):
                lines.pop(idx)
    return "\n".join(lines)

def with_line_numbers(content: str) -> str:
    return "\n".join(f"{i+1:>3}│ {line}" for i, line in enumerate(content.splitlines()))
