#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
export PATH="/home/pdm/.local/share/dev-sdks/node/bin:$PATH"
export RESUME_AI_API_URL=http://127.0.0.1:8001
cd frontend
echo "Abra http://localhost:3000 no Firefox."
exec npm run dev -- --hostname 127.0.0.1 --port 3000
