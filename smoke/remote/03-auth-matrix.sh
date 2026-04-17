#!/usr/bin/env bash
# T03 (remote): exempt vs protected endpoints unauth.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="R-T03-auth-matrix" source "$SCRIPT_DIR/../lib/common.sh"

for path in /api/v1/health /api/v1/auth/status; do
    code=$(http_code "$REMOTE_BASE$path")
    assert_in "$code" "200 204" "exempt $path returns 2xx unauth (got $code)"
done

for path in /api/v1/feeds /api/v1/system/status /api/v1/status/stream /api/v1/history; do
    code=$(http_code "$REMOTE_BASE$path")
    assert_eq "$code" "401" "protected $path returns 401 unauth (got $code)"
done

finish_test "R-T03-auth-matrix"
