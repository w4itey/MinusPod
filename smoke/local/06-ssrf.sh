#!/usr/bin/env bash
# T06: SSRF block on private/loopback IPs at feed-add. Authenticated.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="T06-ssrf" source "$SCRIPT_DIR/../lib/common.sh"

JAR="$RESULTS_DIR/T06-cookies.jar"
rm -f "$JAR"
login_code=$(login "$LOCAL_BASE" "$LOCAL_PASSWORD" "$JAR")
assert_eq "$login_code" "200" 'login for SSRF test'

# Capture CSRF token from /auth/status (token is exposed via cookie + endpoint)
csrf=$(curl -s -b "$JAR" "$LOCAL_BASE/api/v1/auth/status" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("csrf_token","") or d.get("csrfToken",""))' 2>/dev/null || true)
note "csrf token length: ${#csrf}"

urls=(
    "http://127.0.0.1/feed.xml"
    "http://169.254.169.254/latest/meta-data/"
    "http://10.0.0.1/rss"
    "http://[::1]/rss"
    "http://localhost/rss"
    "http://192.168.1.1/rss"
)

for u in "${urls[@]}"; do
    code=$(curl -s -o /dev/null -w '%{http_code}' \
        -b "$JAR" \
        -X POST "$LOCAL_BASE/api/v1/feeds" \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $csrf" \
        -d "{\"sourceUrl\":\"$u\"}")
    assert_in "$code" "400 422 403" "SSRF $u rejected (got $code)"
done

# Verify ssrf_blocked structured event in logs
dump_local_logs
ssrf_count=$(grep -c 'ssrf_blocked' "$LOCAL_LOG_FILE" || true)
if [ "$ssrf_count" -ge 1 ]; then
    pass_step "ssrf_blocked log events present (count=$ssrf_count)"
else
    fail_step 'ssrf_blocked log events missing'
fi

rm -f "$JAR"
finish_test "T06-ssrf"
