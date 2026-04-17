#!/usr/bin/env bash
# T03: auth-exempt matrix. Exempt endpoints answer unauth; protected endpoints 401.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="T03-auth-matrix" source "$SCRIPT_DIR/../lib/common.sh"

# Exempt: /health and /auth/status should answer without a session cookie
for path in /api/v1/health /api/v1/auth/status; do
    code=$(http_code "$LOCAL_BASE$path")
    assert_in "$code" "200 204" "exempt $path returns 2xx unauth"
done

# Protected: must 401 unauth
for path in /api/v1/feeds /api/v1/system/status /api/v1/status/stream /api/v1/history; do
    code=$(http_code "$LOCAL_BASE$path")
    assert_eq "$code" "401" "protected $path returns 401 unauth"
done

finish_test "T03-auth-matrix"
