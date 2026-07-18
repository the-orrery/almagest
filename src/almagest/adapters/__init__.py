"""Read-only consumer adapter descriptors used by live inventory."""

from almagest.adapters.base import (
    AdapterDescriptor,
    Compatibility,
    ConsumerEvidence,
    SurfaceMode,
    SurfaceRule,
)
from almagest.adapters.claude import CLAUDE_WINDOWS
from almagest.adapters.codex import CODEX_MACOS, CODEX_WINDOWS
from almagest.adapters.qodercli import QODERCLI_MACOS
from almagest.registry import Consumer, Platform

ADAPTERS: tuple[AdapterDescriptor, ...] = (
    CODEX_MACOS,
    QODERCLI_MACOS,
    CODEX_WINDOWS,
    CLAUDE_WINDOWS,
)


def adapter_for(
    platform: Platform,
    consumer: Consumer,
) -> AdapterDescriptor | None:
    """Return the single built-in adapter for a platform/consumer pair.

    Args:
        platform: Current target host platform.
        consumer: Registry consumer type.

    Returns:
        The matching descriptor, or ``None`` when the pair is unsupported.
    """
    matches = [
        adapter
        for adapter in ADAPTERS
        if adapter.platform == platform and adapter.consumer == consumer
    ]
    return matches[0] if len(matches) == 1 else None


__all__ = [
    "ADAPTERS",
    "CLAUDE_WINDOWS",
    "CODEX_MACOS",
    "CODEX_WINDOWS",
    "QODERCLI_MACOS",
    "AdapterDescriptor",
    "Compatibility",
    "ConsumerEvidence",
    "SurfaceMode",
    "SurfaceRule",
    "adapter_for",
]
