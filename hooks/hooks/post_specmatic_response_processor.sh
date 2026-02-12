#!/usr/bin/env bash
set -euo pipefail

input="$(cat || true)"

if [ -z "${input}" ]; then
  exit 0
fi

if ! printf '%s' "$input" | grep -Eq '"path"[[:space:]]*:[[:space:]]*"/test"'; then
  echo "$input"
  exit 0
fi

output="$(
  printf '%s' "$input" | sed -E \
    -e 's/"responseHeader"([[:space:]]*:)/"ResponseHeader"\1/g' \
    -e 's/"responseKey"([[:space:]]*:)/"ResponseKey"\1/g' \
    || true
)"

if [ -z "${output}" ]; then
  echo "$input"
  exit 0
fi

echo "$output"
