"""Shared retry/backoff utilities."""
import random


def calculate_backoff(
    attempt: int,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    exponential_base: int = 2,
    jitter: bool = True,
) -> float:
    """Calculate exponential backoff delay with optional jitter.

    Args:
        attempt: Zero-based attempt number
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap in seconds
        exponential_base: Base for exponential growth
        jitter: If True, randomize delay to 50-150% to prevent thundering herd

    Returns:
        Delay in seconds
    """
    delay = min(base_delay * (exponential_base ** attempt), max_delay)
    if jitter:
        delay = delay * (0.5 + random.random())
    return delay
