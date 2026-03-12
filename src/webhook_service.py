"""Outbound webhook dispatch with Jinja2 custom payload templates."""

import datetime
import hashlib
import hmac
import json
import logging
import os
import threading
import time
import urllib.request
import urllib.error

from jinja2 import TemplateError
from jinja2.sandbox import SandboxedEnvironment

logger = logging.getLogger('podcast.webhooks')

EVENT_EPISODE_PROCESSED = 'Episode Processed'
EVENT_EPISODE_FAILED = 'Episode Failed'
VALID_EVENTS = {EVENT_EPISODE_PROCESSED, EVENT_EPISODE_FAILED}

_RETRY_ATTEMPTS = 2
_RETRY_DELAY_SECS = 2
_REQUEST_TIMEOUT_SECS = 5

_sandbox_env = SandboxedEnvironment()

_DUMMY_CONTEXT = {
    'event': 'Episode Processed',
    'timestamp': '',  # overwritten at render time with current UTC
    'episode': {
        'id': 'abc123',
        'title': 'Example Episode Title',
        'slug': 'example-podcast',
        'url': 'http://your-server:8000/ui/feeds/example-podcast/episodes/abc123',
        'ads_removed': 3,
        'processing_time_secs': 42.5,
        'llm_cost': 0.0035,
        'time_saved_secs': 187.0,
        'error_message': None,
    },
}


def _build_context(event, episode_id, slug, episode_title, processing_time,
                   llm_cost, ads_removed, error_message, original_duration,
                   new_duration):
    """Build the template/payload context dict for a webhook event."""
    ui_base_url = os.environ.get('UI_BASE_URL') or os.environ.get('BASE_URL', 'http://localhost:8000')
    episode_url = f"{ui_base_url}/ui/feeds/{slug}/episodes/{episode_id}"

    if original_duration is not None and new_duration is not None:
        time_saved_secs = round(original_duration - new_duration, 2)
    else:
        time_saved_secs = None

    return {
        'event': event,
        'timestamp': datetime.datetime.now(datetime.timezone.utc).strftime(
            '%Y-%m-%dT%H:%M:%SZ'
        ),
        'episode': {
            'id': episode_id,
            'title': episode_title,
            'slug': slug,
            'url': episode_url,
            'ads_removed': ads_removed,
            'processing_time_secs': round(processing_time, 2) if processing_time is not None else None,
            'llm_cost': round(llm_cost, 6) if llm_cost is not None else None,
            'time_saved_secs': time_saved_secs,
            'error_message': error_message,
        },
    }


def _render_template(template_str, context):
    """Render a Jinja2 template in a sandboxed environment."""
    template = _sandbox_env.from_string(template_str)
    return template.render(**context)


def _dispatch_webhook(url, body_bytes, headers, max_attempts=_RETRY_ATTEMPTS):
    """POST body_bytes to url with retry logic. Fire-and-forget."""
    for attempt in range(1, max_attempts + 1):
        try:
            req = urllib.request.Request(
                url, data=body_bytes, headers=headers, method='POST'
            )
            with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT_SECS) as resp:
                logger.info(
                    "Webhook delivered to %s (attempt %d, status %d)",
                    url, attempt, resp.status,
                )
                return resp.status
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            logger.warning(
                "Webhook delivery to %s failed (attempt %d/%d): %s",
                url, attempt, max_attempts, exc,
            )
            if attempt < max_attempts:
                time.sleep(_RETRY_DELAY_SECS)
        except Exception:
            logger.exception(
                "Unexpected error dispatching webhook to %s (attempt %d/%d)",
                url, attempt, max_attempts,
            )
            if attempt < max_attempts:
                time.sleep(_RETRY_DELAY_SECS)
    return None


def _prepare_and_dispatch(webhook_config, context, add_test_flag=False,
                          max_attempts=_RETRY_ATTEMPTS):
    """Render payload and dispatch to a single webhook. Returns HTTP status or None."""
    url = webhook_config.get('url')
    if not url:
        return None

    if add_test_flag:
        context = dict(context)
        context['test'] = True

    content_type = webhook_config.get('contentType', 'application/json')
    template_str = webhook_config.get('payloadTemplate')

    if template_str:
        try:
            body_str = _render_template(template_str, context)
        except TemplateError as exc:
            logger.error("Jinja2 render error for webhook %s, skipping: %s", url, exc)
            return None
    else:
        payload = dict(context)
        body_str = json.dumps(payload)

    body_bytes = body_str.encode('utf-8')

    headers = {'Content-Type': content_type}
    secret = webhook_config.get('secret')
    if secret:
        sig = hmac.new(
            secret.encode('utf-8'), body_bytes, hashlib.sha256
        ).hexdigest()
        headers['X-MinusPod-Signature'] = f"sha256={sig}"

    return _dispatch_webhook(url, body_bytes, headers, max_attempts=max_attempts)


def load_webhooks(db=None):
    """Load webhooks list from DB settings."""
    if db is None:
        from database import Database  # deferred to avoid circular imports
        db = Database()
    raw = db.get_setting('webhooks')
    if not raw:
        return []
    try:
        webhooks = json.loads(raw)
        return webhooks if isinstance(webhooks, list) else []
    except (json.JSONDecodeError, TypeError):
        logger.error("Failed to parse webhooks setting from DB")
        return []


def _fire_event_sync(event, episode_id, slug, episode_title, processing_time,
                     llm_cost, ads_removed, error_message, original_duration,
                     new_duration):
    """Synchronous webhook dispatch -- called in a daemon thread by fire_event."""
    webhooks = load_webhooks()
    if not webhooks:
        return

    context = _build_context(
        event, episode_id, slug, episode_title, processing_time,
        llm_cost, ads_removed, error_message, original_duration, new_duration,
    )

    for wh in webhooks:
        if not wh.get('enabled', False):
            continue
        if event not in wh.get('events', []):
            continue
        try:
            _prepare_and_dispatch(wh, context)
        except Exception:
            logger.exception("Unexpected error dispatching webhook to %s", wh.get('url'))


def fire_event(event, episode_id, slug, episode_title, processing_time,
               llm_cost, ads_removed=0, error_message=None,
               original_duration=None, new_duration=None):
    """Load webhooks from DB and dispatch to all matching subscribers.

    Dispatches in a daemon thread so the processing pipeline is never blocked.
    """
    if event not in VALID_EVENTS:
        logger.error("Invalid webhook event: %s", event)
        return

    thread = threading.Thread(
        target=_fire_event_sync,
        args=(event, episode_id, slug, episode_title, processing_time,
              llm_cost, ads_removed, error_message, original_duration,
              new_duration),
        daemon=True,
    )
    thread.start()


def render_template_preview(template_string):
    """Render a Jinja2 template with dummy data for validation/preview.

    Returns the rendered string. Raises jinja2.TemplateError on invalid
    templates so callers can surface the error to the user.
    """
    context = dict(_DUMMY_CONTEXT)
    context['timestamp'] = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return _render_template(template_string, context)


def fire_test_event(webhook_config):
    """Fire a test payload to a single webhook config dict.

    Attempts to load real data from the most recent completed
    processing_history entry. Falls back to synthetic placeholder data.

    Returns True on HTTP 2xx, False otherwise.
    """
    from database import Database  # deferred to avoid circular imports

    db = Database()
    context = None

    try:
        conn = db.get_connection()
        row = conn.execute(
            """SELECT h.episode_id, h.podcast_slug, h.episode_title,
                      h.processing_duration_seconds, h.llm_cost, h.ads_detected,
                      e.original_duration, e.new_duration
               FROM processing_history h
               LEFT JOIN episodes e ON e.episode_id = h.episode_id
                   AND e.podcast_slug = h.podcast_slug
               WHERE h.status = 'completed'
               ORDER BY h.processed_at DESC
               LIMIT 1"""
        ).fetchone()
        if row:
            context = _build_context(
                event=EVENT_EPISODE_PROCESSED,
                episode_id=row[0],
                slug=row[1],
                episode_title=row[2],
                processing_time=row[3],
                llm_cost=row[4],
                ads_removed=row[5],
                error_message=None,
                original_duration=row[6],
                new_duration=row[7],
            )
    except Exception:
        logger.debug("Could not load real data for test webhook, using placeholders")

    if context is None:
        context = dict(_DUMMY_CONTEXT)

    status = _prepare_and_dispatch(webhook_config, context, add_test_flag=True, max_attempts=1)
    if status is not None and 200 <= status < 300:
        return True
    return False
