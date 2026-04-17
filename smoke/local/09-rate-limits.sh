#!/usr/bin/env bash
# T09: feed-add rate limit. Fire 10 rapid POSTs, expect at least one 429.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="T09-rate-limits" source "$SCRIPT_DIR/../lib/common.sh"

JAR="$RESULTS_DIR/T09-cookies.jar"
rm -f "$JAR"
login "$LOCAL_BASE" "$LOCAL_PASSWORD" "$JAR" >/dev/null
csrf=$(curl -s -b "$JAR" "$LOCAL_BASE/api/v1/auth/status" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("csrf_token","") or d.get("csrfToken",""))' 2>/dev/null || true)

codes=()
for i in $(seq 1 10); do
    code=$(curl -s -o /dev/null -w '%{http_code}' \
        -b "$JAR" \
        -X POST "$LOCAL_BASE/api/v1/feeds" \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $csrf" \
        -d '{"sourceUrl":"https://nonexistent.example.invalid/rss"}')
    codes+=("$code")
done
note "codes: ${codes[*]}"

rate_limited=0
for c in "${codes[@]}"; do
    if [ "$c" = "429" ]; then
        rate_limited=$((rate_limited + 1))
    fi
done

if [ "$rate_limited" -gt 0 ]; then
    pass_step "rate limit engaged: $rate_limited / 10 requests returned 429"
else
    fail_step "no rate limit engagement: 0 / 10 requests were 429 (codes: ${codes[*]})"
fi

rm -f "$JAR"
finish_test "T09-rate-limits"
