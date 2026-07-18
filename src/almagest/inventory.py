"""Read-only live Agent configuration inventory.

Registry remains the authored authority. This module observes only explicitly
bound current-host roots and never adopts live state, renders desired content,
or writes a consumer target.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from almagest import registry
from almagest.adapters import (
    ADAPTERS,
    AdapterDescriptor,
    Compatibility,
    ConsumerEvidence,
    SurfaceMode,
    SurfaceRule,
    adapter_for,
)

INVENTORY_SCHEMA_VERSION = 1
DEFAULT_MAX_ENTRIES = 512
DEFAULT_MAX_FILE_BYTES = 1_048_576


class StrictModel(BaseModel):
    """Reject unknown fields in machine-facing inventory contracts."""

    model_config = ConfigDict(extra="forbid")


class Presence(StrEnum):
    """Whether an inventory object was observed."""

    PRESENT = "present"
    ABSENT = "absent"
    UNKNOWN = "unknown"


class Ownership(StrEnum):
    """Observed live mutation ownership."""

    MANAGED = "managed"
    EXTERNAL_OWNED = "external-owned"
    UNKNOWN_OWNER = "unknown-owner"
    NOT_APPLICABLE = "not-applicable"


class DesiredOwnership(StrEnum):
    """Authored Registry authority, separate from live provenance."""

    ALMAGEST_MANAGED = "almagest-managed"
    NOT_DECLARED = "not-declared"
    NOT_APPLICABLE = "not-applicable"


class Readability(StrEnum):
    """Whether a bounded surface could be interpreted safely."""

    READABLE = "readable"
    UNREADABLE = "unreadable"
    INVALID = "invalid"
    UNKNOWN = "unknown"


class Topology(StrEnum):
    """Relationship between a live object and sibling observations."""

    CANONICAL = "canonical"
    DUPLICATE = "duplicate"
    ORPHAN = "orphan"
    UNKNOWN = "unknown"


class EffectiveState(StrEnum):
    """Whether precedence proves an observed object effective."""

    ACTIVE = "active"
    SHADOWED = "shadowed"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


class Coverage(StrEnum):
    """How completely one adapter surface was observed."""

    COMPLETE = "complete"
    PARTIAL = "partial"
    UNKNOWN = "unknown"
    UNSUPPORTED = "unsupported"


class SnapshotStatus(StrEnum):
    """Inventory execution result, not desired-state compliance."""

    PASS = "pass"
    PARTIAL = "partial"
    BLOCK = "block"


class ClaimType(StrEnum):
    """Source of one inventory claim."""

    LIVE = "live"
    EXPECTED = "expected"
    BINDING = "binding"


class InventoryDiagnostic(StrictModel):
    """Stable diagnostic that never serializes raw consumer input."""

    code: str
    scope: Literal["inventory", "adapter", "target", "surface", "loader"]
    severity: Literal["warning", "block"]
    target_id: str | None = None


class InventoryClaim(StrictModel):
    """One orthogonal expected, live, or binding fact."""

    claim_id: str
    claim_type: ClaimType
    target_id: str
    asset_kind: registry.AssetKind
    adapter_id: str
    root_role: str | None = None
    locator: str | None = None
    namespace: str
    logical_key: str
    assignment_id: str | None = None
    source_revision: str | None = None
    desired_ownership: DesiredOwnership
    presence: Presence
    ownership: Ownership
    readability: Readability
    topology: Topology
    effective: EffectiveState
    precedence: int | None = None
    finding_codes: tuple[str, ...] = ()


class CoverageClaim(StrictModel):
    """Observation coverage for one target/domain/surface tuple."""

    coverage_id: str
    target_id: str
    asset_kind: registry.AssetKind
    adapter_id: str
    root_role: str | None
    surface_id: str
    coverage: Coverage
    diagnostic_codes: tuple[str, ...] = ()


class AdapterUse(StrictModel):
    """Adapter revision and current-host compatibility for one target."""

    target_id: str
    adapter_id: str
    adapter_revision: str
    compatibility: Compatibility
    product: str | None = None
    version: str | None = None


class ConsumerEvidenceDocument(StrictModel):
    """Host-local, non-authoritative consumer identity evidence."""

    schema_version: Literal[INVENTORY_SCHEMA_VERSION]
    consumers: dict[str, ConsumerEvidence] = Field(default_factory=dict)


class InventorySnapshot(StrictModel):
    """Stable machine-facing result of one read-only inventory."""

    schema_version: Literal[INVENTORY_SCHEMA_VERSION] = INVENTORY_SCHEMA_VERSION
    status: SnapshotStatus
    registry_revision: str | None
    inventory_revision: str
    host_id: str | None
    platform: registry.Platform
    adapters: tuple[AdapterUse, ...]
    claims: tuple[InventoryClaim, ...]
    coverage: tuple[CoverageClaim, ...]
    diagnostics: tuple[InventoryDiagnostic, ...]

    def report(self) -> dict[str, object]:
        """Return deterministic JSON with local, root-relative action context.

        Returns:
            A stable report containing no absolute paths, file contents, command
            arguments, environment values, secrets, or raw exceptions.
        """
        claim_counts: dict[str, int] = {}
        for claim in self.claims:
            key = f"{claim.claim_type}:{claim.presence}:{claim.ownership}"
            claim_counts[key] = claim_counts.get(key, 0) + 1
        coverage_counts: dict[str, int] = {}
        for item in self.coverage:
            coverage_counts[item.coverage] = coverage_counts.get(item.coverage, 0) + 1
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "registry_revision": self.registry_revision,
            "inventory_revision": self.inventory_revision,
            "host_id": self.host_id,
            "platform": self.platform,
            "summary": {
                "targets": len(self.adapters),
                "claims": len(self.claims),
                "coverage": len(self.coverage),
                "claim_counts": dict(sorted(claim_counts.items())),
                "coverage_counts": dict(sorted(coverage_counts.items())),
                "diagnostics": len(self.diagnostics),
            },
            "adapters": [
                adapter.model_dump(mode="json")
                for adapter in sorted(self.adapters, key=lambda item: item.target_id)
            ],
            "claims": [
                claim.model_dump(mode="json")
                for claim in sorted(self.claims, key=lambda item: item.claim_id)
            ],
            "coverage": [
                item.model_dump(mode="json")
                for item in sorted(self.coverage, key=lambda value: value.coverage_id)
            ],
            "diagnostics": [
                item.model_dump(mode="json")
                for item in sorted(
                    self.diagnostics,
                    key=lambda value: (
                        value.target_id or "",
                        value.scope,
                        value.code,
                        value.severity,
                    ),
                )
            ],
        }


class ProbeKind(StrEnum):
    """Filesystem node kind returned by a bounded reader."""

    MISSING = "missing"
    FILE = "file"
    DIRECTORY = "directory"
    SYMLINK = "symlink"
    OTHER = "other"


@dataclass(frozen=True)
class ProbeNode:
    """Minimal node metadata without host paths or values."""

    kind: ProbeKind


@dataclass(frozen=True)
class ProbeListing:
    """Bounded directory entry names and truncation state."""

    entries: tuple[str, ...]
    truncated: bool = False


class ProbeFailure(RuntimeError):
    """Bounded reader failure represented only by an allowlisted code."""

    def __init__(self, code: str) -> None:
        """Store a safe failure code.

        Args:
            code: Allowlisted diagnostic code.
        """
        super().__init__(code)
        self.code = code


class DuplicateJsonKeyError(ValueError):
    """Signal duplicate consumer keys without retaining the sensitive key."""


class InventoryReader(Protocol):
    """Filesystem-independent interface used by all adapters."""

    def stat(self, binding_id: str, relative_path: str) -> ProbeNode:
        """Observe one exact node without returning a host path."""

    def list_entries(self, binding_id: str, relative_path: str) -> ProbeListing:
        """List one exact directory with a fixed entry limit."""

    def read_text(self, binding_id: str, relative_path: str) -> str:
        """Read one exact bounded text file."""


class FilesystemReader:
    """Read only explicit binding roots and declared source targets."""

    def __init__(
        self,
        roots: dict[str, Path],
        *,
        allowed_targets: tuple[Path, ...] = (),
        max_entries: int = DEFAULT_MAX_ENTRIES,
        max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
    ) -> None:
        """Create a bounded local reader.

        Args:
            roots: Binding ID to exact file/directory root.
            allowed_targets: Additional declared source roots that an exact
                symlink may resolve into.
            max_entries: Maximum entries returned from one directory.
            max_file_bytes: Maximum bytes read from one file.
        """
        self._roots = roots
        self._allowed = tuple(
            path.expanduser().resolve(strict=False)
            for path in (*roots.values(), *allowed_targets)
        )
        self._max_entries = max_entries
        self._max_file_bytes = max_file_bytes

    def _candidate(self, binding_id: str, relative_path: str) -> Path:
        """Resolve one portable relative locator under an explicit binding.

        Args:
            binding_id: Host binding selected by an adapter role.
            relative_path: Portable path from a descriptor.

        Returns:
            The authorized local candidate path.

        Raises:
            ProbeFailure: The binding or path is unknown or escapes all declared
                roots.
        """
        root = self._roots.get(binding_id)
        if root is None:
            raise ProbeFailure("unknown-reader-binding")
        relative = PurePosixPath(relative_path or ".")
        if relative.is_absolute() or ".." in relative.parts:
            raise ProbeFailure("adapter-path-escape")
        candidate = root.expanduser().joinpath(*relative.parts)
        try:
            resolved = candidate.resolve(strict=False)
        except OSError as exc:
            raise ProbeFailure("unreadable-surface") from exc
        if not any(_is_within(resolved, allowed) for allowed in self._allowed):
            raise ProbeFailure("symlink-target-outside-bindings")
        return candidate

    def stat(self, binding_id: str, relative_path: str) -> ProbeNode:
        """Observe one exact node.

        Args:
            binding_id: Explicit root binding.
            relative_path: Portable relative locator.

        Returns:
            Minimal node kind, including a stable missing result.

        Raises:
            ProbeFailure: The node cannot be safely inspected.
        """
        candidate = self._candidate(binding_id, relative_path)
        try:
            candidate.lstat()
        except FileNotFoundError:
            return ProbeNode(ProbeKind.MISSING)
        except OSError as exc:
            raise ProbeFailure("unreadable-surface") from exc
        try:
            if candidate.is_file():
                return ProbeNode(ProbeKind.FILE)
            if candidate.is_dir():
                return ProbeNode(ProbeKind.DIRECTORY)
            if candidate.is_symlink():
                return ProbeNode(ProbeKind.SYMLINK)
        except OSError as exc:
            raise ProbeFailure("unreadable-surface") from exc
        return ProbeNode(ProbeKind.OTHER)

    def list_entries(self, binding_id: str, relative_path: str) -> ProbeListing:
        """List a bounded directory.

        Args:
            binding_id: Explicit root binding.
            relative_path: Portable relative locator.

        Returns:
            Sorted entry names and whether the limit truncated the result.

        Raises:
            ProbeFailure: The directory is unreadable or has the wrong type.
        """
        candidate = self._candidate(binding_id, relative_path)
        try:
            names = sorted(entry.name for entry in candidate.iterdir())
        except (FileNotFoundError, NotADirectoryError) as exc:
            raise ProbeFailure("invalid-surface-type") from exc
        except OSError as exc:
            raise ProbeFailure("unreadable-surface") from exc
        truncated = len(names) > self._max_entries
        return ProbeListing(tuple(names[: self._max_entries]), truncated)

    def read_text(self, binding_id: str, relative_path: str) -> str:
        """Read one bounded UTF-8 file.

        Args:
            binding_id: Explicit root binding.
            relative_path: Portable relative locator.

        Returns:
            Decoded text.

        Raises:
            ProbeFailure: The file is too large, unreadable, invalid UTF-8, or
                outside declared roots.
        """
        candidate = self._candidate(binding_id, relative_path)
        try:
            if candidate.stat().st_size > self._max_file_bytes:
                raise ProbeFailure("surface-byte-limit")
            return candidate.read_text(encoding="utf-8")
        except ProbeFailure:
            raise
        except UnicodeError as exc:
            raise ProbeFailure("invalid-surface-encoding") from exc
        except OSError as exc:
            raise ProbeFailure("unreadable-surface") from exc


ReaderFactory = Callable[
    [dict[str, Path], tuple[Path, ...]],
    InventoryReader,
]


def _is_within(candidate: Path, root: Path) -> bool:
    """Check whether a resolved path is a root or descendant.

    Args:
        candidate: Resolved candidate.
        root: Resolved authorized root.

    Returns:
        Whether ``candidate`` is inside ``root``.
    """
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _stable_id(prefix: str, *parts: str | None) -> str:
    """Build one opaque deterministic identifier.

    Args:
        prefix: Human-readable ID class.
        parts: Stable non-secret logical fields.

    Returns:
        Prefix plus a SHA-256 digest.
    """
    encoded = "\0".join(part or "" for part in parts).encode()
    return f"{prefix}.{hashlib.sha256(encoded).hexdigest()}"


def _claim(
    *,
    claim_type: ClaimType,
    target_id: str,
    kind: registry.AssetKind,
    adapter_id: str,
    root_role: str | None,
    locator: str | None,
    namespace: str,
    logical_key: str,
    desired_ownership: DesiredOwnership,
    presence: Presence,
    ownership: Ownership,
    readability: Readability,
    topology: Topology,
    effective: EffectiveState,
    assignment_id: str | None = None,
    source_revision: str | None = None,
    precedence: int | None = None,
    finding_codes: tuple[str, ...] = (),
) -> InventoryClaim:
    """Create one deterministic inventory claim.

    Args:
        claim_type: Expected, live, or binding fact.
        target_id: Current-host Registry target.
        kind: Configuration domain.
        adapter_id: Descriptor identity.
        root_role: Semantic binding role, never an absolute path.
        locator: Root-relative locator.
        namespace: Adapter namespace for duplicate grouping.
        logical_key: Consumer or Registry logical key.
        desired_ownership: Authored mutation authority.
        presence: Observed presence.
        ownership: Proven live ownership.
        readability: Parse/read state.
        topology: Duplicate/orphan relationship.
        effective: Precedence result.
        assignment_id: Optional Registry assignment.
        source_revision: Optional authored source revision.
        precedence: Adapter-declared precedence.
        finding_codes: Derived, non-state finding codes.

    Returns:
        A strict claim with an opaque stable ID.
    """
    claim_id = _stable_id(
        "claim",
        claim_type,
        target_id,
        kind,
        adapter_id,
        root_role,
        locator,
        namespace,
        logical_key,
        assignment_id,
    )
    return InventoryClaim(
        claim_id=claim_id,
        claim_type=claim_type,
        target_id=target_id,
        asset_kind=kind,
        adapter_id=adapter_id,
        root_role=root_role,
        locator=locator,
        namespace=namespace,
        logical_key=logical_key,
        assignment_id=assignment_id,
        source_revision=source_revision,
        desired_ownership=desired_ownership,
        presence=presence,
        ownership=ownership,
        readability=readability,
        topology=topology,
        effective=effective,
        precedence=precedence,
        finding_codes=finding_codes,
    )


def _coverage(
    target_id: str,
    adapter_id: str,
    kind: registry.AssetKind,
    root_role: str | None,
    surface_id: str,
    value: Coverage,
    codes: tuple[str, ...] = (),
) -> CoverageClaim:
    """Create one deterministic coverage claim.

    Args:
        target_id: Current-host target.
        adapter_id: Adapter identity.
        kind: Configuration domain.
        root_role: Semantic path role.
        surface_id: Adapter surface rule.
        value: Coverage result.
        codes: Stable explanation codes.

    Returns:
        A strict coverage fact.
    """
    return CoverageClaim(
        coverage_id=_stable_id(
            "coverage", target_id, adapter_id, kind, root_role, surface_id
        ),
        target_id=target_id,
        asset_kind=kind,
        adapter_id=adapter_id,
        root_role=root_role,
        surface_id=surface_id,
        coverage=value,
        diagnostic_codes=codes,
    )


def _relative(base: str, child: str) -> str:
    """Join two portable relative path fragments.

    Args:
        base: Adapter surface path.
        child: Entry or nested file.

    Returns:
        POSIX relative locator without a leading ``./``.
    """
    parts = [part for part in (base, child) if part]
    return str(PurePosixPath(*parts)) if parts else ""


def _surface_claim(
    target_id: str,
    adapter: AdapterDescriptor,
    rule: SurfaceRule,
    *,
    presence: Presence,
    readability: Readability,
    finding_codes: tuple[str, ...] = (),
) -> InventoryClaim:
    """Build a synthetic claim for a surface root or document.

    Args:
        target_id: Current-host target.
        adapter: Selected descriptor.
        rule: Surface being observed.
        presence: File/directory presence.
        readability: Safe interpretation state.
        finding_codes: Derived findings.

    Returns:
        One live surface claim.
    """
    ownership = (
        Ownership.NOT_APPLICABLE
        if presence != Presence.PRESENT
        else Ownership.UNKNOWN_OWNER
    )
    return _claim(
        claim_type=ClaimType.LIVE,
        target_id=target_id,
        kind=rule.kind,
        adapter_id=adapter.adapter_id,
        root_role=rule.role,
        locator=rule.relative_path or ".",
        namespace=rule.namespace,
        logical_key="@surface",
        desired_ownership=DesiredOwnership.NOT_DECLARED,
        presence=presence,
        ownership=ownership,
        readability=readability,
        topology=Topology.UNKNOWN,
        effective=EffectiveState.UNKNOWN,
        precedence=rule.precedence,
        finding_codes=finding_codes,
    )


def _parse_mapping(
    text: str,
    rule: SurfaceRule,
) -> tuple[tuple[str, ...] | None, str | None]:
    """Parse one JSON/TOML mapping and select only key names.

    Args:
        text: Bounded local document.
        rule: Format and selector contract.

    Returns:
        Sorted logical keys, or ``None`` plus an allowlisted parse code.
    """
    try:
        if rule.mode == SurfaceMode.JSON_MAP:
            value: object = json.loads(
                text,
                object_pairs_hook=_reject_duplicate_keys,
            )
        else:
            value = tomllib.loads(text)
    except (
        DuplicateJsonKeyError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
        UnicodeError,
    ):
        return None, "invalid-surface-format"
    for part in rule.selector:
        if not isinstance(value, dict):
            return None, "invalid-surface-schema"
        value = value.get(part, {})
    if isinstance(value, dict):
        return tuple(sorted(str(key) for key in value)), None
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(sorted(set(value))), None
    return None, "invalid-surface-schema"


def _frontmatter_keys(text: str) -> frozenset[str] | None:
    """Extract only top-level frontmatter key names.

    Args:
        text: Bounded ``SKILL.md`` text.

    Returns:
        Key names, or ``None`` when the frontmatter envelope is malformed.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    keys: set[str] = set()
    for line in lines[1:]:
        if line.strip() == "---":
            return frozenset(keys)
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, _separator, _value = line.partition(":")
        if key.strip():
            keys.add(key.strip())
    return None


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a JSON object while rejecting duplicate keys.

    Args:
        pairs: Ordered key/value pairs from ``json.loads``.

    Returns:
        A dictionary with unique keys.

    Raises:
        DuplicateJsonKeyError: Any duplicate key exists.
    """
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateJsonKeyError
        value[key] = item
    return value


def _scan_rule(
    *,
    target_id: str,
    adapter: AdapterDescriptor,
    rule: SurfaceRule,
    binding_id: str,
    reader: InventoryReader,
    semantic: bool,
) -> tuple[list[InventoryClaim], CoverageClaim]:
    """Inspect one exact adapter surface.

    Args:
        target_id: Current-host target.
        adapter: Selected descriptor.
        rule: Exact bounded surface.
        binding_id: Host-local path chosen by semantic role.
        reader: Scoped read-only reader.
        semantic: Whether current-host evidence proves fixture compatibility.

    Returns:
        Live claims and one coverage fact.
    """
    claims: list[InventoryClaim] = []
    try:
        node = reader.stat(binding_id, rule.relative_path)
    except ProbeFailure as exc:
        claims.append(
            _surface_claim(
                target_id,
                adapter,
                rule,
                presence=Presence.UNKNOWN,
                readability=Readability.UNREADABLE,
                finding_codes=(exc.code,),
            )
        )
        return claims, _coverage(
            target_id,
            adapter.adapter_id,
            rule.kind,
            rule.role,
            rule.surface_id,
            Coverage.PARTIAL,
            (exc.code,),
        )
    if node.kind == ProbeKind.MISSING:
        claims.append(
            _surface_claim(
                target_id,
                adapter,
                rule,
                presence=Presence.ABSENT,
                readability=Readability.UNKNOWN,
            )
        )
        return claims, _coverage(
            target_id,
            adapter.adapter_id,
            rule.kind,
            rule.role,
            rule.surface_id,
            Coverage.COMPLETE,
        )
    expected_kind = (
        ProbeKind.DIRECTORY
        if rule.mode
        in {
            SurfaceMode.ROOT,
            SurfaceMode.DIRECTORY,
            SurfaceMode.GLOB,
        }
        else ProbeKind.FILE
    )
    if node.kind != expected_kind:
        claims.append(
            _surface_claim(
                target_id,
                adapter,
                rule,
                presence=Presence.PRESENT,
                readability=Readability.INVALID,
                finding_codes=("invalid-surface-type",),
            )
        )
        return claims, _coverage(
            target_id,
            adapter.adapter_id,
            rule.kind,
            rule.role,
            rule.surface_id,
            Coverage.PARTIAL,
            ("invalid-surface-type",),
        )
    if rule.mode in {SurfaceMode.ROOT, SurfaceMode.FILE}:
        claims.append(
            _claim(
                claim_type=ClaimType.LIVE,
                target_id=target_id,
                kind=rule.kind,
                adapter_id=adapter.adapter_id,
                root_role=rule.role,
                locator=rule.relative_path or ".",
                namespace=rule.namespace,
                logical_key=Path(rule.relative_path).name or "@root",
                desired_ownership=DesiredOwnership.NOT_DECLARED,
                presence=Presence.PRESENT,
                ownership=Ownership.UNKNOWN_OWNER,
                readability=Readability.READABLE,
                topology=Topology.CANONICAL,
                effective=EffectiveState.ACTIVE,
                precedence=rule.precedence,
            )
        )
        return claims, _coverage(
            target_id,
            adapter.adapter_id,
            rule.kind,
            rule.role,
            rule.surface_id,
            Coverage.COMPLETE,
        )
    if rule.mode in {SurfaceMode.DIRECTORY, SurfaceMode.GLOB}:
        try:
            listing = reader.list_entries(binding_id, rule.relative_path)
        except ProbeFailure as exc:
            claims.append(
                _surface_claim(
                    target_id,
                    adapter,
                    rule,
                    presence=Presence.PRESENT,
                    readability=Readability.UNREADABLE,
                    finding_codes=(exc.code,),
                )
            )
            return claims, _coverage(
                target_id,
                adapter.adapter_id,
                rule.kind,
                rule.role,
                rule.surface_id,
                Coverage.PARTIAL,
                (exc.code,),
            )
        claims.append(
            _surface_claim(
                target_id,
                adapter,
                rule,
                presence=Presence.PRESENT,
                readability=Readability.READABLE,
            )
        )
        partial_codes: set[str] = set()
        entries = listing.entries
        if rule.mode == SurfaceMode.GLOB:
            entries = tuple(
                entry
                for entry in entries
                if rule.pattern is not None and fnmatch.fnmatch(entry, rule.pattern)
            )
        if listing.truncated:
            partial_codes.add("surface-entry-limit")
        for entry in entries:
            readability = Readability.READABLE
            findings: list[str] = []
            if rule.required_frontmatter and semantic:
                skill_file = _relative(rule.relative_path, f"{entry}/SKILL.md")
                try:
                    keys = _frontmatter_keys(reader.read_text(binding_id, skill_file))
                except ProbeFailure as exc:
                    keys = None
                    findings.append(exc.code)
                if keys is None or not set(rule.required_frontmatter).issubset(keys):
                    readability = Readability.INVALID
                    findings.append("invalid-frontmatter")
                    partial_codes.add("invalid-frontmatter")
            elif rule.required_frontmatter and not semantic:
                readability = Readability.UNKNOWN
                findings.append("adapter-not-proven")
                partial_codes.add("adapter-not-proven")
            ownership = (
                Ownership.EXTERNAL_OWNED
                if rule.default_ownership == Ownership.EXTERNAL_OWNED
                or entry in rule.external_names
                else Ownership.UNKNOWN_OWNER
            )
            claims.append(
                _claim(
                    claim_type=ClaimType.LIVE,
                    target_id=target_id,
                    kind=rule.kind,
                    adapter_id=adapter.adapter_id,
                    root_role=rule.role,
                    locator=_relative(rule.relative_path, entry),
                    namespace=rule.namespace,
                    logical_key=entry,
                    desired_ownership=DesiredOwnership.NOT_DECLARED,
                    presence=Presence.PRESENT,
                    ownership=ownership,
                    readability=readability,
                    topology=Topology.CANONICAL,
                    effective=EffectiveState.UNKNOWN,
                    precedence=rule.precedence,
                    finding_codes=tuple(sorted(set(findings))),
                )
            )
        value = Coverage.PARTIAL if partial_codes else Coverage.COMPLETE
        return claims, _coverage(
            target_id,
            adapter.adapter_id,
            rule.kind,
            rule.role,
            rule.surface_id,
            value,
            tuple(sorted(partial_codes)),
        )
    if not semantic:
        claims.append(
            _surface_claim(
                target_id,
                adapter,
                rule,
                presence=Presence.PRESENT,
                readability=Readability.UNKNOWN,
                finding_codes=("adapter-not-proven",),
            )
        )
        return claims, _coverage(
            target_id,
            adapter.adapter_id,
            rule.kind,
            rule.role,
            rule.surface_id,
            Coverage.PARTIAL,
            ("adapter-not-proven",),
        )
    try:
        text = reader.read_text(binding_id, rule.relative_path)
    except ProbeFailure as exc:
        claims.append(
            _surface_claim(
                target_id,
                adapter,
                rule,
                presence=Presence.PRESENT,
                readability=Readability.UNREADABLE,
                finding_codes=(exc.code,),
            )
        )
        return claims, _coverage(
            target_id,
            adapter.adapter_id,
            rule.kind,
            rule.role,
            rule.surface_id,
            Coverage.PARTIAL,
            (exc.code,),
        )
    keys, parse_code = _parse_mapping(text, rule)
    if parse_code is not None or keys is None:
        code = parse_code or "invalid-surface-schema"
        claims.append(
            _surface_claim(
                target_id,
                adapter,
                rule,
                presence=Presence.PRESENT,
                readability=Readability.INVALID,
                finding_codes=(code,),
            )
        )
        return claims, _coverage(
            target_id,
            adapter.adapter_id,
            rule.kind,
            rule.role,
            rule.surface_id,
            Coverage.PARTIAL,
            (code,),
        )
    claims.append(
        _surface_claim(
            target_id,
            adapter,
            rule,
            presence=Presence.PRESENT,
            readability=Readability.READABLE,
        )
    )
    for key in keys:
        claims.append(
            _claim(
                claim_type=ClaimType.LIVE,
                target_id=target_id,
                kind=rule.kind,
                adapter_id=adapter.adapter_id,
                root_role=rule.role,
                locator=f"{rule.relative_path}#{'/'.join((*rule.selector, key))}",
                namespace=rule.namespace,
                logical_key=key,
                desired_ownership=DesiredOwnership.NOT_DECLARED,
                presence=Presence.PRESENT,
                ownership=Ownership.UNKNOWN_OWNER,
                readability=Readability.READABLE,
                topology=Topology.CANONICAL,
                effective=EffectiveState.UNKNOWN,
                precedence=rule.precedence,
            )
        )
    return claims, _coverage(
        target_id,
        adapter.adapter_id,
        rule.kind,
        rule.role,
        rule.surface_id,
        Coverage.COMPLETE,
    )


def _mark_duplicates(claims: list[InventoryClaim]) -> list[InventoryClaim]:
    """Mark duplicate live logical keys without guessing precedence.

    Args:
        claims: Claims for one snapshot.

    Returns:
        Claims with orthogonal topology/effective fields updated.
    """
    groups: dict[
        tuple[str, registry.AssetKind, str, str],
        list[InventoryClaim],
    ] = {}
    for claim in claims:
        if (
            claim.claim_type != ClaimType.LIVE
            or claim.presence != Presence.PRESENT
            or claim.logical_key.startswith("@")
        ):
            continue
        groups.setdefault(
            (
                claim.target_id,
                claim.asset_kind,
                claim.namespace,
                claim.logical_key,
            ),
            [],
        ).append(claim)
    replacements: dict[str, InventoryClaim] = {}
    for values in groups.values():
        if len(values) < 2:
            continue
        precedences = [value.precedence for value in values]
        proven = all(value is not None for value in precedences) and len(
            set(precedences)
        ) == len(precedences)
        winner = max(precedences) if proven else None
        for value in values:
            effective = (
                EffectiveState.ACTIVE
                if proven and value.precedence == winner
                else EffectiveState.SHADOWED
                if proven
                else EffectiveState.AMBIGUOUS
            )
            replacements[value.claim_id] = value.model_copy(
                update={
                    "topology": Topology.DUPLICATE,
                    "effective": effective,
                    "finding_codes": tuple(sorted({*value.finding_codes, "duplicate"})),
                }
            )
    return [replacements.get(claim.claim_id, claim) for claim in claims]


def _expected_claims(
    *,
    catalog: registry.RegistryCatalog,
    target_id: str,
    adapter: AdapterDescriptor,
    claims: list[InventoryClaim],
    coverage: list[CoverageClaim],
) -> tuple[list[InventoryClaim], list[InventoryDiagnostic]]:
    """Add Registry expectations without claiming live provenance.

    Args:
        catalog: Authored Registry.
        target_id: Current target.
        adapter: Selected descriptor.
        claims: Already observed live/binding claims.
        coverage: Surface coverage for the target.

    Returns:
        Expected claims and compatibility diagnostics.
    """
    expected: list[InventoryClaim] = []
    diagnostics: list[InventoryDiagnostic] = []
    assignments = [
        (assignment_id, assignment)
        for assignment_id, assignment in catalog.assignments.items()
        if assignment.target == target_id
    ]
    for assignment_id, assignment in assignments:
        asset = catalog.assets[assignment.asset]
        source = catalog.sources[asset.source.source]
        kind_coverage = [
            item.coverage for item in coverage if item.asset_kind == asset.kind
        ]
        live_objects = [
            claim
            for claim in claims
            if claim.claim_type == ClaimType.LIVE
            and claim.asset_kind == asset.kind
            and claim.presence == Presence.PRESENT
            and not claim.logical_key.startswith("@")
        ]
        unsupported = kind_coverage and all(
            value == Coverage.UNSUPPORTED for value in kind_coverage
        )
        complete = bool(kind_coverage) and all(
            value == Coverage.COMPLETE for value in kind_coverage
        )
        absent = complete and not live_objects
        if unsupported:
            diagnostics.append(
                InventoryDiagnostic(
                    code="unsupported-assigned-kind",
                    scope="target",
                    severity="block",
                    target_id=target_id,
                )
            )
        revision = f"{source.revision.kind}:{source.revision.value}"
        expected.append(
            _claim(
                claim_type=ClaimType.EXPECTED,
                target_id=target_id,
                kind=asset.kind,
                adapter_id=adapter.adapter_id,
                root_role=None,
                locator=None,
                namespace="registry-assignment",
                logical_key=assignment.asset,
                assignment_id=assignment_id,
                source_revision=revision,
                desired_ownership=DesiredOwnership.ALMAGEST_MANAGED,
                presence=Presence.ABSENT if absent else Presence.UNKNOWN,
                ownership=Ownership.NOT_APPLICABLE,
                readability=Readability.UNKNOWN,
                topology=Topology.UNKNOWN,
                effective=EffectiveState.UNKNOWN,
                finding_codes=("missing",) if absent else (),
            )
        )
    return expected, diagnostics


def _target_bindings(
    catalog: registry.RegistryCatalog,
    host_bindings: registry.HostBindings,
    target_id: str,
) -> tuple[
    dict[str, str],
    list[InventoryClaim],
]:
    """Resolve semantic roles for all target and assignment bindings.

    Args:
        catalog: Authored Registry.
        host_bindings: Current-host values.
        target_id: Current target.

    Returns:
        Role-to-binding IDs and binding inventory claims.
    """
    target = catalog.targets[target_id]
    binding_ids = set(target.bindings)
    binding_ids.update(
        binding_id
        for assignment in catalog.assignments.values()
        if assignment.target == target_id
        for binding_id in assignment.bindings
    )
    roles: dict[str, str] = {}
    claims: list[InventoryClaim] = []
    adapter = adapter_for(catalog.hosts[target.host].platform, target.consumer)
    adapter_id = adapter.adapter_id if adapter is not None else "missing"
    for binding_id in sorted(binding_ids):
        declaration = catalog.bindings[binding_id]
        roles[declaration.role] = binding_id
        claims.append(
            _claim(
                claim_type=ClaimType.BINDING,
                target_id=target_id,
                kind=registry.AssetKind.BINDING,
                adapter_id=adapter_id,
                root_role=declaration.role,
                locator=None,
                namespace="host-binding",
                logical_key=declaration.role,
                desired_ownership=DesiredOwnership.ALMAGEST_MANAGED,
                presence=(
                    Presence.PRESENT
                    if binding_id in host_bindings.bindings
                    else Presence.ABSENT
                ),
                ownership=Ownership.NOT_APPLICABLE,
                readability=Readability.READABLE,
                topology=Topology.CANONICAL,
                effective=EffectiveState.ACTIVE,
                finding_codes=(
                    () if binding_id in host_bindings.bindings else ("missing",)
                ),
            )
        )
    return roles, claims


def _scan_target(
    *,
    catalog: registry.RegistryCatalog,
    host_bindings: registry.HostBindings,
    target_id: str,
    evidence: ConsumerEvidence | None,
    reader_factory: ReaderFactory,
) -> tuple[
    AdapterUse,
    list[InventoryClaim],
    list[CoverageClaim],
    list[InventoryDiagnostic],
]:
    """Scan one current-host target through its compatible adapter.

    Args:
        catalog: Authored Registry.
        host_bindings: Current-host roots.
        target_id: Target to inspect.
        evidence: Current product/version/format fact.
        reader_factory: Scoped reader constructor.

    Returns:
        Adapter use, claims, coverage, and safe diagnostics.
    """
    target = catalog.targets[target_id]
    host = catalog.hosts[target.host]
    adapter = adapter_for(host.platform, target.consumer)
    roles, binding_claims = _target_bindings(catalog, host_bindings, target_id)
    if adapter is None:
        missing = AdapterUse(
            target_id=target_id,
            adapter_id="missing",
            adapter_revision="",
            compatibility=Compatibility.UNSUPPORTED,
            product=evidence.product if evidence is not None else None,
            version=evidence.version if evidence is not None else None,
        )
        coverage = [
            _coverage(
                target_id,
                "missing",
                kind,
                None,
                f"missing.{kind}",
                Coverage.UNKNOWN,
                ("missing-adapter",),
            )
            for kind in registry.AssetKind
        ]
        return (
            missing,
            binding_claims,
            coverage,
            [
                InventoryDiagnostic(
                    code="missing-adapter",
                    scope="adapter",
                    severity="block",
                    target_id=target_id,
                )
            ],
        )
    compatibility = adapter.compatibility(evidence)
    adapter_use = AdapterUse(
        target_id=target_id,
        adapter_id=adapter.adapter_id,
        adapter_revision=adapter.revision,
        compatibility=compatibility,
        product=evidence.product if evidence is not None else None,
        version=evidence.version if evidence is not None else None,
    )
    diagnostics: list[InventoryDiagnostic] = []
    if compatibility != Compatibility.PROVEN:
        diagnostics.append(
            InventoryDiagnostic(
                code=f"adapter-{compatibility}",
                scope="adapter",
                severity=(
                    "block"
                    if compatibility
                    in {
                        Compatibility.IDENTITY_UNVERIFIED,
                        Compatibility.UNSUPPORTED,
                    }
                    else "warning"
                ),
                target_id=target_id,
            )
        )
    path_roles = {
        role
        for role, binding_id in roles.items()
        if catalog.bindings[binding_id].kind == registry.BindingKind.PATH
    }
    unknown_roles = path_roles - adapter.root_roles
    role_set = adapter.match_role_set(path_roles)
    if unknown_roles or role_set is None:
        code = "unknown-adapter-role" if unknown_roles else "missing-adapter-role"
        diagnostics.append(
            InventoryDiagnostic(
                code=code,
                scope="target",
                severity="block",
                target_id=target_id,
            )
        )
        target_coverage = [
            _coverage(
                target_id,
                adapter.adapter_id,
                kind,
                None,
                f"roles.{kind}",
                Coverage.UNKNOWN,
                (code,),
            )
            for kind in registry.AssetKind
        ]
        expected, expected_diagnostics = _expected_claims(
            catalog=catalog,
            target_id=target_id,
            adapter=adapter,
            claims=binding_claims,
            coverage=target_coverage,
        )
        return (
            adapter_use,
            [*binding_claims, *expected],
            target_coverage,
            [*diagnostics, *expected_diagnostics],
        )
    role_to_binding = {role: roles[role] for role in role_set}
    roots = {
        binding_id: Path(value.path)
        for role, binding_id in role_to_binding.items()
        if (
            (value := host_bindings.bindings[binding_id])
            and isinstance(value, registry.PathBindingValue)
        )
    }
    source_roots = tuple(Path(path) for path in host_bindings.source_roots.values())
    reader = reader_factory(roots, source_roots)
    claims = list(binding_claims)
    coverage: list[CoverageClaim] = [
        _coverage(
            target_id,
            adapter.adapter_id,
            registry.AssetKind.BINDING,
            None,
            "registry.bindings",
            Coverage.COMPLETE,
        )
    ]
    rules = [rule for rule in adapter.rules if rule.role in role_set]
    semantic = compatibility == Compatibility.PROVEN
    for rule in rules:
        rule_claims, rule_coverage = _scan_rule(
            target_id=target_id,
            adapter=adapter,
            rule=rule,
            binding_id=role_to_binding[rule.role],
            reader=reader,
            semantic=semantic,
        )
        claims.extend(rule_claims)
        coverage.append(rule_coverage)
    covered_kinds = {item.asset_kind for item in coverage}
    for kind in registry.AssetKind:
        if kind in covered_kinds:
            continue
        if kind in adapter.unsupported_kinds:
            coverage.append(
                _coverage(
                    target_id,
                    adapter.adapter_id,
                    kind,
                    None,
                    f"unsupported.{kind}",
                    Coverage.UNSUPPORTED,
                    ("consumer-domain-unsupported",),
                )
            )
        else:
            coverage.append(
                _coverage(
                    target_id,
                    adapter.adapter_id,
                    kind,
                    None,
                    f"unknown.{kind}",
                    Coverage.UNKNOWN,
                    ("missing-adapter-coverage",),
                )
            )
            diagnostics.append(
                InventoryDiagnostic(
                    code="missing-adapter-coverage",
                    scope="adapter",
                    severity="block",
                    target_id=target_id,
                )
            )
    expected, expected_diagnostics = _expected_claims(
        catalog=catalog,
        target_id=target_id,
        adapter=adapter,
        claims=claims,
        coverage=coverage,
    )
    claims.extend(expected)
    diagnostics.extend(expected_diagnostics)
    return adapter_use, claims, coverage, diagnostics


def _load_evidence(
    path: Path,
) -> tuple[ConsumerEvidenceDocument | None, InventoryDiagnostic | None]:
    """Load strict current-host consumer evidence.

    Args:
        path: Explicit host-local evidence JSON.

    Returns:
        Parsed evidence or one safe diagnostic.
    """
    try:
        raw = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (
        DuplicateJsonKeyError,
        OSError,
        UnicodeError,
        json.JSONDecodeError,
    ):
        return None, InventoryDiagnostic(
            code="invalid-consumer-evidence",
            scope="loader",
            severity="block",
        )
    try:
        return ConsumerEvidenceDocument.model_validate(raw), None
    except ValidationError:
        return None, InventoryDiagnostic(
            code="invalid-consumer-evidence",
            scope="loader",
            severity="block",
        )


def _snapshot(
    *,
    status: SnapshotStatus,
    registry_revision: str | None,
    host_id: str | None,
    platform: registry.Platform,
    adapters: list[AdapterUse] | None = None,
    claims: list[InventoryClaim] | None = None,
    coverage: list[CoverageClaim] | None = None,
    diagnostics: list[InventoryDiagnostic] | None = None,
) -> InventorySnapshot:
    """Create a deterministic snapshot and its canonical revision.

    Args:
        status: Execution status.
        registry_revision: Authored Registry revision.
        host_id: Current host.
        platform: Current platform.
        adapters: Adapter uses.
        claims: Inventory claims.
        coverage: Coverage facts.
        diagnostics: Safe diagnostics.

    Returns:
        Stable snapshot.
    """
    adapters_value = tuple(
        sorted(adapters or [], key=lambda item: (item.target_id, item.adapter_id))
    )
    claims_value = tuple(sorted(claims or [], key=lambda item: item.claim_id))
    coverage_value = tuple(sorted(coverage or [], key=lambda item: item.coverage_id))
    diagnostics_value = tuple(
        sorted(
            diagnostics or [],
            key=lambda item: (
                item.target_id or "",
                item.scope,
                item.code,
                item.severity,
            ),
        )
    )
    payload = {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "status": status,
        "registry_revision": registry_revision,
        "host_id": host_id,
        "platform": platform,
        "adapters": [item.model_dump(mode="json") for item in adapters_value],
        "claims": [item.model_dump(mode="json") for item in claims_value],
        "coverage": [item.model_dump(mode="json") for item in coverage_value],
        "diagnostics": [item.model_dump(mode="json") for item in diagnostics_value],
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return InventorySnapshot(
        status=status,
        registry_revision=registry_revision,
        inventory_revision=f"sha256:{hashlib.sha256(encoded).hexdigest()}",
        host_id=host_id,
        platform=platform,
        adapters=adapters_value,
        claims=claims_value,
        coverage=coverage_value,
        diagnostics=diagnostics_value,
    )


def scan_inventory(
    shared_paths: list[Path],
    *,
    host_bindings_path: Path,
    consumer_evidence_path: Path,
    local_paths: list[Path] | None = None,
    platform: registry.Platform | None = None,
    reader_factory: ReaderFactory | None = None,
) -> InventorySnapshot:
    """Inventory current-host targets through bounded consumer adapters.

    Args:
        shared_paths: Portable shared Registry documents.
        host_bindings_path: Current-host binding values.
        consumer_evidence_path: Current product/version/format evidence.
        local_paths: Mac-local Registry documents. Windows rejects this argument
            before any Registry, evidence, binding, or reader access.
        platform: Test-only platform override.
        reader_factory: Test-only scoped reader constructor.

    Returns:
        Stable read-only snapshot. No code path writes live configuration.
    """
    selected_platform = platform or registry.current_platform()
    local = local_paths or []
    if selected_platform == registry.Platform.WINDOWS and local:
        return _snapshot(
            status=SnapshotStatus.BLOCK,
            registry_revision=None,
            host_id=None,
            platform=selected_platform,
            diagnostics=[
                InventoryDiagnostic(
                    code="forbidden-local-layer",
                    scope="inventory",
                    severity="block",
                )
            ],
        )
    checked = registry.check_registry(
        shared_paths,
        host_bindings_path=host_bindings_path,
        local_paths=local,
        platform=selected_platform,
    )
    if not checked.ok or checked.catalog is None or checked.host_bindings is None:
        return _snapshot(
            status=SnapshotStatus.BLOCK,
            registry_revision=(
                checked.catalog.revision if checked.catalog is not None else None
            ),
            host_id=(
                checked.host_bindings.host
                if checked.host_bindings is not None
                else None
            ),
            platform=selected_platform,
            diagnostics=[
                InventoryDiagnostic(
                    code=diagnostic.code,
                    scope="inventory",
                    severity="block",
                )
                for diagnostic in checked.normalized_diagnostics
            ],
        )
    evidence_document, evidence_diagnostic = _load_evidence(consumer_evidence_path)
    if evidence_diagnostic is not None or evidence_document is None:
        return _snapshot(
            status=SnapshotStatus.BLOCK,
            registry_revision=checked.catalog.revision,
            host_id=checked.host_bindings.host,
            platform=selected_platform,
            diagnostics=[
                evidence_diagnostic
                or InventoryDiagnostic(
                    code="invalid-consumer-evidence",
                    scope="loader",
                    severity="block",
                )
            ],
        )
    factory = reader_factory or (
        lambda roots, allowed: FilesystemReader(roots, allowed_targets=allowed)
    )
    adapters: list[AdapterUse] = []
    claims: list[InventoryClaim] = []
    coverage: list[CoverageClaim] = []
    diagnostics: list[InventoryDiagnostic] = []
    target_ids = sorted(
        target_id
        for target_id, target in checked.catalog.targets.items()
        if target.host == checked.host_bindings.host
    )
    for target_id in target_ids:
        adapter_use, target_claims, target_coverage, target_diagnostics = _scan_target(
            catalog=checked.catalog,
            host_bindings=checked.host_bindings,
            target_id=target_id,
            evidence=evidence_document.consumers.get(target_id),
            reader_factory=factory,
        )
        adapters.append(adapter_use)
        claims.extend(target_claims)
        coverage.extend(target_coverage)
        diagnostics.extend(target_diagnostics)
    claims = _mark_duplicates(claims)
    if any(diagnostic.severity == "block" for diagnostic in diagnostics):
        status = SnapshotStatus.BLOCK
    elif any(
        item.coverage in {Coverage.PARTIAL, Coverage.UNKNOWN} for item in coverage
    ):
        status = SnapshotStatus.PARTIAL
    else:
        status = SnapshotStatus.PASS
    return _snapshot(
        status=status,
        registry_revision=checked.catalog.revision,
        host_id=checked.host_bindings.host,
        platform=selected_platform,
        adapters=adapters,
        claims=claims,
        coverage=coverage,
        diagnostics=diagnostics,
    )


def adapter_report() -> dict[str, object]:
    """Return deterministic built-in adapter compatibility metadata.

    Returns:
        Machine-facing descriptors without host paths or live values.
    """
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "adapters": [
            {
                "adapter_id": adapter.adapter_id,
                "adapter_revision": adapter.revision,
                "platform": adapter.platform,
                "consumer": adapter.consumer,
                "product": adapter.product,
                "format_fingerprint": adapter.format_fingerprint,
                "fixture_version_prefixes": adapter.fixture_version_prefixes,
                "required_role_sets": [
                    sorted(role_set) for role_set in adapter.required_role_sets
                ],
                "coverage": sorted(
                    {
                        *(rule.kind for rule in adapter.rules),
                        registry.AssetKind.BINDING,
                        *adapter.unsupported_kinds,
                    }
                ),
            }
            for adapter in sorted(ADAPTERS, key=lambda item: item.adapter_id)
        ],
    }
