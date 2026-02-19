#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
  echo "Usage: $0 <url> <name> <max_attempts> <sleep_seconds> [allowed_status_codes_csv]" >&2
  exit 2
fi

url="$1"
name="$2"
max_attempts="$3"
sleep_seconds="$4"
allowed_codes="${5:-200}"

attempt=1
while true; do
  http_code="$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)"
  ready=false

  IFS=',' read -r -a code_list <<< "$allowed_codes"
  for code in "${code_list[@]}"; do
    if [ "$http_code" = "$code" ]; then
      ready=true
      break
    fi
  done

  if [ "$ready" = true ]; then
    break
  fi

  if [ "$attempt" -ge "$max_attempts" ]; then
    echo "$name did not become ready in time: $url (last_status=$http_code, allowed=$allowed_codes)" >&2
    exit 1
  fi

  echo "Waiting for $name ($attempt/$max_attempts), last_status=$http_code, allowed=$allowed_codes..."
  attempt=$((attempt + 1))
  sleep "$sleep_seconds"
done
