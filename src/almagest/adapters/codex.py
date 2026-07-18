"""Codex inventory adapter descriptors."""

from almagest.adapters.base import AdapterDescriptor, SurfaceMode, SurfaceRule
from almagest.registry import AssetKind, Consumer, Platform


def _codex_rules() -> tuple[SurfaceRule, ...]:
    """Build shared Codex rules for runtime and user homes.

    Returns:
        Bounded rules used by both macOS and Windows descriptors.
    """
    return (
        SurfaceRule(
            "codex.active-root",
            AssetKind.SELECTOR,
            "codex.runtime-home",
            "",
            SurfaceMode.ROOT,
            "active-root",
        ),
        SurfaceRule(
            "codex.settings",
            AssetKind.SETTINGS,
            "codex.runtime-home",
            "config.toml",
            SurfaceMode.FILE,
            "settings",
        ),
        SurfaceRule(
            "codex.profiles",
            AssetKind.PROFILE,
            "codex.runtime-home",
            "",
            SurfaceMode.GLOB,
            "profile",
            pattern="*.config.toml",
        ),
        SurfaceRule(
            "codex.mcp",
            AssetKind.MCP,
            "codex.runtime-home",
            "config.toml",
            SurfaceMode.TOML_TABLE,
            "mcp",
            selector=("mcp_servers",),
            precedence=20,
        ),
        SurfaceRule(
            "codex.hooks-config",
            AssetKind.HOOK,
            "codex.runtime-home",
            "hooks.json",
            SurfaceMode.JSON_MAP,
            "hook-config",
            precedence=30,
        ),
        SurfaceRule(
            "codex.hooks-home",
            AssetKind.HOOK,
            "codex.user-home",
            "hooks",
            SurfaceMode.DIRECTORY,
            "hook-file",
            precedence=10,
        ),
        SurfaceRule(
            "codex.plugins-config",
            AssetKind.PLUGIN,
            "codex.runtime-home",
            "config.toml",
            SurfaceMode.TOML_TABLE,
            "plugin-config",
            selector=("plugins",),
            precedence=20,
        ),
        SurfaceRule(
            "codex.plugins-packages",
            AssetKind.PLUGIN,
            "codex.user-home",
            "plugins",
            SurfaceMode.DIRECTORY,
            "plugin-package",
            default_ownership="external-owned",
        ),
        SurfaceRule(
            "codex.instructions",
            AssetKind.INSTRUCTION,
            "codex.user-home",
            "AGENTS.md",
            SurfaceMode.FILE,
            "instruction",
        ),
        SurfaceRule(
            "codex.skills",
            AssetKind.SKILL,
            "codex.user-home",
            "skills",
            SurfaceMode.DIRECTORY,
            "skill",
            external_names=(".system",),
            required_frontmatter=("name", "description"),
        ),
    )


CODEX_MACOS = AdapterDescriptor(
    adapter_id="codex.macos",
    platform=Platform.MACOS,
    consumer=Consumer.CODEX,
    product="codex-cli",
    format_fingerprint="codex-config-v1",
    fixture_version_prefixes=("0.144.",),
    required_role_sets=(frozenset({"codex.runtime-home", "codex.user-home"}),),
    rules=_codex_rules(),
)

CODEX_WINDOWS = AdapterDescriptor(
    adapter_id="codex.windows",
    platform=Platform.WINDOWS,
    consumer=Consumer.CODEX,
    product="codex-cli",
    format_fingerprint="codex-config-v1",
    fixture_version_prefixes=("0.144.",),
    required_role_sets=(frozenset({"codex.runtime-home", "codex.user-home"}),),
    rules=_codex_rules(),
)
