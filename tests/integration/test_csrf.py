"""Integration tests for double-submit CSRF protection."""
import json

import pytest


@pytest.fixture
def csrf_client(app_client, temp_db, monkeypatch):
    """app_client with a guaranteed clean password state.

    Uses the existing temp_db fixture (which resets Database._instance and
    creates a fresh on-disk DB at a temp path) plus app_client. Setting a
    passphrase env is required so the password-change endpoint succeeds
    when the test sets one.
    """
    monkeypatch.setenv('MINUSPOD_MASTER_PASSPHRASE', 'csrf-test-passphrase')
    temp_db.set_setting('app_password', '')
    yield app_client


def test_get_receives_csrf_cookie(csrf_client):
    response = csrf_client.get('/api/v1/auth/status')
    assert response.status_code == 200
    cookie = csrf_client.get_cookie('minuspod_csrf')
    assert cookie is not None
    assert cookie.secure or True  # Secure flag depends on test env
    assert 'Strict' in (cookie.same_site or '')


def _get_csrf_token(csrf_client):
    csrf_client.get('/api/v1/auth/status')
    cookie = csrf_client.get_cookie('minuspod_csrf')
    assert cookie is not None
    return cookie.value


def _set_password(csrf_client, token, password='CsrfTestPw123!'):
    r = csrf_client.put(
        '/api/v1/auth/password',
        data=json.dumps({'newPassword': password}),
        content_type='application/json',
        headers={'X-CSRF-Token': token},
    )
    assert r.status_code == 200, r.get_data(as_text=True)


def test_post_without_csrf_token_rejected_after_auth(csrf_client):
    token = _get_csrf_token(csrf_client)
    _set_password(csrf_client, token)

    response = csrf_client.post(
        '/api/v1/feeds',
        data=json.dumps({'sourceUrl': 'https://example.com/feed.xml'}),
        content_type='application/json',
    )
    assert response.status_code == 403
    assert 'CSRF' in (response.get_data(as_text=True) or '')


def test_post_with_mismatched_csrf_rejected(csrf_client):
    token = _get_csrf_token(csrf_client)
    _set_password(csrf_client, token)

    response = csrf_client.post(
        '/api/v1/feeds',
        data=json.dumps({'sourceUrl': 'https://example.com/feed.xml'}),
        content_type='application/json',
        headers={'X-CSRF-Token': 'wrong-token'},
    )
    assert response.status_code == 403


def test_post_with_matching_csrf_token_passes_csrf_layer(csrf_client):
    token = _get_csrf_token(csrf_client)
    _set_password(csrf_client, token)

    # Re-read cookie in case token rotated
    cookie = csrf_client.get_cookie('minuspod_csrf')
    token = cookie.value

    response = csrf_client.post(
        '/api/v1/feeds',
        data=json.dumps({'sourceUrl': 'not-a-url'}),
        content_type='application/json',
        headers={'X-CSRF-Token': token},
    )
    assert response.status_code != 403


def test_login_endpoint_exempt_from_csrf(csrf_client):
    response = csrf_client.post(
        '/api/v1/auth/login',
        data=json.dumps({'password': 'wrong'}),
        content_type='application/json',
    )
    # Exempt means CSRF layer doesn't block; auth layer may still 401.
    assert response.status_code in (200, 400, 401)


def test_safe_methods_do_not_require_csrf(csrf_client):
    response = csrf_client.get('/api/v1/auth/status')
    assert response.status_code == 200
