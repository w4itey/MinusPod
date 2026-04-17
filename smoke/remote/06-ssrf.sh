#!/usr/bin/env bash
# T06 (remote): SSRF block. Authenticated via cookies.txt. We test a SHORT
# list of public-IP-only patterns; private-IP patterns blocked by SSRF
# defenses are exercised on local. Here we only verify the API rejects
# obviously malformed URLs and an internal AWS metadata IP without actually
# attempting many private addresses (gentle on prod).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_NAME="R-T06-ssrf" source "$SCRIPT_DIR/../lib/common.sh"

csrf=$(curl -s -b "$REMOTE_COOKIES" "$REMOTE_BASE/api/v1/auth/status" \
    | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("csrf_token","") or d.get("csrfToken",""))' 2>/dev/null || true)
note "csrf token length: ${#csrf}"

# Only one private-net + one metadata target on remote (read-only spirit)
urls=(
    "http://169.254.169.254/latest/meta-data/"
    "http://[::1]/rss"
)

for u in "${urls[@]}"; do
    code=$(curl -s -o /dev/null -w '%{http_code}' \
        -b "$REMOTE_COOKIES" \
        -X POST "$REMOTE_BASE/api/v1/feeds" \
        -H "Content-Type: application/json" \
        -H "X-CSRF-Token: $csrf" \
        -d "{\"sourceUrl\":\"$u\"}")
    assert_in "$code" "400 422 403" "SSRF $u rejected (got $code)"
done

finish_test "R-T06-ssrf"
