#!/usr/bin/env bash
# T10: destructive endpoint rate limit. Two POST /system/cleanup within an
# hour should yield 1x success + 1x 429. Audit log line WARN expected.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="T10-destructive-rate" source "$SCRIPT_DIR/../lib/common.sh"

JAR="$RESULTS_DIR/T10-cookies.jar"
rm -f "$JAR"
login "$LOCAL_BASE" "$LOCAL_PASSWORD" "$JAR" >/dev/null
csrf=$(curl -s -b "$JAR" "$LOCAL_BASE/api/v1/auth/status" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("csrf_token","") or d.get("csrfToken",""))' 2>/dev/null || true)

first=$(curl -s -o /dev/null -w '%{http_code}' \
    -b "$JAR" \
    -X POST "$LOCAL_BASE/api/v1/system/cleanup" \
    -H "X-CSRF-Token: $csrf")
second=$(curl -s -o /dev/null -w '%{http_code}' \
    -b "$JAR" \
    -X POST "$LOCAL_BASE/api/v1/system/cleanup" \
    -H "X-CSRF-Token: $csrf")

assert_in "$first" "200 202 204" "first cleanup succeeds (got $first)"
assert_eq "$second" "429" 'second cleanup rate-limited'

dump_local_logs
if grep -E 'Destructive cleanup triggered|cleanup_triggered' "$LOCAL_LOG_FILE" >/dev/null; then
    pass_step 'WARN audit log present for destructive cleanup'
else
    fail_step 'WARN audit log missing for destructive cleanup'
fi

rm -f "$JAR"
finish_test "T10-destructive-rate"
