#!/usr/bin/env bash
# T03: auth-exempt matrix. Exempt endpoints answer unauth; protected endpoints 401.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="T03-auth-matrix" source "$SCRIPT_DIR/../lib/common.sh"

# Exempt-by-design: /health, /auth/status always answer unauth. /status/stream
# is exempt-by-prefix because EventSource can't handle 401; it signals auth
# failure via an `event: auth-failed` SSE frame instead.
for path in /api/v1/health /api/v1/auth/status; do
    code=$(http_code "$LOCAL_BASE$path")
    assert_in "$code" "200 204" "exempt $path returns 2xx unauth"
done

# 00-setup configures an admin password, so check_auth is live. Every
# non-exempt endpoint must 401 when hit without a session cookie. SSE
# used to be exempt-by-prefix; post-audit-gap-fix G01 removed the
# exemption so the HTTP-level 401 is correct (frontend handles the
# EventSource reconnect via /api/v1/auth/status probe).
for path in /api/v1/feeds /api/v1/system/status /api/v1/history /api/v1/status/stream; do
    code=$(http_code "$LOCAL_BASE$path")
    assert_eq "$code" "401" "protected $path returns 401 unauth (got $code)"
done

finish_test "T03-auth-matrix"
