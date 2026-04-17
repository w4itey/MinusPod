#!/usr/bin/env bash
# T11: account lockout. From a private IP (loopback): 6 fails should NOT lock.
# From a spoofed public IP via X-Forwarded-For (requires TRUSTED_PROXY_COUNT=1):
# 5 fails then a 6th attempt with correct password should be 429 with Retry-After.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="T11-lockout" source "$SCRIPT_DIR/../lib/common.sh"

# 1) Private IP path: 6 wrong, then correct should still 200
for i in $(seq 1 6); do
    curl -s -o /dev/null -X POST "$LOCAL_BASE/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"password":"wrong"}'
done
priv=$(curl -s -o /dev/null -w '%{http_code}' \
    -X POST "$LOCAL_BASE/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"password\":\"$LOCAL_PASSWORD\"}")
assert_eq "$priv" "200" 'private-IP login succeeds after 6 failures (no lockout)'

# 2) Public IP path: 5 wrong from 203.0.113.5
SPOOF="203.0.113.5"
for i in $(seq 1 5); do
    curl -s -o /dev/null -X POST "$LOCAL_BASE/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -H "X-Forwarded-For: $SPOOF" \
        -d '{"password":"wrong"}'
done

# 6th attempt (even with correct password) should be 429 with Retry-After
resp=$(curl -s -i -X POST "$LOCAL_BASE/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: $SPOOF" \
    -d "{\"password\":\"$LOCAL_PASSWORD\"}")
status=$(printf '%s' "$resp" | head -1 | awk '{print $2}')
retry=$(printf '%s' "$resp" | awk -F': ' 'tolower($1)=="retry-after"{print $2}' | tr -d '\r' | head -1)

assert_eq "$status" "429" 'spoofed public IP locked out after 5 failures'
[ -n "$retry" ] && pass_step "Retry-After header present (=$retry)" \
                || fail_step 'Retry-After header missing on lockout response'

finish_test "T11-lockout"
