"""Unit tests for cancel.py cooperative cancellation primitives."""
import threading
import pytest

from cancel import (
    ProcessingCancelled,
    _check_cancel,
    cancel_processing,
    _cancel_events,
    _cancel_events_lock,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Ensure the cancel registry is clean before and after each test."""
    with _cancel_events_lock:
        _cancel_events.clear()
    yield
    with _cancel_events_lock:
        _cancel_events.clear()


def _register_event(slug, episode_id):
    """Helper: register a cancel event and return it."""
    key = f"{slug}:{episode_id}"
    event = threading.Event()
    with _cancel_events_lock:
        _cancel_events[key] = event
    return event


class TestCancelProcessing:
    def test_returns_true_and_sets_event_when_registered(self):
        event = _register_event("pod", "ep1")
        assert not event.is_set()
        result = cancel_processing("pod", "ep1")
        assert result is True
        assert event.is_set()

    def test_returns_false_when_no_event_registered(self):
        result = cancel_processing("pod", "ep_missing")
        assert result is False

    def test_does_not_affect_other_episodes(self):
        event_a = _register_event("pod", "ep_a")
        event_b = _register_event("pod", "ep_b")
        cancel_processing("pod", "ep_a")
        assert event_a.is_set()
        assert not event_b.is_set()


class TestCheckCancel:
    def test_raises_when_event_is_set(self):
        event = threading.Event()
        event.set()
        with pytest.raises(ProcessingCancelled):
            _check_cancel(event, "pod", "ep1")

    def test_noop_when_event_not_set(self):
        event = threading.Event()
        _check_cancel(event, "pod", "ep1")  # should not raise

    def test_noop_when_cancel_event_is_none(self):
        _check_cancel(None, "pod", "ep1")  # should not raise


class TestRegistryCleanup:
    def test_pop_removes_entry(self):
        _register_event("pod", "ep1")
        key = "pod:ep1"
        with _cancel_events_lock:
            _cancel_events.pop(key, None)
        assert cancel_processing("pod", "ep1") is False
