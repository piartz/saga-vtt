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

confirm() {
  local prompt="$1"
  local answer=""
  read -r -p "[setup-run] ${prompt} [y/N] " answer
  case "$answer" in
    y|Y|yes|YES|Yes) return 0 ;;
    *) return 1 ;;
  esac
}

have_cmd() {
  command -v "$1" >/dev/null 2>&1
}

run_with_timeout() {
  local seconds="$1"
  shift

  if have_cmd timeout; then
    timeout "$seconds" "$@"
    return
  fi

  if have_cmd gtimeout; then
    gtimeout "$seconds" "$@"
    return
  fi

  perl -e 'alarm shift; exec @ARGV' "$seconds" "$@"
}

get_version_line() {
  local cmd="$1"
  local output=""

  if [ "$cmd" = "pnpm" ]; then
    output="$(COREPACK_ENABLE_DOWNLOAD_PROMPT=0 run_with_timeout 8 "$cmd" --version 2>/dev/null | head -n 1 || true)"
  else
    output="$(run_with_timeout 8 "$cmd" --version 2>/dev/null | head -n 1 || true)"
  fi

  printf '%s' "$output"
}

detect_platform() {
  local uname_s
  uname_s="$(uname -s)"
  case "$uname_s" in
    Darwin) printf 'macos' ;;
    Linux) printf 'linux' ;;
    *) printf 'unsupported' ;;
  esac
}

install_node() {
  local platform="$1"
  if [ "$platform" = "macos" ]; then
    have_cmd brew || fail "Homebrew is required to install Node.js on macOS."
    brew install node
    return
  fi

  if [ "$platform" = "linux" ]; then
    if have_cmd apt-get; then
      sudo apt-get update
      sudo apt-get install -y nodejs npm
      return
    fi
    if have_cmd dnf; then
      sudo dnf install -y nodejs npm
      return
    fi
    fail "Unsupported Linux package manager for Node.js install (expected apt-get or dnf)."
  fi

  fail "Unsupported platform for Node.js auto-install."
}

install_pnpm() {
  local platform="$1"
  local min_major="$2"
  if [ "$platform" = "macos" ] && have_cmd brew; then
    info "Installing pnpm via Homebrew..."
    brew install pnpm && return
    info "Homebrew pnpm install failed; trying fallback methods."
  fi

  if have_cmd corepack; then
    info "Trying pnpm installation via Corepack..."
    if corepack enable && corepack prepare "pnpm@${min_major}" --activate; then
      return
    fi
    info "Corepack pnpm install failed; trying fallback methods."
  fi

  if have_cmd npm; then
    info "Trying pnpm installation via npm..."
    if npm install -g "pnpm@${min_major}"; then
      return
    fi

    if confirm "Retry pnpm npm install with sudo?"; then
      sudo npm install -g "pnpm@${min_major}" && return
    fi
  fi

  fail "Could not install pnpm automatically with brew/corepack/npm."
}

install_python3() {
  local platform="$1"
  if [ "$platform" = "macos" ]; then
    have_cmd brew || fail "Homebrew is required to install Python on macOS."
    brew install python
    return
  fi

  if [ "$platform" = "linux" ]; then
    if have_cmd apt-get; then
      sudo apt-get update
      sudo apt-get install -y python3 python3-pip
      return
    fi
    if have_cmd dnf; then
      sudo dnf install -y python3 python3-pip
      return
    fi
    fail "Unsupported Linux package manager for Python install (expected apt-get or dnf)."
  fi

  fail "Unsupported platform for Python auto-install."
}

install_poetry() {
  local platform="$1"
  if [ "$platform" = "macos" ]; then
    if have_cmd brew; then
      brew install poetry
      return
    fi
  fi

  if [ "$platform" = "linux" ]; then
    if have_cmd apt-get; then
      sudo apt-get update
      sudo apt-get install -y poetry && return
    fi
    if have_cmd dnf; then
      sudo dnf install -y poetry && return
    fi
  fi

  if have_cmd python3; then
    curl -sSL https://install.python-poetry.org | python3 -
    return
  fi

  fail "Could not install Poetry automatically."
}

attempt_install_or_upgrade() {
  local cmd="$1"
  local label="$2"
  local min_version="$3"
  local platform="$4"
  local min_major="${min_version%%.*}"

  if ! confirm "Install/upgrade ${label} to >= ${min_version}?"; then
    fail "${label} is required (>= ${min_version}) but was not installed."
  fi

  case "$cmd" in
    node) install_node "$platform" ;;
    pnpm) install_pnpm "$platform" "$min_major" ;;
    python3) install_python3 "$platform" ;;
    poetry) install_poetry "$platform" ;;
    *) fail "No installer configured for ${label} (${cmd})." ;;
  esac
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
  local platform="$4"
  local raw_version version

  if ! have_cmd "$cmd"; then
    info "$label was not found."
    attempt_install_or_upgrade "$cmd" "$label" "$min_version" "$platform"
    hash -r
  fi

  raw_version="$(get_version_line "$cmd")"
  version="$(extract_version "$raw_version")"
  if [ -z "$version" ]; then
    info "Could not read a valid $label version (tool may be broken)."
    attempt_install_or_upgrade "$cmd" "$label" "$min_version" "$platform"
    hash -r
    raw_version="$(get_version_line "$cmd")"
    version="$(extract_version "$raw_version")"
    [ -n "$version" ] || fail "Could not parse $label version from: $raw_version"
  fi

  if [ "$(version_lt "$version" "$min_version")" -eq 1 ]; then
    info "$label version $version is too old; need >= $min_version."
    attempt_install_or_upgrade "$cmd" "$label" "$min_version" "$platform"
    hash -r
    raw_version="$(get_version_line "$cmd")"
    version="$(extract_version "$raw_version")"
    [ -n "$version" ] || fail "Could not parse $label version from: $raw_version"
    if [ "$(version_lt "$version" "$min_version")" -eq 1 ]; then
      fail "$label version $version is still too old after install attempt; need >= $min_version."
    fi
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
PLATFORM="$(detect_platform)"
[ "$PLATFORM" != "unsupported" ] || fail "Unsupported platform. This script supports Linux and macOS."
info "Detected platform: $PLATFORM"
check_tool "node" "$MIN_NODE" "Node.js" "$PLATFORM"
check_tool "pnpm" "$MIN_PNPM" "pnpm" "$PLATFORM"
check_tool "python3" "$MIN_PYTHON" "Python" "$PLATFORM"
check_tool "poetry" "$MIN_POETRY" "Poetry" "$PLATFORM"

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
