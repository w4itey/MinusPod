#!/usr/bin/env bash
# Pull ttlequals0/minuspod:2.0.0 and run isolated container on port 8001.
# Sets MINUSPOD_PASSWORD via -e so login works for tests.
#
# Idempotent: if a container with the same name already exists, it's removed.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=../lib/common.sh
TEST_NAME="00-setup" source "$SCRIPT_DIR/../lib/common.sh"

IMAGE="${IMAGE:-ttlequals0/minuspod:2.0.0}"
PORT="${PORT:-8001}"

log "pulling $IMAGE"
docker pull "$IMAGE" >/dev/null

if docker inspect "$LOCAL_CONTAINER" >/dev/null 2>&1; then
    log "removing existing container $LOCAL_CONTAINER"
    docker rm -f "$LOCAL_CONTAINER" >/dev/null
fi

if docker volume inspect "$LOCAL_VOLUME" >/dev/null 2>&1; then
    log "removing existing volume $LOCAL_VOLUME"
    docker volume rm -f "$LOCAL_VOLUME" >/dev/null
fi

log "creating volume $LOCAL_VOLUME"
docker volume create "$LOCAL_VOLUME" >/dev/null

log "starting $LOCAL_CONTAINER on port $PORT"
docker run -d \
    --name "$LOCAL_CONTAINER" \
    --platform linux/amd64 \
    -p "${PORT}:8000" \
    -v "${LOCAL_VOLUME}:/data" \
    -e MINUSPOD_PASSWORD="$LOCAL_PASSWORD" \
    -e MINUSPOD_SESSION_COOKIE_SECURE=false \
    -e MINUSPOD_TRUSTED_PROXY_COUNT=1 \
    -e ANTHROPIC_API_KEY=dummy-key-no-llm-calls-in-smoke \
    -e MINUSPOD_LOG_LEVEL=INFO \
    "$IMAGE" >/dev/null

log "waiting for /api/v1/health on $LOCAL_BASE"
if wait_for_health "$LOCAL_BASE" 90; then
    pass_step "container healthy at $LOCAL_BASE"
else
    fail_step "container did not become healthy in 90s"
    log "last 80 lines of container logs:"
    docker logs --tail 80 "$LOCAL_CONTAINER" 2>&1 | tee -a "$TEST_RESULT_FILE" >&2 || true
fi

dump_local_logs
finish_test "00-setup"
