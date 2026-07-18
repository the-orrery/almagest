"""Portable Agent configuration registry and host-local validation.

The registry is authored state only. It does not discover live configuration,
render consumer formats, or prove that a declared source revision is currently
materialized on disk.
"""

from __future__ import annotations

import hashlib
import json
import platform as runtime_platform
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from almagest.source import SourceRef, resolve_source

REGISTRY_SCHEMA_VERSION = 1
HOST_BINDINGS_SCHEMA_VERSION = 1
STABLE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._:/@-]*$")
REPOSITORY_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*(?:/[a-z0-9][a-z0-9._-]*)*$")
GIT_REVISION_PATTERN = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class StrictModel(BaseModel):
    """Reject unknown fields so configuration drift fails closed."""

    model_config = ConfigDict(extra="forbid")


class Platform(StrEnum):
    """Supported host operating systems."""

    MACOS = "macos"
    WINDOWS = "windows"


class LayerResidency(StrEnum):
    """Physical registry-document residency."""

    SHARED = "shared"
    MAC_LOCAL = "mac-local"


class SourceResidency(StrEnum):
    """Where authored source metadata is allowed to exist."""

    SHARED = "shared"
    MAC_LOCAL_WORK = "mac-local-work"


class Consumer(StrEnum):
    """Consumers in the confirmed product scope."""

    CODEX = "codex"
    QODERCLI = "qodercli"
    CLAUDE = "claude"


class AssetKind(StrEnum):
    """Agent configuration domains governed by the registry."""

    SKILL = "skill"
    MCP = "mcp"
    INSTRUCTION = "instruction"
    SETTINGS = "settings"
    PROFILE = "profile"
    HOOK = "hook"
    PLUGIN = "plugin"
    SELECTOR = "selector"
    BINDING = "binding"


class RevisionKind(StrEnum):
    """Immutable revision declaration formats."""

    GIT_COMMIT = "git-commit"
    SHA256 = "sha256"


class BindingKind(StrEnum):
    """Host-local binding categories."""

    PATH = "path"
    ACCOUNT = "account"
    SECRET_REF = "secret-ref"


class LayerSpec(StrictModel):
    """Declare the trust boundary of one physical registry document."""

    residency: LayerResidency
    host: str | None = None


class SourceRevision(StrictModel):
    """Declare an immutable authored revision without resolving its content."""

    kind: RevisionKind
    value: str = Field(min_length=1)


class RegistrySource(StrictModel):
    """Declare one revision-pinned portable source repository."""

    repository: str = Field(min_length=1)
    revision: SourceRevision
    residency: SourceResidency
    authority: Literal["authored-owned"]
    host: str | None = None


class RegistryHost(StrictModel):
    """Declare one host identity without granting it source authority."""

    platform: Platform


class RegistryTarget(StrictModel):
    """Declare one consumer instance on one host."""

    host: str = Field(min_length=1)
    consumer: Consumer
    bindings: list[str] = Field(default_factory=list)


class BindingDeclaration(StrictModel):
    """Declare a typed host-local value required by a target or assignment."""

    host: str = Field(min_length=1)
    kind: BindingKind
    role: str = Field(min_length=1)


class AssetSource(StrictModel):
    """Reference a source revision and a portable path within its repository."""

    source: str = Field(min_length=1)
    path: str = Field(min_length=1)


class RegistryAsset(StrictModel):
    """Declare one logical Agent configuration asset."""

    kind: AssetKind
    source: AssetSource
    mutation_authority: Literal["almagest-managed"]


class RegistryAssignment(StrictModel):
    """Assign one logical asset to one consumer target."""

    asset: str = Field(min_length=1)
    target: str = Field(min_length=1)
    bindings: list[str] = Field(default_factory=list)


class RegistryDocument(StrictModel):
    """Represent one physical portable or Mac-local registry layer."""

    schema_version: Literal[REGISTRY_SCHEMA_VERSION]
    layer: LayerSpec
    sources: dict[str, RegistrySource] = Field(default_factory=dict)
    hosts: dict[str, RegistryHost] = Field(default_factory=dict)
    targets: dict[str, RegistryTarget] = Field(default_factory=dict)
    bindings: dict[str, BindingDeclaration] = Field(default_factory=dict)
    assets: dict[str, RegistryAsset] = Field(default_factory=dict)
    assignments: dict[str, RegistryAssignment] = Field(default_factory=dict)


class PathBindingValue(StrictModel):
    """Resolve a host-local filesystem binding."""

    kind: Literal[BindingKind.PATH]
    path: str = Field(min_length=1)


class AccountBindingValue(StrictModel):
    """Resolve a host-local account selector without storing credentials."""

    kind: Literal[BindingKind.ACCOUNT]
    account: str = Field(min_length=1)


class SecretRefBindingValue(StrictModel):
    """Resolve a secret-provider reference, never an inline secret value."""

    kind: Literal[BindingKind.SECRET_REF]
    provider: str = Field(min_length=1)
    reference: str = Field(min_length=1)


BindingValue = Annotated[
    PathBindingValue | AccountBindingValue | SecretRefBindingValue,
    Field(discriminator="kind"),
]


class HostBindings(StrictModel):
    """Resolve source roots and typed values for one current host."""

    schema_version: Literal[HOST_BINDINGS_SCHEMA_VERSION]
    host: str = Field(min_length=1)
    source_roots: dict[str, str] = Field(default_factory=dict)
    bindings: dict[str, BindingValue] = Field(default_factory=dict)


class RegistryDiagnostic(StrictModel):
    """Return a stable, allowlisted error without echoing configuration input."""

    code: str
    scope: Literal["loader", "layer", "registry", "host", "source", "binding"]
    severity: Literal["block"] = "block"


@dataclass(frozen=True)
class RegistryCatalog:
    """Hold the assembled authored catalog and its deterministic revision."""

    layers: tuple[LayerSpec, ...]
    sources: dict[str, RegistrySource]
    hosts: dict[str, RegistryHost]
    targets: dict[str, RegistryTarget]
    bindings: dict[str, BindingDeclaration]
    assets: dict[str, RegistryAsset]
    assignments: dict[str, RegistryAssignment]
    revision: str


@dataclass(frozen=True)
class RegistryCheck:
    """Hold a safe validation result for library and CLI consumers."""

    catalog: RegistryCatalog | None
    diagnostics: tuple[RegistryDiagnostic, ...]
    host_bindings: HostBindings | None = None

    @property
    def ok(self) -> bool:
        """Return whether no fail-closed diagnostic exists.

        Returns:
            ``True`` only when a catalog was assembled and no diagnostic exists.
        """
        return self.catalog is not None and not self.diagnostics

    @property
    def normalized_diagnostics(self) -> tuple[RegistryDiagnostic, ...]:
        """Return de-duplicated diagnostics in deterministic order.

        Returns:
            Diagnostics sorted by safe envelope fields, independent of document
            and assignment traversal order.
        """
        values = {
            (diagnostic.code, diagnostic.scope, diagnostic.severity)
            for diagnostic in self.diagnostics
        }
        return tuple(
            RegistryDiagnostic(code=code, scope=scope, severity=severity)
            for code, scope, severity in sorted(values)
        )

    def report(self) -> dict[str, object]:
        """Build the stable JSON-safe validation envelope.

        Returns:
            A report containing only counts, a catalog revision, and allowlisted
            diagnostics. Entity identifiers and local values are never included.
        """
        summary: dict[str, int] = {}
        revision: str | None = None
        if self.catalog is not None:
            revision = self.catalog.revision
            summary = {
                "layers": len(self.catalog.layers),
                "sources": len(self.catalog.sources),
                "hosts": len(self.catalog.hosts),
                "targets": len(self.catalog.targets),
                "bindings": len(self.catalog.bindings),
                "assets": len(self.catalog.assets),
                "assignments": len(self.catalog.assignments),
            }
        return {
            "schema_version": 1,
            "status": "pass" if self.ok else "block",
            "registry_revision": revision,
            "summary": summary,
            "diagnostics": [
                diagnostic.model_dump(mode="json")
                for diagnostic in self.normalized_diagnostics
            ],
        }


class DuplicateJsonKeyError(ValueError):
    """Signal a duplicate JSON object key without preserving the sensitive key."""


def current_platform() -> Platform:
    """Return the supported runtime platform.

    Returns:
        ``macos`` or ``windows``.

    Raises:
        RuntimeError: The current operating system is outside the product scope.
    """
    name = runtime_platform.system()
    if name == "Darwin":
        return Platform.MACOS
    if name == "Windows":
        return Platform.WINDOWS
    raise RuntimeError("unsupported host platform")


def _diagnostic(
    code: str,
    scope: Literal["loader", "layer", "registry", "host", "source", "binding"],
) -> RegistryDiagnostic:
    """Create one safe blocking diagnostic.

    Args:
        code: Stable machine-readable error code.
        scope: Coarse non-sensitive subsystem location.

    Returns:
        A blocking diagnostic.
    """
    return RegistryDiagnostic(code=code, scope=scope)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a JSON object while rejecting duplicate keys.

    Args:
        pairs: Ordered key-value pairs produced by ``json.loads``.

    Returns:
        A dictionary when all keys are unique.

    Raises:
        DuplicateJsonKeyError: Any duplicate key is present.
    """
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError
        result[key] = value
    return result


def _read_json(path: Path) -> tuple[object | None, RegistryDiagnostic | None]:
    """Read strict JSON without exposing paths or input in diagnostics.

    Args:
        path: Explicit registry or host-binding document path.

    Returns:
        Parsed JSON and no diagnostic, or ``None`` plus a safe diagnostic.
    """
    try:
        raw = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except DuplicateJsonKeyError:
        return None, _diagnostic("duplicate-json-key", "loader")
    except (json.JSONDecodeError, UnicodeError):
        return None, _diagnostic("invalid-json", "loader")
    except OSError:
        return None, _diagnostic("unreadable-document", "loader")
    return raw, None


def _load_document(
    path: Path,
    *,
    expected_layer: LayerResidency,
) -> tuple[RegistryDocument | None, RegistryDiagnostic | None]:
    """Load one document under an already trusted physical-layer policy.

    Args:
        path: Explicit registry document path.
        expected_layer: Layer class assigned by the trusted caller.

    Returns:
        A strict model or one safe diagnostic.
    """
    raw, diagnostic = _read_json(path)
    if diagnostic is not None:
        return None, diagnostic
    if not isinstance(raw, dict):
        return None, _diagnostic("invalid-registry-schema", "loader")
    if raw.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        return None, _diagnostic("unsupported-registry-version", "loader")
    layer = raw.get("layer")
    if not isinstance(layer, dict) or layer.get("residency") != expected_layer:
        return None, _diagnostic("forbidden-registry-layer", "layer")
    try:
        return RegistryDocument.model_validate(raw), None
    except ValidationError:
        return None, _diagnostic("invalid-registry-schema", "loader")


def _load_host_bindings(
    path: Path,
) -> tuple[HostBindings | None, RegistryDiagnostic | None]:
    """Load one strict host-local binding document.

    Args:
        path: Explicit host-binding document path.

    Returns:
        A strict model or one safe diagnostic.
    """
    raw, diagnostic = _read_json(path)
    if diagnostic is not None:
        return None, diagnostic
    if not isinstance(raw, dict):
        return None, _diagnostic("invalid-host-bindings", "binding")
    if raw.get("schema_version") != HOST_BINDINGS_SCHEMA_VERSION:
        return None, _diagnostic("unsupported-host-bindings-version", "binding")
    try:
        return HostBindings.model_validate(raw), None
    except ValidationError:
        return None, _diagnostic("invalid-host-bindings", "binding")


def _stable_id(value: str) -> bool:
    """Check one explicit logical identifier.

    Args:
        value: Candidate map key or reference.

    Returns:
        Whether it uses the portable stable-ID alphabet.
    """
    return STABLE_ID_PATTERN.fullmatch(value) is not None


def _portable_path(value: str) -> bool:
    """Check a consumer-neutral relative path.

    Args:
        value: Path declared inside an authored asset.

    Returns:
        Whether it is non-absolute, POSIX-like, and contains no parent traversal.
    """
    if (
        not value
        or any(character in value for character in ("\\", ":", "\0"))
        or value.startswith("/")
    ):
        return False
    return all(part not in {"", ".", ".."} for part in value.split("/"))


def _repository_identity(value: str) -> bool:
    """Check one portable repository identity.

    Args:
        value: Authored repository identity used as a host-root lookup key.

    Returns:
        Whether the identity is portable and cannot be mistaken for a host path.
    """
    return REPOSITORY_ID_PATTERN.fullmatch(value) is not None


def _revision_valid(revision: SourceRevision) -> bool:
    """Validate an immutable revision declaration's shape.

    Args:
        revision: Declared source revision.

    Returns:
        Whether the value is a full Git object ID or SHA-256 digest.
    """
    if revision.kind == RevisionKind.GIT_COMMIT:
        return GIT_REVISION_PATTERN.fullmatch(revision.value) is not None
    return SHA256_PATTERN.fullmatch(revision.value) is not None


def _canonicalize(value: object) -> object:
    """Normalize maps and semantically unordered lists for hashing.

    Args:
        value: JSON-compatible model dump.

    Returns:
        Canonically ordered JSON-compatible data.
    """
    if isinstance(value, dict):
        return {key: _canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        items = [_canonicalize(item) for item in value]
        return sorted(
            items,
            key=lambda item: json.dumps(
                item, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ),
        )
    return value


def _catalog_revision(
    *,
    layers: tuple[LayerSpec, ...],
    sources: dict[str, RegistrySource],
    hosts: dict[str, RegistryHost],
    targets: dict[str, RegistryTarget],
    bindings: dict[str, BindingDeclaration],
    assets: dict[str, RegistryAsset],
    assignments: dict[str, RegistryAssignment],
) -> str:
    """Hash only portable authored state.

    Args:
        layers: Physical layer declarations.
        sources: Assembled source declarations.
        hosts: Assembled host declarations.
        targets: Assembled target declarations.
        bindings: Assembled binding declarations.
        assets: Assembled asset declarations.
        assignments: Assembled target assignments.

    Returns:
        A ``sha256:<hex>`` catalog revision. Resolved paths and local values are
        absent by construction.
    """
    payload = {
        "layers": [layer.model_dump(mode="json") for layer in layers],
        "sources": {
            key: value.model_dump(mode="json") for key, value in sources.items()
        },
        "hosts": {key: value.model_dump(mode="json") for key, value in hosts.items()},
        "targets": {
            key: value.model_dump(mode="json") for key, value in targets.items()
        },
        "bindings": {
            key: value.model_dump(mode="json") for key, value in bindings.items()
        },
        "assets": {key: value.model_dump(mode="json") for key, value in assets.items()},
        "assignments": {
            key: value.model_dump(mode="json") for key, value in assignments.items()
        },
    }
    encoded = json.dumps(
        _canonicalize(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _merge_maps(
    documents: list[RegistryDocument],
    field: Literal["sources", "hosts", "targets", "bindings", "assets", "assignments"],
    diagnostics: list[RegistryDiagnostic],
) -> dict[str, object]:
    """Merge one keyed collection and reject cross-document identity collisions.

    Args:
        documents: Parsed registry documents.
        field: Registry collection to assemble.
        diagnostics: Mutable safe diagnostic accumulator.

    Returns:
        Add-only merged values.
    """
    merged: dict[str, object] = {}
    for document in documents:
        values = getattr(document, field)
        for key, value in values.items():
            if key in merged:
                diagnostics.append(_diagnostic("registry-id-collision", "registry"))
                continue
            merged[key] = value
    return merged


def _validate_shared_closure(
    documents: list[RegistryDocument],
    diagnostics: list[RegistryDiagnostic],
) -> None:
    """Ensure shared documents never reference Mac-local definitions.

    Args:
        documents: Shared registry documents.
        diagnostics: Mutable safe diagnostic accumulator.
    """
    source_ids = {key for document in documents for key in document.sources}
    host_ids = {key for document in documents for key in document.hosts}
    target_ids = {key for document in documents for key in document.targets}
    binding_ids = {key for document in documents for key in document.bindings}
    asset_ids = {key for document in documents for key in document.assets}

    for document in documents:
        if document.layer.host is not None:
            diagnostics.append(_diagnostic("shared-layer-host-authority", "layer"))
        if any(
            source.residency != SourceResidency.SHARED or source.host is not None
            for source in document.sources.values()
        ):
            diagnostics.append(_diagnostic("shared-layer-work-data", "layer"))
        if any(target.host not in host_ids for target in document.targets.values()):
            diagnostics.append(_diagnostic("shared-layer-not-closed", "layer"))
        if any(binding.host not in host_ids for binding in document.bindings.values()):
            diagnostics.append(_diagnostic("shared-layer-not-closed", "layer"))
        if any(
            any(binding not in binding_ids for binding in target.bindings)
            for target in document.targets.values()
        ):
            diagnostics.append(_diagnostic("shared-layer-not-closed", "layer"))
        if any(
            asset.source.source not in source_ids for asset in document.assets.values()
        ):
            diagnostics.append(_diagnostic("shared-layer-not-closed", "layer"))
        if any(
            assignment.asset not in asset_ids
            or assignment.target not in target_ids
            or any(binding not in binding_ids for binding in assignment.bindings)
            for assignment in document.assignments.values()
        ):
            diagnostics.append(_diagnostic("shared-layer-not-closed", "layer"))


def _validate_local_layers(
    documents: list[RegistryDocument],
    diagnostics: list[RegistryDiagnostic],
) -> None:
    """Ensure every Mac-local document is scoped to its declared Mac host.

    Args:
        documents: Mac-local registry documents.
        diagnostics: Mutable safe diagnostic accumulator.
    """
    for document in documents:
        host_id = document.layer.host
        if host_id is None:
            diagnostics.append(_diagnostic("local-layer-missing-host", "layer"))
            continue
        if any(
            source.residency != SourceResidency.MAC_LOCAL_WORK or source.host != host_id
            for source in document.sources.values()
        ):
            diagnostics.append(_diagnostic("local-layer-source-boundary", "layer"))
        if any(key != host_id for key in document.hosts):
            diagnostics.append(_diagnostic("local-layer-host-boundary", "layer"))
        if any(target.host != host_id for target in document.targets.values()):
            diagnostics.append(_diagnostic("local-layer-target-boundary", "layer"))
        if any(binding.host != host_id for binding in document.bindings.values()):
            diagnostics.append(_diagnostic("local-layer-binding-boundary", "layer"))


def assemble_registry(
    shared_documents: list[RegistryDocument],
    local_documents: list[RegistryDocument] | None = None,
) -> RegistryCheck:
    """Assemble add-only registry layers and validate authored relationships.

    Args:
        shared_documents: Documents trusted as portable shared input.
        local_documents: Documents explicitly selected by the current Mac host.

    Returns:
        A catalog or stable blocking diagnostics.
    """
    local = local_documents or []
    diagnostics: list[RegistryDiagnostic] = []
    _validate_shared_closure(shared_documents, diagnostics)
    _validate_local_layers(local, diagnostics)
    documents = [*shared_documents, *local]

    sources = _merge_maps(documents, "sources", diagnostics)
    hosts = _merge_maps(documents, "hosts", diagnostics)
    targets = _merge_maps(documents, "targets", diagnostics)
    bindings = _merge_maps(documents, "bindings", diagnostics)
    assets = _merge_maps(documents, "assets", diagnostics)
    assignments = _merge_maps(documents, "assignments", diagnostics)

    all_ids = [
        *sources,
        *hosts,
        *targets,
        *bindings,
        *assets,
        *assignments,
    ]
    if any(not _stable_id(identifier) for identifier in all_ids):
        diagnostics.append(_diagnostic("invalid-logical-id", "registry"))

    typed_sources = {
        key: value
        for key, value in sources.items()
        if isinstance(value, RegistrySource)
    }
    typed_hosts = {
        key: value for key, value in hosts.items() if isinstance(value, RegistryHost)
    }
    typed_targets = {
        key: value
        for key, value in targets.items()
        if isinstance(value, RegistryTarget)
    }
    typed_bindings = {
        key: value
        for key, value in bindings.items()
        if isinstance(value, BindingDeclaration)
    }
    typed_assets = {
        key: value for key, value in assets.items() if isinstance(value, RegistryAsset)
    }
    typed_assignments = {
        key: value
        for key, value in assignments.items()
        if isinstance(value, RegistryAssignment)
    }

    if any(not _revision_valid(source.revision) for source in typed_sources.values()):
        diagnostics.append(_diagnostic("invalid-source-revision", "source"))
    if any(
        not _repository_identity(source.repository) for source in typed_sources.values()
    ):
        diagnostics.append(_diagnostic("invalid-source-repository", "source"))
    if any(
        source.residency == SourceResidency.MAC_LOCAL_WORK
        and (
            source.host not in typed_hosts
            or typed_hosts[source.host].platform != Platform.MACOS
        )
        for source in typed_sources.values()
    ):
        diagnostics.append(_diagnostic("invalid-work-source-host", "source"))
    if any(target.host not in typed_hosts for target in typed_targets.values()):
        diagnostics.append(_diagnostic("unknown-target-host", "registry"))
    supported_pairs = {
        (Platform.MACOS, Consumer.CODEX),
        (Platform.MACOS, Consumer.QODERCLI),
        (Platform.WINDOWS, Consumer.CODEX),
        (Platform.WINDOWS, Consumer.CLAUDE),
    }
    if any(
        target.host in typed_hosts
        and (typed_hosts[target.host].platform, target.consumer) not in supported_pairs
        for target in typed_targets.values()
    ):
        diagnostics.append(_diagnostic("unsupported-host-consumer", "registry"))
    if any(binding.host not in typed_hosts for binding in typed_bindings.values()):
        diagnostics.append(_diagnostic("unknown-binding-host", "binding"))
    if any(not _stable_id(binding.role) for binding in typed_bindings.values()):
        diagnostics.append(_diagnostic("invalid-binding-role", "binding"))
    if any(
        any(
            binding not in typed_bindings or typed_bindings[binding].host != target.host
            for binding in target.bindings
        )
        for target in typed_targets.values()
    ):
        diagnostics.append(_diagnostic("invalid-target-binding", "binding"))
    if any(
        asset.source.source not in typed_sources
        or not _portable_path(asset.source.path)
        for asset in typed_assets.values()
    ):
        diagnostics.append(_diagnostic("invalid-asset-source", "source"))
    if any(
        assignment.asset not in typed_assets or assignment.target not in typed_targets
        for assignment in typed_assignments.values()
    ):
        diagnostics.append(_diagnostic("invalid-assignment-reference", "registry"))
    if any(
        assignment.target in typed_targets
        and any(
            binding not in typed_bindings
            or typed_bindings[binding].host != typed_targets[assignment.target].host
            for binding in assignment.bindings
        )
        for assignment in typed_assignments.values()
    ):
        diagnostics.append(_diagnostic("invalid-assignment-binding", "binding"))
    for target_id, target in typed_targets.items():
        binding_ids = set(target.bindings)
        binding_ids.update(
            binding_id
            for assignment in typed_assignments.values()
            if assignment.target == target_id
            for binding_id in assignment.bindings
        )
        role_bindings: dict[str, set[str]] = {}
        for binding_id in binding_ids:
            declaration = typed_bindings.get(binding_id)
            if declaration is None:
                continue
            role_bindings.setdefault(declaration.role, set()).add(binding_id)
        if any(len(role_ids) > 1 for role_ids in role_bindings.values()):
            diagnostics.append(_diagnostic("duplicate-target-binding-role", "binding"))
    if any(
        document.layer.host is not None
        and any(
            assignment.target in typed_targets
            and typed_targets[assignment.target].host != document.layer.host
            for assignment in document.assignments.values()
        )
        for document in local
    ):
        diagnostics.append(_diagnostic("local-layer-assignment-boundary", "layer"))

    assignment_pairs = [
        (assignment.asset, assignment.target)
        for assignment in typed_assignments.values()
    ]
    if len(set(assignment_pairs)) != len(assignment_pairs):
        diagnostics.append(_diagnostic("duplicate-assignment", "registry"))
    assigned_assets = {assignment.asset for assignment in typed_assignments.values()}
    if any(asset_id not in assigned_assets for asset_id in typed_assets):
        diagnostics.append(_diagnostic("unassigned-asset", "registry"))

    for assignment in typed_assignments.values():
        asset = typed_assets.get(assignment.asset)
        target = typed_targets.get(assignment.target)
        if asset is None or target is None:
            continue
        source = typed_sources.get(asset.source.source)
        if (
            source is not None
            and source.residency == SourceResidency.MAC_LOCAL_WORK
            and (target.host != source.host or target.consumer == Consumer.CLAUDE)
        ):
            diagnostics.append(_diagnostic("work-residency-violation", "layer"))

    if diagnostics:
        return RegistryCheck(catalog=None, diagnostics=tuple(diagnostics))

    layers = tuple(document.layer for document in documents)
    revision = _catalog_revision(
        layers=layers,
        sources=typed_sources,
        hosts=typed_hosts,
        targets=typed_targets,
        bindings=typed_bindings,
        assets=typed_assets,
        assignments=typed_assignments,
    )
    return RegistryCheck(
        catalog=RegistryCatalog(
            layers=layers,
            sources=typed_sources,
            hosts=typed_hosts,
            targets=typed_targets,
            bindings=typed_bindings,
            assets=typed_assets,
            assignments=typed_assignments,
            revision=revision,
        ),
        diagnostics=(),
    )


def load_registry(
    shared_paths: list[Path],
    *,
    local_paths: list[Path] | None = None,
    platform: Platform | None = None,
) -> RegistryCheck:
    """Load physical layers under a host-enforced no-probe policy.

    Args:
        shared_paths: Portable registry documents explicitly selected as shared.
        local_paths: Mac-local documents selected by trusted host configuration.
        platform: Runtime platform override for library tests; production callers
            should omit it.

    Returns:
        An assembled catalog or safe diagnostics. Windows rejects local paths
        before opening or statting them.
    """
    selected_platform = platform or current_platform()
    local = local_paths or []
    if selected_platform == Platform.WINDOWS and local:
        return RegistryCheck(
            catalog=None,
            diagnostics=(_diagnostic("forbidden-local-layer", "layer"),),
        )
    if not shared_paths:
        return RegistryCheck(
            catalog=None,
            diagnostics=(_diagnostic("missing-shared-registry", "loader"),),
        )

    shared_documents: list[RegistryDocument] = []
    local_documents: list[RegistryDocument] = []
    diagnostics: list[RegistryDiagnostic] = []
    for path in shared_paths:
        document, diagnostic = _load_document(
            path, expected_layer=LayerResidency.SHARED
        )
        if diagnostic is not None:
            diagnostics.append(diagnostic)
        elif document is not None:
            shared_documents.append(document)
    for path in local:
        document, diagnostic = _load_document(
            path, expected_layer=LayerResidency.MAC_LOCAL
        )
        if diagnostic is not None:
            diagnostics.append(diagnostic)
        elif document is not None:
            local_documents.append(document)
    if diagnostics:
        return RegistryCheck(catalog=None, diagnostics=tuple(diagnostics))
    return assemble_registry(shared_documents, local_documents)


def validate_host_bindings(
    catalog: RegistryCatalog,
    host_bindings: HostBindings,
) -> tuple[RegistryDiagnostic, ...]:
    """Validate the current host's roots and typed binding references.

    Args:
        catalog: Successfully assembled authored catalog.
        host_bindings: Host-local values for one current host.

    Returns:
        Stable blocking diagnostics. Source content and declared revisions are not
        compared in this phase.
    """
    diagnostics: list[RegistryDiagnostic] = []
    host = catalog.hosts.get(host_bindings.host)
    if host is None:
        return (_diagnostic("unknown-current-host", "host"),)

    current_targets = {
        target_id: target
        for target_id, target in catalog.targets.items()
        if target.host == host_bindings.host
    }
    assignments = [
        assignment
        for assignment in catalog.assignments.values()
        if assignment.target in current_targets
    ]
    required_bindings: set[str] = {
        binding_id
        for target in current_targets.values()
        for binding_id in target.bindings
    }
    for assignment in assignments:
        required_bindings.update(assignment.bindings)

    for binding_id in required_bindings:
        declaration = catalog.bindings.get(binding_id)
        value = host_bindings.bindings.get(binding_id)
        if declaration is None or value is None:
            diagnostics.append(_diagnostic("missing-host-binding", "binding"))
            continue
        if declaration.host != host_bindings.host or value.kind != declaration.kind:
            diagnostics.append(_diagnostic("host-binding-mismatch", "binding"))
            continue
        if (
            isinstance(value, PathBindingValue)
            and not Path(value.path).expanduser().is_absolute()
        ):
            diagnostics.append(_diagnostic("invalid-host-path", "binding"))
    if any(binding not in catalog.bindings for binding in host_bindings.bindings):
        diagnostics.append(_diagnostic("unknown-host-binding", "binding"))

    known_repositories = {source.repository for source in catalog.sources.values()}
    if any(
        repository not in known_repositories
        for repository in host_bindings.source_roots
    ):
        diagnostics.append(_diagnostic("unknown-source-root", "source"))
    roots: dict[str, Path] = {}
    for repository, path in host_bindings.source_roots.items():
        root = Path(path).expanduser()
        if not root.is_absolute():
            diagnostics.append(_diagnostic("invalid-source-root", "source"))
            continue
        roots[repository] = root
    for assignment in assignments:
        asset = catalog.assets[assignment.asset]
        source = catalog.sources[asset.source.source]
        resolution = resolve_source(
            SourceRef(repository=source.repository, path=asset.source.path),
            source_roots=roots,
        )
        if resolution.status != "ok":
            diagnostics.append(_diagnostic(resolution.status, "source"))
    return tuple(diagnostics)


def check_registry(
    shared_paths: list[Path],
    *,
    host_bindings_path: Path,
    local_paths: list[Path] | None = None,
    platform: Platform | None = None,
) -> RegistryCheck:
    """Load a registry and validate it for one current host.

    Args:
        shared_paths: Portable shared registry documents.
        host_bindings_path: Current host's local roots and typed references.
        local_paths: Mac-local registry documents.
        platform: Optional test override for the runtime platform.

    Returns:
        A safe result suitable for direct JSON serialization.
    """
    selected_platform = platform or current_platform()
    loaded = load_registry(
        shared_paths,
        local_paths=local_paths,
        platform=selected_platform,
    )
    if loaded.catalog is None:
        return loaded
    host_bindings, diagnostic = _load_host_bindings(host_bindings_path)
    if diagnostic is not None or host_bindings is None:
        return RegistryCheck(
            catalog=loaded.catalog,
            diagnostics=(
                diagnostic or _diagnostic("invalid-host-bindings", "binding"),
            ),
        )
    host = loaded.catalog.hosts.get(host_bindings.host)
    if host is not None and host.platform != selected_platform:
        return RegistryCheck(
            catalog=loaded.catalog,
            diagnostics=(_diagnostic("host-platform-mismatch", "host"),),
            host_bindings=host_bindings,
        )
    if any(
        layer.residency == LayerResidency.MAC_LOCAL and layer.host != host_bindings.host
        for layer in loaded.catalog.layers
    ):
        return RegistryCheck(
            catalog=loaded.catalog,
            diagnostics=(_diagnostic("local-layer-host-mismatch", "layer"),),
            host_bindings=host_bindings,
        )
    diagnostics = validate_host_bindings(loaded.catalog, host_bindings)
    return RegistryCheck(
        catalog=loaded.catalog,
        diagnostics=diagnostics,
        host_bindings=host_bindings,
    )
