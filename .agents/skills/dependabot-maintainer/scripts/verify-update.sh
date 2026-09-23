#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s {web|api|actions|all}\n' "${0##*/}"
  printf 'Runs the repository verification stack for a dependency update.\n'
}

if [[ ${1:-} == "--help" || ${1:-} == "-h" ]]; then
  usage
  exit 0
fi

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root=$(cd "$script_dir/../../../.." && pwd)

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Required command not found: %s\n' "$1" >&2
    exit 127
  fi
}

run_web() {
  require_command pnpm
  printf 'Running web dependency verification...\n'
  (
    cd "$repo_root/apps/web"
    pnpm install --frozen-lockfile
    pnpm lint
    pnpm build
  )
}

run_api() {
  require_command poetry
  printf 'Running API dependency verification...\n'
  (
    cd "$repo_root/services/api"
    poetry install --sync --no-interaction
    poetry run ruff check .
    poetry run mypy app
    poetry run pytest -q
  )
}

case "$1" in
  web)
    run_web
    ;;
  api)
    run_api
    ;;
  actions)
    run_web
    run_api
    printf 'Local checks passed. A hosted GitHub Actions run is still required.\n'
    ;;
  all)
    run_web
    run_api
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
