#!/usr/bin/env bash
#
# The two query paths, run against a live API and the real 38,483-chunk index.
#
# This script exists so the recording in the README is reproducible rather
# than a screenshot nobody can re-derive. It calls the same endpoints a user
# would and invents nothing: every figure on screen comes back over HTTP.
# Response formatting lives in scripts/demo_format.py.
#
# The warmup request at the top is not decoration. The first /ask after a
# process starts has been measured at ~3s end to end, almost all of it MPS
# kernel warmup and cold OpenSearch query caches. Recording that would
# misrepresent the system's latency in the wrong direction, so the demo pays
# it explicitly and on camera rather than quietly excluding it.
#
# Usage:
#   docker compose -f docker/docker-compose.yml up -d
#   ENABLE_GENERATION=true .venv/bin/uvicorn duediligence.api.app:app --port 8000
#   ./scripts/demo.sh
#
set -euo pipefail

# Run from the repository root regardless of where the caller invoked this,
# because both the formatter and the default interpreter are relative paths.
# Without this, running it from elsewhere spends the warmup request — which
# costs one call against a 20/day quota — and only then fails on a missing
# .venv/bin/python.
cd "$(dirname "${BASH_SOURCE[0]}")/.."

API="${DUEDILIGENCE_API:-http://localhost:8000}"
PY="${PYTHON:-.venv/bin/python}"
PAUSE="${DEMO_PAUSE:-2}"

bold=$'\033[1m'; dim=$'\033[2m'; cyan=$'\033[36m'; green=$'\033[32m'; reset=$'\033[0m'

say()  { printf '%s\n' "$*"; }
rule() { printf '%s\n' "${dim}────────────────────────────────────────────────────────────────${reset}"; }
step() { printf '\n%s\n' "${bold}${cyan}$*${reset}"; sleep "$PAUSE"; }

# Sends one question to /ask and formats the response.
ask() {
  local question="$1"
  printf '%s$ curl -X POST %s/ask -d %s%s\n' \
    "$dim" "$API" "'{\"question\": \"$question\"}'" "$reset"
  curl -s -m 180 -X POST "$API/ask" \
    -H 'content-type: application/json' \
    --data-binary "$("$PY" -c 'import json,sys; print(json.dumps({"question": sys.argv[1]}))' "$question")" \
    | "$PY" scripts/demo_format.py
}

# ---------------------------------------------------------------- warmup

say "${bold}Bank M&A Due-Diligence RAG${reset} ${dim}— 502 SEC filings, 38,483 indexed chunks${reset}"
say ""
say "${dim}Warming up (the first call pays MPS kernel + query-cache warmup;${reset}"
say "${dim}it is not steady state, so it happens here rather than off camera).${reset}"
curl -s -m 180 -X POST "$API/ask" -H 'content-type: application/json' \
  -d '{"question": "warmup"}' > /dev/null
say "${green}ready${reset}"
sleep "$PAUSE"

# ------------------------------------------------------ 1. structured path

rule
step "1. A factual question — routes to exact XBRL lookup, no model call"
ask "What was Columbia's net income for 2023?"
sleep "$PAUSE"

# -------------------------------------------------------- 2. semantic path

rule
step "2. A narrative question — hybrid search, rerank, cited generation"
ask "What are the risks of the Umpqua merger?"
sleep "$PAUSE"

rule
say ""
say "${dim}One endpoint, two paths, chosen by deterministic rules — not an LLM.${reset}"
say "${dim}Numbers: results/retrieval/report.json, results/routing/report.json${reset}"
