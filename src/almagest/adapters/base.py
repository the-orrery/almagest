"""Consumer-neutral contracts for read-only configuration adapters."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from almagest.registry import AssetKind, Consumer, Platform


class StrictModel(BaseModel):
    """Reject unknown evidence fields so compatibility fails closed."""

    model_config = ConfigDict(extra="forbid")


class Compatibility(StrEnum):
    """Relationship between one live consumer fact and an adapter fixture."""

    PROVEN = "proven"
    HOST_UNVERIFIED = "host-unverified"
    VERSION_UNVERIFIED = "version-unverified"
    IDENTITY_UNVERIFIED = "identity-unverified"
    UNSUPPORTED = "unsupported"


class EvidenceSource(StrEnum):
    """How an operator obtained a current-host consumer fact."""

    CONSUMER_CLI = "consumer-cli"
    CONSUMER_DOCTOR = "consumer-doctor"
    OPERATOR = "operator"
    FIXTURE = "fixture"


class ConsumerEvidence(StrictModel):
    """Non-authoritative evidence about one installed consumer."""

    product: str = Field(min_length=1)
    version: str = Field(min_length=1)
    format_fingerprint: str = Field(min_length=1)
    evidence_source: EvidenceSource
    host_verified: bool = False


class SurfaceMode(StrEnum):
    """Bounded read shape for one adapter surface."""

    ROOT = "root"
    FILE = "file"
    DIRECTORY = "directory"
    GLOB = "glob"
    JSON_MAP = "json-map"
    TOML_TABLE = "toml-table"


@dataclass(frozen=True)
class SurfaceRule:
    """Describe one exact, bounded consumer configuration surface."""

    surface_id: str
    kind: AssetKind
    role: str
    relative_path: str
    mode: SurfaceMode
    namespace: str
    selector: tuple[str, ...] = ()
    pattern: str | None = None
    precedence: int | None = None
    default_ownership: str = "unknown-owner"
    external_names: tuple[str, ...] = ()
    required_frontmatter: tuple[str, ...] = ()


@dataclass(frozen=True)
class AdapterDescriptor:
    """Freeze compatibility and bounded root/format behavior for one consumer."""

    adapter_id: str
    platform: Platform
    consumer: Consumer
    product: str
    format_fingerprint: str
    fixture_version_prefixes: tuple[str, ...]
    required_role_sets: tuple[frozenset[str], ...]
    rules: tuple[SurfaceRule, ...]
    unsupported_kinds: frozenset[AssetKind] = frozenset()

    @property
    def revision(self) -> str:
        """Return a stable revision for the adapter contract.

        Returns:
            A SHA-256 identifier over compatibility, roles, and surface rules.
        """
        payload = {
            "adapter_id": self.adapter_id,
            "platform": self.platform,
            "consumer": self.consumer,
            "product": self.product,
            "format_fingerprint": self.format_fingerprint,
            "fixture_version_prefixes": self.fixture_version_prefixes,
            "required_role_sets": [
                sorted(role_set) for role_set in self.required_role_sets
            ],
            "rules": [
                {
                    "surface_id": rule.surface_id,
                    "kind": rule.kind,
                    "role": rule.role,
                    "relative_path": rule.relative_path,
                    "mode": rule.mode,
                    "namespace": rule.namespace,
                    "selector": rule.selector,
                    "pattern": rule.pattern,
                    "precedence": rule.precedence,
                    "default_ownership": rule.default_ownership,
                    "external_names": rule.external_names,
                    "required_frontmatter": rule.required_frontmatter,
                }
                for rule in self.rules
            ],
            "unsupported_kinds": sorted(self.unsupported_kinds),
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    @property
    def root_roles(self) -> frozenset[str]:
        """Return every path role this adapter understands.

        Returns:
            Role names used by at least one bounded surface rule.
        """
        return frozenset(rule.role for rule in self.rules)

    def compatibility(
        self,
        evidence: ConsumerEvidence | None,
    ) -> Compatibility:
        """Classify current-host evidence against the frozen fixture contract.

        Args:
            evidence: Operator-supplied live product/version/format evidence.

        Returns:
            A fail-closed compatibility state. Fixture evidence never proves a
            live host.
        """
        if evidence is None:
            return Compatibility.IDENTITY_UNVERIFIED
        if evidence.product != self.product:
            return Compatibility.UNSUPPORTED
        if evidence.format_fingerprint != self.format_fingerprint:
            return Compatibility.UNSUPPORTED
        if not any(
            evidence.version.startswith(prefix)
            for prefix in self.fixture_version_prefixes
        ):
            return Compatibility.VERSION_UNVERIFIED
        if (
            not evidence.host_verified
            or evidence.evidence_source == EvidenceSource.FIXTURE
        ):
            return Compatibility.HOST_UNVERIFIED
        return Compatibility.PROVEN

    def match_role_set(self, roles: set[str]) -> frozenset[str] | None:
        """Select one unambiguous required role set for a target.

        Args:
            roles: Path binding roles attached to the target.

        Returns:
            The single matching role set, or ``None`` when missing/ambiguous.
        """
        matches = [
            role_set for role_set in self.required_role_sets if role_set.issubset(roles)
        ]
        return matches[0] if len(matches) == 1 else None
