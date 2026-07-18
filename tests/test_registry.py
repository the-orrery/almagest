from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from typer.testing import CliRunner

from almagest import registry
from almagest.cli import app

REVISION_A = "a" * 40
REVISION_B = "b" * 40
SECRET_SENTINEL = "must-never-appear"
runner = CliRunner()
REPOSITORY_ROOT = Path(__file__).parent.parent


def _shared_document() -> dict:
    """Return a complete portable Windows registry layer."""
    return {
        "schema_version": 1,
        "layer": {"residency": "shared"},
        "sources": {
            "personal-source": {
                "repository": "personal/skill-vault",
                "revision": {"kind": "git-commit", "value": REVISION_A},
                "residency": "shared",
                "authority": "authored-owned",
            }
        },
        "hosts": {"win": {"platform": "windows"}},
        "targets": {
            "win.codex": {
                "host": "win",
                "consumer": "codex",
                "bindings": ["win.codex.skills-root"],
            },
            "win.claude": {
                "host": "win",
                "consumer": "claude",
                "bindings": ["win.claude.skills-root"],
            },
        },
        "bindings": {
            "win.codex.skills-root": {
                "host": "win",
                "kind": "path",
                "role": "codex.user-home",
            },
            "win.claude.skills-root": {
                "host": "win",
                "kind": "path",
                "role": "claude.user-home",
            },
        },
        "assets": {
            "skill.demo": {
                "kind": "skill",
                "source": {
                    "source": "personal-source",
                    "path": "skills/demo",
                },
                "mutation_authority": "almagest-managed",
            }
        },
        "assignments": {
            "skill.demo@win.codex": {
                "asset": "skill.demo",
                "target": "win.codex",
            },
            "skill.demo@win.claude": {
                "asset": "skill.demo",
                "target": "win.claude",
            },
        },
    }


def _local_document() -> dict:
    """Return a Mac-local layer that assigns shared and work assets."""
    return {
        "schema_version": 1,
        "layer": {"residency": "mac-local", "host": "mac"},
        "sources": {
            "work-source": {
                "repository": "work/skill-vault",
                "revision": {"kind": "git-commit", "value": REVISION_B},
                "residency": "mac-local-work",
                "authority": "authored-owned",
                "host": "mac",
            }
        },
        "hosts": {"mac": {"platform": "macos"}},
        "targets": {
            "mac.codex": {
                "host": "mac",
                "consumer": "codex",
                "bindings": ["mac.codex.skills-root"],
            },
            "mac.qoder": {
                "host": "mac",
                "consumer": "qodercli",
                "bindings": ["mac.qoder.skills-root"],
            },
        },
        "bindings": {
            "mac.codex.skills-root": {
                "host": "mac",
                "kind": "path",
                "role": "codex.user-home",
            },
            "mac.qoder.skills-root": {
                "host": "mac",
                "kind": "path",
                "role": "qoder.user-home",
            },
        },
        "assets": {
            "skill.work": {
                "kind": "skill",
                "source": {"source": "work-source", "path": "skills/work"},
                "mutation_authority": "almagest-managed",
            }
        },
        "assignments": {
            "skill.demo@mac.codex": {
                "asset": "skill.demo",
                "target": "mac.codex",
            },
            "skill.demo@mac.qoder": {
                "asset": "skill.demo",
                "target": "mac.qoder",
            },
            "skill.work@mac.codex": {
                "asset": "skill.work",
                "target": "mac.codex",
            },
            "skill.work@mac.qoder": {
                "asset": "skill.work",
                "target": "mac.qoder",
            },
        },
    }


def _write_json(path: Path, value: object) -> Path:
    """Write one deterministic JSON fixture and return its path."""
    path.write_text(json.dumps(value))
    return path


def _windows_bindings(tmp_path: Path) -> dict:
    """Return complete Windows host-local roots and bindings."""
    source_root = tmp_path / "personal-source"
    source_root.mkdir(exist_ok=True)
    return {
        "schema_version": 1,
        "host": "win",
        "source_roots": {"personal/skill-vault": str(source_root)},
        "bindings": {
            "win.codex.skills-root": {
                "kind": "path",
                "path": str(tmp_path / "codex-skills"),
            },
            "win.claude.skills-root": {
                "kind": "path",
                "path": str(tmp_path / "claude-skills"),
            },
        },
    }


def _mac_bindings(tmp_path: Path) -> dict:
    """Return complete Mac host-local roots and bindings."""
    personal_root = tmp_path / "personal-source"
    work_root = tmp_path / "work-source"
    personal_root.mkdir(exist_ok=True)
    work_root.mkdir(exist_ok=True)
    return {
        "schema_version": 1,
        "host": "mac",
        "source_roots": {
            "personal/skill-vault": str(personal_root),
            "work/skill-vault": str(work_root),
        },
        "bindings": {
            "mac.codex.skills-root": {
                "kind": "path",
                "path": str(tmp_path / "codex-skills"),
            },
            "mac.qoder.skills-root": {
                "kind": "path",
                "path": str(tmp_path / "qoder-skills"),
            },
        },
    }


def _codes(result: registry.RegistryCheck) -> set[str]:
    """Return stable diagnostic codes from one result."""
    return {diagnostic.code for diagnostic in result.diagnostics}


def test_checked_in_registry_examples_match_the_public_schema() -> None:
    """Checked-in examples remain executable schema fixtures."""
    shared = REPOSITORY_ROOT / "registry.shared.json.example"
    local = REPOSITORY_ROOT / "registry.mac-local.json.example"

    mac_result = registry.load_registry(
        [shared],
        local_paths=[local],
        platform=registry.Platform.MACOS,
    )
    windows_result = registry.load_registry(
        [shared],
        platform=registry.Platform.WINDOWS,
    )
    mac_bindings = registry.HostBindings.model_validate_json(
        (REPOSITORY_ROOT / "host-bindings.macos.json.example").read_text()
    )
    windows_bindings = registry.HostBindings.model_validate_json(
        (REPOSITORY_ROOT / "host-bindings.windows.json.example").read_text()
    )

    assert mac_result.ok
    assert windows_result.ok
    assert mac_bindings.host == "mac"
    assert windows_bindings.host == "win"


def test_shared_and_mac_local_layers_validate_without_leaking_authority(
    tmp_path: Path,
) -> None:
    """Mac may add a local work layer while shared remains independently closed."""
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    local = _write_json(tmp_path / "local.json", _local_document())
    bindings = _write_json(tmp_path / "bindings.json", _mac_bindings(tmp_path))

    result = registry.check_registry(
        [shared],
        local_paths=[local],
        host_bindings_path=bindings,
        platform=registry.Platform.MACOS,
    )

    assert result.ok
    assert result.catalog is not None
    assert len(result.catalog.assets) == 2
    assert result.catalog.revision.startswith("sha256:")


def test_windows_rejects_local_layer_before_reading_it(tmp_path: Path) -> None:
    """A nonexistent local path proves the Windows no-probe branch never opens it."""
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    local = tmp_path / f"{SECRET_SENTINEL}-does-not-exist.json"

    result = registry.load_registry(
        [shared],
        local_paths=[local],
        platform=registry.Platform.WINDOWS,
    )

    assert _codes(result) == {"forbidden-local-layer"}
    assert SECRET_SENTINEL not in json.dumps(result.report())
    assert result.report()["summary"] == {}


def test_shared_layer_rejects_work_data_and_local_references(tmp_path: Path) -> None:
    """Shared input must be transitively closed over shared definitions."""
    raw = _shared_document()
    raw["sources"]["work-source"] = {
        "repository": "work/private",
        "revision": {"kind": "git-commit", "value": REVISION_B},
        "residency": "mac-local-work",
        "authority": "authored-owned",
        "host": "mac",
    }
    raw["assets"]["skill.demo"]["source"]["source"] = "local-only-source"
    shared = _write_json(tmp_path / "shared.json", raw)

    result = registry.load_registry([shared], platform=registry.Platform.WINDOWS)

    assert "shared-layer-work-data" in _codes(result)
    assert "shared-layer-not-closed" in _codes(result)
    report = json.dumps(result.report())
    assert "work/private" not in report
    assert "local-only-source" not in report


def test_work_asset_cannot_target_windows(tmp_path: Path) -> None:
    """Mac-local authored source cannot gain a Windows assignment."""
    local_raw = _local_document()
    local_raw["assignments"]["skill.work@win"] = {
        "asset": "skill.work",
        "target": "win.codex",
    }
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    local = _write_json(tmp_path / "local.json", local_raw)

    result = registry.load_registry(
        [shared],
        local_paths=[local],
        platform=registry.Platform.MACOS,
    )

    assert "work-residency-violation" in _codes(result)
    report = json.dumps(result.report())
    assert "skill.work" not in report
    assert REVISION_B not in report


@pytest.mark.parametrize(
    "kind",
    [
        "skill",
        "mcp",
        "instruction",
        "settings",
        "profile",
        "hook",
        "plugin",
        "selector",
        "binding",
    ],
)
def test_registry_accepts_every_managed_asset_kind(tmp_path: Path, kind: str) -> None:
    """The registry covers all confirmed Agent configuration domains."""
    raw = _shared_document()
    raw["assets"]["skill.demo"]["kind"] = kind
    shared = _write_json(tmp_path / f"{kind}.json", raw)

    result = registry.load_registry([shared], platform=registry.Platform.WINDOWS)

    assert result.ok


def test_catalog_revision_is_order_stable_and_revision_sensitive(
    tmp_path: Path,
) -> None:
    """JSON order is irrelevant, while an authored source revision is not."""
    first_raw = _shared_document()
    reordered = deepcopy(first_raw)
    reordered["targets"] = dict(reversed(list(reordered["targets"].items())))
    reordered["assignments"] = dict(reversed(list(reordered["assignments"].items())))
    changed = deepcopy(first_raw)
    changed["sources"]["personal-source"]["revision"]["value"] = "c" * 40
    first = _write_json(tmp_path / "first.json", first_raw)
    second = _write_json(tmp_path / "second.json", reordered)
    third = _write_json(tmp_path / "third.json", changed)

    one = registry.load_registry([first], platform=registry.Platform.WINDOWS)
    two = registry.load_registry([second], platform=registry.Platform.WINDOWS)
    three = registry.load_registry([third], platform=registry.Platform.WINDOWS)

    assert one.ok and two.ok and three.ok
    assert one.catalog is not None
    assert two.catalog is not None
    assert three.catalog is not None
    assert one.catalog.revision == two.catalog.revision
    assert one.catalog.revision != three.catalog.revision
    assert "skill.demo" in one.catalog.assets


def test_invalid_revision_path_and_cross_document_collision_block(
    tmp_path: Path,
) -> None:
    """Unstable revisions, parent traversal, and duplicate identities fail closed."""
    first_raw = _shared_document()
    first_raw["sources"]["personal-source"]["revision"]["value"] = "floating-head"
    first_raw["assets"]["skill.demo"]["source"]["path"] = "../private"
    second_raw = _shared_document()
    first = _write_json(tmp_path / "first.json", first_raw)
    second = _write_json(tmp_path / "second.json", second_raw)

    result = registry.load_registry(
        [first, second],
        platform=registry.Platform.WINDOWS,
    )

    assert {
        "registry-id-collision",
        "invalid-source-revision",
        "invalid-asset-source",
    }.issubset(_codes(result))


def test_repository_identity_cannot_smuggle_a_host_path(tmp_path: Path) -> None:
    """A portable source key cannot contain an authored machine path."""
    raw = _shared_document()
    raw["sources"]["personal-source"]["repository"] = "c:/private/secret-source"
    shared = _write_json(tmp_path / "shared.json", raw)

    result = registry.load_registry(
        [shared],
        platform=registry.Platform.WINDOWS,
    )

    assert "invalid-source-repository" in _codes(result)
    assert "c:/private/secret-source" not in json.dumps(result.report())


def test_local_assignment_cannot_target_another_host(tmp_path: Path) -> None:
    """A local layer may add only assignments for its declared Mac host."""
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    raw = _local_document()
    raw["assignments"]["skill.work@mac.codex"]["target"] = "win.codex"
    local = _write_json(tmp_path / "local.json", raw)

    result = registry.load_registry(
        [shared],
        local_paths=[local],
        platform=registry.Platform.MACOS,
    )

    assert "local-layer-assignment-boundary" in _codes(result)


def test_missing_root_and_symlink_escape_are_stable_source_diagnostics(
    tmp_path: Path,
) -> None:
    """Registry host validation reuses the legacy source-root escape guard."""
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    raw_bindings = _windows_bindings(tmp_path)
    raw_bindings["source_roots"] = {}
    missing = _write_json(tmp_path / "missing.json", raw_bindings)

    missing_result = registry.check_registry(
        [shared],
        host_bindings_path=missing,
        platform=registry.Platform.WINDOWS,
    )

    assert "missing-source-root" in _codes(missing_result)
    assert len(missing_result.report()["diagnostics"]) == 1

    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "skills").symlink_to(outside, target_is_directory=True)
    escape_bindings = _windows_bindings(tmp_path)
    escape_bindings["source_roots"] = {"personal/skill-vault": str(root)}
    escape = _write_json(tmp_path / "escape.json", escape_bindings)

    escape_result = registry.check_registry(
        [shared],
        host_bindings_path=escape,
        platform=registry.Platform.WINDOWS,
    )

    assert "source-path-escape" in _codes(escape_result)


def test_source_resolution_failure_is_a_safe_diagnostic(tmp_path: Path) -> None:
    """Filesystem resolution errors block without escaping the safe envelope."""
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    root = tmp_path / "loop-root"
    root.mkdir()
    (root / "skills").symlink_to(root / "skills", target_is_directory=True)
    raw = _windows_bindings(tmp_path)
    raw["source_roots"] = {"personal/skill-vault": str(root)}
    bindings = _write_json(tmp_path / "bindings.json", raw)

    result = registry.check_registry(
        [shared],
        host_bindings_path=bindings,
        platform=registry.Platform.WINDOWS,
    )

    assert "source-resolution-failed" in _codes(result)
    assert str(root) not in json.dumps(result.report())


def test_missing_and_mismatched_host_bindings_block(tmp_path: Path) -> None:
    """Typed host-local requirements cannot be absent or silently coerced."""
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    raw = _windows_bindings(tmp_path)
    del raw["bindings"]["win.codex.skills-root"]
    raw["bindings"]["win.claude.skills-root"] = {
        "kind": "account",
        "account": "demo",
    }
    bindings = _write_json(tmp_path / "bindings.json", raw)

    result = registry.check_registry(
        [shared],
        host_bindings_path=bindings,
        platform=registry.Platform.WINDOWS,
    )

    assert {"missing-host-binding", "host-binding-mismatch"}.issubset(_codes(result))


def test_current_host_platform_and_local_layer_host_must_match(
    tmp_path: Path,
) -> None:
    """Host bindings cannot select another platform or another Mac overlay."""
    shared_raw = _shared_document()
    shared_raw["hosts"]["mac2"] = {"platform": "macos"}
    shared = _write_json(tmp_path / "shared.json", shared_raw)
    local = _write_json(tmp_path / "local.json", _local_document())
    windows_bindings = _write_json(
        tmp_path / "windows-bindings.json",
        _windows_bindings(tmp_path),
    )
    mac2_bindings_raw = _mac_bindings(tmp_path)
    mac2_bindings_raw["host"] = "mac2"
    mac2_bindings = _write_json(
        tmp_path / "mac2-bindings.json",
        mac2_bindings_raw,
    )

    platform_mismatch = registry.check_registry(
        [shared],
        host_bindings_path=windows_bindings,
        platform=registry.Platform.MACOS,
    )
    local_host_mismatch = registry.check_registry(
        [shared],
        local_paths=[local],
        host_bindings_path=mac2_bindings,
        platform=registry.Platform.MACOS,
    )

    assert _codes(platform_mismatch) == {"host-platform-mismatch"}
    assert _codes(local_host_mismatch) == {"local-layer-host-mismatch"}


def test_host_paths_and_source_roots_must_be_declared_and_absolute(
    tmp_path: Path,
) -> None:
    """Host-local values reject CWD-relative and unknown root declarations."""
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    raw = _windows_bindings(tmp_path)
    raw["source_roots"]["personal/skill-vault"] = "relative/source"
    raw["source_roots"]["unknown/source"] = str(tmp_path / "unknown")
    raw["bindings"]["win.codex.skills-root"]["path"] = "relative/skills"
    bindings = _write_json(tmp_path / "bindings.json", raw)

    result = registry.check_registry(
        [shared],
        host_bindings_path=bindings,
        platform=registry.Platform.WINDOWS,
    )

    assert {
        "invalid-host-path",
        "invalid-source-root",
        "missing-source-root",
        "unknown-source-root",
    }.issubset(_codes(result))


def test_inline_secret_and_unknown_fields_never_echo_input(tmp_path: Path) -> None:
    """Strict host-binding errors return only an allowlisted safe envelope."""
    shared_raw = _shared_document()
    shared_raw["bindings"]["win.codex.secret"] = {
        "host": "win",
        "kind": "secret-ref",
        "role": "secret.mcp",
    }
    shared_raw["targets"]["win.codex"]["bindings"].append("win.codex.secret")
    shared = _write_json(tmp_path / "shared.json", shared_raw)
    raw = _windows_bindings(tmp_path)
    raw["bindings"]["win.codex.secret"] = {
        "kind": "secret-ref",
        "provider": "vault",
        "reference": "agent/token",
        "value": SECRET_SENTINEL,
    }
    bindings = _write_json(tmp_path / "bindings.json", raw)

    result = registry.check_registry(
        [shared],
        host_bindings_path=bindings,
        platform=registry.Platform.WINDOWS,
    )

    report = json.dumps(result.report())
    assert _codes(result) == {"invalid-host-bindings"}
    assert SECRET_SENTINEL not in report
    assert "agent/token" not in report


def test_duplicate_key_unknown_field_and_version_have_stable_codes(
    tmp_path: Path,
) -> None:
    """Malformed registry documents fail without serializing validation input."""
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text(
        '{"schema_version":1,"schema_version":1,"layer":{"residency":"shared"}}'
    )
    unknown_raw = _shared_document()
    unknown_raw["unexpected"] = SECRET_SENTINEL
    unknown = _write_json(tmp_path / "unknown.json", unknown_raw)
    version_raw = _shared_document()
    version_raw["schema_version"] = 2
    version = _write_json(tmp_path / "version.json", version_raw)

    duplicate_result = registry.load_registry(
        [duplicate], platform=registry.Platform.WINDOWS
    )
    unknown_result = registry.load_registry(
        [unknown], platform=registry.Platform.WINDOWS
    )
    version_result = registry.load_registry(
        [version], platform=registry.Platform.WINDOWS
    )

    assert _codes(duplicate_result) == {"duplicate-json-key"}
    assert _codes(unknown_result) == {"invalid-registry-schema"}
    assert _codes(version_result) == {"unsupported-registry-version"}
    assert SECRET_SENTINEL not in json.dumps(unknown_result.report())


def test_registry_validate_cli_returns_stable_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The Agent-facing CLI exposes the same safe validation envelope."""
    shared = _write_json(tmp_path / "shared.json", _shared_document())
    bindings = _write_json(
        tmp_path / "bindings.json",
        _windows_bindings(tmp_path),
    )
    monkeypatch.setattr(registry.runtime_platform, "system", lambda: "Windows")

    result = runner.invoke(
        app,
        [
            "registry",
            "validate",
            "--shared",
            str(shared),
            "--host-bindings",
            str(bindings),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stdout
    report = json.loads(result.stdout)
    assert report["status"] == "pass"
    assert report["summary"]["assets"] == 1
    assert report["registry_revision"].startswith("sha256:")
