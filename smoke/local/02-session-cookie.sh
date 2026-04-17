#!/usr/bin/env bash
# T02: session cookie flags. Smoke env sets MINUSPOD_SESSION_COOKIE_SECURE=false,
# so Set-Cookie should NOT include 'Secure'. HttpOnly should be present.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="T02-session-cookie" source "$SCRIPT_DIR/../lib/common.sh"

resp=$(curl -s -i -X POST "$LOCAL_BASE/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"password\":\"$LOCAL_PASSWORD\"}")

status=$(printf '%s' "$resp" | head -1 | awk '{print $2}')
assert_eq "$status" "200" 'login returns HTTP 200'

cookie_line=$(printf '%s' "$resp" | grep -i '^set-cookie:' | head -1 || true)
if [ -z "$cookie_line" ]; then
    fail_step 'no Set-Cookie header on login response'
else
    pass_step 'Set-Cookie header present'
    note "cookie: $cookie_line"
    # In smoke env (override=false), Secure flag should be absent
    assert_no_match "$cookie_line" '[Ss]ecure' 'Secure flag absent (override=false in smoke env)'
    assert_match "$cookie_line" '[Hh]ttp[Oo]nly' 'HttpOnly flag present'
    assert_match "$cookie_line" '[Ss]ame[Ss]ite' 'SameSite attribute present'
fi

finish_test "T02-session-cookie"
