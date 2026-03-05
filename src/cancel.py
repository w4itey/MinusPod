"""Cooperative cancellation primitives for in-flight episode processing.

Lightweight module with no Flask/CUDA dependencies so it can be imported
in unit tests without triggering heavy initialization.
"""
import logging
import threading

logger = logging.getLogger('podcast.audio')

# Cancel event registry -- maps "slug:episode_id" to threading.Event
_cancel_events: dict[str, threading.Event] = {}
_cancel_events_lock = threading.Lock()


class ProcessingCancelled(Exception):
    """Raised when processing is cancelled by user."""
    pass


def _check_cancel(cancel_event, slug, episode_id):
    """Check if cancellation has been requested and raise if so."""
    if cancel_event and cancel_event.is_set():
        logger.info(f"[{slug}:{episode_id}] Processing cancelled by user")
        raise ProcessingCancelled()


def cancel_processing(slug, episode_id):
    """Signal an in-flight processing thread to stop.

    Returns True if a cancel event was found and signalled, False otherwise.
    """
    key = f"{slug}:{episode_id}"
    with _cancel_events_lock:
        event = _cancel_events.get(key)
    if event:
        event.set()
        return True
    return False
