"""Double-submit CSRF protection for the Flask API.

The session cookie is ``SameSite=Strict`` so cross-site requests already
cannot carry auth. This module is the second layer: mutating requests
must present an ``X-CSRF-Token`` header that matches the non-HttpOnly
``minuspod_csrf`` cookie set on every authenticated response. An attacker
on an evil origin cannot read either the session cookie or the CSRF
cookie (cross-origin), cannot set a ``X-CSRF-Token`` header on a form
POST, and cannot mount a fetch with credentials under same-origin
policy, so the double-submit closes the remaining same-site vectors.
"""
from __future__ import annotations

import secrets
from typing import Optional

from flask import Request, Response, session


CSRF_COOKIE_NAME = 'minuspod_csrf'
CSRF_HEADER_NAME = 'X-CSRF-Token'
CSRF_SESSION_KEY = '_csrf_token'
SAFE_METHODS = frozenset({'GET', 'HEAD', 'OPTIONS'})


def get_or_create_token() -> str:
    token = session.get(CSRF_SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CSRF_SESSION_KEY] = token
    return token


def apply_csrf_cookie(response: Response, cookie_secure: bool) -> Response:
    """Ensure ``response`` carries the minuspod_csrf cookie.

    Called from the global ``after_request`` hook; the cookie tracks the
    same-name session field so that a reused session keeps its token
    across responses. Set ``HttpOnly=False`` so the frontend JS can read
    it to populate the header; ``SameSite=Strict`` so the cookie never
    travels cross-site in the first place.
    """
    token = get_or_create_token()
    if response.headers.get('X-Skip-CSRF-Cookie'):
        response.headers.pop('X-Skip-CSRF-Cookie', None)
        return response
    existing = response.headers.get('Set-Cookie', '')
    if CSRF_COOKIE_NAME not in existing:
        response.set_cookie(
            CSRF_COOKIE_NAME,
            token,
            secure=cookie_secure,
            httponly=False,
            samesite='Strict',
        )
    return response


def validate(request: Request) -> Optional[str]:
    """Return None if the CSRF check passes, else a user-safe error string.

    Callers translate the error string into a 403. The check is skipped
    for safe methods and when no session token has been issued yet
    (pre-login bootstrap requests).
    """
    if request.method in SAFE_METHODS:
        return None
    expected = session.get(CSRF_SESSION_KEY)
    if not expected:
        # No session token to double-submit against; let auth layer decide
        # whether the request is allowed.
        return None
    supplied = request.headers.get(CSRF_HEADER_NAME)
    if not supplied or not secrets.compare_digest(supplied, expected):
        return 'CSRF token missing or invalid'
    return None
