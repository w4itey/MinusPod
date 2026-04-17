"""HTTP utility helpers.

The `post_with_retry` / `get_with_retry` wrappers that lived here were
removed after the 2.0 security audit; every outbound caller now routes
through ``utils.safe_http`` so the per-redirect SSRF revalidation and
downgrade guards apply. Only the log-scrubbing helper remains here.
"""
from urllib.parse import urlsplit


def safe_url_for_log(url) -> str:
    """Return only scheme+host for logging; drops path, query, fragment so
    tokens embedded anywhere in the URL never reach logs.

    Tolerant of non-string input (e.g. test doubles, None): anything that
    can't be parsed reduces to the sentinel ``<url>`` rather than raising.
    """
    try:
        parts = urlsplit(str(url))
        host = parts.hostname or ''
        scheme = parts.scheme or 'http'
        return f"{scheme}://{host}" if host else '<url>'
    except (TypeError, ValueError):
        return '<url>'
