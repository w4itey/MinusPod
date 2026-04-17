"""End-to-end path-traversal tests through the HTTP surface.

Unit tests in test_path_containment cover Storage directly; these
exercise the HTTP routes to confirm a traversal payload cannot leak
through to the filesystem via a request.
"""
import os
import sys
import tempfile

import pytest

_test_data_dir = tempfile.mkdtemp(prefix='pathtrav_test_')
os.environ.setdefault('SECRET_KEY', 'pathtrav-test-secret')
os.environ.setdefault('DATA_DIR', _test_data_dir)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import database
import storage as storage_mod
database.Database._instance = None
database.Database.__init__.__defaults__ = (_test_data_dir,)
storage_mod.Storage.__init__.__defaults__ = (_test_data_dir,)

from main_app import app


@pytest.fixture
def client():
    db = database.Database()
    db.set_setting('app_password', '')
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.mark.parametrize("slug", [
    "..",
    "../etc",
    "..%2Fetc",
    "foo/bar",
    "foo\\bar",
    ".hidden",
])
def test_traversal_slug_never_returns_200(client, slug):
    """Any traversal payload must not return 200 from an artwork or RSS
    route; the storage layer raises PathContainmentError which the
    handler must translate into a 4xx."""
    for path in (
        f"/api/v1/feeds/{slug}/artwork",
    ):
        response = client.get(path)
        assert response.status_code < 200 or response.status_code >= 300


@pytest.mark.parametrize("episode_id", [
    "..",
    "../escape",
    "ZZZZZZZZZZZZ",  # correct length, wrong alphabet
    "short",
    "0123456789abc",  # one char too long
])
def test_traversal_episode_id_never_returns_200(client, episode_id):
    """Episode-id traversal payloads must not return the served file."""
    paths = [
        f"/episodes/some-slug/{episode_id}.mp3",
        f"/episodes/some-slug/{episode_id}.vtt",
        f"/episodes/some-slug/{episode_id}/chapters.json",
    ]
    for path in paths:
        response = client.get(path)
        assert response.status_code < 200 or response.status_code >= 300, (
            f"{path} returned {response.status_code}"
        )
