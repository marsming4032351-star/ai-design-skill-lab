#!/usr/bin/env bash
set -euo pipefail

dry_run=false
if [ "${1:-}" = "--dry-run" ]; then
  dry_run=true
  shift
fi

if [ "$#" -ne 3 ]; then
  echo "Usage: ./scripts/capture.sh [--dry-run] <source> \"title\" \"content-or-link\"" >&2
  echo "Example: ./scripts/capture.sh wechat \"北京老字号案例\" \"这是一篇关于北京老字号升级的微信文章\"" >&2
  echo "Preview: ./scripts/capture.sh --dry-run wechat \"北京老字号案例\" \"这是一篇关于北京老字号升级的微信文章\"" >&2
  exit 2
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

source="$1"
title="$2"
input="$3"

cd "${repo_root}"
cmd=(
  python3 scripts/obsidian_capture.py
  --input "${input}"
  --title "${title}"
  --source "${source}"
  --out 00_Inbox_Staging
)
if [ "${dry_run}" = true ]; then
  cmd+=(--dry-run)
fi
"${cmd[@]}"
