#!/usr/bin/env bash
# Confirm a deployed instance is alive and ready. No functional assertions.
# Usage: sanity_check.sh <base_url>
set -euo pipefail

base_url="${1:?usage: sanity_check.sh <base_url>}"
failed=0

for path in /health /ready; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$base_url$path") || true
    echo "$path — HTTP $status"
    if [ "$status" != "200" ]; then
        failed=1
    fi
done

exit "$failed"
