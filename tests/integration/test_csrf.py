"""Integration tests for double-submit CSRF protection."""
import json
import os
import sys
import tempfile

import pytest

_test_data_dir = tempfile.mkdtemp(prefix='csrf_test_')
os.environ['SECRET_KEY'] = 'csrf-test-secret'
os.environ['DATA_DIR'] = _test_data_dir
os.environ['MINUSPOD_MASTER_PASSPHRASE'] = 'csrf-test-passphrase'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import database
import storage as storage_mod
database.Database._instance = None
database.Database.__init__.__defaults__ = (_test_data_dir,)
storage_mod.Storage.__init__.__defaults__ = (_test_data_dir,)

from main_app import app


@pytest.fixture
def client():
    # Reset any password / session state from earlier tests so each test
    # sees a clean "no password yet" starting state.
    db = database.Database()
    db.set_setting('app_password', '')
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_get_receives_csrf_cookie(client):
    response = client.get('/api/v1/auth/status')
    assert response.status_code == 200
    cookie_header = '\n'.join(response.headers.getlist('Set-Cookie'))
    assert 'minuspod_csrf=' in cookie_header
    assert 'SameSite=Strict' in cookie_header
    assert 'HttpOnly' not in cookie_header.split('minuspod_csrf=')[1].split(';')[0:1][0]


def _set_password_and_login(client, password: str = 'CsrfTestPw123!'):
    """Set a password via PUT /auth/password then log in, returning the
    CSRF cookie value in the authenticated session.
    """
    # First GET warms up the session and issues a CSRF token.
    warmup = client.get('/api/v1/auth/status')
    assert warmup.status_code == 200
    # Grab the CSRF cookie so we can send mutating requests.
    cookie = client.get_cookie('minuspod_csrf')
    token = cookie.value if cookie else None
    assert token is not None

    # First PUT /auth/password sets the password. Must carry CSRF header.
    r = client.put(
        '/api/v1/auth/password',
        data=json.dumps({'newPassword': password}),
        content_type='application/json',
        headers={'X-CSRF-Token': token},
    )
    assert r.status_code == 200, r.get_data(as_text=True)

    cookie = client.get_cookie('minuspod_csrf')
    return cookie.value


def test_post_without_csrf_token_rejected_after_auth(client):
    token = _set_password_and_login(client)

    # Same authenticated session, but omit the header: CSRF layer should 403.
    response = client.post(
        '/api/v1/feeds',
        data=json.dumps({'sourceUrl': 'https://example.com/feed.xml'}),
        content_type='application/json',
    )
    assert response.status_code == 403
    assert 'CSRF' in (response.get_data(as_text=True) or '')


def test_post_with_matching_csrf_token_passes_csrf_layer(client):
    token = _set_password_and_login(client)

    # Mismatched header: still 403.
    r_bad = client.post(
        '/api/v1/feeds',
        data=json.dumps({'sourceUrl': 'not-a-url'}),
        content_type='application/json',
        headers={'X-CSRF-Token': 'wrong-token'},
    )
    assert r_bad.status_code == 403

    # Matching header: CSRF layer passes, may 400 on invalid URL downstream.
    r_ok = client.post(
        '/api/v1/feeds',
        data=json.dumps({'sourceUrl': 'not-a-url'}),
        content_type='application/json',
        headers={'X-CSRF-Token': token},
    )
    assert r_ok.status_code != 403


def test_login_endpoint_exempt_from_csrf(client):
    """/auth/login must not require a CSRF token, since the client has not
    yet received a session."""
    response = client.post(
        '/api/v1/auth/login',
        data=json.dumps({'password': 'wrong'}),
        content_type='application/json',
    )
    # Exempt means CSRF layer doesn't block; auth layer may still 401.
    assert response.status_code in (200, 400, 401)


def test_safe_methods_do_not_require_csrf(client):
    response = client.get('/api/v1/auth/status')
    assert response.status_code == 200
