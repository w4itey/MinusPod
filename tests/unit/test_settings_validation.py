"""Unit tests for settings API validation (OpenRouter key format)."""
import os
import sys
import tempfile
import json
from unittest.mock import patch, MagicMock

import pytest

# Create temp data dir and set env before any imports that touch /app/data
_test_data_dir = tempfile.mkdtemp(prefix='settings_test_')
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['DATA_DIR'] = _test_data_dir

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import database
import storage as storage_mod
database.Database._instance = None
database.Database.__init__.__defaults__ = (_test_data_dir,)
database.Database.__new__.__defaults__ = (_test_data_dir,)
storage_mod.Storage.__init__.__defaults__ = (_test_data_dir,)

from main_app import app


@pytest.fixture
def client():
    """Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


class TestOpenRouterKeyValidation:
    """Tests for OpenRouter API key format validation in settings endpoint."""

    def test_rejects_key_without_sk_or_prefix(self, client):
        response = client.put(
            '/api/v1/settings/ad-detection',
            data=json.dumps({'openrouterApiKey': 'sk-ant-wrong-prefix'}),
            content_type='application/json',
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'sk-or-' in data['error']

    def test_accepts_valid_sk_or_key(self, client):
        response = client.put(
            '/api/v1/settings/ad-detection',
            data=json.dumps({'openrouterApiKey': 'sk-or-v1-valid-key'}),
            content_type='application/json',
        )
        assert response.status_code == 200

    def test_accepts_empty_key_for_reset(self, client):
        response = client.put(
            '/api/v1/settings/ad-detection',
            data=json.dumps({'openrouterApiKey': ''}),
            content_type='application/json',
        )
        assert response.status_code == 200

    def test_strips_whitespace_before_validation(self, client):
        response = client.put(
            '/api/v1/settings/ad-detection',
            data=json.dumps({'openrouterApiKey': '  sk-or-v1-padded  '}),
            content_type='application/json',
        )
        assert response.status_code == 200
