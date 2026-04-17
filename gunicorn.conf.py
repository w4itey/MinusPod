"""Gunicorn configuration.

Mirrors the flags previously inlined in ``entrypoint.sh`` so lifecycle hooks
(``on_starting``, ``post_fork``, ``when_ready``) can be wired from a tracked
config file rather than command-line arguments.
"""

from __future__ import annotations

import logging
import os
import sys


bind = os.environ.get("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "8"))
timeout = int(os.environ.get("GUNICORN_TIMEOUT", "600"))
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", "330"))
keepalive = int(os.environ.get("GUNICORN_KEEPALIVE", "5"))

worker_class = "gthread"
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOG_LEVEL", "info")

_log = logging.getLogger("gunicorn.lifecycle")


def on_starting(server):
    """Master-only, pre-fork.

    Runs DB schema init exactly once before any worker is spawned so that
    concurrent migration attempts from multiple workers can't race each
    other. Import ``Database`` here so the master process, not just workers,
    materialises the singleton and applies pending migrations.

    Any failure aborts the gunicorn master — workers must never accept
    requests against an un-migrated database.
    """
    src_dir = "/app/src"
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    try:
        from database import Database
        Database()
        _log.info("gunicorn on_starting: schema init complete")
    except Exception:
        _log.exception("gunicorn on_starting: schema init FAILED, aborting master")
        raise


def post_fork(server, worker):
    """Per-worker, post-fork.

    Reset the ``Database`` singleton so each worker opens its own sqlite
    connection instead of inheriting the master's fds. Fork-inherited
    SQLite connections corrupt state the moment two workers hit them;
    a reset failure is serious enough to refuse serving from this worker.
    """
    src_dir = "/app/src"
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from database import Database
    Database._instance = None


def when_ready(server):
    """Master, after all workers booted."""
    _log.info("gunicorn when_ready: workers=%s threads=%s", workers, threads)
