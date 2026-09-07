#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
AI_ENV_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/curriculo-ats/ai.env"
if [[ -r "$AI_ENV_FILE" ]]; then
  set -a
  source "$AI_ENV_FILE"
  set +a
fi
exec /home/pdm/.local/share/dev-envs/curriculo-ats/bin/python -m uvicorn resume_ai.interfaces.api.app:create_app --factory --reload --host 127.0.0.1 --port 8001
