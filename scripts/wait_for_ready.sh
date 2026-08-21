#!/usr/bin/env bash
# Poll <base_url>/ready until it answers 200, or fail after a timeout.
# Usage: wait_for_ready.sh <base_url> [max_attempts] [interval_seconds]
set -euo pipefail

base_url="${1:?usage: wait_for_ready.sh <base_url> [max_attempts] [interval_seconds]}"
max_attempts="${2:-36}"
interval_seconds="${3:-10}"

for attempt in $(seq 1 "$max_attempts"); do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$base_url/ready") || true
    echo "attempt $attempt/$max_attempts — HTTP $status"
    if [ "$status" = "200" ]; then
        echo "ready"
        exit 0
    fi
    sleep "$interval_seconds"
done

echo "timeout: $base_url/ready never returned 200 after $((max_attempts * interval_seconds))s" >&2
exit 1
