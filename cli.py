import argparse
import json
import sys
from typing import List
from core.storage import (
    new_prompt_id, save_new_version, latest_by_id, list_prompts, find_ids_by_title, all_versions, append_record
)
from prompts.define import make_draft
from prompts.edit import apply_edits, with_line_numbers
from prompts.eval import run_llm_eval, extract_goal_from_content

def _resolve_prompt_id(title: str = None, prompt_id: str = None) -> str:
    if prompt_id:
        return prompt_id
    if title:
        ids = find_ids_by_title(title)
        if not ids:
            print(f"[!] 제목 '{title}' 로 저장된 프롬프트를 찾을 수 없음.")
            sys.exit(1)
        if len(ids) > 1:
            print(f"[!] 제목이 같은 프롬프트가 여러 개입니다. 다음 중 하나를 --id로 지정하세요:\n- " + "\n- ".join(ids))
            sys.exit(1)
        return ids[0]
    print("[!] --title 또는 --id 를 제공하세요.")
    sys.exit(1)

def cmd_define(args):
    pid = new_prompt_id()
    draft = make_draft(args.goal)
    rec = save_new_version(pid, args.title, draft, meta={"kind":"define","goal":args.goal})
    print(f"[+] created: {rec['prompt_id']} v{rec['version']}")
    print(with_line_numbers(rec["content"]))

def _parse_edit_flags(args) -> List[dict]:
    edits = []
    for s in (args.set or []):
        n, text = s.split(":", 1)
        edits.append({"op": "set", "line": int(n), "text": text})
    for s in (args.insert or []):
        n, text = s.split(":", 1)
        edits.append({"op": "insert", "line": int(n), "text": text})
    for s in (args.delete or []):
        edits.append({"op": "delete", "line": int(s)})
    return edits

def cmd_edit(args):
    pid = _resolve_prompt_id(args.title, args.id)
    latest = latest_by_id(pid)
    if not latest:
        print("[!] 해당 ID의 프롬프트를 찾을 수 없음.")
        sys.exit(1)
    edits = _parse_edit_flags(args)
    if args.patch_json:
        edits.extend(json.loads(args.patch_json))
    new_content = apply_edits(latest["content"], edits)
    rec = save_new_version(pid, latest["title"], new_content, meta={"kind":"edit","edits":edits})
    print(f"[+] saved: {rec['prompt_id']} v{rec['version']}")
    print(with_line_numbers(rec["content"]))

def cmd_eval(args):
    pid = _resolve_prompt_id(args.title, args.id)
    latest = latest_by_id(pid)
    if not latest:
        print("[!] 해당 ID의 프롬프트를 찾을 수 없음.")
        sys.exit(1)

    prompt_text = latest["content"]
    desired = args.desired or (latest.get("meta") or {}).get("goal")
    undesired = args.undesired

    try:
        result = run_llm_eval(
            prompt_text=prompt_text,
            desired=desired,
            undesired=undesired,
            model=args.model,
            temperature=args.temperature,
        )
    except Exception as e:
        print(f"[!] LLM 평가 실패: {e}")
        sys.exit(1)

    # 출력
    print("# === Meta Prompt Sent ===")
    print(result["meta_prompt"])
    print("\n# === LLM Feedback ===")
    print(result["llm_output"])

    # 기록
    append_record({
        "record_type": "eval",
        "prompt_id": pid,
        "source_version": latest["version"],
        "title": latest["title"],
        "desired": result["desired_used"],
        "undesired": undesired,
        "llm_model": args.model or "env:OPENAI_MODEL",
        "llm_temperature": args.temperature,
        "meta_prompt": result["meta_prompt"],
        "llm_output": result["llm_output"],
    })


def cmd_show(args):
    pid = _resolve_prompt_id(args.title, args.id)
    if args.version:
        versions = all_versions(pid)
        target = next((v for v in versions if v["version"] == args.version), None)
    else:
        target = latest_by_id(pid)
    if not target:
        print("[!] 해당 버전을 찾을 수 없음.")
        sys.exit(1)
    print(f"{target['prompt_id']} v{target['version']} | {target['title']}")
    print(with_line_numbers(target["content"]))

def cmd_list(_args):
    rows = list_prompts()
    if not rows:
        print("(empty)")
        return
    seen = {}
    for r in rows:
        k = r["prompt_id"]
        seen[k] = max(seen.get(k, 0), r.get("version", 0))
    for pid, ver in seen.items():
        title = next((x["title"] for x in rows if x["prompt_id"] == pid), "")
        print(f"- {pid}  v{ver}  | {title}")

def cmd_diff(args):
    import difflib
    pid = _resolve_prompt_id(args.title, args.id)
    vlist = all_versions(pid)
    a = next((v for v in vlist if v["version"] == args.a), None)
    b = next((v for v in vlist if v["version"] == args.b), None)
    if not a or not b:
        print("[!] 버전 번호 확인필.")
        sys.exit(1)
    diff = difflib.unified_diff(
        a["content"].splitlines(),
        b["content"].splitlines(),
        fromfile=f"v{a['version']}",
        tofile=f"v{b['version']}",
        lineterm=""
    )
    print("\n".join(diff))

def build_parser():
    p = argparse.ArgumentParser(prog="sparkling", description="Minimal prompting notebook CLI")
    sub = p.add_subparsers()

    p_def = sub.add_parser("define", help="목표로 초안 생성")
    p_def.add_argument("--title", required=True)
    p_def.add_argument("--goal", required=True)
    p_def.set_defaults(func=cmd_define)

    p_edit = sub.add_parser("edit", help="라인 기반 편집")
    p_edit.add_argument("--title")
    p_edit.add_argument("--id")
    p_edit.add_argument("--set", action="append", help='예: --set "12:새 문장"')
    p_edit.add_argument("--insert", action="append", help='예: --insert "7:추가 문장"')
    p_edit.add_argument("--delete", action="append", help='예: --delete 9')
    p_edit.add_argument("--patch-json", help='[{"op":"set","line":3,"text":"..."}] 형태')
    p_edit.set_defaults(func=cmd_edit)

    p_eval = sub.add_parser("eval", help="LLM 메타 프롬프트로 품질 점검")
    p_eval.add_argument("--title")
    p_eval.add_argument("--id")
    p_eval.add_argument("--undesired", required=True, help="현재 드러난 바람직하지 않은 동작 설명")
    p_eval.add_argument("--desired", help="원하는 동작(미지정 시 '# 목표'에서 추출)")
    p_eval.add_argument("--model", help="LLM 모델명(기본: OPENAI_MODEL 환경변수)")
    p_eval.add_argument("--temperature", type=float)
    p_eval.set_defaults(func=cmd_eval)

    p_show = sub.add_parser("show", help="내용 보기(라인 번호 포함)")
    p_show.add_argument("--title")
    p_show.add_argument("--id")
    p_show.add_argument("--version", type=int)
    p_show.set_defaults(func=cmd_show)

    p_list = sub.add_parser("list", help="프롬프트 목록(최신 버전 요약)")
    p_list.set_defaults(func=cmd_list)

    p_diff = sub.add_parser("diff", help="두 버전 비교")
    p_diff.add_argument("--title")
    p_diff.add_argument("--id")
    p_diff.add_argument("--a", type=int, required=True, help="from 버전")
    p_diff.add_argument("--b", type=int, required=True, help="to 버전")
    p_diff.set_defaults(func=cmd_diff)

    return p

def main():
    p = build_parser()
    args = p.parse_args()
    if not hasattr(args, "func"):
        p.print_help()
        return
    args.func(args)

if __name__ == "__main__":
    main()
