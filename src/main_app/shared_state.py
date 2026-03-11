"""Shared mutable state for main_app sub-modules.

Provides module-level sets/dicts that multiple main_app modules need to share
(e.g. log-dedup sets that were a single object in the original monolith).
"""

# Track episodes already warned about permanent failure (avoid log spam on repeated requests).
# Shared across routes.py and processing.py so warn-dedup works across both code paths.
permanently_failed_warned: set = set()
