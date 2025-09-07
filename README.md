## Prompting Pipeline
1) DEFINE: 프롬프팅 목표 입력 → AI가 기본 프롬프트 초안(v1) 자동 생성
2) EDIT: 사용자가 라인 단위로 조건/형식/금지사항을 보강(v2, v3…)
3) EVAL: 메타 프롬프트로 점검 + 지표(BLEU/F1/Distinct/latency) 평가
→ 필요시 2로 회귀하여 품질이 개선될 때까지 반복

## Design Rationale
### 1) Define
Anthropic에서 공개한 프롬프트 작성 가이드라인을 참고하여, 목표를 구체화하고 기본적인 제약조건을 포함하는 초안 프롬프트를 자동으로 작성합니다.
'명확한 지시사항, 구체적 제약, 원하는 출력 형식, 평가 기준'을 빠짐없이 포함하는 것을 목표로 합니다.

### 2) Edit
블록 기반 편집과 버전 히스토리 개념을 차용했습니다. 사용자가 직접 라인 단위로 프롬프트를 다듬으며, 버전 관리 및 산출물 기록을 통해 점진적 개선 과정을 지원합니다.
프롬프팅은 단어 하나의 뉘앙스, 연관 토큰의 선택에 따라서도 출력이 크게 달라질 수 있기 때문에, 수정 사항을 라인 단위로 쪼개어 기록하는 방식을 채택했습니다. 이를 통해 작은 변화가 산출물에 어떤 영향을 주는지 추적할 수 있고, 점진적 개선 과정을 데이터로 남길 수 있습니다.  

### 3) Eval  
OpenAI에서 제시한 메타 프롬프트를 활용하여 프롬프트 품질을 점검합니다.  
Anthropic 가이드라인에서 제시한 평가 기준(명확성, 구체성, 일관성, 제약조건 충족, 금지사항 준수)을 체크리스트화했습니다.  
추가적으로 정량적 지표(BLEU, F1, Distinct, 응답 지연시간)를 계산하고,  
정성적 척도를 함께 고려합니다:
- 리커트 척도: 일관성을 1(무의미)에서 5(완벽하게 논리적)까지 평가
- 전문가 평가 기준: 언어학자가 정의한 기준에 따라 번역/요약 품질을 평가 
이를 통해 프롬프트 품질을 다각도로 확인하고, 개선 방향을 정량·정성적으로 동시에 점검할 수 있습니다.


# 구조
```
sparkling/
├─ apps/
│  ├─ api/                       # FastAPI 백엔드
│  │  ├─ app/
│  │  │  ├─ core/               # 공통 설정, 의존성 주입, 로깅/설정
│  │  │  │  ├─ config.py
│  │  │  │  ├─ logging.py
│  │  │  │  └─ deps.py
│  │  │  ├─ db/                 # DB 연결/마이그레이션
│  │  │  │  ├─ base.py
│  │  │  │  ├─ session.py       ## async engine/session
│  │  │  │  └─ migrations/      ## alembic (또는 aerich)
│  │  │  ├─ models/             # ORM 모델
│  │  │  │  ├─ prompt.py
│  │  │  │  ├─ event.py
│  │  │  │  ├─ run.py
│  │  │  │  └─ evaluation.py
│  │  │  ├─ schemas/            # Pydantic 스키마
│  │  │  │  ├─ prompts.py
│  │  │  │  ├─ runs.py
│  │  │  │  └─ evals.py
│  │  │  ├─ services/           # 비즈 로직(LLM, 평가, A/B)
│  │  │  │  ├─ llm.py
│  │  │  │  ├─ evals/           # 정량 지표 모듈
│  │  │  │  │  ├─ bleu.py
│  │  │  │  │  ├─ f1.py
│  │  │  │  │  └─ distinct.py
│  │  │  │  ├─ abtest.py        ## 실험 러너/집계
│  │  │  │  └─ outputs.py       ## 결과 저장/로드(diff 포함)
│  │  │  ├─ routers/            # 엔드포인트
│  │  │  │  ├─ health.py
│  │  │  │  ├─ prompts.py
│  │  │  │  ├─ criteria.py
│  │  │  │  ├─ runs.py
│  │  │  │  ├─ evals.py         ## /evals/run/{id}, /evals/abtest 등
│  │  │  │  └─ meta.py
│  │  │  ├─ tasks/              # 백그라운드 작업(Q 처리)
│  │  │  │  └─ worker.py        ## rq/celery/apscheduler 중 택1
│  │  │  ├─ main.py             # FastAPI create_app
│  │  │  └─ __init__.py
│  │  ├─ tests/                 # API/서비스 단위 테스트
│  │  │  ├─ test_prompts.py
│  │  │  ├─ test_evals.py
│  │  │  └─ test_abtest.py
│  │  ├─ Dockerfile
│  │  └─ pyproject.toml         ## 의존성/도구 통일(ruff, black, pytest 등)
│  └─ web/                      # Next.js 프론트엔드
│     ├─ app/                   ## App Router
│     ├─ lib/                   ## API 클라이언트, fetch 유틸
│     ├─ components/            ## UI 컴포넌트
│     ├─ features/
│     │  ├─ prompts/
│     │  ├─ runs/
│     │  ├─ evals/              ## 점수/세부 결과 차트
│     │  └─ abtest/             ## 두 버전 비교 화면
│     ├─ public/
│     ├─ tests/                 ## e2e(Playwright) 또는 컴포넌트 테스트
│     └─ next.config.js
├─ packages/                    # 공유 라이브러리 모놀리포화
│  ├─ eval-kits/                ## 파이썬 순수 평가 모듈(BLUE/F1)
│  └─ prompt-templates/         ## 공통 템플릿/롤(문서화/버저닝)
├─ data/                        # 실행 산출물(옵션, .gitignore)
│  ├─ runs/                     ## JSONL/CSV/Artifacts
│  └─ refs/                     ## 기준 정답
├─ scripts/
│  ├─ dev.sh                    ## 로컬 부팅(백/프론트/워커)
│  ├─ migrate.sh                ## DB 마이그레이션
│  └─ seed.sh                   ## 예시 데이터 주입
├─ .env.example
├─ docker-compose.yml
```
