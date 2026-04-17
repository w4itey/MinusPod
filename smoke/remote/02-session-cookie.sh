#!/usr/bin/env bash
# T02 (remote): On HTTPS production, Set-Cookie MUST include Secure + HttpOnly
# + SameSite. We use a deliberately wrong password so we don't churn an
# active session, and inspect the Set-Cookie that WOULD be issued.
#
# NOTE: a wrong-password login will NOT issue Set-Cookie. To actually inspect
# cookie flags on remote, we hit a non-mutating authenticated endpoint with
# the existing cookies.txt and look at the Set-Cookie on the response (Flask
# refreshes session cookies on access).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="R-T02-session-cookie" source "$SCRIPT_DIR/../lib/common.sh"

resp=$(curl -s -i -b "$REMOTE_COOKIES" "$REMOTE_BASE/api/v1/auth/status")
status=$(printf '%s' "$resp" | head -1 | awk '{print $2}')
note "auth/status HTTP $status"

cookie_line=$(printf '%s' "$resp" | grep -i '^set-cookie:' | head -1 || true)
if [ -z "$cookie_line" ]; then
    skip_step 'no Set-Cookie refresh on /auth/status (session may not refresh on this endpoint); cannot inspect flags this way'
else
    pass_step 'Set-Cookie inspectable on /auth/status'
    note "cookie: $cookie_line"
    assert_match "$cookie_line" '[Ss]ecure' 'Secure flag PRESENT on production HTTPS cookie'
    assert_match "$cookie_line" '[Hh]ttp[Oo]nly' 'HttpOnly flag present'
    assert_match "$cookie_line" '[Ss]ame[Ss]ite' 'SameSite attribute present'
fi

finish_test "R-T02-session-cookie"
