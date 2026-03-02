#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_DIR="$ROOT_DIR/services/api"
WEB_DIR="$ROOT_DIR/apps/web"

MIN_NODE="20.0.0"
MIN_PNPM="9.0.0"
MIN_PYTHON="3.11.0"
MIN_POETRY="1.6.0"

API_PID=""
WEB_PID=""

info() {
  printf '[setup-run] %s\n' "$1"
}

fail() {
  printf '[setup-run] ERROR: %s\n' "$1" >&2
  exit 1
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

extract_version() {
  local raw="$1"
  printf '%s' "$raw" | sed -E 's/[^0-9]*([0-9]+\.[0-9]+\.[0-9]+).*/\1/'
}

version_lt() {
  # Returns 0 (true) if current < required.
  python3 - "$1" "$2" <<'PY'
import re
import sys

current = sys.argv[1]
required = sys.argv[2]

def to_tuple(value: str):
    nums = [int(x) for x in re.findall(r"\d+", value)[:3]]
    nums += [0] * (3 - len(nums))
    return tuple(nums)

print(1 if to_tuple(current) < to_tuple(required) else 0)
PY
}

check_tool() {
  local cmd="$1"
  local min_version="$2"
  local label="$3"
  local raw_version version

  have_cmd "$cmd" || fail "$label is required (>= $min_version) but was not found."

  raw_version="$("$cmd" --version 2>/dev/null | head -n 1)"
  version="$(extract_version "$raw_version")"
  [ -n "$version" ] || fail "Could not parse $label version from: $raw_version"

  if [ "$(version_lt "$version" "$min_version")" -eq 1 ]; then
    fail "$label version $version is too old; need >= $min_version."
  fi

  info "$label $version OK"
}

stop_services() {
  if [ -n "$API_PID" ] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [ -n "$WEB_PID" ] && kill -0 "$WEB_PID" 2>/dev/null; then
    kill "$WEB_PID" 2>/dev/null || true
  fi
}

trap 'stop_services' EXIT INT TERM

info "Checking required tools..."
check_tool "node" "$MIN_NODE" "Node.js"
check_tool "pnpm" "$MIN_PNPM" "pnpm"
check_tool "python3" "$MIN_PYTHON" "Python"
check_tool "poetry" "$MIN_POETRY" "Poetry"

info "Installing backend dependencies with Poetry..."
(
  cd "$API_DIR"
  poetry install --no-interaction
)

info "Installing frontend dependencies with pnpm..."
(
  cd "$ROOT_DIR"
  pnpm install --frozen-lockfile
)

info "Starting API on http://127.0.0.1:8000 ..."
(
  cd "$API_DIR"
  poetry run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
) &
API_PID=$!

info "Starting web app on http://127.0.0.1:5173 ..."
(
  cd "$WEB_DIR"
  pnpm dev --host 127.0.0.1 --port 5173
) &
WEB_PID=$!

info "Services are running. Press Ctrl+C to stop both."

api_status=0
web_status=0

while true; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    wait "$API_PID" || api_status=$?
    break
  fi
  if ! kill -0 "$WEB_PID" 2>/dev/null; then
    wait "$WEB_PID" || web_status=$?
    break
  fi
  sleep 1
done

if [ "$api_status" -ne 0 ]; then
  fail "API process exited with status $api_status."
fi
if [ "$web_status" -ne 0 ]; then
  fail "Web process exited with status $web_status."
fi
