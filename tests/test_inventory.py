from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from almagest import inventory, registry
from almagest.adapters import ADAPTERS
from almagest.cli import app

REVISION = "a" * 40
SECRET_SENTINEL = "must-never-appear"
runner = CliRunner()
REPOSITORY_ROOT = Path(__file__).parent.parent


def _write_json(path: Path, value: object) -> Path:
    """Write a deterministic JSON test document.

    Args:
        path: Destination path.
        value: JSON-compatible value.

    Returns:
        The destination path.
    """
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _registry_document(
    *,
    platform: str,
    consumer: str,
    target_id: str,
    roles: dict[str, str],
    with_skill: bool = True,
) -> dict[str, object]:
    """Build one complete shared Registry fixture.

    Args:
        platform: Registry host platform.
        consumer: Consumer enum value.
        target_id: Target logical ID.
        roles: Binding ID to adapter role.
        with_skill: Whether to add one expected skill assignment.

    Returns:
        Strict Registry JSON.
    """
    document: dict[str, object] = {
        "schema_version": 1,
        "layer": {"residency": "shared"},
        "sources": {},
        "hosts": {"host": {"platform": platform}},
        "targets": {
            target_id: {
                "host": "host",
                "consumer": consumer,
                "bindings": list(roles),
            }
        },
        "bindings": {
            binding_id: {
                "host": "host",
                "kind": "path",
                "role": role,
            }
            for binding_id, role in roles.items()
        },
        "assets": {},
        "assignments": {},
    }
    if with_skill:
        document["sources"] = {
            "source": {
                "repository": "personal/test",
                "revision": {"kind": "git-commit", "value": REVISION},
                "residency": "shared",
                "authority": "authored-owned",
            }
        }
        document["assets"] = {
            "skill.demo": {
                "kind": "skill",
                "source": {"source": "source", "path": "skills/demo"},
                "mutation_authority": "almagest-managed",
            }
        }
        document["assignments"] = {
            f"skill.demo@{target_id}": {
                "asset": "skill.demo",
                "target": target_id,
            }
        }
    return document


def _bindings(
    tmp_path: Path,
    *,
    roles: dict[str, str],
    roots: dict[str, Path],
    with_source: bool = True,
) -> dict[str, object]:
    """Build host-local bindings for one Registry fixture.

    Args:
        tmp_path: Temporary test root.
        roles: Binding ID to adapter role.
        roots: Binding ID to concrete test path.
        with_source: Whether to materialize the expected source skill.

    Returns:
        Strict host-binding JSON.
    """
    source_roots: dict[str, str] = {}
    if with_source:
        source = tmp_path / "source"
        (source / "skills" / "demo").mkdir(parents=True)
        (source / "skills" / "demo" / "SKILL.md").write_text(
            "---\nname: demo\ndescription: demo\n---\n",
            encoding="utf-8",
        )
        source_roots["personal/test"] = str(source)
    return {
        "schema_version": 1,
        "host": "host",
        "source_roots": source_roots,
        "bindings": {
            binding_id: {"kind": "path", "path": str(roots[binding_id])}
            for binding_id in roles
        },
    }


def _evidence(
    target_id: str,
    *,
    product: str,
    version: str,
    fingerprint: str,
    host_verified: bool = True,
) -> dict[str, object]:
    """Build one current-host consumer evidence fixture.

    Args:
        target_id: Registry target.
        product: Adapter product identity.
        version: Observed version.
        fingerprint: Adapter format fingerprint.
        host_verified: Whether evidence came from the current host.

    Returns:
        Strict evidence JSON.
    """
    return {
        "schema_version": 1,
        "consumers": {
            target_id: {
                "product": product,
                "version": version,
                "format_fingerprint": fingerprint,
                "evidence_source": "consumer-cli",
                "host_verified": host_verified,
            }
        },
    }


def _codex_fixture(
    tmp_path: Path,
    *,
    valid_frontmatter: bool = True,
    skills_present: bool = True,
) -> tuple[Path, Path, Path]:
    """Materialize a proven Mac Codex inventory fixture.

    Args:
        tmp_path: Temporary test root.
        valid_frontmatter: Whether the live skill metadata is compatible.
        skills_present: Whether the live skills root exists.

    Returns:
        Shared Registry, host bindings, and evidence paths.
    """
    roles = {
        "codex.runtime": "codex.runtime-home",
        "codex.user": "codex.user-home",
    }
    runtime = tmp_path / "runtime"
    user = tmp_path / "user"
    runtime.mkdir()
    user.mkdir()
    (runtime / "config.toml").write_text(
        '[mcp_servers.demo]\ncommand = "secret-command"\n'
        '[plugins."github@example"]\nenabled = true\n',
        encoding="utf-8",
    )
    (runtime / "hooks.json").write_text(
        '{"session_start": [{"command": "secret-hook"}]}',
        encoding="utf-8",
    )
    (user / "AGENTS.md").write_text("# instructions\n", encoding="utf-8")
    (user / "plugins" / "github").mkdir(parents=True)
    if skills_present:
        skill = user / "skills" / "demo"
        skill.mkdir(parents=True)
        frontmatter = (
            "---\nname: demo\ndescription: demo\n---\n"
            if valid_frontmatter
            else "# missing frontmatter\n"
        )
        (skill / "SKILL.md").write_text(frontmatter, encoding="utf-8")
    shared = _write_json(
        tmp_path / "shared.json",
        _registry_document(
            platform="macos",
            consumer="codex",
            target_id="mac.codex",
            roles=roles,
        ),
    )
    bindings = _write_json(
        tmp_path / "bindings.json",
        _bindings(
            tmp_path,
            roles=roles,
            roots={"codex.runtime": runtime, "codex.user": user},
        ),
    )
    evidence = _write_json(
        tmp_path / "evidence.json",
        _evidence(
            "mac.codex",
            product="codex-cli",
            version="0.144.5",
            fingerprint="codex-config-v1",
        ),
    )
    return shared, bindings, evidence


class MemoryReader:
    """Platform-independent reader used by Windows adapter fixtures."""

    def __init__(
        self,
        nodes: dict[tuple[str, str], inventory.ProbeKind],
        *,
        listings: dict[tuple[str, str], tuple[str, ...]] | None = None,
        texts: dict[tuple[str, str], str] | None = None,
    ) -> None:
        """Create an in-memory bounded filesystem.

        Args:
            nodes: Node kinds by binding and portable locator.
            listings: Directory entry names.
            texts: Bounded text file contents.
        """
        self.nodes = nodes
        self.listings = listings or {}
        self.texts = texts or {}
        self.calls = 0

    def stat(self, binding_id: str, relative_path: str) -> inventory.ProbeNode:
        """Return one in-memory node.

        Args:
            binding_id: Fixture binding.
            relative_path: Portable locator.

        Returns:
            Node metadata.
        """
        self.calls += 1
        return inventory.ProbeNode(
            self.nodes.get(
                (binding_id, relative_path),
                inventory.ProbeKind.MISSING,
            )
        )

    def list_entries(
        self, binding_id: str, relative_path: str
    ) -> inventory.ProbeListing:
        """Return one in-memory directory listing.

        Args:
            binding_id: Fixture binding.
            relative_path: Portable locator.

        Returns:
            Stable listing.
        """
        self.calls += 1
        return inventory.ProbeListing(
            self.listings.get((binding_id, relative_path), ())
        )

    def read_text(self, binding_id: str, relative_path: str) -> str:
        """Return one in-memory text document.

        Args:
            binding_id: Fixture binding.
            relative_path: Portable locator.

        Returns:
            Fixture text.
        """
        self.calls += 1
        try:
            return self.texts[(binding_id, relative_path)]
        except KeyError as exc:
            raise inventory.ProbeFailure("unreadable-surface") from exc


def test_all_four_adapters_cover_every_registry_kind() -> None:
    """Every confirmed consumer pair has explicit complete/unsupported coverage."""
    assert {adapter.adapter_id for adapter in ADAPTERS} == {
        "codex.macos",
        "qodercli.macos",
        "codex.windows",
        "claude-code.windows",
    }
    for adapter in ADAPTERS:
        covered = {
            *(rule.kind for rule in adapter.rules),
            registry.AssetKind.BINDING,
            *adapter.unsupported_kinds,
        }
        assert covered == set(registry.AssetKind)
        assert adapter.revision.startswith("sha256:")


def test_checked_in_compatibility_fixture_matches_adapter_contracts() -> None:
    """Root, version, format, and frontmatter fixtures cannot drift from code."""
    fixture = json.loads(
        (
            REPOSITORY_ROOT / "tests" / "fixtures" / "inventory" / "compatibility.json"
        ).read_text()
    )

    assert fixture["schema_version"] == 1
    assert set(fixture["adapters"]) == {adapter.adapter_id for adapter in ADAPTERS}
    for adapter in ADAPTERS:
        expected = fixture["adapters"][adapter.adapter_id]
        assert expected["product"] == adapter.product
        assert expected["fixture_version_prefixes"] == list(
            adapter.fixture_version_prefixes
        )
        assert expected["format_fingerprint"] == adapter.format_fingerprint
        assert expected["required_role_sets"] == [
            sorted(role_set) for role_set in adapter.required_role_sets
        ]
        skill_rules = [
            rule for rule in adapter.rules if rule.kind == registry.AssetKind.SKILL
        ]
        assert expected["skill_frontmatter"] == list(
            skill_rules[0].required_frontmatter
        )


def test_mac_codex_inventory_keeps_expected_and_live_ownership_separate(
    tmp_path: Path,
) -> None:
    """Registry authority never fabricates live managed provenance."""
    shared, bindings, evidence = _codex_fixture(tmp_path)

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    assert result.status == inventory.SnapshotStatus.PASS
    live_demo = next(
        claim
        for claim in result.claims
        if claim.claim_type == inventory.ClaimType.LIVE and claim.logical_key == "demo"
    )
    expected_demo = next(
        claim
        for claim in result.claims
        if claim.claim_type == inventory.ClaimType.EXPECTED
    )
    assert live_demo.ownership == inventory.Ownership.UNKNOWN_OWNER
    assert (
        expected_demo.desired_ownership == inventory.DesiredOwnership.ALMAGEST_MANAGED
    )
    assert expected_demo.presence == inventory.Presence.UNKNOWN
    assert any(
        claim.ownership == inventory.Ownership.EXTERNAL_OWNED
        and claim.logical_key == "github"
        for claim in result.claims
    )


def test_invalid_frontmatter_makes_coverage_partial_not_absent(
    tmp_path: Path,
) -> None:
    """Invalid live metadata cannot be translated into a missing assignment."""
    shared, bindings, evidence = _codex_fixture(tmp_path, valid_frontmatter=False)

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    assert result.status == inventory.SnapshotStatus.PARTIAL
    expected = next(
        claim
        for claim in result.claims
        if claim.claim_type == inventory.ClaimType.EXPECTED
    )
    assert expected.presence == inventory.Presence.UNKNOWN
    assert "missing" not in expected.finding_codes
    assert any(
        item.coverage == inventory.Coverage.PARTIAL
        and "invalid-frontmatter" in item.diagnostic_codes
        for item in result.coverage
    )


def test_unreadable_surface_makes_coverage_partial_not_absent(
    tmp_path: Path,
) -> None:
    """An escaped live root is an unknown observation, never a missing asset."""
    shared, bindings, evidence = _codex_fixture(tmp_path)
    skills_root = tmp_path / "user" / "skills"
    shutil.rmtree(skills_root)
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    skills_root.symlink_to(outside, target_is_directory=True)

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    expected = next(
        claim
        for claim in result.claims
        if claim.claim_type == inventory.ClaimType.EXPECTED
    )
    assert result.status == inventory.SnapshotStatus.PARTIAL
    assert expected.presence == inventory.Presence.UNKNOWN
    assert "missing" not in expected.finding_codes
    assert any(
        item.asset_kind == registry.AssetKind.SKILL
        and item.coverage == inventory.Coverage.PARTIAL
        and "symlink-target-outside-bindings" in item.diagnostic_codes
        for item in result.coverage
    )


def test_wrong_surface_type_is_partial_not_readable(tmp_path: Path) -> None:
    """A directory at an instruction-file locator fails closed."""
    shared, bindings, evidence = _codex_fixture(tmp_path)
    instructions = tmp_path / "user" / "AGENTS.md"
    instructions.unlink()
    instructions.mkdir()

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    assert result.status == inventory.SnapshotStatus.PARTIAL
    assert any(
        item.asset_kind == registry.AssetKind.INSTRUCTION
        and item.coverage == inventory.Coverage.PARTIAL
        and item.diagnostic_codes == ("invalid-surface-type",)
        for item in result.coverage
    )


def test_complete_missing_surface_can_derive_missing_assignment(
    tmp_path: Path,
) -> None:
    """Absent is legal only after every relevant surface is completely observed."""
    shared, bindings, evidence = _codex_fixture(tmp_path, skills_present=False)

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    expected = next(
        claim
        for claim in result.claims
        if claim.claim_type == inventory.ClaimType.EXPECTED
    )
    assert expected.presence == inventory.Presence.ABSENT
    assert expected.finding_codes == ("missing",)


def test_unverified_version_preserves_structural_facts_without_semantic_parse(
    tmp_path: Path,
) -> None:
    """Unknown versions remain partial and never claim semantic completeness."""
    shared, bindings, evidence = _codex_fixture(tmp_path)
    raw = json.loads(evidence.read_text())
    raw["consumers"]["mac.codex"]["version"] = "9.9.9"
    _write_json(evidence, raw)

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    assert result.status == inventory.SnapshotStatus.PARTIAL
    assert result.adapters[0].compatibility == (
        inventory.Compatibility.VERSION_UNVERIFIED
    )
    assert any(
        claim.claim_type == inventory.ClaimType.LIVE
        and claim.logical_key == "@surface"
        and claim.presence == inventory.Presence.PRESENT
        for claim in result.claims
    )
    assert not any(
        claim.logical_key == "demo" and claim.asset_kind == registry.AssetKind.MCP
        for claim in result.claims
    )


def test_qoder_duplicate_mcp_is_ambiguous_without_proven_precedence(
    tmp_path: Path,
) -> None:
    """Two proven physical definitions do not get a guessed winner."""
    roles = {"qoder.home": "qoder.user-home"}
    home = tmp_path / "qoder"
    home.mkdir()
    (home / "settings.json").write_text(
        '{"mcpServers": {"demo": {"command": "one"}}, "enabledPlugins": {}}',
        encoding="utf-8",
    )
    (home / "mcp.json").write_text(
        '{"mcpServers": {"demo": {"command": "two"}}}',
        encoding="utf-8",
    )
    shared = _write_json(
        tmp_path / "shared.json",
        _registry_document(
            platform="macos",
            consumer="qodercli",
            target_id="mac.qoder",
            roles=roles,
            with_skill=False,
        ),
    )
    bindings = _write_json(
        tmp_path / "bindings.json",
        _bindings(
            tmp_path,
            roles=roles,
            roots={"qoder.home": home},
            with_source=False,
        ),
    )
    evidence = _write_json(
        tmp_path / "evidence.json",
        _evidence(
            "mac.qoder",
            product="qodercli",
            version="1.0.47",
            fingerprint="qoder-config-v1",
        ),
    )

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    duplicates = [
        claim
        for claim in result.claims
        if claim.logical_key == "demo" and claim.asset_kind == registry.AssetKind.MCP
    ]
    assert len(duplicates) == 2
    assert all(
        claim.topology == inventory.Topology.DUPLICATE
        and claim.effective == inventory.EffectiveState.AMBIGUOUS
        for claim in duplicates
    )


def test_target_without_assignment_is_still_scanned(tmp_path: Path) -> None:
    """Target bindings are inventory scope even when desired assets are empty."""
    roles = {
        "codex.runtime": "codex.runtime-home",
        "codex.user": "codex.user-home",
    }
    runtime = tmp_path / "runtime"
    user = tmp_path / "user"
    runtime.mkdir()
    user.mkdir()
    (user / "skills" / "external").mkdir(parents=True)
    (user / "skills" / "external" / "SKILL.md").write_text(
        "---\nname: external\ndescription: external\n---\n",
        encoding="utf-8",
    )
    shared = _write_json(
        tmp_path / "shared.json",
        _registry_document(
            platform="macos",
            consumer="codex",
            target_id="mac.codex",
            roles=roles,
            with_skill=False,
        ),
    )
    bindings = _write_json(
        tmp_path / "bindings.json",
        _bindings(
            tmp_path,
            roles=roles,
            roots={"codex.runtime": runtime, "codex.user": user},
            with_source=False,
        ),
    )
    evidence = _write_json(
        tmp_path / "evidence.json",
        _evidence(
            "mac.codex",
            product="codex-cli",
            version="0.144.5",
            fingerprint="codex-config-v1",
        ),
    )

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    assert any(
        claim.logical_key == "external"
        and claim.ownership == inventory.Ownership.UNKNOWN_OWNER
        for claim in result.claims
    )


def test_duplicate_semantic_role_blocks_even_without_assignment(
    tmp_path: Path,
) -> None:
    """Adapter roots cannot depend on an ambiguous semantic role."""
    roles = {
        "codex.runtime.one": "codex.runtime-home",
        "codex.runtime.two": "codex.runtime-home",
        "codex.user": "codex.user-home",
    }
    runtime_one = tmp_path / "runtime-one"
    runtime_two = tmp_path / "runtime-two"
    user = tmp_path / "user"
    runtime_one.mkdir()
    runtime_two.mkdir()
    user.mkdir()
    shared = _write_json(
        tmp_path / "shared.json",
        _registry_document(
            platform="macos",
            consumer="codex",
            target_id="mac.codex",
            roles=roles,
            with_skill=False,
        ),
    )
    bindings = _write_json(
        tmp_path / "bindings.json",
        _bindings(
            tmp_path,
            roles=roles,
            roots={
                "codex.runtime.one": runtime_one,
                "codex.runtime.two": runtime_two,
                "codex.user": user,
            },
            with_source=False,
        ),
    )
    evidence = _write_json(
        tmp_path / "evidence.json",
        _evidence(
            "mac.codex",
            product="codex-cli",
            version="0.144.5",
            fingerprint="codex-config-v1",
        ),
    )

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    assert result.status == inventory.SnapshotStatus.BLOCK
    assert {item.code for item in result.diagnostics} == {
        "duplicate-target-binding-role"
    }
    assert result.adapters == ()


def test_windows_claude_fixture_is_not_live_proof(tmp_path: Path) -> None:
    """Cross-OS fixture behavior cannot masquerade as Windows host evidence."""
    roles = {
        "claude.home": "claude.user-home",
        "claude.state": "claude.state-file",
    }
    shared = _write_json(
        tmp_path / "shared.json",
        _registry_document(
            platform="windows",
            consumer="claude",
            target_id="win.claude",
            roles=roles,
            with_skill=False,
        ),
    )
    bindings = _write_json(
        tmp_path / "bindings.json",
        _bindings(
            tmp_path,
            roles=roles,
            roots={
                "claude.home": tmp_path / "unused-home",
                "claude.state": tmp_path / "unused-state",
            },
            with_source=False,
        ),
    )
    evidence = _write_json(
        tmp_path / "evidence.json",
        _evidence(
            "win.claude",
            product="claude-code",
            version="2.1.0",
            fingerprint="claude-code-config-v1",
            host_verified=False,
        ),
    )
    reader = MemoryReader(
        {
            ("claude.home", ""): inventory.ProbeKind.DIRECTORY,
            ("claude.home", "settings.json"): inventory.ProbeKind.FILE,
            ("claude.state", ""): inventory.ProbeKind.FILE,
        },
        texts={
            ("claude.home", "settings.json"): '{"hooks": {}, "enabledPlugins": {}}',
            ("claude.state", ""): '{"mcpServers": {}}',
        },
    )

    result = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.WINDOWS,
        reader_factory=lambda _roots, _allowed: reader,
    )

    assert result.status == inventory.SnapshotStatus.PARTIAL
    assert result.adapters[0].compatibility == (inventory.Compatibility.HOST_UNVERIFIED)
    assert reader.calls > 0


def test_windows_local_layer_blocks_before_reader_or_input_probe(
    tmp_path: Path,
) -> None:
    """Inventory enforces zero-probe/zero-leak independently of the CLI."""
    calls = 0

    def reader_factory(
        _roots: dict[str, Path], _allowed: tuple[Path, ...]
    ) -> MemoryReader:
        """Record an illegal reader construction.

        Args:
            _roots: Unused roots.
            _allowed: Unused source roots.

        Returns:
            Empty reader.
        """
        nonlocal calls
        calls += 1
        return MemoryReader({})

    result = inventory.scan_inventory(
        [tmp_path / "unread-shared.json"],
        host_bindings_path=tmp_path / "unread-bindings.json",
        consumer_evidence_path=tmp_path / "unread-evidence.json",
        local_paths=[tmp_path / f"{SECRET_SENTINEL}-local.json"],
        platform=registry.Platform.WINDOWS,
        reader_factory=reader_factory,
    )

    report = json.dumps(result.report())
    assert result.status == inventory.SnapshotStatus.BLOCK
    assert calls == 0
    assert SECRET_SENTINEL not in report
    assert result.claims == ()
    assert result.coverage == ()


def test_snapshot_is_deterministic_and_report_never_contains_values_or_paths(
    tmp_path: Path,
) -> None:
    """Repeated inventory fixes facts without echoing raw configuration."""
    shared, bindings, evidence = _codex_fixture(tmp_path)

    first = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )
    second = inventory.scan_inventory(
        [shared],
        host_bindings_path=bindings,
        consumer_evidence_path=evidence,
        platform=registry.Platform.MACOS,
    )

    first_report = json.dumps(first.report())
    assert first.inventory_revision == second.inventory_revision
    assert str(tmp_path) not in first_report
    assert "secret-command" not in first_report
    assert "secret-hook" not in first_report


def test_inventory_cli_returns_stable_json_and_nonzero_for_partial(
    tmp_path: Path,
) -> None:
    """Operator CLI exposes the same machine contract and exit semantics."""
    shared, bindings, evidence = _codex_fixture(tmp_path)
    raw = json.loads(evidence.read_text())
    raw["consumers"]["mac.codex"]["host_verified"] = False
    _write_json(evidence, raw)

    result = runner.invoke(
        app,
        [
            "inventory",
            "scan",
            "--shared",
            str(shared),
            "--host-bindings",
            str(bindings),
            "--consumer-evidence",
            str(evidence),
            "--json",
        ],
    )

    assert result.exit_code == 1
    report = json.loads(result.stdout)
    assert report["status"] == "partial"
    assert report["adapters"][0]["compatibility"] == "host-unverified"
