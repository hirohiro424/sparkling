## Prompting Pipeline
1) DEFINE: 프롬프팅 목표 입력 → AI가 기본 프롬프트 초안(v1) 자동 생성
2) EDIT: 사용자가 라인 단위로 조건/형식/금지사항을 보강(v2, v3…)
3) EVAL: 메타 프롬프트로 점검
→ 필요시 2로 회귀하여 품질이 개선될 때까지 반복

## Design Rationale
### 1) Define
Anthropic에서 공개한 프롬프트 작성 가이드라인을 참고하여, 목표를 구체화하고 기본적인 제약조건을 포함하는 초안 프롬프트를 자동으로 작성.
'명확한 지시사항, 구체적 제약, 원하는 출력 형식, 평가 기준'을 빠짐없이 포함하는 것을 목표로 함.

### 2) Edit
라인 단위로 프롬프트를 다듬으며, 버전 관리 및 산출물 기록을 통해 점진적 개선 과정을 지원.
프롬프팅은 단어 하나의 뉘앙스, 연관 토큰의 선택에 따라서도 출력이 크게 달라질 수 있기 때문에, 수정 사항을 라인 단위로 쪼개어 기록하는 것이 필요함.

### 3) Eval  
OpenAI에서 제시한 메타 프롬프트를 활용하여 프롬프트 품질을 점검.

# 구조
```
sparkling/
├─ core/
│  ├─ config.py         # 설정
│  └─ storage.py        # JSON 저장/불러오기
├─ prompts/
│  ├─ define.py         # 초안 생성
│  ├─ edit.py           # 라인 단위 수정
│  └─ eval.py           # 메타 프롬프트 점검
├─ cli.py               # 명령어 실행 (define/edit/eval)
├─ data/
│  └─ prompts.jsonl     # 히스토리 저장
└─ tests/
   ├─ test_define.py
   ├─ test_edit.py
   └─ test_eval.py
```