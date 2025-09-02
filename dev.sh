#!/usr/bin/env bash
set -Eeuo pipefail

# dev.sh가 위치한 디렉터리를 프로젝트 루트로 고정
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 백엔드: FastAPI
(
  cd "$ROOT_DIR/apps/api"
  # 가상환경이 없다면 만들어두기 (있으면 건너뜀)
  if [ ! -d ".venv" ]; then
    python3 -m venv .venv
  fi
  source .venv/bin/activate
  # 0.0.0.0 바인딩: WSL/브라우저에서 접근 안정화
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &
API_PID=$!

# 프런트: Next.js (pnpm 필요)
(
  cd "$ROOT_DIR/apps/web"
  pnpm dev
) &
WEB_PID=$!

# Ctrl+C 시 두 프로세스 함께 종료
trap "kill $API_PID $WEB_PID 2>/dev/null || true" EXIT
wait
