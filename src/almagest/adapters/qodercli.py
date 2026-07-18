"""QoderCLI inventory adapter descriptor."""

from almagest.adapters.base import AdapterDescriptor, SurfaceMode, SurfaceRule
from almagest.registry import AssetKind, Consumer, Platform


def _home_rules(role: str, prefix: str) -> tuple[SurfaceRule, ...]:
    """Build the same bounded surface shape for one Qoder config home.

    Args:
        role: Registry binding role for this profile home.
        prefix: Stable fixture ID prefix.

    Returns:
        Rules for settings, MCP, hooks, plugins, instructions, and skills.
    """
    return (
        SurfaceRule(
            f"{prefix}.active-root",
            AssetKind.SELECTOR,
            role,
            "",
            SurfaceMode.ROOT,
            "active-root",
        ),
        SurfaceRule(
            f"{prefix}.settings",
            AssetKind.SETTINGS,
            role,
            "settings.json",
            SurfaceMode.FILE,
            "settings",
        ),
        SurfaceRule(
            f"{prefix}.mcp-settings",
            AssetKind.MCP,
            role,
            "settings.json",
            SurfaceMode.JSON_MAP,
            "mcp",
            selector=("mcpServers",),
            precedence=10,
        ),
        SurfaceRule(
            f"{prefix}.mcp-file",
            AssetKind.MCP,
            role,
            "mcp.json",
            SurfaceMode.JSON_MAP,
            "mcp",
            selector=("mcpServers",),
            precedence=None,
        ),
        SurfaceRule(
            f"{prefix}.hooks-settings",
            AssetKind.HOOK,
            role,
            "settings.json",
            SurfaceMode.JSON_MAP,
            "hook-config",
            selector=("hooks",),
            precedence=20,
        ),
        SurfaceRule(
            f"{prefix}.hooks-files",
            AssetKind.HOOK,
            role,
            "hooks",
            SurfaceMode.DIRECTORY,
            "hook-file",
            precedence=10,
        ),
        SurfaceRule(
            f"{prefix}.plugins-config",
            AssetKind.PLUGIN,
            role,
            "settings.json",
            SurfaceMode.JSON_MAP,
            "plugin-config",
            selector=("enabledPlugins",),
        ),
        SurfaceRule(
            f"{prefix}.plugins-packages",
            AssetKind.PLUGIN,
            role,
            "plugins",
            SurfaceMode.DIRECTORY,
            "plugin-package",
            default_ownership="external-owned",
        ),
        SurfaceRule(
            f"{prefix}.instructions",
            AssetKind.INSTRUCTION,
            role,
            "AGENTS.md",
            SurfaceMode.FILE,
            "instruction",
        ),
        SurfaceRule(
            f"{prefix}.skills",
            AssetKind.SKILL,
            role,
            "skills",
            SurfaceMode.DIRECTORY,
            "skill",
            required_frontmatter=("name", "description"),
        ),
    )


QODERCLI_MACOS = AdapterDescriptor(
    adapter_id="qodercli.macos",
    platform=Platform.MACOS,
    consumer=Consumer.QODERCLI,
    product="qodercli",
    format_fingerprint="qoder-config-v1",
    fixture_version_prefixes=("1.0.47",),
    required_role_sets=(
        frozenset({"qoder.user-home"}),
        frozenset({"qoder.work-home"}),
    ),
    rules=(
        *_home_rules("qoder.user-home", "qoder.user"),
        *_home_rules("qoder.work-home", "qoder.work"),
    ),
    unsupported_kinds=frozenset({AssetKind.PROFILE}),
)
